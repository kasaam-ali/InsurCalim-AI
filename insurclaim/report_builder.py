"""Build a detailed investigation report and render it to PDF.

Takes the pipeline's final state and produces a structured, human-readable
report: risk summary, coverage, the ordered event timeline, the points that
require verification ("what we're suspicious about"), flags, and similar
known-fraud matches. to_pdf() renders a 1-2 page PDF an adjuster can file.
"""

from __future__ import annotations

from typing import Any


def build_detailed(state: dict[str, Any], coverage: dict | None = None) -> dict[str, Any]:
    """Assemble a detailed report dict from the pipeline final state."""
    report = state.get("report", {}) or {}
    timeline = state.get("timeline", {}) or {}
    reasoning = state.get("fraud_reasoning", {}) or {}
    signals = state.get("fraud_signals", []) or []
    similar = state.get("similar_claims", []) or []

    flags = report.get("top_flags") or [
        {"summary": s.get("message"), "evidence": s.get("evidence"), "confidence": ""}
        for s in signals
    ]

    # Points requiring verification — the "what we're suspicious about" section.
    verify: list[dict] = []
    for inc in timeline.get("inconsistencies", []):
        verify.append(
            {
                "point": inc.get("description", ""),
                "why": inc.get("evidence", ""),
                "action": "Cross-check the narrative against the supporting documents.",
            }
        )
    for gap in timeline.get("gaps", []):
        verify.append(
            {
                "point": gap.get("description", ""),
                "why": "Unexplained gap in the sequence of events.",
                "action": "Request clarification for the missing time / step.",
            }
        )
    for s in signals:
        if s.get("severity") == "high":
            verify.append(
                {
                    "point": s.get("message", ""),
                    "why": s.get("evidence", ""),
                    "action": "Escalate to a senior investigator before payout.",
                }
            )

    similar_fraud = [
        {
            "claim_id": m.get("metadata", {}).get("claim_id"),
            "similarity": m.get("similarity"),
            "fraud_type": m.get("metadata", {}).get("fraud_type"),
        }
        for m in similar
        if m.get("metadata", {}).get("is_fraud")
    ]

    # Score contributions (reason-code weights) for the PDF chart.
    weights = {"low": 10, "medium": 25, "high": 40}
    contributions = [(s.get("code", "signal"), weights.get(s.get("severity"), 10)) for s in signals]
    prob = state.get("fraud_probability")
    if prob is not None:
        contributions.append(("ml_fraud_probability", int(prob * 40)))

    return {
        "risk_score": float(report.get("risk_score", 0) or 0),
        "recommended_action": report.get("recommended_action", "-"),
        "fraud_probability": state.get("fraud_probability"),
        "summary": reasoning.get("narrative") or report.get("timeline_summary") or "",
        "flags": flags,
        "events": timeline.get("events", []),
        "verify": verify,
        "similar_fraud": similar_fraud,
        "contributions": contributions,
        "coverage": coverage,
        "citations": report.get("citations", []),
    }


def _san(text: Any) -> str:
    """Make text safe for the PDF core fonts (latin-1)."""
    s = str(text or "")
    return s.encode("latin-1", "replace").decode("latin-1")


def to_pdf(detailed: dict[str, Any], claim_ref: str = "claim") -> bytes:
    """Render the detailed report to a compact PDF and return the bytes."""
    from fpdf import FPDF

    score = detailed["risk_score"]
    if score >= 60:
        band, rgb = "HIGH RISK", (208, 59, 59)
    elif score >= 30:
        band, rgb = "MEDIUM RISK", (229, 130, 14)
    else:
        band, rgb = "LOW RISK", (15, 157, 88)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def mcell(text: str, size: int = 10, style: str = "", color: tuple = (0, 0, 0)) -> None:
        """Write a full-width paragraph, always resetting x to the left margin."""
        pdf.set_font("Helvetica", style, size)
        pdf.set_text_color(*color)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5, _san(text), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)

    def section(title: str) -> None:
        pdf.ln(1)
        mcell(title, size=12, style="B")

    # Header
    mcell("InsurCalim AI - Investigation Report", size=16, style="B")
    mcell(f"Reference: {claim_ref}   |   Human-in-the-loop - ranks and recommends, never auto-denies.",
          size=9, color=(120, 120, 120))
    pdf.ln(1)

    # Risk banner
    prob = detailed.get("fraud_probability")
    prob_txt = f"   |   ML fraud probability: {prob*100:.0f}%" if prob is not None else ""
    pdf.set_fill_color(*rgb)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(
        0, 10,
        _san(f"  Risk {score:.0f}/100 - {band}   |   Action: {detailed['recommended_action']}{prob_txt}"),
        new_x="LMARGIN", new_y="NEXT", fill=True,
    )
    pdf.set_text_color(0, 0, 0)

    # Risk bar chart
    pdf.ln(2)
    bx, by, bw, bh = pdf.l_margin, pdf.get_y(), 180, 6
    pdf.set_fill_color(230, 228, 222)
    pdf.rect(bx, by, bw, bh, style="F")
    pdf.set_fill_color(*rgb)
    pdf.rect(bx, by, bw * min(score, 100) / 100, bh, style="F")
    pdf.set_y(by + bh + 1)
    mcell("Risk score (0 - 100)", size=8, color=(140, 140, 140))

    # Reason-code contribution bars
    contribs = detailed.get("contributions") or []
    if contribs:
        section("Score contributions (reason codes)")
        maxc = max((c for _, c in contribs), default=1) or 1
        pdf.set_font("Helvetica", "", 9)
        for code, pts in contribs:
            y = pdf.get_y()
            pdf.set_xy(pdf.l_margin, y)
            pdf.cell(66, 5, _san(str(code)[:32]))
            pdf.set_fill_color(74, 58, 167)
            pdf.rect(pdf.l_margin + 68, y + 0.6, 96 * pts / maxc, 3.6, style="F")
            pdf.set_xy(pdf.l_margin + 168, y)
            pdf.cell(20, 5, _san(f"{pts} pts"), new_x="LMARGIN", new_y="NEXT")

    if detailed.get("summary"):
        section("Summary")
        mcell(detailed["summary"])

    cov = detailed.get("coverage")
    if cov:
        section("Policy coverage")
        mcell(f"Decision: {cov.get('decision','-')}. {cov.get('rationale','')}")
        if cov.get("clause"):
            mcell(f"Cited clause: {cov['clause'][:300]}", color=(110, 110, 110))

    if detailed.get("verify"):
        section("Points requiring verification (flagged as suspicious)")
        for i, v in enumerate(detailed["verify"], 1):
            mcell(f"{i}. {v['point']}", style="B")
            if v.get("why"):
                mcell(f"     Why: {v['why']}", color=(110, 110, 110))
            mcell(f"     Verify: {v['action']}")

    if detailed.get("events"):
        section("Event timeline")
        for ev in detailed["events"]:
            facts = ", ".join(ev.get("facts", []) or [])
            line = f"{ev.get('order','-')}. {ev.get('summary','')}"
            if facts:
                line += f"  [{facts}]"
            mcell(line)

    if detailed.get("flags"):
        section("Flags")
        for f in detailed["flags"]:
            conf = f.get("confidence")
            suffix = f" (confidence {conf}%)" if conf not in ("", None) else ""
            mcell(f"- {f.get('summary','')}{suffix}")
            if f.get("evidence"):
                mcell(f"     {f.get('evidence','')}", color=(110, 110, 110))

    if detailed.get("similar_fraud"):
        section("Similar known-fraud matches")
        for m in detailed["similar_fraud"]:
            mcell(f"- {int((m.get('similarity') or 0)*100)}% match to claim #{m.get('claim_id')} ({m.get('fraud_type')})")

    pdf.ln(2)
    mcell(
        "Generated by InsurCalim AI. Decision support for a human investigator, not an "
        "automated decision. Synthetic demo data - no real customer information.",
        size=8, style="I", color=(130, 130, 130),
    )
    return bytes(pdf.output())
