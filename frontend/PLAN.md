# InsurClaim AI Frontend / Dashboard Plan

A web dashboard for a **claims investigator** to review AI-analyzed auto-insurance
claims. It surfaces the pipeline's output risk score, flags, timeline, similar
past claims, and the ML fraud score in an explainable, human-in-the-loop UI.
It never auto-denies; it ranks and recommends.

## Technology

**Streamlit** (Python). It imports the existing `insurclaim` package directly
(database repo, the LangGraph pipeline, the tabular model), so no separate API
layer is needed. Fast to build, integrates with the ML/data code, and looks
professional. A FastAPI + React version is a possible future upgrade for a
"full-stack" story, but Streamlit is the right first build for this ML project.

Run with: `streamlit run frontend/app.py`

## Screens

1. **Overview** portfolio health at a glance.
   - KPI tiles: total claims, % high-risk, fraud-type breakdown, average risk.
   - Chart: claims by risk band (low / medium / high).
   - List: most recent high-risk claims (quick jump to detail).

2. **Claims Queue** the investigator's worklist.
   - Sortable, filterable table of claims ranked by risk score.
   - Color-coded risk (green / amber / red) and the recommended action.
   - Filters: risk band, recommended action, fraud type.
   - Click a row to open the investigation report.

3. **Investigation Report** (claim detail the hero screen).
   - Big risk-score gauge, color-coded, with the recommended-action badge.
   - Top flags, most severe first, each with severity, confidence, and the
     evidence pointer.
   - Timeline: ordered events, flagged inconsistencies, and gaps.
   - Similar past claims (RAG): "66% match to claim #11 (staged_collision)".
   - ML fraud probability.
   - Claim facts: parties, vehicles, policy, amounts.
   - Source citations for every assertion.

4. **Analyze New Claim** paste raw FNOL / report text, run the pipeline live,
   and render the resulting report.

5. **Model Performance** trust and transparency.
   - Tabular classifier metrics (ROC-AUC, precision/recall at the operating
     threshold, confusion matrix).
   - Top feature importances (what drives the fraud score).
   - Dataset stats (real 30k rows + synthetic narratives).

## Design principles

- **Risk-first:** the score and recommended action are the first thing seen.
- **Explainable everywhere:** every flag links to its evidence; nothing is a
  black box.
- **Human-in-the-loop:** actions are *recommendations* (route to investigator /
  request more info / fast-track), never automatic denials.
- **Color language:** red = high risk, amber = medium, green = low.
- **Clean and professional:** minimal chrome, generous spacing, readable tables.
- **Theme-aware and responsive** where Streamlit allows.

## Connection to the backend

- `insurclaim.db.repo` list/read claims for the queue and detail views.
- `insurclaim.graph.run_claim` run the full pipeline for a claim or raw text.
- `insurclaim.ml.predict_tabular` / `insurclaim.ml.train_tabular` model score
  and performance metrics.

## Future enhancements

- Authentication and per-investigator worklists.
- Click-through from a citation to the exact source document/field.
- Side-by-side comparison of a claim with its closest known-fraud match.
- Export a report to PDF.
- Swap Streamlit for FastAPI + React if a full-stack build is wanted.
