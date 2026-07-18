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
from insurclaim.llm import call_llm_json, search_web

AMOUNT_SYSTEM = """
You are a motor-insurance claims cost assessor (a quantum analyst) working in the
PAKISTANI market. You are given a claim file (all documents concatenated) and, when
known, the amount the claimant is demanding. Estimate a fair, reasonable settlement for
the vehicle damage and any injuries the claim actually describes, then judge whether the
demanded amount is justified.

This is an ESTIMATE to help a human adjuster, not a final settlement figure.

Base every number on what the claim describes (vehicle, parts damaged, repairs,
medical treatment, region). If a MARKET PRICE RESEARCH block is provided, it contains
current real-world prices found via live web search - base each line-item estimate on
those live prices rather than your own guess, and set "priced_from" to "market". For
each line item, put WHERE the price came from (the marketplace / workshop / source
name) in its "source" field. If no market research is provided, estimate from your own
knowledge, set "priced_from" to "model_estimate", and set each "source" to
"model estimate". If a policy excerpt is provided, respect any stated sum-insured
limit, sub-limits, or deductible. If the file lacks enough detail to estimate a fair
amount, say so instead of guessing.

CURRENCY RULE (strict): price everything in Pakistani Rupees (PKR). If any market
figure is found in another currency (USD, INR, etc.), CONVERT it to PKR before using
it. "currency" must be "PKR" unless the claim file clearly states the incident happened
in another country, in which case use that country's currency.

Return strict JSON:
{
  "currency": "PKR",
  "claimed_amount": number | null,
  "fair_estimate": number | null,
  "fair_low": number | null,
  "fair_high": number | null,
  "verdict": "reasonable" | "overstated" | "understated" | "insufficient_info",
  "priced_from": "market" | "model_estimate",
  "line_items": [{"item": "...", "estimate": number, "source": "..."}],
  "rationale": "one or two sentences explaining the estimate and the verdict"
}
Verdict rules:
- "reasonable": the demanded amount is within, or close to, the fair range.
- "overstated": the demanded amount is materially above the fair range (possible inflation).
- "understated": the demanded amount is below the fair range.
- "insufficient_info": there is not enough detail to estimate a fair amount.
Return ONLY the JSON object.
"""

PARTS_RESEARCH_PROMPT = """
You are a vehicle parts-price researcher working in the PAKISTANI market. From the
claim file below, identify the vehicle (make, model, year if stated) and every damaged
part or required repair. Then search the web for the CURRENT market price of each part
and the typical labour cost in Pakistan. Assume the Pakistani market and price in PKR
unless the claim clearly states the incident happened in another country. If you find a
price quoted in another currency (USD, INR, etc.), convert it to PKR.

Return a concise plain-text list, one line per item. Each line MUST end with a source
note naming where the price came from (e.g. PakWheels, OLX Pakistan, a local workshop
rate, a parts-dealer listing):
  <part / repair> - PKR <price or price range> - <source name>
Include a labour line if relevant. Do not add commentary beyond the list.

CLAIM FILE:
{claim_text}
"""


def _research_parts_prices(claim_text: str) -> str:
    """Find live market prices for the claim's damaged parts via web search.

    Returns grounded plain-text price findings, or an empty string if the search
    is unavailable so the caller can fall back to a knowledge-only estimate.
    """
    try:
        return search_web(PARTS_RESEARCH_PROMPT.format(claim_text=claim_text[:12000]))
    except Exception:
        return ""


def assess_amount(
    claim_text: str,
    claimed_amount: float | int | None = None,
    doc_ids: list[int] | None = None,
    use_web: bool = True,
) -> dict[str, Any] | None:
    """Estimate a fair claim amount and judge the demanded amount against it.

    When use_web is True, first searches the web for live market prices of the damaged
    parts and grounds the estimate in them; otherwise (or if the search fails) it falls
    back to a knowledge-only estimate. Returns None when there is no claim text to
    assess. On LLM failure returns a minimal "insufficient_info" result so the caller
    can still render a graceful note.
    """
    if not claim_text or not claim_text.strip():
        return None

    policy_text = _selected_policy_text(doc_ids)
    market_text = _research_parts_prices(claim_text) if use_web else ""
    market_block = (
        f"MARKET PRICE RESEARCH (live web search):\n{market_text}\n\n" if market_text else ""
    )
    known = (
        f"\n\nThe claimant is demanding: {claimed_amount}"
        if claimed_amount not in (None, "")
        else ""
    )
    prompt = (
        f"{market_block}"
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
            "priced_from": "model_estimate",
            "line_items": [],
            "sources_text": market_text,
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
    # Reflect whether the estimate was grounded in live market prices.
    result.setdefault("priced_from", "market" if market_text else "model_estimate")
    # Ensure every line item has a "source" the UI can show (where the price came from).
    default_source = "live web search" if market_text else "model estimate"
    for li in result["line_items"]:
        if isinstance(li, dict) and not li.get("source"):
            li["source"] = default_source
    # Carry the raw market-price findings through so the UI can show the grounding /
    # references the estimate was based on.
    result["sources_text"] = market_text
    # Fall back to the amount we extracted upstream if the model did not surface one.
    if result.get("claimed_amount") in (None, "") and claimed_amount not in (None, ""):
        result["claimed_amount"] = claimed_amount
    return result
