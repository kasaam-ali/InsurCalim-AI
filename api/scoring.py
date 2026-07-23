"""Fast portfolio scoring + analytics for the dashboard's data sections.

Ports the Streamlit ``score_all`` / ``page_analytics`` / ``detect_rings`` /
``_render_investigation`` logic (frontend/app.py) into the API layer, without
importing the Streamlit module (which runs ``st.set_page_config`` on import).
The scored portfolio is cached in-process; only the first request pays the cost.
"""

from __future__ import annotations

import threading
from collections import Counter, defaultdict
from typing import Any

RISK_HIGH = 60
RISK_MEDIUM = 30
# Reason-code weights, matching the fallback risk score (agents/report.py).
SEVERITY_PTS = {"low": 10, "medium": 25, "high": 40}

_CACHE: list[dict[str, Any]] | None = None
_LOCK = threading.Lock()


def band(score: float) -> str:
    if score >= RISK_HIGH:
        return "HIGH"
    if score >= RISK_MEDIUM:
        return "MEDIUM"
    return "LOW"


def recommended_action(score: float) -> str:
    if score >= RISK_HIGH:
        return "route_to_investigator"
    if score < RISK_MEDIUM:
        return "fast_track_approve"
    return "request_more_info"


def invalidate() -> None:
    """Drop the cache (e.g. after a policy changes)."""
    global _CACHE
    with _LOCK:
        _CACHE = None


def score_all(force: bool = False) -> list[dict[str, Any]]:
    """Score every labeled claim once and cache the full result."""
    global _CACHE
    if _CACHE is not None and not force:
        return _CACHE
    with _LOCK:
        if _CACHE is not None and not force:
            return _CACHE

        from insurclaim.db import repo
        from insurclaim.agents.fraud import _duplicate_photo_signals, _similar_claim_signals
        from insurclaim.agents.report import _fallback_risk_score
        from insurclaim.ml.predict import predict_fraud
        from insurclaim.rules import deterministic

        scored: list[dict[str, Any]] = []
        for base in repo.list_labeled_claims():
            claim = repo.get_claim(base["id"])
            desc = claim.get("description") or ""
            signals = deterministic.run_all(claim, [])
            signals += _duplicate_photo_signals(claim)
            matches: list[dict[str, Any]] = []
            try:
                sim_sigs, matches = _similar_claim_signals(desc, exclude_claim_id=claim["id"])
                signals += sim_sigs
            except Exception:
                matches = []
            prob = predict_fraud(desc)
            score = _fallback_risk_score({"fraud_signals": signals, "fraud_probability": prob})
            scored.append({
                "id": claim["id"],
                "fraud_type": base.get("fraud_type") or "legit",
                "is_fraud": bool(base.get("is_fraud")),
                "risk": score,
                "band": band(score),
                "prob": prob,
                "signals": signals,
                "matches": matches,
                "signal_count": len(signals),
                "description": desc,
                "location": claim.get("location") or "",
                "amount": claim.get("claimed_amount"),
                "incident_date": str(claim.get("incident_date")) if claim.get("incident_date") else None,
            })
        _CACHE = scored
        return scored


def _row(s: dict[str, Any]) -> dict[str, Any]:
    """List-friendly projection of a scored claim (no heavy nested data)."""
    return {
        "id": s["id"],
        "fraud_type": s["fraud_type"],
        "is_fraud": s["is_fraud"],
        "risk": s["risk"],
        "band": s["band"],
        "signals": s["signal_count"],
        "description": s["description"],
        "location": s["location"],
        "amount": s["amount"],
    }


def claims_list() -> list[dict[str, Any]]:
    """Claims sorted most-risky first (list-friendly fields only)."""
    return sorted((_row(s) for s in score_all()), key=lambda s: -s["risk"])


def claim_detail(claim_id: int) -> dict[str, Any] | None:
    """Full investigation detail for one claim: flags, reason codes, similar claims."""
    match = next((s for s in score_all() if s["id"] == claim_id), None)
    if match is None:
        return None

    flags = [
        {
            "severity": sig.get("severity", "low"),
            "code": sig.get("code", "signal"),
            "message": sig.get("message", ""),
            "evidence": sig.get("evidence", ""),
        }
        for sig in match["signals"]
    ]

    # Reason codes: what added up to the score (mirrors _render_investigation).
    reason_codes = [
        {"code": sig.get("code", "signal"), "points": SEVERITY_PTS.get(sig.get("severity"), 10)}
        for sig in match["signals"]
    ]
    if match["prob"] is not None:
        reason_codes.append({"code": "ml_fraud_probability", "points": int(match["prob"] * 40)})

    similar = []
    for m in match["matches"]:
        md = m.get("metadata", {}) or {}
        similar.append({
            "claim_id": md.get("claim_id"),
            "is_fraud": bool(md.get("is_fraud")),
            "similarity": round(float(m.get("similarity", 0)), 3),
            "fraud_type": md.get("fraud_type"),
        })

    return {
        "id": match["id"],
        "fraud_type": match["fraud_type"],
        "is_fraud": match["is_fraud"],
        "risk": match["risk"],
        "band": match["band"],
        "prob": match["prob"],
        "recommended_action": recommended_action(match["risk"]),
        "description": match["description"],
        "location": match["location"],
        "amount": match["amount"],
        "flags": flags,
        "reason_codes": reason_codes,
        "similar_claims": similar,
    }


def portfolio_stats() -> dict[str, Any]:
    """Aggregate KPIs for the Overview section."""
    scored = score_all()
    total = len(scored)
    high = sum(1 for s in scored if s["band"] == "HIGH")
    medium = sum(1 for s in scored if s["band"] == "MEDIUM")
    low = sum(1 for s in scored if s["band"] == "LOW")
    fraud = sum(1 for s in scored if s["is_fraud"])
    avg = sum(s["risk"] for s in scored) / total if total else 0
    money_at_risk = sum(float(s["amount"] or 0) for s in scored if s["band"] == "HIGH")
    fast_trackable = sum(1 for s in scored if s["risk"] < RISK_MEDIUM)
    fraud_types = Counter(s["fraud_type"] for s in scored if s["is_fraud"])
    rings, _adj = _rings(scored)

    return {
        "total": total,
        "high": high,
        "medium": medium,
        "low": low,
        "fraud": fraud,
        "avg_score": round(avg, 1),
        "money_at_risk": round(money_at_risk),
        "fast_trackable": fast_trackable,
        "rings": len(rings),
        "risk_bands": {"HIGH": high, "MEDIUM": medium, "LOW": low},
        "fraud_types": dict(fraud_types.most_common()),
    }


def _monthly_series(scored: list[dict[str, Any]]) -> dict[str, Any]:
    """Real per-metric monthly series (for the trend chart + KPI sparklines)."""
    months = sorted({str(s["incident_date"])[:7] for s in scored if s.get("incident_date")})
    claims = {m: 0 for m in months}
    high = {m: 0 for m in months}
    fraud = {m: 0 for m in months}
    money = {m: 0.0 for m in months}
    risk_total = {m: 0.0 for m in months}
    for s in scored:
        if not s.get("incident_date"):
            continue
        m = str(s["incident_date"])[:7]
        claims[m] += 1
        risk_total[m] += float(s["risk"] or 0)
        if s["band"] == "HIGH":
            high[m] += 1
            money[m] += float(s["amount"] or 0)
        if s["is_fraud"]:
            fraud[m] += 1
    return {
        "months": months,
        "claims": [claims[m] for m in months],
        "high": [high[m] for m in months],
        "fraud": [fraud[m] for m in months],
        "money": [round(money[m]) for m in months],
        # Mean risk score per month, so the Avg-risk KPI has its own real trend.
        "risk": [round(risk_total[m] / claims[m], 1) if claims[m] else 0 for m in months],
    }


def analytics() -> dict[str, Any]:
    """Chart-ready aggregates for the Analytics + Overview sections."""
    scored = score_all()
    months: Counter = Counter()
    for s in scored:
        if s.get("incident_date"):
            months[str(s["incident_date"])[:7]] += 1
    bands = Counter(s["band"] for s in scored)
    fraud_types = Counter(s["fraud_type"] for s in scored if s["is_fraud"])

    sums: dict[str, list[float]] = defaultdict(list)
    for s in scored:
        if s.get("amount"):
            sums[s["band"]].append(float(s["amount"]))
    avg_by_band = {
        b: round(sum(sums[b]) / len(sums[b])) if sums.get(b) else 0
        for b in ["HIGH", "MEDIUM", "LOW"]
    }

    return {
        "claims_per_month": [{"month": m, "claims": months[m]} for m in sorted(months)],
        "risk_bands": {b: bands.get(b, 0) for b in ["HIGH", "MEDIUM", "LOW"]},
        "fraud_types": dict(fraud_types.most_common()),
        "avg_claimed_by_band": avg_by_band,
        "series": _monthly_series(scored),
    }


def _rings(scored: list[dict[str, Any]]) -> tuple[list[list[int]], dict[int, list[int]]]:
    """Connected components (size >= 3) of RAG-linked fraud claims (detect_rings)."""
    ids = {s["id"] for s in scored}
    adj: dict[int, set] = defaultdict(set)
    for s in scored:
        if not s["is_fraud"]:
            continue
        for m in s["matches"]:
            md = m.get("metadata", {}) or {}
            other = md.get("claim_id")
            if md.get("is_fraud") and m.get("similarity", 0) >= 0.40 and other in ids:
                adj[s["id"]].add(other)
                adj[other].add(s["id"])
    seen: set[int] = set()
    rings: list[list[int]] = []
    for node in list(adj):
        if node in seen:
            continue
        stack, comp = [node], set()
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            comp.add(n)
            stack.extend(adj[n] - seen)
        if len(comp) >= 3:
            rings.append(sorted(comp))
    rings.sort(key=len, reverse=True)
    return rings, {k: sorted(v) for k, v in adj.items()}


def fraud_rings() -> dict[str, Any]:
    """Fraud rings for the Fraud-rings section: member details + edges."""
    scored = score_all()
    by_id = {s["id"]: s for s in scored}
    rings, adj = _rings(scored)

    out_rings = []
    for members in rings:
        nodes = [
            {
                "id": mid,
                "fraud_type": by_id[mid]["fraud_type"] if mid in by_id else "?",
                "risk": by_id[mid]["risk"] if mid in by_id else 0,
                "location": by_id[mid]["location"] if mid in by_id else "",
            }
            for mid in members
        ]
        edges = []
        mset = set(members)
        for a in members:
            for b in adj.get(a, []):
                if b in mset and a < b:
                    edges.append([a, b])
        out_rings.append({"members": nodes, "edges": edges, "size": len(members)})

    return {"rings": out_rings, "count": len(out_rings)}
