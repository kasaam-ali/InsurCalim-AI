"""Adjudication / Report agent - the differentiator.

Synthesizes every signal into a ranked, explainable report:
  - an overall risk score
  - the top flags, most severe first, each with a confidence value
  - a short timeline summary and source citations
  - a recommended action (never an automatic denial - human-in-the-loop)

A deterministic risk score is computed in code as a safety net, so the pipeline
still produces a sensible recommendation even if the LLM call fails.
"""

from __future__ import annotations

from typing import Any

from insurclaim.llm import call_llm_json

# Severity weights used for the fallback risk score.
SEVERITY_WEIGHTS = {"low": 10, "medium": 25, "high": 40}

REPORT_SYSTEM = """
You are an insurance claim adjudicator producing an explainable report for a human
investigator. You never auto-approve or auto-deny; you only rank and recommend.
Given the signals, timeline, and ML score, return strict JSON:
{
  "risk_score": 0-100,
  "top_flags": [{"summary": "...", "evidence": "...", "confidence": 0-100}],
  "timeline_summary": "...",
  "citations": ["source field or document for each key claim"],
  "recommended_action": "route_to_investigator | fast_track_approve | request_more_info"
}
Order top_flags most severe first. Return ONLY the JSON object.
"""


def _fallback_risk_score(state: dict[str, Any]) -> int:
    """Compute a simple risk score from signals + ML probability (0-100)."""
    score = 0
    for signal in state.get("fraud_signals", []):
        score += SEVERITY_WEIGHTS.get(signal.get("severity", "low"), 10)
    probability = state.get("fraud_probability")
    if probability is not None:
        score += int(probability * 40)
    return min(score, 100)


def _action_for_score(score: int) -> str:
    """Map a risk score to a recommended action."""
    if score >= 60:
        return "route_to_investigator"
    if score <= 20:
        return "fast_track_approve"
    return "request_more_info"


def run(state: dict[str, Any]) -> dict[str, Any]:
    """Produce the final report dict."""
    fallback_score = _fallback_risk_score(state)

    payload = {
        "fraud_signals": state.get("fraud_signals", []),
        "fraud_probability": state.get("fraud_probability"),
        "fraud_reasoning": state.get("fraud_reasoning", {}),
        "timeline": state.get("timeline", {}),
    }

    try:
        report = call_llm_json(prompt=str(payload), system=REPORT_SYSTEM, reasoning=True)
    except Exception:
        # LLM unavailable: build a minimal report from deterministic data.
        report = {
            "risk_score": fallback_score,
            "top_flags": [
                {"summary": s["message"], "evidence": s["evidence"], "confidence": 60}
                for s in state.get("fraud_signals", [])
            ],
            "timeline_summary": "",
            "citations": [],
            "recommended_action": _action_for_score(fallback_score),
        }

    # Always attach the deterministic score and the ML probability for transparency.
    report.setdefault("risk_score", fallback_score)
    report["fraud_probability"] = state.get("fraud_probability")
    report.setdefault("recommended_action", _action_for_score(report["risk_score"]))

    return {"report": report}
