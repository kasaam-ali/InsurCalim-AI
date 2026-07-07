"""Intake & Extraction agent.

Turns raw claim inputs (FNOL text, police report text, and - later - damage
photos) into a single structured claim dictionary. When the claim is already
loaded from the database, this agent simply normalizes it; when raw text is
provided, it uses the cheap Claude model to extract the structured fields.

Every agent is a plain function that takes the shared pipeline state (a dict)
and returns the keys it wants to add to that state.
"""

from __future__ import annotations

from typing import Any

from insurclaim.llm import call_llm_json

EXTRACTION_SYSTEM = """
You extract structured data from an auto-insurance claim. Return strict JSON with:
  incident_date (YYYY-MM-DD), report_date (YYYY-MM-DD), location (string),
  description (string), claimed_amount (number),
  parties (list of {full_name, role}), vehicles (list of {vin, make, model}).
Return ONLY the JSON object.
"""


def _extract_from_text(raw_text: str) -> dict[str, Any]:
    """Use the cheap extraction model to structure free-text claim documents.

    Falls back to a minimal structure built from the raw text when every LLM
    provider is unavailable (e.g. all keys rate-limited), so the pipeline degrades
    gracefully instead of crashing - the local ML + RAG fraud layers still run.
    """
    try:
        return call_llm_json(prompt=raw_text, system=EXTRACTION_SYSTEM, reasoning=False)
    except Exception:
        return {
            "incident_date": None,
            "report_date": None,
            "location": "",
            "description": raw_text[:4000],
            "claimed_amount": None,
            "parties": [],
            "vehicles": [],
            "_extraction_degraded": True,
        }


def run(state: dict[str, Any]) -> dict[str, Any]:
    """Produce the 'extracted' claim structure for the rest of the pipeline."""
    claim = state.get("claim")
    raw_text = state.get("raw_documents")

    if raw_text:
        extracted = _extract_from_text(raw_text)
    elif claim:
        # Already structured in the database; pass the relevant fields through.
        extracted = {
            "incident_date": claim.get("incident_date"),
            "report_date": claim.get("report_date"),
            "location": claim.get("location"),
            "description": claim.get("description"),
            "claimed_amount": claim.get("claimed_amount"),
            "parties": claim.get("parties", []),
            "vehicles": claim.get("vehicles", []),
        }
    else:
        raise ValueError("Intake agent needs either 'claim' or 'raw_documents' in state.")

    return {"extracted": extracted}
