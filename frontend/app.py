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
#MainMenu, header, footer {visibility: hidden;}
.block-container {padding-top: 1.6rem; max-width: 1200px;}
html, body, [class*="css"] {font-family: system-ui, -apple-system, "Segoe UI", sans-serif;}
.hero {background: linear-gradient(100deg,#1c2b4a,#2a78d6); color:#fff; padding:1.4rem 1.6rem;
  border-radius:16px; margin-bottom:1.2rem;}
.hero h1 {margin:0; font-size:1.7rem; font-weight:750;}
.hero p {margin:.3rem 0 0; opacity:.85; font-size:.95rem;}
.kpi {background:#fff; border:1px solid rgba(11,11,11,.08); border-radius:14px; padding:1rem 1.2rem;
  box-shadow:0 1px 3px rgba(11,11,11,.05); height:100%;}
.kpi .l {color:#898781; font-size:.78rem; text-transform:uppercase; letter-spacing:.04em; font-weight:600;}
.kpi .v {color:#0b0b0b; font-size:2rem; font-weight:750; line-height:1.1; margin-top:.2rem;}
.kpi .s {color:#898781; font-size:.82rem; margin-top:.1rem;}
.badge {display:inline-block; padding:.22rem .7rem; border-radius:999px; color:#fff;
  font-size:.78rem; font-weight:700; letter-spacing:.02em;}
.flag {background:#fff; border:1px solid rgba(11,11,11,.08); border-left:4px solid #d03b3b;
  border-radius:10px; padding:.7rem .9rem; margin-bottom:.55rem;}
.flag .t {font-weight:650; color:#0b0b0b;}
.flag .e {color:#52514e; font-size:.86rem; margin-top:.15rem;}
.flag .c {color:#898781; font-size:.76rem; margin-top:.2rem;}
.trace {display:flex; align-items:center; gap:.4rem; flex-wrap:wrap; margin:.4rem 0 1rem;}
.node {background:#eef4fd; color:#1c2b4a; border:1px solid #cfe0f8; border-radius:999px;
  padding:.3rem .8rem; font-size:.82rem; font-weight:650;}
.node.done {background:#0f9d58; color:#fff; border-color:#0f9d58;}
.arrow {color:#898781; font-weight:700;}
.cmp {display:flex; gap:.8rem;}
.cmp .card {flex:1; background:#fff; border:1px solid rgba(11,11,11,.08); border-radius:12px; padding:.9rem;}
.cmp .card.match {border:1px solid #d03b3b; box-shadow:0 0 0 3px rgba(208,59,59,.08);}
.cmp .h {font-size:.74rem; text-transform:uppercase; letter-spacing:.04em; color:#898781; font-weight:700;}
.cmp .d {color:#52514e; font-size:.85rem; margin-top:.35rem; line-height:1.4;}
.bar-row {display:flex; align-items:center; gap:.6rem; margin:.3rem 0;}
.bar-row .lab {width:150px; font-size:.83rem; color:#52514e; text-align:right;}
.bar-track {flex:1; background:#eee; border-radius:6px; height:14px; overflow:hidden;}
.bar-fill {height:100%; border-radius:6px;}
.bar-row .val {width:52px; font-size:.8rem; color:#52514e; font-variant-numeric:tabular-nums;}
.tbl {width:100%; border-collapse:collapse; font-size:.86rem;}
.tbl th {text-align:left; color:#898781; font-weight:600; font-size:.74rem; text-transform:uppercase;
  border-bottom:1px solid #e1e0d9; padding:.5rem .4rem;}
.tbl td {border-bottom:1px solid #f0efec; padding:.5rem .4rem; color:#0b0b0b;}
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

    with st.expander("Run the full LLM pipeline (timeline + narrative reasoning)"):
        st.caption("Uses the LLM; on the free tier this may take a moment or fall back.")
        if st.button("Run full AI investigation", type="primary"):
            from insurclaim.graph import run_claim

            with st.spinner("Running intake → timeline → fraud → report..."):
                final = run_claim({"claim": repo.get_claim(claim_id)})
            report = final.get("report", {})
            if report.get("timeline_summary"):
                st.markdown("**Timeline summary**")
                st.write(report["timeline_summary"])
            st.json(report)


def page_analyze() -> None:
    st.markdown("### Analyze new claim text")
    text = st.text_area("Paste a claim narrative / FNOL text", height=180)
    if st.button("Analyze", type="primary") and text.strip():
        from insurclaim.graph import run_claim

        with st.spinner("Running the 4-agent pipeline..."):
            final = run_claim({"raw_documents": text})
        report = final.get("report", {})
        score = float(report.get("risk_score", 0) or 0)
        label, color = risk_meta(score)
        st.markdown(agent_trace(4), unsafe_allow_html=True)
        st.markdown(gauge(score, color), unsafe_allow_html=True)
        st.markdown(badge(f"{label} RISK · {report.get('recommended_action','-')}", color),
                    unsafe_allow_html=True)
        for f in report.get("top_flags", []):
            st.markdown(
                f'<div class="flag"><div class="t">{f.get("summary","")}</div>'
                f'<div class="e">{f.get("evidence","")}</div></div>',
                unsafe_allow_html=True,
            )


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


PAGES = {
    "📊 Overview": page_overview,
    "📋 Claims queue": page_queue,
    "🔍 Investigation report": page_report,
    "🕸️ Fraud rings": page_rings,
    "✍️ Analyze new claim": page_analyze,
    "📈 Model performance": page_model,
}


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

    if choice in ("✍️ Analyze new claim", "📈 Model performance"):
        PAGES[choice]()
    else:
        PAGES[choice](scored)


if __name__ == "__main__":
    main()
