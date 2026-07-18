"""InsurCalim AI - investigator dashboard (Streamlit).

A modern, human-in-the-loop UI over the claim-investigation pipeline: portfolio
overview, a risk-scored claims queue, an explainable investigation report with a
live agent trace and similar-claim comparison, ad-hoc claim analysis, and model
performance. Imports the insurclaim package directly.

Run from the project root:  streamlit run frontend/app.py
"""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

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
/* Force dark text in the main area so headings stay visible even if the viewer's
   OS/browser theme is dark (h5/h6 + body text otherwise inherit a white color). */
.stApp, .block-container, [data-testid="stMarkdownContainer"] {color:#1f2733;}
.block-container h1, .block-container h2, .block-container h3,
.block-container h4, .block-container h5, .block-container h6 {color:#0b1220 !important;}
h1,h2,h3,h4,h5,h6 {letter-spacing:-.015em; color:#0b1220;}
.main .block-container {animation: fadeUp .45s ease;}
@keyframes fadeUp {from{opacity:0; transform:translateY(10px);} to{opacity:1; transform:none;}}

/* Sidebar — dark modern with nav hover/active */
section[data-testid="stSidebar"] {background:linear-gradient(180deg,#0e1628,#131d33); border-right:1px solid rgba(255,255,255,.06);}
section[data-testid="stSidebar"] * {color:#cbd5e1;}
section[data-testid="stSidebar"] h2 {color:#fff; font-weight:800;}
section[data-testid="stSidebar"] div[role="radiogroup"] {gap:3px;}
section[data-testid="stSidebar"] div[role="radiogroup"] label {display:flex !important; align-items:center; gap:.55rem;
  padding:.62rem .85rem; border-radius:10px; margin:3px 0; cursor:pointer;
  background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.08);}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {background:rgba(255,255,255,.14); transform:translateX(2px);}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
  background:linear-gradient(135deg,rgba(58,135,229,.40),rgba(74,58,167,.34)); border-color:rgba(58,135,229,.6);}
section[data-testid="stSidebar"] div[role="radiogroup"] label p {font-weight:600; font-size:.9rem; color:#eef2f8 !important; margin:0;}
section[data-testid="stSidebar"] div[role="radiogroup"] label div[data-baseweb="radio"] > div:first-child {
  border-color:rgba(255,255,255,.4);}

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

.trace {display:flex; align-items:center; gap:.3rem; flex-wrap:wrap; margin:.2rem 0 .7rem;}
.node {background:#eef4fd; color:#1c2b4a; border:1px solid #cfe0f8; border-radius:999px; padding:.16rem .55rem;
  font-size:.68rem; font-weight:650;}
.node.done {background:linear-gradient(135deg,#0f9d58,#0c8a4d); color:#fff; border-color:transparent;
  box-shadow:0 2px 6px rgba(15,157,88,.28);}
.arrow {color:#b6bdca; font-weight:700; font-size:.7rem;}

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


# --- Floating nav toggle ----------------------------------------------------
# A fancy black button pinned to the right edge that opens/closes the sidebar.
# It drives Streamlit's own collapse/expand control so the sidebar state stays
# in sync (rather than just hiding it with CSS). Runs in a 0-height component
# iframe but appends the button to the parent document so it floats over the app.
components.html(
    """
    <script>
    const doc = window.parent.document;
    const ID = "insur-nav-toggle";

    function sidebarOpen() {
        const sb = doc.querySelector('section[data-testid="stSidebar"]');
        return sb && sb.getAttribute("aria-expanded") !== "false"
                  && sb.offsetWidth > 5;
    }

    function toggleSidebar() {
        if (sidebarOpen()) {
            const c = doc.querySelector(
                '[data-testid="stSidebarCollapseButton"] button,'
              + '[data-testid="stSidebarCollapseButton"]');
            if (c) c.click();
        } else {
            const e = doc.querySelector(
                '[data-testid="stSidebarCollapsedControl"] button,'
              + '[data-testid="stExpandSidebarButton"],'
              + '[data-testid="stSidebarCollapsedControl"]');
            if (e) e.click();
        }
        setTimeout(paint, 260);
    }

    function paint() {
        const btn = doc.getElementById(ID);
        if (!btn) return;
        const open = sidebarOpen();
        btn.innerHTML = open ? "&#10005;" : "&#9776;";
        btn.title = open ? "Hide navigation" : "Show navigation";
    }

    if (!doc.getElementById(ID)) {
        const btn = doc.createElement("button");
        btn.id = ID;
        btn.innerHTML = "&#10005;";
        Object.assign(btn.style, {
            position: "fixed",
            top: "50%",
            right: "18px",
            transform: "translateY(-50%)",
            zIndex: "999999",
            width: "48px",
            height: "48px",
            borderRadius: "14px",
            border: "1px solid rgba(255,255,255,.14)",
            background: "linear-gradient(145deg,#1b1b1f,#050506)",
            color: "#f4f6fb",
            fontSize: "20px",
            lineHeight: "1",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 10px 26px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.10)",
            transition: "transform .18s ease, box-shadow .2s ease, filter .18s ease",
        });
        btn.onmouseenter = () => {
            btn.style.transform = "translateY(-50%) scale(1.08)";
            btn.style.boxShadow = "0 14px 34px rgba(0,0,0,.55), inset 0 1px 0 rgba(255,255,255,.14)";
            btn.style.filter = "brightness(1.15)";
        };
        btn.onmouseleave = () => {
            btn.style.transform = "translateY(-50%) scale(1)";
            btn.style.boxShadow = "0 10px 26px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.10)";
            btn.style.filter = "none";
        };
        btn.onclick = toggleSidebar;
        doc.body.appendChild(btn);
        paint();
    } else {
        paint();
    }
    </script>
    """,
    height=0,
)


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


def claim_chat_ui(chat_key: str, context: str) -> None:
    """A multi-turn AI chat about a claim; history persists in session state."""
    st.markdown("##### 💬 Chat about this claim")
    history = st.session_state.setdefault(f"chat_{chat_key}", [])
    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    question = st.chat_input("Ask anything about this claim...", key=f"chatin_{chat_key}")
    if question:
        from insurclaim.llm import call_llm

        history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        recent = "\n".join(f"{m['role']}: {m['content']}" for m in history[-6:])
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    answer = call_llm(
                        prompt=f"CLAIM CONTEXT:\n{context[:6000]}\n\n"
                        f"CONVERSATION SO FAR:\n{recent}\n\n"
                        "Answer the user's latest question concisely and specifically.",
                        system="You are a claims-investigation assistant helping a human "
                        "investigator. Answer briefly, grounded ONLY in the claim "
                        "information provided. When asked why something was flagged or "
                        "changed, give the concrete reason (the specific inconsistency).",
                    )
                except Exception as exc:
                    answer = f"(assistant unavailable: {exc})"
            st.markdown(answer)
        history.append({"role": "assistant", "content": answer})


def _investigation_context(
    s: dict, documents: dict | None, coverage: dict | None, amount: dict | None = None
) -> str:
    """Build a compact context string for the claim chat."""
    label, _ = risk_meta(s["risk"])
    action = ("route_to_investigator" if s["risk"] >= RISK_HIGH
              else "fast_track_approve" if s["risk"] < RISK_MEDIUM else "request_more_info")
    parts = [f"Risk score: {s['risk']:.0f}/100 ({label}); recommended action: {action}."]
    if s.get("prob") is not None:
        parts.append(f"ML fraud probability: {s['prob']*100:.0f}%.")
    reasons = [f"- {x.get('message')} ({x.get('evidence')})" for x in s["signals"]]
    if reasons:
        parts.append("Flags / inconsistencies:\n" + "\n".join(reasons))
    if documents and documents.get("missing"):
        parts.append("Missing documents: " + ", ".join(str(d) for d in documents["missing"]))
    if coverage:
        parts.append(f"Coverage: {coverage.get('decision')} - {coverage.get('rationale','')}")
    if amount:
        cur = amount.get("currency") or ""
        parts.append(
            f"Amount assessment: verdict={amount.get('verdict')}; "
            f"demanded={cur} {amount.get('claimed_amount')}; "
            f"fair estimate={cur} {amount.get('fair_estimate')}. "
            f"{amount.get('rationale','')}"
        )
    parts.append("Claim description:\n" + (s.get("description") or "")[:4000])
    return "\n\n".join(parts)


def _render_investigation(s: dict, case_ref: str, *, moved: bool = False,
                          sub: dict | None = None) -> None:
    """Render the full investigation view — the SAME layout for demo and moved claims."""
    label, color = risk_meta(s["risk"])
    action = ("route_to_investigator" if s["risk"] >= RISK_HIGH
              else "fast_track_approve" if s["risk"] < RISK_MEDIUM else "request_more_info")

    st.markdown(agent_trace(4), unsafe_allow_html=True)
    left, right = st.columns([1, 2])
    with left:
        st.markdown(gauge(s["risk"], color), unsafe_allow_html=True)
        st.markdown(badge(f"{label} RISK", color), unsafe_allow_html=True)
        if s["prob"] is not None:
            st.markdown(f"**ML fraud probability:** {s['prob']*100:.0f}%")
        st.markdown(f"**Recommended action:** `{action}`")
        if not moved:
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
        "InsurCalim AI - investigation summary",
        f"Claim {case_ref}  |  risk score: {s['risk']:.0f} ({label})  |  action: {action}",
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
        file_name=f"{case_ref.replace(' ', '_').replace('#', '')}_summary.txt",
        key=f"exp_{case_ref}",
    )

    documents = sub.get("documents") if (moved and sub) else None
    coverage = sub.get("coverage") if (moved and sub) else None
    amount = sub.get("amount") if (moved and sub) else None

    if moved:
        if coverage:
            cmap = {"covered": GOOD, "not_covered": CRITICAL, "needs_review": WARNING}
            st.markdown("##### Policy coverage")
            st.markdown(badge(coverage["decision"].upper().replace("_", " "),
                              cmap.get(coverage["decision"], MUTED)), unsafe_allow_html=True)
            st.caption(coverage.get("rationale", ""))
        if amount:
            st.markdown("##### Claim amount")
            _render_amount(amount)
    else:
        if st.button("🛡️ Check policy coverage", key=f"cov_{case_ref}"):
            from insurclaim import coverage as cov_mod

            with st.spinner("Checking against uploaded policies..."):
                cov = cov_mod.check_coverage(s["description"])
            cmap = {"covered": GOOD, "not_covered": CRITICAL, "needs_review": WARNING}
            st.markdown("##### Policy coverage")
            st.markdown(badge(cov["decision"].upper().replace("_", " "),
                              cmap.get(cov["decision"], MUTED)), unsafe_allow_html=True)
            st.write(cov["rationale"])
            if cov.get("clause"):
                st.caption(f"Cited clause: {cov['clause'][:200]}")

    # AI chat — same for both; each claim keeps its own thread.
    claim_chat_ui(f"moved_{case_ref}" if moved else f"demo_{case_ref}",
                  _investigation_context(s, documents, coverage, amount))

    case_management_ui(case_ref)

    # A moved claim additionally exposes its full detailed report + PDF.
    if moved and sub:
        with st.expander("📄 Full detailed report + PDF (coverage, documents, why flagged)"):
            render_detailed_and_pdf(
                sub["final"], case_ref, sub.get("text", ""),
                doc_ids=sub.get("doc_ids"), documents=sub.get("documents"),
                coverage=sub.get("coverage"), amount=sub.get("amount"),
                media=sub.get("media"),
            )

    with st.expander("Run the full LLM pipeline (timeline + narrative reasoning)"):
        st.caption("Uses the LLM; on the free tier this may take a moment or fall back.")
        if st.button("Run full AI investigation", type="primary", key=f"runfull_{case_ref}"):
            from insurclaim.graph import run_claim

            if moved and sub:
                with st.spinner("Running intake → timeline → fraud → report..."):
                    sub["final"] = run_claim({"raw_documents": sub.get("text", "")})
                st.rerun()
            else:
                with st.spinner("Running intake → timeline → fraud → report..."):
                    final = run_claim({"claim": repo.get_claim(int(s["id"]))})
                render_detailed_and_pdf(final, case_ref, s["description"])


def page_report(scored: list[dict]) -> None:
    st.markdown("### Investigation report")
    by_id = {s["id"]: s for s in scored}
    cases = st.session_state.get("investigation_cases", {})

    # One unified picker: moved (uploaded) cases first, then the demo claims — so a
    # moved claim never pushes the demo claims out of view.
    options: list[str] = [f"moved::{ref}" for ref in cases] + [f"demo::{i}" for i in by_id]
    if not options:
        st.info("No claims to investigate.")
        return

    def _label(key: str) -> str:
        kind, val = key.split("::", 1)
        if kind == "moved":
            return f"📥 {val} (uploaded)"
        return f"#{val} · {by_id[int(val)]['fraud_type']}"

    sel = st.session_state.get("selected_investigation_case")
    default_key = f"moved::{sel}" if sel and f"moved::{sel}" in options else options[0]
    choice = st.selectbox("Select a claim to investigate", options,
                          index=options.index(default_key), format_func=_label,
                          key="inv_select")

    kind, val = choice.split("::", 1)
    if kind == "moved":
        sub = cases[val]
        final = sub.get("final", {}) or {}
        report = final.get("report", {}) or {}
        # Adapt the moved claim into the exact shape the demo view expects.
        s = {
            "id": val,
            "fraud_type": "uploaded",
            "is_fraud": None,
            "risk": float(report.get("risk_score", 0) or 0),
            "prob": final.get("fraud_probability"),
            "signals": final.get("fraud_signals", []) or [],
            "matches": final.get("similar_claims", []) or [],
            "description": sub.get("text", ""),
            "location": "",
            "amount": None,
        }
        _render_investigation(s, val, moved=True, sub=sub)
    else:
        claim_id = int(val)
        _render_investigation(by_id[claim_id], f"claim #{claim_id}", moved=False)


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


def _two_line(text: str, max_chars: int = 180) -> str:
    """Trim a long block to a short ~2-line overview, cutting on a word boundary."""
    text = " ".join((text or "").split())
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"


def _render_quick_report(report: dict, media: list[dict] | None = None) -> None:
    score = float(report.get("risk_score", 0) or 0)
    lbl, col = risk_meta(score)
    st.markdown(agent_trace(4), unsafe_allow_html=True)
    # Gauge + risk badge on the left; the key findings fill the space on the right.
    left, right = st.columns([1, 1.7], gap="medium")
    with left:
        st.markdown(gauge(score, col), unsafe_allow_html=True)
        st.markdown(
            badge(f"{lbl} RISK · {report.get('recommended_action','-')}", col),
            unsafe_allow_html=True,
        )
    with right:
        flags = report.get("top_flags", []) or []
        if flags:
            st.markdown("**Key findings — what stands out about this claim**")
            # Concise bullet points (one line each); the full evidence for each is in
            # the "Go Deeper" detail below.
            st.markdown("\n".join(f"- {fl['summary']}" for fl in flags if fl.get("summary")))
        else:
            st.caption("No specific red flags surfaced for this claim.")
        # A short 2-line overview of each uploaded photo / video frame. The full vision
        # read lives under "Go Deeper" so this stays a quick glance.
        photos = [m for m in (media or []) if m.get("damage")]
        if photos:
            st.markdown("**📷 What the photos show**")
            st.markdown(
                "\n".join(
                    f"- **{m.get('file_name','')}** — {_two_line(m.get('damage',''))}"
                    for m in photos
                )
            )


_AUTO_COVERAGE = object()  # sentinel: compute coverage internally when not supplied


_AMOUNT_VERDICT = {
    "reasonable": ("Amount looks reasonable", GOOD),
    "overstated": ("Amount overstated", CRITICAL),
    "understated": ("Amount understated", WARNING),
    "insufficient_info": ("Not enough detail to price", MUTED),
}


def _fmt_money(currency: str, value) -> str | None:
    """Format a monetary value like 'PKR 250,000', or None when not numeric."""
    try:
        return f"{currency} {float(value):,.0f}".strip()
    except (TypeError, ValueError):
        return None


def _render_amount(amount: dict | None) -> None:
    """Render the 'is the demanded amount fair, and if not how much?' block."""
    if not amount:
        return
    verdict = amount.get("verdict") or "insufficient_info"
    label, col = _AMOUNT_VERDICT.get(verdict, ("", MUTED))
    cur = amount.get("currency") or "PKR"
    st.markdown("**💰 Claim amount assessment — is the demanded cost justified?**")
    st.markdown(badge(label, col), unsafe_allow_html=True)
    st.caption(
        "🌐 Estimated from live market prices (web search)."
        if amount.get("priced_from") == "market"
        else "🧮 Estimated from the model's own knowledge (no live prices available)."
    )
    st.caption("This is a fair-cost **estimate** to guide a human adjuster — not a final settlement.")
    claimed = _fmt_money(cur, amount.get("claimed_amount"))
    if claimed:
        st.markdown(f"- **Demanded:** {claimed}")
    fair = _fmt_money(cur, amount.get("fair_estimate"))
    if fair:
        lo = _fmt_money(cur, amount.get("fair_low"))
        hi = _fmt_money(cur, amount.get("fair_high"))
        rng = f"  _(fair range {lo} – {hi})_" if lo and hi else ""
        st.markdown(f"- **Fair estimate:** {fair}{rng}")
    for li in amount.get("line_items", []) or []:
        est = _fmt_money(cur, li.get("estimate"))
        src = (li.get("source") or "").strip()
        src_note = f"  ·  _{src}_" if src else ""
        st.markdown(f"    - {li.get('item','')}: {est or '—'}{src_note}")
    if amount.get("rationale"):
        st.caption(amount["rationale"])
    # Show the raw market-price findings the estimate was grounded in (the "reference"
    # a reviewer asked for), when a live web search returned anything.
    sources_text = (amount.get("sources_text") or "").strip()
    if sources_text:
        with st.expander("🌐 Sources (live web search) — prices this estimate is based on"):
            st.text(sources_text)


def render_detailed_and_pdf(
    state: dict,
    claim_ref: str,
    description: str = "",
    doc_ids: list[int] | None = None,
    documents: dict | None = None,
    coverage=_AUTO_COVERAGE,
    amount: dict | None = None,
    media: list[dict] | None = None,
) -> None:
    """Show a detailed view (coverage, documents, amount, fraud reasons, timeline) + a PDF.

    Pass a precomputed `coverage` dict (or None) to avoid re-running the coverage
    LLM on every rerender; omit it to compute coverage here. `media` carries the
    per-photo vision reads so the full damage description is shown here (the top panel
    only shows a short overview).
    """
    from insurclaim import coverage as cov_mod
    from insurclaim import report_builder

    if coverage is _AUTO_COVERAGE:
        cov = None
        try:
            if description:
                cov = cov_mod.check_coverage(description, doc_ids=doc_ids)
                if cov.get("decision") == "needs_review" and not cov.get("citations"):
                    cov = None  # no policies uploaded - skip the coverage block
        except Exception:
            cov = None
    else:
        cov = coverage

    detailed = report_builder.build_detailed(
        state, coverage=cov, documents=documents, amount=amount
    )
    with st.expander("📄 Detailed view — coverage, documents, why flagged, timeline",
                     expanded=True):
        if detailed["summary"]:
            st.markdown("**Investigator summary**")
            st.write(detailed["summary"])
        # Full per-photo / per-video vision analysis (the short overview is shown up top).
        photos = [m for m in (media or []) if m.get("damage")]
        if photos:
            st.markdown("**📷 Photo analysis — full damage read**")
            for m in photos:
                st.markdown(f"- **{m.get('file_name','')}**: {m.get('damage','')}")
        if cov:
            cmap = {"covered": GOOD, "not_covered": CRITICAL, "needs_review": WARNING}
            st.markdown("**Policy coverage**")
            st.markdown(badge(cov["decision"].upper().replace("_", " "),
                              cmap.get(cov["decision"], MUTED)), unsafe_allow_html=True)
            st.caption(cov.get("rationale", ""))
        if documents and (documents.get("required") or documents.get("missing")
                          or documents.get("incomplete")):
            st.markdown("**Document completeness**")
            if documents.get("present"):
                st.markdown("✓ Present: " + ", ".join(str(d) for d in documents["present"]))
            if documents.get("missing"):
                st.markdown(
                    ":red[✗ Missing: " + ", ".join(str(d) for d in documents["missing"]) + "]"
                )
            for inc in documents.get("incomplete", []):
                if isinstance(inc, dict):
                    st.markdown(
                        f":orange[⚠ Incomplete: {inc.get('document','')} — {inc.get('issue','')}]"
                    )
                else:
                    st.markdown(f":orange[⚠ Incomplete: {inc}]")
            if documents.get("notes"):
                st.caption(documents["notes"])
        _render_amount(amount)
        if detailed.get("fraud_reasons"):
            st.markdown("**🔎 Why we flagged this — specific inconsistencies**")
            for i, r in enumerate(detailed["fraud_reasons"], 1):
                sev = (r.get("severity") or "").upper()
                st.markdown(
                    f"{i}. **{r.get('summary','')}**" + (f" · `{sev}`" if sev else "")
                    + (f"  \n   _{r.get('evidence','')}_" if r.get("evidence") else "")
                )
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
            st.markdown("**Similar known-fraud matches — what matches**")
            for m in detailed["similar_fraud"]:
                st.markdown(
                    f"- {int((m.get('similarity') or 0)*100)}% match to claim "
                    f"#{m.get('claim_id')} ({m.get('fraud_type')})"
                    + (f"  \n   _That claim: {m['snippet']}_" if m.get("snippet") else "")
                )

    pdf = report_builder.to_pdf(detailed, claim_ref=claim_ref)
    st.download_button(
        "⬇ Download full PDF report",
        pdf,
        file_name=f"{claim_ref.replace(' ', '_').replace('#', '')}_report.pdf",
        mime="application/pdf",
        type="primary",
    )


def _move_to_investigation(sub: dict) -> None:
    """Button (below the PDF download) to hand this claim to the Investigation page."""
    cases = st.session_state.setdefault("investigation_cases", {})
    ref = sub.get("case_ref")
    if ref and ref in cases:
        st.success(
            f"✔ Moved to the Investigation report as **{ref}** — open the "
            "🔍 Investigation report section to work the case."
        )
        return
    if st.button("➡ Move to Investigation Report", key="move_to_investigation"):
        ref = f"uploaded #{len(cases) + 1}"
        sub["case_ref"] = ref
        cases[ref] = sub
        try:
            repo.set_case_status(ref, "open", None)
        except Exception:
            pass
        st.session_state["selected_investigation_case"] = ref
        st.session_state["_goto"] = "🔍 Investigation report"
        st.rerun()


_ACTION_PHRASING = {
    "route_to_investigator": "route this claim to a human investigator before any payout",
    "investigate": "route this claim to a human investigator before any payout",
    "auto_approve": "let this claim proceed on the normal track",
    "approve": "let this claim proceed on the normal track",
    "pay": "let this claim proceed on the normal track",
    "request_more_info": "ask the claimant for more information before deciding",
    "deny": "flag this claim for a decline decision by a human adjuster",
}


def _plain_summary(report: dict, amount: dict | None) -> str:
    """Compose a short plain-English paragraph from data already in the report.

    Deterministic (no extra LLM call) so it renders instantly and works even when the
    providers are rate-limited. Explains, in everyday words, what the system concluded
    and what it recommends a human do next.
    """
    score = float(report.get("risk_score", 0) or 0)
    lbl, _ = risk_meta(score)
    action_key = str(report.get("recommended_action", "")).lower()
    action = _ACTION_PHRASING.get(action_key, "have a human adjuster review this claim")

    sentences = [
        f"This claim scored **{score:.0f}/100** ({lbl.lower()} risk), so the system "
        f"recommends we **{action}**."
    ]
    flags = report.get("top_flags", []) or []
    if flags:
        first = flags[0].get("summary", "").strip().rstrip(".")
        extra = f", the most notable being *{first}*" if first else ""
        n = len(flags)
        sentences.append(
            f"It surfaced **{n} point{'s' if n != 1 else ''}** worth checking{extra}."
        )
    if amount:
        verdict = amount.get("verdict") or "insufficient_info"
        cur = amount.get("currency") or "PKR"
        fair = _fmt_money(cur, amount.get("fair_estimate"))
        if verdict == "insufficient_info":
            sentences.append("There was not enough detail to estimate a fair cost.")
        elif fair:
            sentences.append(
                f"On cost, the demanded amount looks **{verdict}** against a fair "
                f"estimate of about **{fair}**."
            )
    sentences.append(
        "Nothing is auto-decided — a human makes the final call using the detail below."
    )
    return " ".join(sentences)


def _render_submission(sub: dict) -> None:
    """Render a stored claim submission as three tiers: headline → plain summary → detail.

    Reads from session state so the result survives navigating away and back.
    """
    for method, msg in sub.get("notices", []):
        getattr(st, method, st.write)(msg)
    if sub.get("degraded"):
        st.error(
            "⚠ AI models were unavailable (all LLM providers rate-limited), so the "
            "document, coverage and fraud-reasoning checks were skipped — only the "
            "local ML + similarity ran. **This risk score is not reliable.** Add a "
            "working API key or try again later, then re-run this claim."
        )

    report = sub["final"].get("report", {})

    # Tier 1 — headline: gauge + risk badge + key-finding bullets + short photo overview.
    _render_quick_report(report, media=sub.get("media"))

    # Tier 2 — plain-English paragraph anyone can read at a glance.
    st.markdown("**In plain English**")
    st.info(_plain_summary(report, sub.get("amount")))

    # Tier 3 — the full investigator detail, gated behind a "Go Deeper" toggle so the
    # headline stays clean until the reviewer asks for everything.
    go_key = "go_deeper_submission"
    if st.toggle("🔬 Go Deeper — full investigator detail", key=go_key):
        render_detailed_and_pdf(
            sub["final"], sub.get("ref", "uploaded claim"), sub.get("text", ""),
            doc_ids=sub.get("doc_ids"), documents=sub.get("documents"),
            coverage=sub.get("coverage"), amount=sub.get("amount"),
            media=sub.get("media"),
        )
    _move_to_investigation(sub)


def page_submit() -> None:
    st.markdown("### ✍️ Submit a claim (documents, photos & videos)")
    st.caption(
        "Upload the claim narrative / police report / FIR (txt · pdf · docx), damage "
        "photos, and dashcam / walkaround videos. The system extracts the data, "
        "checks media for reuse, damage, and signs of AI-generated (deepfake) "
        "evidence, then runs the full investigation."
    )
    if st.session_state.get("last_submission"):
        if st.button("🆕 Start a new claim"):
            st.session_state.pop("last_submission", None)
            st.rerun()
    files = st.file_uploader(
        "Upload claim files (documents, photos, or videos)",
        type=["txt", "pdf", "docx", "jpg", "jpeg", "png",
              "mp4", "mov", "avi", "mkv", "webm"],
        accept_multiple_files=True,
    )
    extra = st.text_area("Or paste claim text", height=100)

    # Pick which uploaded policy (or policies) this claim falls under. The claim is
    # checked for coverage and required-document completeness against these first.
    available_policies = repo.list_policy_documents()
    policy_label = {
        f"#{p['id']} · {p['company']} · {p['doc_name']}": p["id"] for p in available_policies
    }
    selected_labels = st.multiselect(
        "Check this claim against which policy? (select one or more)",
        options=list(policy_label.keys()),
        help="Policies come from the 'Policy & coverage' page. Leave empty to check "
             "against all uploaded policies.",
    )
    selected_doc_ids = [policy_label[label] for label in selected_labels]
    if not available_policies:
        st.caption("No policies uploaded yet — add them on the 'Policy & coverage' page.")

    if st.button("Process & investigate", type="primary"):
        from insurclaim import intake_docs
        from insurclaim.graph import run_claim

        # A single live "status" panel so the user can see exactly what the system is
        # doing at each moment, using the real pipeline steps (no fake progress bar).
        with st.status("🔎 Investigating the claim…", expanded=True) as status:
            doc_tuples: list[tuple[str, bytes]] = []
            media_infos: list[dict] = []
            n_docs = n_img = n_vid = 0

            st.write("📥 **Reading the files you uploaded…**")
            for f in files or []:
                kind = intake_docs.classify_upload(f.name)
                data = f.getvalue()
                if kind == "document":
                    st.write(f"📄 Reading the text inside `{f.name}`…")
                    doc_tuples.append((f.name, data))
                    n_docs += 1
                elif kind == "image":
                    st.write(f"🖼 Checking whether photo `{f.name}` was reused from another claim…")
                    info = intake_docs.process_photo(f.name, data)
                    info["kind"] = "photo"
                    st.write(f"👁 Looking at `{f.name}` to see the damage and whether the photo is AI-generated…")
                    info["damage"] = intake_docs.analyze_damage(data)
                    info["synthetic"] = intake_docs.detect_synthetic_media(f.name, data)
                    media_infos.append(info)
                    n_img += 1
                elif kind == "video":
                    st.write(f"🎞 Taking a still picture from the video `{f.name}`…")
                    info = intake_docs.process_video(f.name, data)
                    frame = info.get("frame_jpeg")
                    if frame:
                        st.write(f"👁 Looking at the video from `{f.name}` for damage and signs of fakery…")
                        info["damage"] = intake_docs.analyze_damage(frame)
                        info["synthetic"] = intake_docs.detect_synthetic_media(f.name, frame)
                    media_infos.append(info)
                    n_vid += 1
                else:
                    st.warning(f"Unsupported file type skipped: {f.name}")

            text = intake_docs.build_claim_text(doc_tuples, media_infos)
            if extra.strip():
                text = (extra.strip() + "\n\n" + text).strip()
            if not text:
                status.update(label="Nothing to investigate", state="error")
                st.warning("Provide at least one document, photo, video, or some text.")
                return

            # Collect user-facing notices so they can be re-shown when the stored result
            # is re-rendered after navigating away and back.
            notices: list[tuple[str, str]] = [
                ("success",
                 f"Ingested {n_docs} document(s) · {n_img} photo(s) · {n_vid} video(s).")
            ]
            for info in media_infos:
                label = info.get("kind", "media").capitalize()
                if info.get("duplicate_of"):
                    notices.append((
                        "error",
                        f"⚠ {label} {info['file_name']} matches media already on claim "
                        f"#{info['duplicate_of']['claim_id']} — possible reuse.",
                    ))
                syn = info.get("synthetic")
                if syn:
                    notices.append((
                        "error",
                        f"🧪 AI-generated media suspected · {info['file_name']} "
                        f"({syn['severity']}): {syn['evidence']}",
                    ))
                # The full vision damage read is NOT dumped as a notice here — a short
                # 2-line overview is shown in the key-findings panel, and the full text
                # under "Go Deeper" (see _render_quick_report / render_detailed_and_pdf).

            # 1) Policy gate FIRST: coverage + required-document completeness, checked
            #    against the selected policy (or all policies if none selected).
            from insurclaim import coverage as cov_mod

            documents = coverage_result = None
            st.write("🛡 **Checking whether the policy covers this claim, and which documents are missing…**")
            try:
                documents = cov_mod.check_documents(text, doc_ids=selected_doc_ids or None)
            except Exception:
                documents = None
            try:
                coverage_result = cov_mod.check_coverage(text, doc_ids=selected_doc_ids or None)
                if (coverage_result.get("decision") == "needs_review"
                        and not coverage_result.get("citations")):
                    coverage_result = None  # no policies on file - skip the block
            except Exception:
                coverage_result = None
            if documents and documents.get("missing"):
                notices.append((
                    "warning",
                    "📄 Missing documents: " + ", ".join(str(d) for d in documents["missing"]),
                ))

            # 2) Then the fraud pipeline. Describe it in plain language (no agent jargon)
            #    so a non-technical viewer understands what the system is doing.
            st.write("🧾 **Understanding the claim and pulling out the key facts…**")
            st.write("🕵️ **Rebuilding what happened and checking the story for fraud…**")
            st.write("📝 **Writing up the findings into an investigator report…**")
            final = run_claim({"raw_documents": text})

            # 3) Assess whether the demanded amount is justified (and if not, how much
            #    a fair settlement would be) — useful even when the claim is not fraud.
            from insurclaim import amount as amount_mod

            amount_assessment = None
            st.write("💰 **Working out a fair repair cost from today's market prices…**")
            try:
                claimed = (final.get("extracted") or {}).get("claimed_amount")
                amount_assessment = amount_mod.assess_amount(
                    text, claimed_amount=claimed, doc_ids=selected_doc_ids or None
                )
            except Exception:
                amount_assessment = None

            # 4) Store the whole result so it survives navigation, then render below.
            st.session_state["last_submission"] = {
                "ref": "uploaded claim",
                "text": text,
                "doc_ids": selected_doc_ids or None,
                "documents": documents,
                "coverage": coverage_result,
                "amount": amount_assessment,
                "final": final,
                "notices": notices,
                "media": media_infos,
                "degraded": bool(final.get("extracted", {}).get("_extraction_degraded")),
            }
            status.update(label="✅ Investigation complete", state="complete", expanded=False)

    # Render the last submission (fresh, or restored after navigating away and back).
    if st.session_state.get("last_submission"):
        _render_submission(st.session_state["last_submission"])


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
        up = st.file_uploader("...or upload a policy file (txt / pdf / docx)",
                              type=["txt", "pdf", "docx"])
        submitted = st.form_submit_button("Save & index policy")
    if submitted:
        content = text.strip()
        if up:
            from insurclaim import intake_docs

            with st.spinner(
                f"Extracting text from {up.name} "
                "(scanned PDFs are OCR'd with the vision model — this can take a moment)..."
            ):
                content = intake_docs.extract_text(up.name, up.getvalue())
            if not content:
                st.error(
                    f"Could not extract any text from **{up.name}**, even with OCR. "
                    "The vision model may be unavailable, or the file has no readable "
                    "text. Try again, use a text-based PDF / DOCX, or paste the policy "
                    "text into the box above."
                )
                return
        if content:
            doc_id = coverage.add_policy_document(company, name, content)
            st.success(f"Saved policy #{doc_id} and indexed it for coverage checks.")
            st.cache_data.clear()
        else:
            st.warning("Provide policy text or a file.")

    docs = repo.list_policy_documents()
    if docs:
        st.markdown("##### Policies on file")
        for d in docs:
            row = st.columns([1, 3, 3, 1])
            row[0].markdown(f"**#{d['id']}**")
            row[1].markdown(f"**{d['company']}**  \n{d['doc_name']}")
            row[2].caption(f"{d['preview']}...")
            if row[3].button("🗑 Remove", key=f"del_policy_{d['id']}"):
                coverage.remove_policy_document(d["id"])
                st.cache_data.clear()
                st.success(f"Removed policy #{d['id']}.")
                st.rerun()

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


def _render_overview(ov: dict, sub: dict) -> None:
    """Render the consolidated claimant overview: profile, summary, documents, risk."""
    label, color = risk_meta(ov["risk_score"])

    st.markdown(
        f'<div class="hero"><h1>🧾 {ov["claimant"]}</h1>'
        "<p>Consolidated overview of this claimant and their claim, built from the "
        "uploaded documents.</p></div>",
        unsafe_allow_html=True,
    )

    # Claimed amount: reuse the amount assessment's currency when available.
    cur = (sub.get("amount") or {}).get("currency") or "PKR"
    claimed = _fmt_money(cur, ov.get("claimed_amount")) or "-"

    row1 = st.columns(4)
    for col, card in zip(row1, [
        kpi("Claimant", ov["claimant"]),
        kpi("Incident date", ov["incident_date"]),
        kpi("Location", ov["location"] or "-"),
        kpi("Demanded amount", claimed),
    ]):
        col.markdown(card, unsafe_allow_html=True)

    row2 = st.columns(4)
    docs = ov.get("documents") or {}
    present_n = len(docs.get("present") or [])
    required_n = len(docs.get("required") or [])
    for col, card in zip(row2, [
        kpi("Vehicle", ov["vehicle"]),
        kpi("Reported date", ov["report_date"]),
        kpi("Documents", f"{present_n}/{required_n}" if required_n else str(present_n),
            "present / required"),
        kpi("Risk score", f"{ov['risk_score']:.0f}", label),
    ]):
        col.markdown(card, unsafe_allow_html=True)

    st.write("")
    left, right = st.columns([2, 1])
    with left:
        st.markdown("##### Claim summary")
        st.markdown(ov["summary"])

        if ov.get("parties"):
            st.markdown("##### Parties")
            for p in ov["parties"]:
                st.markdown(f"- **{p['full_name']}** — {p['role']}")

        if docs and (docs.get("required") or docs.get("missing") or docs.get("incomplete")):
            st.markdown("##### Documents checklist")
            if docs.get("present"):
                st.markdown("✓ Present: " + ", ".join(str(d) for d in docs["present"]))
            if docs.get("missing"):
                st.markdown(
                    ":red[✗ Missing: " + ", ".join(str(d) for d in docs["missing"]) + "]"
                )
            for inc in docs.get("incomplete", []):
                if isinstance(inc, dict):
                    st.markdown(
                        f":orange[⚠ Incomplete: {inc.get('document','')} — {inc.get('issue','')}]"
                    )
                else:
                    st.markdown(f":orange[⚠ Incomplete: {inc}]")
            if docs.get("notes"):
                st.caption(docs["notes"])

    with right:
        st.markdown("##### Risk snapshot")
        st.markdown(gauge(ov["risk_score"], color), unsafe_allow_html=True)
        st.markdown(badge(f"{label} RISK", color), unsafe_allow_html=True)
        st.markdown(f"**Recommended action:** `{ov['recommended_action']}`")


def page_overview_claimant() -> None:
    """A dedicated section: overview of an uploaded claimant after their documents load."""
    from insurclaim import overview as overview_mod

    st.markdown("### 🧾 Claimant overview")

    # Collect uploaded cases: the latest submission plus any moved to investigation.
    cases: dict[str, dict] = {}
    for ref, sub in st.session_state.get("investigation_cases", {}).items():
        cases[ref] = sub
    last = st.session_state.get("last_submission")
    if last:
        cases.setdefault(last.get("ref", "uploaded claim"), last)

    if not cases:
        st.info("Upload a claim on the '✍️ Submit a claim' page first — the claimant "
                "overview will appear here.")
        return

    refs = list(cases.keys())
    choice = st.selectbox("Select a claimant", refs, index=len(refs) - 1,
                          key="overview_select")
    sub = cases[choice]
    final = sub.get("final", {}) or {}

    ov = overview_mod.build_overview(
        final.get("extracted"), final.get("report"), sub.get("documents")
    )
    _render_overview(ov, sub)


PAGES = {
    "📊 Overview": page_overview,
    "📋 Claims queue": page_queue,
    "🔍 Investigation report": page_report,
    "🕸️ Fraud rings": page_rings,
    "📈 Analytics": page_analytics,
    "✍️ Submit a claim": page_submit,
    "🧾 Claimant overview": page_overview_claimant,
    "🛡️ Policy & coverage": page_policy,
    "📉 Model performance": page_model,
}
NO_ARG_PAGES = ("✍️ Submit a claim", "🧾 Claimant overview",
                "🛡️ Policy & coverage", "📉 Model performance")


def _check_auth() -> None:
    """Gate the dashboard behind a landing page + login. Stops rendering when not authed."""
    if st.session_state.get("authenticated"):
        return

    # Demo credentials come from the environment; defaults let the demo run out of the box.
    expected_user = os.getenv("APP_USERNAME", "admin")
    expected_pass = os.getenv("APP_PASSWORD", "insurclaim2026")

    # Single sign-in hand-off from the React landing page: it redirects here with
    # "?token=<APP_LOGIN_TOKEN>" after the user signs in there, so we don't ask again.
    expected_token = os.getenv("APP_LOGIN_TOKEN", "insurclaim-demo-2026")
    incoming_token = st.query_params.get("token")
    if expected_token and incoming_token == expected_token:
        st.session_state["authenticated"] = True
        st.query_params.clear()  # drop the token from the URL once consumed
        return

    st.markdown(
        '<div class="hero"><h1>🔎 InsurCalim AI</h1>'
        "<p>AI-assisted auto-insurance claim investigation — explainable, human-in-the-loop. "
        "The system flags and ranks; it never auto-denies. Sign in to open the investigator "
        "dashboard.</p></div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(4)
    for col, card in zip(cols, [
        kpi("Fraud drained / yr", "$80B+", "globally (2025)"),
        kpi("Claims with fraud", "~10%", "of P&C losses"),
        kpi("AI-fake media", "25-30%", "of claims"),
        kpi("Cost / claim", "~$0.02", "on the balanced tier"),
    ]):
        col.markdown(card, unsafe_allow_html=True)

    st.write("")
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        st.markdown("#### 🔐 Sign in")
        with st.form("login_form"):
            username = st.text_input("Username", value="")
            password = st.text_input("Password", type="password", value="")
            submitted = st.form_submit_button("Sign in", use_container_width=True)
        if submitted:
            if username == expected_user and password == expected_pass:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Invalid username or password.")
        st.caption("Demo access — synthetic & public data only, no real customer information.")

    st.stop()


def main() -> None:
    _check_auth()
    st.sidebar.markdown("## 🔎 InsurCalim AI")
    st.sidebar.caption("Fraud investigation dashboard")
    # Honour a one-shot programmatic navigation request (e.g. "Move to Investigation
    # Report"). Set before the radio is created so we don't modify a live widget key.
    goto = st.session_state.pop("_goto", None)
    if goto in PAGES:
        st.session_state["nav"] = goto
    choice = st.sidebar.radio("Navigate", list(PAGES.keys()),
                              label_visibility="collapsed", key="nav")
    st.sidebar.markdown("---")
    if st.sidebar.button("🔓 Log out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()
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
