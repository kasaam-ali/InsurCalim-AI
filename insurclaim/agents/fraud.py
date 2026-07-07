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

# Cap on how much of the full claim file we send to the narrative analysis, to
# stay within model context while still covering the key documents.
MAX_FRAUD_TEXT = 30000

NARRATIVE_FRAUD_SYSTEM = """
You are an experienced auto-insurance fraud investigator. Read the FULL claim file
below (all submitted documents: claim form, police report, medical report, repair
estimate, invoice, surveyor report, photo metadata, etc.) and identify concrete
fraud indicators that are SUPPORTED by the text. Cross-check the documents against
each other. Look especially for:
- location / GPS inconsistencies (e.g. photos taken away from the stated incident site)
- timeline contradictions or long unexplained delays (late FIR/report, photos taken
  hours after the incident)
- physically implausible damage (e.g. a crushed panel next to an undamaged tyre,
  shattered glass with no debris, clean tool-strike patterns, airbags deployed with
  no injury/medical record)
- damage patterns inconsistent with the described accident (e.g. only one side
  damaged after a multi-impact swerve)
- repeat or duplicate claims on the same vehicle / party
- inflated or inconsistent repair costs versus the actual damage
- missing expected evidence, untraceable third parties, non-authorized workshops,
  or pressure for a fast settlement

Only report indicators you can justify from the text; do NOT invent facts. If the
file is internally consistent and looks genuine, return an empty list. Be calibrated:
reserve "high" for strong, clearly-evidenced fraud indicators.

Return strict JSON:
{"red_flags": [{"summary": "...", "evidence": "specific detail or quote from the file",
                "severity": "low|medium|high"}]}
Return ONLY the JSON object.
"""


def _narrative_red_flags(full_text: str) -> list[dict[str, Any]]:
    """LLM layer: read the whole claim file and surface grounded fraud red flags.

    Turns each red flag into a fraud signal so it feeds the risk score and report.
    Returns an empty list when there is no text or the model is unavailable.
    """
    if not full_text or not full_text.strip():
        return []
    try:
        result = call_llm_json(
            prompt=full_text[:MAX_FRAUD_TEXT],
            system=NARRATIVE_FRAUD_SYSTEM,
            reasoning=True,
        )
    except Exception:
        return []

    flags = result.get("red_flags", []) if isinstance(result, dict) else []
    signals: list[dict[str, Any]] = []
    for flag in flags:
        if not isinstance(flag, dict) or not flag.get("summary"):
            continue
        severity = flag.get("severity", "medium")
        if severity not in ("low", "medium", "high"):
            severity = "medium"
        signals.append(
            {
                "code": "narrative_red_flag",
                "message": flag.get("summary", ""),
                "evidence": flag.get("evidence", ""),
                "severity": severity,
            }
        )
    return signals


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


def _similar_claim_signals(
    description: str, exclude_claim_id: int | None = None
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (signals, raw_matches) from similar prior claims.

    exclude_claim_id drops the claim being scored from its own results, so an
    already-indexed claim does not match itself at 100%.
    """
    matches = claim_store().similar_claims(description, n_results=4)
    matches = [
        m for m in matches if m.get("metadata", {}).get("claim_id") != exclude_claim_id
    ][:3]
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
    # The full claim file (all uploaded documents) when available, so the LLM can
    # cross-check documents; falls back to the extracted description for DB claims.
    full_text = state.get("raw_documents") or description
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
        similar_signals, similar_matches = _similar_claim_signals(
            description, exclude_claim_id=claim.get("id")
        )
        signals.extend(similar_signals)
    except Exception:  # vector store may be empty / unavailable
        similar_matches = []

    # 5. Narrative fraud analysis over the full document file (grounded red flags).
    signals.extend(_narrative_red_flags(full_text))

    # 6. LLM reasoning over everything.
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
