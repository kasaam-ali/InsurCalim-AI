# InsurClaim AI - Dashboard

A Streamlit investigator dashboard over the claim-investigation pipeline.
See [`PLAN.md`](./PLAN.md) for the design.

## Run

From the project root, with the database running and data loaded:

```bash
docker compose -f infra/docker-compose.yml up -d db
streamlit run frontend/app.py
```

It opens in the browser at http://localhost:8501.

## Screens

- **Overview** - portfolio KPIs and fraud-type breakdown.
- **Claims queue** - the list of claims to review.
- **Investigation report** - run the full 4-agent pipeline on a claim and read
  the explainable report (risk score, flags, timeline, similar past claims, ML score).
- **Analyze new claim** - paste raw claim text and analyze it live.
- **Model performance** - the fraud model's top signals (feature importances).
