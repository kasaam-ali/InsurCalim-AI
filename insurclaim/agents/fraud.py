"""Fraud & Anomaly agent - a hybrid of several layers.

Layers, in order of trust:
  1. Deterministic rules (policy, coverage, velocity)         -> rules/deterministic
  2. Image checks (duplicate/reused damage photos)            -> repo photo hashes
  3. Fine-tuned ML classifier (fraud probability)             -> ml/predict
  4. Similar-past-claims retrieval (matches known fraud?)     -> vectordb/store
  5. LLM reasoning that weighs all of the above into red flags -> Claude

Numbers and policy logic come from code, never the LLM. Every signal carries an
evidence pointer so the report agent can cite it.
"""

from __future__ import annotations

from typing import Any

from insurclaim.db import repo
from insurclaim.llm import call_llm_json
from insurclaim.ml.predict import predict_fraud
from insurclaim.rules import deterministic
from insurclaim.vectordb.store import claim_store

# Similarity above this against a known-fraud claim becomes a flag. Tuned to the
# Chroma default embeddings (MiniLM), where genuine matches score ~0.3-0.5 and
# unrelated claims score near zero or negative - so 0.85 would never fire.
SIMILAR_FRAUD_THRESHOLD = 0.30

FRAUD_SYSTEM = """
You are a fraud analyst. You are given deterministic signals, an ML fraud score,
and similar past claims. Weigh them and return strict JSON:
{
  "red_flags": [{"summary": "...", "evidence": "...", "severity": "low|medium|high"}],
  "narrative": "one-paragraph explanation for a human investigator"
}
Do not invent numbers; rely on the signals provided. Return ONLY the JSON object.
"""


def _duplicate_photo_signals(claim: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag stored photo hashes that also appear on other claims."""
    signals: list[dict[str, Any]] = []
    claim_id = claim.get("id")
    for photo in claim.get("photos", []):
        matches = repo.find_duplicate_photos(photo["phash"], exclude_claim_id=claim_id)
        if matches:
            other = matches[0]
            signals.append(
                {
                    "code": "duplicate_photo",
                    "message": "A damage photo on this claim is reused from another claim.",
                    "evidence": f"phash={photo['phash']}, also on claim_id={other['claim_id']}",
                    "severity": "high",
                }
            )
    return signals


def _similar_claim_signals(description: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (signals, raw_matches) from similar prior claims."""
    matches = claim_store().similar_claims(description, n_results=3)
    signals: list[dict[str, Any]] = []
    for match in matches:
        metadata = match.get("metadata", {})
        if metadata.get("is_fraud") and match["similarity"] >= SIMILAR_FRAUD_THRESHOLD:
            signals.append(
                {
                    "code": "similar_to_known_fraud",
                    "message": "Claim closely matches a prior known-fraud claim.",
                    "evidence": (
                        f"{int(match['similarity'] * 100)}% match to "
                        f"claim {metadata.get('claim_id')} ({metadata.get('fraud_type')})"
                    ),
                    "severity": "high",
                }
            )
    return signals, matches


def run(state: dict[str, Any]) -> dict[str, Any]:
    """Collect signals from every layer and let the LLM weigh them."""
    claim = state.get("claim", {})
    extracted = state.get("extracted", {})
    description = extracted.get("description", "")
    events = state.get("timeline", {}).get("events", [])

    # 1. Deterministic rules + timeline physics signals.
    signals: list[dict[str, Any]] = deterministic.run_all(claim, events)
    signals.extend(state.get("timeline_signals", []))

    # 2. Duplicate-photo checks.
    signals.extend(_duplicate_photo_signals(claim))

    # 3. Fine-tuned ML fraud probability (None if model not trained yet).
    fraud_probability = predict_fraud(description) if description else None

    # 4. Similar past claims (RAG).
    try:
        similar_signals, similar_matches = _similar_claim_signals(description)
        signals.extend(similar_signals)
    except Exception:  # vector store may be empty / unavailable
        similar_matches = []

    # 5. LLM reasoning over everything.
    llm_input = {
        "deterministic_signals": signals,
        "ml_fraud_probability": fraud_probability,
        "similar_claims": [
            {"similarity": m["similarity"], "metadata": m["metadata"]} for m in similar_matches
        ],
    }
    try:
        reasoning = call_llm_json(
            prompt=str(llm_input), system=FRAUD_SYSTEM, reasoning=True
        )
    except Exception:
        reasoning = {"red_flags": [], "narrative": ""}

    return {
        "fraud_signals": signals,
        "fraud_probability": fraud_probability,
        "similar_claims": similar_matches,
        "fraud_reasoning": reasoning,
    }
