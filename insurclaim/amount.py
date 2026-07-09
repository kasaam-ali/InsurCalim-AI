"""Claim amount assessment (quantum analysis).

Estimates a fair, reasonable settlement/repair cost for the damage and injuries a
claim actually describes, then judges whether the amount the claimant is demanding is
justified. This answers the "even if it is not fraud, is the money they are asking for
reasonable - and if not, how much should it be?" question for a human adjuster.

Grounded only in what the claim file describes; degrades gracefully when the LLM is
unavailable.
"""

from __future__ import annotations

from typing import Any

from insurclaim.coverage import _selected_policy_text
from insurclaim.llm import call_llm_json

AMOUNT_SYSTEM = """
You are a motor-insurance claims cost assessor (a quantum analyst). You are given a
claim file (all documents concatenated) and, when known, the amount the claimant is
demanding. Estimate a fair, reasonable settlement for the vehicle damage and any
injuries the claim actually describes, then judge whether the demanded amount is
justified.

Base every number ONLY on what the claim describes (vehicle, parts damaged, repairs,
medical treatment, region). If a policy excerpt is provided, respect any stated
sum-insured limit, sub-limits, or deductible. If the file lacks enough detail to
estimate a fair amount, say so instead of guessing.

Return strict JSON:
{
  "currency": "PKR",
  "claimed_amount": number | null,
  "fair_estimate": number | null,
  "fair_low": number | null,
  "fair_high": number | null,
  "verdict": "reasonable" | "overstated" | "understated" | "insufficient_info",
  "line_items": [{"item": "...", "estimate": number}],
  "rationale": "one or two sentences explaining the estimate and the verdict"
}
Verdict rules:
- "reasonable": the demanded amount is within, or close to, the fair range.
- "overstated": the demanded amount is materially above the fair range (possible inflation).
- "understated": the demanded amount is below the fair range.
- "insufficient_info": there is not enough detail to estimate a fair amount.
Infer "currency" from the file (e.g. PKR, USD); default to PKR if unclear.
Return ONLY the JSON object.
"""


def assess_amount(
    claim_text: str,
    claimed_amount: float | int | None = None,
    doc_ids: list[int] | None = None,
) -> dict[str, Any] | None:
    """Estimate a fair claim amount and judge the demanded amount against it.

    Returns None when there is no claim text to assess. On LLM failure returns a
    minimal "insufficient_info" result so the caller can still render a graceful note.
    """
    if not claim_text or not claim_text.strip():
        return None

    policy_text = _selected_policy_text(doc_ids)
    known = (
        f"\n\nThe claimant is demanding: {claimed_amount}"
        if claimed_amount not in (None, "")
        else ""
    )
    prompt = (
        f"POLICY EXCERPT (for limits / deductible, may be empty):\n"
        f"{policy_text or '(none provided)'}\n\n"
        f"CLAIM FILE:\n{claim_text[:24000]}{known}"
    )

    try:
        result = call_llm_json(prompt=prompt, system=AMOUNT_SYSTEM, reasoning=True)
    except Exception:
        return {
            "currency": "PKR",
            "claimed_amount": claimed_amount,
            "fair_estimate": None,
            "fair_low": None,
            "fair_high": None,
            "verdict": "insufficient_info",
            "line_items": [],
            "rationale": "Cost-assessment model unavailable.",
        }

    # Normalise the shape so the UI / report can rely on it.
    result.setdefault("currency", "PKR")
    result.setdefault("fair_estimate", None)
    result.setdefault("fair_low", None)
    result.setdefault("fair_high", None)
    result.setdefault("verdict", "insufficient_info")
    result.setdefault("line_items", [])
    result.setdefault("rationale", "")
    # Fall back to the amount we extracted upstream if the model did not surface one.
    if result.get("claimed_amount") in (None, "") and claimed_amount not in (None, ""):
        result["claimed_amount"] = claimed_amount
    return result
