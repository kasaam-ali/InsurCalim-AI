"""InsurCalim AI - investigator dashboard (Streamlit).

A human-in-the-loop UI over the claim-investigation pipeline: browse claims,
open an explainable investigation report, analyze new claim text, and view the
fraud model's performance. Imports the insurclaim package directly.

Run from the project root:  streamlit run frontend/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Make the project package importable when Streamlit runs this file directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from insurclaim.db import repo  # noqa: E402

st.set_page_config(page_title="InsurCalim AI", page_icon="🔎", layout="wide")

# Risk bands drive the color language used across the dashboard.
RISK_HIGH, RISK_MEDIUM = 60, 30


def risk_band(score: float) -> tuple[str, str]:
    """Return (label, color) for a 0-100 risk score."""
    if score >= RISK_HIGH:
        return "HIGH", "#e5484d"
    if score >= RISK_MEDIUM:
        return "MEDIUM", "#f5a623"
    return "LOW", "#30a46c"


@st.cache_data(show_spinner=False)
def load_claims() -> list[dict]:
    """Load labeled claims from the database (cached)."""
    try:
        return repo.list_labeled_claims()
    except Exception as exc:  # database not reachable
        st.error(f"Could not reach the database: {exc}")
        return []


def render_report(report: dict) -> None:
    """Render an investigation report dict as the hero view."""
    score = float(report.get("risk_score", 0) or 0)
    label, color = risk_band(score)
    action = report.get("recommended_action", "-")

    left, right = st.columns([1, 2])
    with left:
        st.markdown(
            f"<div style='padding:1rem;border-radius:12px;background:{color};"
            f"color:white;text-align:center'>"
            f"<div style='font-size:0.9rem;opacity:0.9'>RISK SCORE</div>"
            f"<div style='font-size:3rem;font-weight:700'>{score:.0f}</div>"
            f"<div style='font-size:1rem'>{label} RISK</div></div>",
            unsafe_allow_html=True,
        )
        prob = report.get("fraud_probability")
        if prob is not None:
            st.metric("ML fraud probability", f"{float(prob) * 100:.0f}%")
        st.markdown(f"**Recommended action**\n\n`{action}`")
    with right:
        st.subheader("Top flags")
        flags = report.get("top_flags") or []
        if not flags:
            st.info("No flags raised.")
        for flag in flags:
            conf = flag.get("confidence", "")
            st.markdown(
                f"- **{flag.get('summary', '')}**  \n"
                f"  _{flag.get('evidence', '')}_"
                + (f"  \n  confidence: {conf}%" if conf != "" else "")
            )

    summary = report.get("timeline_summary")
    if summary:
        st.subheader("Timeline summary")
        st.write(summary)

    citations = report.get("citations") or []
    if citations:
        with st.expander("Source citations"):
            for c in citations:
                st.markdown(f"- `{c}`")


def page_overview(claims: list[dict]) -> None:
    st.title("🔎 InsurCalim AI")
    st.caption("AI-assisted auto-insurance claim investigation - human-in-the-loop.")

    total = len(claims)
    fraud = sum(1 for c in claims if c.get("is_fraud"))
    from collections import Counter

    types = Counter(c.get("fraud_type") for c in claims if c.get("is_fraud"))

    a, b, c = st.columns(3)
    a.metric("Claims in system", total)
    b.metric("Labeled fraud", fraud)
    c.metric("Fraud rate", f"{(fraud / total * 100) if total else 0:.0f}%")

    if types:
        st.subheader("Fraud types")
        st.bar_chart({k or "?": v for k, v in types.items()})


def page_queue(claims: list[dict]) -> None:
    st.title("Claims queue")
    if not claims:
        st.warning("No claims found. Load data first (see DEMO.md).")
        return
    rows = [
        {
            "id": c["id"],
            "fraud_type (label)": c.get("fraud_type") or "legit",
            "is_fraud": bool(c.get("is_fraud")),
            "description": (c.get("description") or "")[:90] + "...",
        }
        for c in claims
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.caption("Open a claim in 'Investigation report' to run the full analysis.")


def page_report(claims: list[dict]) -> None:
    st.title("Investigation report")
    if not claims:
        st.warning("No claims found.")
        return
    ids = [c["id"] for c in claims]
    claim_id = st.selectbox("Select a claim id", ids)
    if st.button("Run investigation", type="primary"):
        from insurclaim.graph import run_claim

        with st.spinner("Running the 4-agent pipeline..."):
            claim = repo.get_claim(claim_id)
            final_state = run_claim({"claim": claim})
        render_report(final_state.get("report", {}))


def page_analyze() -> None:
    st.title("Analyze new claim text")
    text = st.text_area("Paste a claim narrative / FNOL text", height=200)
    if st.button("Analyze", type="primary") and text.strip():
        from insurclaim.graph import run_claim

        with st.spinner("Running the 4-agent pipeline..."):
            final_state = run_claim({"raw_documents": text})
        render_report(final_state.get("report", {}))


def page_model() -> None:
    st.title("Model performance")
    st.write(
        "The tabular fraud classifier is trained on a real 30,000-row dataset; "
        "the narrative classifier is fine-tuned on claim descriptions."
    )
    try:
        import joblib

        from insurclaim.ml.train_tabular import (
            CATEGORICAL_FEATURES,
            MODEL_PATH,
            NUMERIC_FEATURES,
        )

        if not MODEL_PATH.exists():
            st.info("Tabular model not trained yet. Run: python -m insurclaim.ml.train_tabular")
            return
        model = joblib.load(MODEL_PATH)
        names = model.named_steps["preprocess"].get_feature_names_out()
        importances = model.named_steps["classifier"].feature_importances_
        top = sorted(zip(names, importances), key=lambda x: -x[1])[:12]
        st.subheader("Top fraud signals (feature importance)")
        st.bar_chart({name.split("__")[-1]: float(score) for name, score in top})
    except Exception as exc:
        st.error(f"Could not load the model: {exc}")


PAGES = {
    "Overview": page_overview,
    "Claims queue": page_queue,
    "Investigation report": page_report,
    "Analyze new claim": page_analyze,
    "Model performance": page_model,
}


def main() -> None:
    st.sidebar.title("🔎 InsurCalim AI")
    choice = st.sidebar.radio("Navigate", list(PAGES.keys()))
    st.sidebar.caption("Human-in-the-loop - the system flags and ranks; it never auto-denies.")

    claims = load_claims()
    if choice in ("Overview", "Claims queue", "Investigation report"):
        PAGES[choice](claims)
    else:
        PAGES[choice]()


if __name__ == "__main__":
    main()
