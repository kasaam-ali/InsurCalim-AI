"""Claimant overview assembly.

Builds a single consolidated view of a claimant and their claim from data the
pipeline has already produced (extracted fields, the report, and the document
completeness check). This powers the "Claimant overview" section, which shows a
profile, a plain-language summary, a document checklist, and a quick risk snapshot
right after a claim's documents are uploaded.

Deterministic and dependency-light: it reads existing structured data and makes no
LLM call, so the same claim always yields the same overview.
"""

from __future__ import annotations

from typing import Any

# Roles that identify the person making the claim, in priority order.
_CLAIMANT_ROLE_HINTS = ("insured", "policyholder", "policy holder", "claimant", "driver")


def _pick_claimant(parties: list[dict]) -> str:
    """Choose the claimant's name from the extracted parties list."""
    for hint in _CLAIMANT_ROLE_HINTS:
        for p in parties:
            if hint in str(p.get("role", "")).lower() and p.get("full_name"):
                return str(p["full_name"])
    for p in parties:
        if p.get("full_name"):
            return str(p["full_name"])
    return "Unknown claimant"


def _format_vehicle(vehicles: list[dict]) -> str:
    """Format the first vehicle as 'Make Model (VIN ...)', omitting empty parts."""
    if not vehicles:
        return "-"
    v = vehicles[0]
    name = " ".join(str(v.get(k, "")).strip() for k in ("make", "model")).strip()
    vin = str(v.get("vin", "")).strip()
    if name and vin:
        return f"{name} (VIN {vin})"
    return name or (f"VIN {vin}" if vin else "-")


def build_overview(
    extracted: dict[str, Any] | None,
    report: dict[str, Any] | None = None,
    documents: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble a normalized claimant-overview dict from already-extracted data.

    Every field is defaulted so the UI can rely on the shape even when the pipeline
    ran in a degraded mode and some inputs are missing.
    """
    extracted = extracted or {}
    report = report or {}
    parties = extracted.get("parties") or []

    # Prefer the report's AI-generated summary; fall back to the raw description so
    # there is always something readable, without spending another LLM call.
    summary = (report.get("timeline_summary") or "").strip()
    if not summary:
        summary = (extracted.get("description") or "").strip()[:400]
    if not summary:
        summary = "No summary available for this claim yet."

    return {
        "claimant": _pick_claimant(parties),
        "parties": [
            {"full_name": p.get("full_name") or "-", "role": p.get("role") or "-"}
            for p in parties
        ],
        "vehicle": _format_vehicle(extracted.get("vehicles") or []),
        "incident_date": extracted.get("incident_date") or "-",
        "report_date": extracted.get("report_date") or "-",
        "location": extracted.get("location") or "-",
        "claimed_amount": extracted.get("claimed_amount"),
        "summary": summary,
        "risk_score": float(report.get("risk_score", 0) or 0),
        "recommended_action": report.get("recommended_action") or "-",
        "documents": documents or {},
    }
