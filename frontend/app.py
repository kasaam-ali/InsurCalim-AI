"""InsurCalim AI - investigator dashboard (Streamlit).

A modern, human-in-the-loop UI over the claim-investigation pipeline: portfolio
overview, a risk-scored claims queue, an explainable investigation report with a
live agent trace and similar-claim comparison, ad-hoc claim analysis, and model
performance. Imports the insurclaim package directly.

Run from the project root:  streamlit run frontend/app.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import streamlit as st

# Make the project package importable when Streamlit runs this file directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from insurclaim.db import repo  # noqa: E402

st.set_page_config(page_title="InsurCalim AI", page_icon="🔎", layout="wide")

# --- Design tokens (validated data-viz palette) -----------------------------
CRITICAL, WARNING, GOOD = "#d03b3b", "#e5820e", "#0f9d58"
BLUE, AQUA, VIOLET = "#2a78d6", "#1baf7a", "#4a3aa7"
INK, MUTED = "#0b0b0b", "#898781"
RISK_HIGH, RISK_MEDIUM = 60, 30

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
#MainMenu, header, footer {visibility: hidden;}
* {transition: background-color .18s ease, box-shadow .2s ease, transform .18s ease, border-color .18s ease, filter .18s ease;}
html, body, [class*="css"], .stApp {font-family:'Inter', system-ui, -apple-system, "Segoe UI", sans-serif;}
.stApp {background: radial-gradient(1100px 560px at 8% -12%, #eaf0fb 0%, #f5f7fb 42%, #f3f5f9 100%);}
.block-container {padding-top:1.4rem; max-width:1180px;}
h1,h2,h3,h4 {letter-spacing:-.015em; color:#0b1220;}
.main .block-container {animation: fadeUp .45s ease;}
@keyframes fadeUp {from{opacity:0; transform:translateY(10px);} to{opacity:1; transform:none;}}

/* Sidebar — dark modern with nav hover/active */
section[data-testid="stSidebar"] {background:linear-gradient(180deg,#0e1628,#131d33); border-right:1px solid rgba(255,255,255,.06);}
section[data-testid="stSidebar"] * {color:#cbd5e1;}
section[data-testid="stSidebar"] h2 {color:#fff; font-weight:800;}
section[data-testid="stSidebar"] div[role="radiogroup"] label {display:flex; align-items:center; padding:.55rem .8rem;
  border-radius:10px; margin:2px 0; cursor:pointer;}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {background:rgba(255,255,255,.07); transform:translateX(2px);}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {background:rgba(58,135,229,.22); box-shadow:inset 3px 0 0 #3987e5;}
section[data-testid="stSidebar"] div[role="radiogroup"] label p {font-weight:600; font-size:.92rem; color:#e5e7eb !important;}
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {opacity:0; width:0; overflow:hidden; margin:0;}

/* Buttons */
.stButton>button, .stDownloadButton>button, .stFormSubmitButton>button {border-radius:10px; font-weight:600;
  border:1px solid rgba(11,11,11,.10);}
.stButton>button:hover, .stDownloadButton>button:hover, .stFormSubmitButton>button:hover {transform:translateY(-1px);
  box-shadow:0 8px 18px rgba(42,120,214,.2);}
.stButton>button[kind="primary"], .stDownloadButton>button[kind="primary"], .stFormSubmitButton>button {
  background:linear-gradient(135deg,#2a78d6,#4a3aa7); color:#fff; border:none;}
.stButton>button[kind="primary"]:hover {filter:brightness(1.07);}

/* Inputs + uploader */
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-baseweb="select"]>div {border-radius:10px !important;}
[data-testid="stTextInput"] input:focus {box-shadow:0 0 0 3px rgba(42,120,214,.16) !important; border-color:#2a78d6 !important;}
[data-testid="stFileUploaderDropzone"] {border-radius:14px; border:1.5px dashed #b9c6de; background:#fbfcfe;}
[data-testid="stFileUploaderDropzone"]:hover {border-color:#2a78d6; background:#f2f7ff;}

/* Hero */
.hero {background:linear-gradient(120deg,#0e1628 0%,#1c2b4a 42%,#2a78d6 100%); color:#fff; padding:1.7rem 1.9rem;
  border-radius:20px; margin-bottom:1.2rem; box-shadow:0 14px 34px rgba(28,43,74,.28); position:relative; overflow:hidden;}
.hero:after {content:""; position:absolute; right:-40px; top:-50px; width:220px; height:220px;
  background:radial-gradient(circle,rgba(255,255,255,.16),transparent 70%);}
.hero h1 {margin:0; font-size:1.85rem; font-weight:800; color:#fff;}
.hero p {margin:.45rem 0 0; opacity:.9; font-size:.95rem; max-width:660px;}

/* KPI cards with hover lift */
.kpi {background:#fff; border:1px solid rgba(11,11,11,.06); border-radius:16px; padding:1.1rem 1.25rem;
  box-shadow:0 1px 2px rgba(11,11,11,.04); height:100%; position:relative; overflow:hidden;}
.kpi:before {content:""; position:absolute; left:0; top:0; height:100%; width:4px;
  background:linear-gradient(#2a78d6,#4a3aa7); opacity:0;}
.kpi:hover {transform:translateY(-3px); box-shadow:0 14px 28px rgba(11,11,11,.11); border-color:rgba(42,120,214,.28);}
.kpi:hover:before {opacity:1;}
.kpi .l {color:#6b7280; font-size:.72rem; text-transform:uppercase; letter-spacing:.06em; font-weight:700;}
.kpi .v {color:#0b1220; font-size:2.05rem; font-weight:800; line-height:1.1; margin-top:.25rem; letter-spacing:-.02em;}
.kpi .s {color:#8a90a0; font-size:.8rem; margin-top:.15rem;}

.badge {display:inline-block; padding:.26rem .75rem; border-radius:999px; color:#fff; font-size:.76rem;
  font-weight:700; letter-spacing:.02em; box-shadow:0 2px 7px rgba(11,11,11,.14);}

.flag {background:#fff; border:1px solid rgba(11,11,11,.06); border-left:4px solid #d03b3b; border-radius:12px;
  padding:.8rem 1rem; margin-bottom:.6rem; box-shadow:0 1px 2px rgba(11,11,11,.04);}
.flag:hover {transform:translateX(3px); box-shadow:0 8px 18px rgba(11,11,11,.09);}
.flag .t {font-weight:650; color:#0b1220;}
.flag .e {color:#52514e; font-size:.86rem; margin-top:.15rem;}
.flag .c {color:#898781; font-size:.76rem; margin-top:.2rem;}

.trace {display:flex; align-items:center; gap:.4rem; flex-wrap:wrap; margin:.4rem 0 1rem;}
.node {background:#eef4fd; color:#1c2b4a; border:1px solid #cfe0f8; border-radius:999px; padding:.32rem .85rem;
  font-size:.82rem; font-weight:650;}
.node.done {background:linear-gradient(135deg,#0f9d58,#0c8a4d); color:#fff; border-color:transparent;
  box-shadow:0 3px 9px rgba(15,157,88,.3);}
.arrow {color:#b6bdca; font-weight:700;}

.cmp {display:flex; gap:.8rem;}
.cmp .card {flex:1; background:#fff; border:1px solid rgba(11,11,11,.06); border-radius:14px; padding:1rem;
  box-shadow:0 1px 2px rgba(11,11,11,.04);}
.cmp .card:hover {box-shadow:0 10px 22px rgba(11,11,11,.09); transform:translateY(-2px);}
.cmp .card.match {border:1px solid #d03b3b; box-shadow:0 0 0 3px rgba(208,59,59,.08);}
.cmp .h {font-size:.72rem; text-transform:uppercase; letter-spacing:.05em; color:#8a90a0; font-weight:700;}
.cmp .d {color:#52514e; font-size:.85rem; margin-top:.4rem; line-height:1.45;}

.bar-row {display:flex; align-items:center; gap:.6rem; margin:.35rem 0;}
.bar-row .lab {width:160px; font-size:.83rem; color:#52514e; text-align:right;}
.bar-track {flex:1; background:#edf0f5; border-radius:8px; height:15px; overflow:hidden;}
.bar-fill {height:100%; border-radius:8px; transition:width .6s ease;}
.bar-row .val {width:60px; font-size:.8rem; color:#52514e; font-variant-numeric:tabular-nums;}

.tbl {width:100%; border-collapse:separate; border-spacing:0; font-size:.86rem; background:#fff;
  border:1px solid rgba(11,11,11,.06); border-radius:14px; overflow:hidden; box-shadow:0 1px 2px rgba(11,11,11,.04);}
.tbl th {text-align:left; color:#6b7280; font-weight:700; font-size:.7rem; text-transform:uppercase; letter-spacing:.05em;
  background:#f8fafc; border-bottom:1px solid #eef0f4; padding:.65rem .8rem;}
.tbl td {border-bottom:1px solid #f2f4f7; padding:.6rem .8rem; color:#0b1220;}
.tbl tr:last-child td {border-bottom:none;}
.tbl tr:hover td {background:#f4f8ff;}

::-webkit-scrollbar {width:10px; height:10px;}
::-webkit-scrollbar-thumb {background:#c7cfdd; border-radius:8px;}
::-webkit-scrollbar-thumb:hover {background:#aab6c9;}
"""
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


# --- Helpers ----------------------------------------------------------------
def risk_meta(score: float) -> tuple[str, str]:
    if score >= RISK_HIGH:
        return "HIGH", CRITICAL
    if score >= RISK_MEDIUM:
        return "MEDIUM", WARNING
    return "LOW", GOOD


def kpi(label: str, value, sub: str = "") -> str:
    return f'<div class="kpi"><div class="l">{label}</div><div class="v">{value}</div><div class="s">{sub}</div></div>'


def badge(text: str, color: str) -> str:
    return f'<span class="badge" style="background:{color}">{text}</span>'


def gauge(score: float, color: str) -> str:
    r, circ = 56, 2 * math.pi * 56
    dash = circ * min(max(score, 0), 100) / 100
    return (
        f'<svg width="150" height="150" viewBox="0 0 150 150">'
        f'<circle cx="75" cy="75" r="{r}" fill="none" stroke="#eceae3" stroke-width="14"/>'
        f'<circle cx="75" cy="75" r="{r}" fill="none" stroke="{color}" stroke-width="14" '
        f'stroke-linecap="round" stroke-dasharray="{dash:.1f} {circ:.1f}" transform="rotate(-90 75 75)"/>'
        f'<text x="75" y="72" text-anchor="middle" font-size="38" font-weight="750" fill="{color}">{score:.0f}</text>'
        f'<text x="75" y="95" text-anchor="middle" font-size="12" fill="#898781">risk / 100</text></svg>'
    )


def agent_trace(done: int = 4) -> str:
    steps = ["Intake", "Timeline", "Fraud", "Report"]
    parts = []
    for i, s in enumerate(steps):
        cls = "node done" if i < done else "node"
        mark = "✓ " if i < done else ""
        parts.append(f'<span class="{cls}">{mark}{s}</span>')
        if i < len(steps) - 1:
            parts.append('<span class="arrow">→</span>')
    return f'<div class="trace">{"".join(parts)}</div>'


def bar_row(label: str, value: float, maximum: float, color: str, suffix: str = "") -> str:
    pct = 0 if maximum == 0 else min(value / maximum * 100, 100)
    return (
        f'<div class="bar-row"><div class="lab">{label}</div>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{pct:.0f}%;background:{color}"></div></div>'
        f'<div class="val">{value:.0f}{suffix}</div></div>'
    )


@st.cache_data(show_spinner="Scoring claims...")
def score_all() -> list[dict]:
    """Compute a fast (no-LLM) risk score for every claim: deterministic rules +
    duplicate-photo + similar-claim RAG + narrative ML, via the report fallback.
    """
    from insurclaim.agents.fraud import _duplicate_photo_signals, _similar_claim_signals
    from insurclaim.agents.report import _fallback_risk_score
    from insurclaim.ml.predict import predict_fraud
    from insurclaim.rules import deterministic

    scored = []
    for base in repo.list_labeled_claims():
        claim = repo.get_claim(base["id"])
        desc = claim.get("description") or ""
        signals = deterministic.run_all(claim, [])
        signals += _duplicate_photo_signals(claim)
        try:
            sim_sigs, matches = _similar_claim_signals(desc, exclude_claim_id=claim["id"])
            signals += sim_sigs
        except Exception:
            matches = []
        prob = predict_fraud(desc)
        score = _fallback_risk_score({"fraud_signals": signals, "fraud_probability": prob})
        scored.append(
            {
                "id": claim["id"],
                "fraud_type": base.get("fraud_type") or "legit",
                "is_fraud": bool(base.get("is_fraud")),
                "risk": score,
                "prob": prob,
                "signals": signals,
                "matches": matches,
                "description": desc,
                "location": claim.get("location") or "",
                "amount": claim.get("claimed_amount"),
                "incident_date": claim.get("incident_date"),
            }
        )
    return scored


# --- Pages ------------------------------------------------------------------
def page_overview(scored: list[dict]) -> None:
    st.markdown(
        '<div class="hero"><h1>🔎 InsurCalim AI</h1>'
        "<p>AI-assisted auto-insurance claim investigation — explainable, human-in-the-loop. "
        "The system flags and ranks; it never auto-denies.</p></div>",
        unsafe_allow_html=True,
    )
    total = len(scored)
    high = sum(1 for s in scored if s["risk"] >= RISK_HIGH)
    fraud = sum(1 for s in scored if s["is_fraud"])
    avg = sum(s["risk"] for s in scored) / total if total else 0

    cols = st.columns(4)
    cards = [
        kpi("Claims in system", total),
        kpi("High-risk", high, f"{(high/total*100) if total else 0:.0f}% of portfolio"),
        kpi("Labeled fraud", fraud, f"{(fraud/total*100) if total else 0:.0f}% base rate"),
        kpi("Avg risk score", f"{avg:.0f}", "0-100"),
    ]
    for col, card in zip(cols, cards):
        col.markdown(card, unsafe_allow_html=True)

    # Business impact — the mission: catch fraud, and pay honest people faster.
    money = sum(float(s["amount"] or 0) for s in scored if s["risk"] >= RISK_HIGH)
    fast = sum(1 for s in scored if s["risk"] < RISK_MEDIUM)
    rings = len(detect_rings(scored)[0])
    st.write("")
    d, e, f = st.columns(3)
    d.markdown(kpi("Money at risk", f"${money:,.0f}", "flagged in high-risk claims"), unsafe_allow_html=True)
    e.markdown(kpi("Fast-trackable", fast, "low-risk — pay honest claimants in days"), unsafe_allow_html=True)
    f.markdown(kpi("Fraud rings", rings, "organized fraud detected"), unsafe_allow_html=True)

    st.write("")
    left, right = st.columns(2)
    with left:
        st.markdown("##### Risk distribution")
        bands = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for s in scored:
            bands[risk_meta(s["risk"])[0]] += 1
        html = ""
        for name, color in [("HIGH", CRITICAL), ("MEDIUM", WARNING), ("LOW", GOOD)]:
            html += bar_row(name, bands[name], total, color)
        st.markdown(html, unsafe_allow_html=True)
    with right:
        st.markdown("##### Fraud types (labeled)")
        from collections import Counter

        types = Counter(s["fraud_type"] for s in scored if s["is_fraud"])
        maxv = max(types.values()) if types else 1
        html = ""
        for name, count in types.most_common():
            html += bar_row(name, count, maxv, BLUE)
        st.markdown(html or "_none_", unsafe_allow_html=True)


def page_queue(scored: list[dict]) -> None:
    st.markdown("### Claims queue")
    c1, c2 = st.columns([1, 2])
    band = c1.selectbox("Risk band", ["All", "HIGH", "MEDIUM", "LOW"])
    search = c2.text_input("Search description / location", "")

    rows = sorted(scored, key=lambda s: -s["risk"])
    if band != "All":
        rows = [s for s in rows if risk_meta(s["risk"])[0] == band]
    if search.strip():
        q = search.lower()
        rows = [s for s in rows if q in s["description"].lower() or q in s["location"].lower()]

    body = ""
    for s in rows:
        label, color = risk_meta(s["risk"])
        body += (
            f"<tr><td>#{s['id']}</td>"
            f"<td>{badge(f'{s['risk']:.0f} {label}', color)}</td>"
            f"<td>{s['fraud_type']}</td>"
            f"<td>{s['location'][:40]}</td>"
            f"<td>{'⚑ ' + str(len(s['signals'])) if s['signals'] else '0'} signals</td></tr>"
        )
    st.markdown(
        f'<table class="tbl"><tr><th>Claim</th><th>Risk</th><th>Type (label)</th>'
        f"<th>Location</th><th>Evidence</th></tr>{body}</table>",
        unsafe_allow_html=True,
    )
    st.caption(f"{len(rows)} claims. Open one in 'Investigation report' for the full analysis.")


def _render_signals(signals: list[dict]) -> None:
    if not signals:
        st.info("No deterministic / RAG / photo flags.")
        return
    order = {"high": 0, "medium": 1, "low": 2}
    for s in sorted(signals, key=lambda x: order.get(x.get("severity"), 3)):
        color = {"high": CRITICAL, "medium": WARNING}.get(s.get("severity"), MUTED)
        st.markdown(
            f'<div class="flag" style="border-left-color:{color}">'
            f'<div class="t">{s.get("message","")}</div>'
            f'<div class="e">{s.get("evidence","")}</div>'
            f'<div class="c">severity: {s.get("severity","-")}</div></div>',
            unsafe_allow_html=True,
        )


def _comparison(current: dict) -> None:
    matches = [m for m in current["matches"] if m.get("metadata", {}).get("is_fraud")]
    if not matches:
        return
    m = matches[0]
    mid = m["metadata"].get("claim_id")
    match_claim = repo.get_claim(mid)
    st.markdown("##### Closest known-fraud match (RAG)")
    st.markdown(
        f'<div class="cmp"><div class="card"><div class="h">This claim · #{current["id"]}</div>'
        f'<div class="d">{current["description"][:280]}...</div></div>'
        f'<div class="card match"><div class="h">Known fraud · #{mid} · '
        f'{int(m["similarity"]*100)}% match · {m["metadata"].get("fraud_type")}</div>'
        f'<div class="d">{(match_claim.get("description") or "")[:280]}...</div></div></div>',
        unsafe_allow_html=True,
    )


def page_report(scored: list[dict]) -> None:
    st.markdown("### Investigation report")
    by_id = {s["id"]: s for s in scored}
    claim_id = st.selectbox("Select a claim", list(by_id.keys()),
                            format_func=lambda i: f"#{i} · {by_id[i]['fraud_type']}")
    s = by_id[claim_id]
    label, color = risk_meta(s["risk"])

    st.markdown(agent_trace(4), unsafe_allow_html=True)
    left, right = st.columns([1, 2])
    with left:
        st.markdown(gauge(s["risk"], color), unsafe_allow_html=True)
        st.markdown(badge(f"{label} RISK", color), unsafe_allow_html=True)
        if s["prob"] is not None:
            st.markdown(f"**ML fraud probability:** {s['prob']*100:.0f}%")
        action = ("route_to_investigator" if s["risk"] >= RISK_HIGH
                  else "fast_track_approve" if s["risk"] < RISK_MEDIUM else "request_more_info")
        st.markdown(f"**Recommended action:** `{action}`")
        st.caption(f"Ground truth (demo): {'FRAUD' if s['is_fraud'] else 'legit'}")
    with right:
        st.markdown("##### Flags")
        _render_signals(s["signals"])

    _comparison(s)

    # Explainable score breakdown ("reason codes"): what added up to the score.
    st.markdown("##### Why this score (reason codes)")
    weights = {"low": 10, "medium": 25, "high": 40}
    contribs = [(sig.get("code", "signal"), weights.get(sig.get("severity"), 10)) for sig in s["signals"]]
    if s["prob"] is not None:
        contribs.append(("ml_fraud_probability", int(s["prob"] * 40)))
    if contribs:
        maxc = max(c for _, c in contribs)
        html = "".join(bar_row(code, pts, maxc, color, " pts") for code, pts in contribs)
        st.markdown(html, unsafe_allow_html=True)
        st.caption(f"Signals sum to the risk score (capped at 100). This claim: {s['risk']:.0f}.")
    else:
        st.caption("No contributing signals.")

    # Audit-defensible export for the investigator.
    lines = [
        f"InsurCalim AI - investigation summary",
        f"Claim #{s['id']}  |  risk score: {s['risk']:.0f} ({label})  |  action: {action}",
        f"ML fraud probability: {(s['prob'] or 0) * 100:.0f}%",
        "",
        "Reason codes:",
        *[f"  - {code}: +{pts} pts" for code, pts in contribs],
        "",
        "Flags:",
        *[f"  - [{x.get('severity')}] {x.get('message')} ({x.get('evidence')})" for x in s["signals"]],
        "",
        f"Description: {s['description']}",
    ]
    st.download_button(
        "⬇ Export investigation summary",
        "\n".join(lines),
        file_name=f"claim_{s['id']}_summary.txt",
    )

    if st.button("🛡️ Check policy coverage"):
        from insurclaim import coverage

        with st.spinner("Checking against uploaded policies..."):
            cov = coverage.check_coverage(s["description"])
        cmap = {"covered": GOOD, "not_covered": CRITICAL, "needs_review": WARNING}
        st.markdown("##### Policy coverage")
        st.markdown(badge(cov["decision"].upper().replace("_", " "),
                          cmap.get(cov["decision"], MUTED)), unsafe_allow_html=True)
        st.write(cov["rationale"])
        if cov.get("clause"):
            st.caption(f"Cited clause: {cov['clause'][:200]}")

    st.markdown("##### 💬 Ask about this claim")
    q = st.text_input("Question", key=f"ask_{claim_id}",
                      placeholder="e.g. Why is this suspicious? What should I verify first?")
    if q.strip():
        from insurclaim.llm import call_llm

        codes = [x.get("code") for x in s["signals"]]
        with st.spinner("Thinking..."):
            try:
                ans = call_llm(
                    prompt=f"Claim description:\n{s['description']}\n\n"
                    f"Detected signals: {codes}\nRisk score: {s['risk']:.0f}/100\n\nQuestion: {q}",
                    system="You are a claims-investigation assistant. Answer briefly, "
                    "using only the claim information provided.",
                )
            except Exception as exc:
                ans = f"(assistant unavailable: {exc})"
        st.info(ans)

    case_management_ui(f"claim #{claim_id}")

    with st.expander("Run the full LLM pipeline (timeline + narrative reasoning)"):
        st.caption("Uses the LLM; on the free tier this may take a moment or fall back.")
        if st.button("Run full AI investigation", type="primary"):
            from insurclaim.graph import run_claim

            with st.spinner("Running intake → timeline → fraud → report..."):
                final = run_claim({"claim": repo.get_claim(claim_id)})
            render_detailed_and_pdf(final, f"claim #{claim_id}", s["description"])


def case_management_ui(claim_ref: str) -> None:
    """Persistent investigator status, assignee, and notes for a claim."""
    st.markdown("##### 🗂️ Case management")
    case = repo.get_case_status(claim_ref) or {}
    statuses = ["open", "investigating", "cleared", "confirmed_fraud"]
    cur = case.get("status", "open")
    c1, c2 = st.columns(2)
    status = c1.selectbox("Status", statuses,
                          index=statuses.index(cur) if cur in statuses else 0,
                          key=f"st_{claim_ref}")
    assignee = c2.text_input("Assignee", case.get("assignee") or "", key=f"as_{claim_ref}")
    if st.button("Save case", key=f"sv_{claim_ref}"):
        repo.set_case_status(claim_ref, status, assignee)
        st.success("Case updated.")
    note = st.text_input("Add an investigation note", key=f"nt_{claim_ref}")
    if st.button("Add note", key=f"an_{claim_ref}") and note.strip():
        repo.add_case_note(claim_ref, note.strip())
        st.success("Note added.")
        st.rerun()
    notes = repo.list_case_notes(claim_ref)
    if notes:
        st.markdown("**Notes (audit trail)**")
        for n in notes:
            st.markdown(f"- {n['note']}  \n  _{str(n['created_at'])[:16]}_")


def page_analytics(scored: list[dict]) -> None:
    import pandas as pd
    from collections import Counter, defaultdict

    st.markdown("### 📈 Analytics & trends")

    months: Counter = Counter()
    for s in scored:
        d = s.get("incident_date")
        if d:
            months[str(d)[:7]] += 1
    if months:
        st.markdown("##### Claims per month")
        st.line_chart(pd.Series({m: months[m] for m in sorted(months)}, name="claims"))

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Claims by risk band")
        bands = Counter(risk_meta(s["risk"])[0] for s in scored)
        st.bar_chart(pd.Series({k: bands.get(k, 0) for k in ["HIGH", "MEDIUM", "LOW"]}, name="claims"))
    with c2:
        st.markdown("##### Labeled fraud types")
        ft = Counter(s["fraud_type"] for s in scored if s["is_fraud"])
        st.bar_chart(pd.Series(dict(ft.most_common()), name="claims"))

    st.markdown("##### Average claimed amount by risk band ($)")
    sums: dict = defaultdict(list)
    for s in scored:
        if s.get("amount"):
            sums[risk_meta(s["risk"])[0]].append(float(s["amount"]))
    avg = {k: (sum(sums[k]) / len(sums[k]) if sums.get(k) else 0) for k in ["HIGH", "MEDIUM", "LOW"]}
    st.bar_chart(pd.Series(avg, name="avg $"))


def page_model() -> None:
    st.markdown("### Model performance")
    st.caption("Tabular classifier: real 30,000-row dataset · Narrative classifier: fine-tuned on claim text.")
    a, b, c = st.columns(3)
    a.markdown(kpi("Tabular ROC-AUC", "0.74", "real held-out"), unsafe_allow_html=True)
    b.markdown(kpi("Fraud recall", "67%", "@ threshold 0.25"), unsafe_allow_html=True)
    c.markdown(kpi("Narrative recall", "high", "fine-tuned on text"), unsafe_allow_html=True)
    st.write("")
    try:
        import joblib

        from insurclaim.ml.train_tabular import MODEL_PATH

        if not MODEL_PATH.exists():
            st.info("Tabular model not trained. Run: python -m insurclaim.ml.train_tabular")
            return
        model = joblib.load(MODEL_PATH)
        names = model.named_steps["preprocess"].get_feature_names_out()
        importances = model.named_steps["classifier"].feature_importances_
        top = sorted(zip(names, importances), key=lambda x: -x[1])[:10]
        maxv = top[0][1]
        st.markdown("##### Top fraud signals the model learned")
        html = "".join(
            bar_row(n.split("__")[-1][:26], v * 100, maxv * 100, VIOLET, "%") for n, v in top
        )
        st.markdown(html, unsafe_allow_html=True)
    except Exception as exc:
        st.error(f"Could not load the tabular model: {exc}")


def detect_rings(scored: list[dict]) -> tuple[list[list[int]], dict]:
    """Link fraud claims to their similar known-fraud matches (RAG) and return
    connected components of size >= 3 as fraud rings, plus the adjacency map.
    """
    from collections import defaultdict

    ids = {s["id"] for s in scored}
    adj: dict[int, set] = defaultdict(set)
    for s in scored:
        if not s["is_fraud"]:
            continue
        for m in s["matches"]:
            md = m.get("metadata", {})
            other = md.get("claim_id")
            if md.get("is_fraud") and m["similarity"] >= 0.40 and other in ids:
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


def ring_svg(members: list[int], adj: dict, size: int = 360) -> str:
    cx = cy = size / 2
    r = size / 2 - 26
    n = len(members)
    pos = {
        m: (
            cx + r * math.cos(2 * math.pi * i / n - math.pi / 2),
            cy + r * math.sin(2 * math.pi * i / n - math.pi / 2),
        )
        for i, m in enumerate(members)
    }
    edges, drawn = "", set()
    for a in members:
        for b in adj.get(a, ()):
            if b in pos and (b, a) not in drawn:
                drawn.add((a, b))
                x1, y1 = pos[a]
                x2, y2 = pos[b]
                edges += (
                    f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
                    f'stroke="#d03b3b" stroke-opacity="0.3" stroke-width="1.4"/>'
                )
    nodes = ""
    for m, (x, y) in pos.items():
        nodes += (
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="15" fill="#d03b3b"/>'
            f'<text x="{x:.0f}" y="{y+3:.0f}" text-anchor="middle" font-size="9" '
            f'fill="#fff" font-weight="700">{m}</text>'
        )
    return f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">{edges}{nodes}</svg>'


def page_rings(scored: list[dict]) -> None:
    st.markdown("### 🕸️ Fraud rings")
    st.caption(
        "Claims linked by narrative similarity to known fraud (RAG). Connected "
        "groups reveal organized fraud rings that isolated review would miss."
    )
    rings, adj = detect_rings(scored)
    if not rings:
        st.info("No fraud rings detected.")
        return
    by_id = {s["id"]: s for s in scored}
    a, b = st.columns(2)
    a.markdown(kpi("Rings detected", len(rings)), unsafe_allow_html=True)
    b.markdown(kpi("Claims in rings", sum(len(r) for r in rings)), unsafe_allow_html=True)
    st.write("")
    for i, ring in enumerate(rings, 1):
        from collections import Counter

        types = Counter(by_id[m]["fraud_type"] for m in ring if m in by_id)
        pattern = types.most_common(1)[0][0] if types else "?"
        st.markdown(f"#### Ring {i} — {len(ring)} linked claims · pattern: `{pattern}`")
        left, right = st.columns([1, 1])
        with left:
            st.markdown(ring_svg(ring, adj), unsafe_allow_html=True)
        with right:
            st.markdown("**Members**")
            st.markdown(
                " ".join(badge(f"#{m}", CRITICAL) for m in ring[:24]), unsafe_allow_html=True
            )
            st.caption("Shared modus operandi detected across these claims.")
        st.divider()


def _render_quick_report(report: dict) -> None:
    score = float(report.get("risk_score", 0) or 0)
    lbl, col = risk_meta(score)
    st.markdown(agent_trace(4), unsafe_allow_html=True)
    st.markdown(gauge(score, col), unsafe_allow_html=True)
    st.markdown(badge(f"{lbl} RISK · {report.get('recommended_action','-')}", col), unsafe_allow_html=True)
    for fl in report.get("top_flags", []):
        st.markdown(
            f'<div class="flag"><div class="t">{fl.get("summary","")}</div>'
            f'<div class="e">{fl.get("evidence","")}</div></div>',
            unsafe_allow_html=True,
        )
    if report.get("timeline_summary"):
        st.markdown("**Timeline summary**")
        st.write(report["timeline_summary"])


def render_detailed_and_pdf(state: dict, claim_ref: str, description: str = "") -> None:
    """Show a detailed view (events, points to verify, coverage) + a PDF download."""
    from insurclaim import coverage as cov_mod
    from insurclaim import report_builder

    cov = None
    try:
        if description:
            cov = cov_mod.check_coverage(description)
            if cov.get("decision") == "needs_review" and not cov.get("citations"):
                cov = None  # no policies uploaded - skip the coverage block
    except Exception:
        cov = None

    detailed = report_builder.build_detailed(state, coverage=cov)
    with st.expander("📄 Detailed view — events, points to verify, coverage", expanded=True):
        if detailed["summary"]:
            st.markdown("**Investigator summary**")
            st.write(detailed["summary"])
        if cov:
            cmap = {"covered": GOOD, "not_covered": CRITICAL, "needs_review": WARNING}
            st.markdown("**Policy coverage**")
            st.markdown(badge(cov["decision"].upper().replace("_", " "),
                              cmap.get(cov["decision"], MUTED)), unsafe_allow_html=True)
            st.caption(cov.get("rationale", ""))
        if detailed["verify"]:
            st.markdown("**⚠ Points requiring verification (what we're suspicious about)**")
            for i, v in enumerate(detailed["verify"], 1):
                st.markdown(
                    f"{i}. **{v['point']}**  \n"
                    + (f"   _Why:_ {v['why']}  \n" if v.get("why") else "")
                    + f"   _→ Verify:_ {v['action']}"
                )
        if detailed["events"]:
            st.markdown("**Event timeline**")
            for ev in detailed["events"]:
                facts = ", ".join(ev.get("facts", []) or [])
                st.markdown(
                    f"- **{ev.get('order','-')}.** {ev.get('summary','')}"
                    + (f"  _[{facts}]_" if facts else "")
                )
        if detailed["similar_fraud"]:
            st.markdown("**Similar known-fraud matches**")
            for m in detailed["similar_fraud"]:
                st.markdown(
                    f"- {int((m.get('similarity') or 0)*100)}% match to claim "
                    f"#{m.get('claim_id')} ({m.get('fraud_type')})"
                )

    pdf = report_builder.to_pdf(detailed, claim_ref=claim_ref)
    st.download_button(
        "⬇ Download full PDF report",
        pdf,
        file_name=f"{claim_ref.replace(' ', '_').replace('#', '')}_report.pdf",
        mime="application/pdf",
        type="primary",
    )


def page_submit() -> None:
    st.markdown("### ✍️ Submit a claim (documents & photos)")
    st.caption(
        "Upload the claim narrative / police report / FIR (txt or pdf) and damage "
        "photos. The system extracts the data, checks photos for reuse and damage, "
        "then runs the full investigation."
    )
    docs = st.file_uploader("Claim documents (txt / pdf)", type=["txt", "pdf"],
                            accept_multiple_files=True)
    photos = st.file_uploader("Damage photos", type=["jpg", "jpeg", "png"],
                              accept_multiple_files=True)
    extra = st.text_area("Or paste claim text", height=100)

    if st.button("Process & investigate", type="primary"):
        from insurclaim import intake_docs
        from insurclaim.graph import run_claim

        doc_tuples = [(f.name, f.getvalue()) for f in (docs or [])]
        photo_infos = []
        for f in photos or []:
            info = intake_docs.process_photo(f.name, f.getvalue())
            with st.spinner(f"Reading {f.name} with the vision model..."):
                info["damage"] = intake_docs.analyze_damage(f.getvalue())
            photo_infos.append(info)

        text = intake_docs.build_claim_text(doc_tuples, photo_infos)
        if extra.strip():
            text = (extra.strip() + "\n\n" + text).strip()
        if not text:
            st.warning("Provide at least one document, photo, or some text.")
            return

        for info in photo_infos:
            if info["duplicate_of"]:
                st.error(
                    f"⚠ Photo {info['file_name']} matches a photo already on claim "
                    f"#{info['duplicate_of']['claim_id']} — possible reuse."
                )
            if info.get("damage"):
                st.info(f"👁 Vision · {info['file_name']}: {info['damage']}")

        with st.spinner("Running intake → timeline → fraud → report..."):
            final = run_claim({"raw_documents": text})
        _render_quick_report(final.get("report", {}))
        render_detailed_and_pdf(final, "uploaded claim", text)


def page_policy() -> None:
    st.markdown("### 🛡️ Policy & coverage")
    st.caption(
        "Upload your company's policies / rules. Incoming claims are checked "
        "against them — is the claim actually covered by your policy?"
    )
    from insurclaim import coverage

    with st.form("policy_form"):
        company = st.text_input("Company", "DemoInsure")
        name = st.text_input("Document name", "auto_policy")
        text = st.text_area("Policy text (paste, or upload a file below)", height=130)
        up = st.file_uploader("...or upload a policy file (txt / pdf)", type=["txt", "pdf"])
        submitted = st.form_submit_button("Save & index policy")
    if submitted:
        content = text.strip()
        if up:
            from insurclaim import intake_docs

            content = intake_docs.extract_text(up.name, up.getvalue())
        if content:
            doc_id = coverage.add_policy_document(company, name, content)
            st.success(f"Saved policy #{doc_id} and indexed it for coverage checks.")
            st.cache_data.clear()
        else:
            st.warning("Provide policy text or a file.")

    docs = repo.list_policy_documents()
    if docs:
        st.markdown("##### Policies on file")
        body = "".join(
            f"<tr><td>#{d['id']}</td><td>{d['company']}</td><td>{d['doc_name']}</td>"
            f"<td>{d['preview']}...</td></tr>"
            for d in docs
        )
        st.markdown(
            f'<table class="tbl"><tr><th>#</th><th>Company</th><th>Name</th>'
            f"<th>Preview</th></tr>{body}</table>",
            unsafe_allow_html=True,
        )

    st.markdown("##### Coverage check")
    claim_text = st.text_area("Claim description to check", height=90)
    if st.button("Check coverage", type="primary") and claim_text.strip():
        with st.spinner("Checking against your policies..."):
            r = coverage.check_coverage(claim_text)
        cmap = {"covered": GOOD, "not_covered": CRITICAL, "needs_review": WARNING}
        st.markdown(badge(r["decision"].upper().replace("_", " "),
                          cmap.get(r["decision"], MUTED)), unsafe_allow_html=True)
        st.write(r["rationale"])
        if r.get("clause"):
            st.markdown(
                f'<div class="flag" style="border-left-color:{BLUE}">'
                f'<div class="e">Cited clause: {r["clause"]}</div></div>',
                unsafe_allow_html=True,
            )


PAGES = {
    "📊 Overview": page_overview,
    "📋 Claims queue": page_queue,
    "🔍 Investigation report": page_report,
    "🕸️ Fraud rings": page_rings,
    "📈 Analytics": page_analytics,
    "✍️ Submit a claim": page_submit,
    "🛡️ Policy & coverage": page_policy,
    "📉 Model performance": page_model,
}
NO_ARG_PAGES = ("✍️ Submit a claim", "🛡️ Policy & coverage", "📉 Model performance")


def main() -> None:
    st.sidebar.markdown("## 🔎 InsurCalim AI")
    st.sidebar.caption("Fraud investigation dashboard")
    choice = st.sidebar.radio("Navigate", list(PAGES.keys()), label_visibility="collapsed")
    st.sidebar.markdown("---")
    st.sidebar.caption("Human-in-the-loop — flags & ranks, never auto-denies.")

    try:
        scored = score_all()
    except Exception as exc:
        st.error(f"Could not load / score claims (is the database running?): {exc}")
        return

    if choice in NO_ARG_PAGES:
        PAGES[choice]()
    else:
        PAGES[choice](scored)


if __name__ == "__main__":
    main()
