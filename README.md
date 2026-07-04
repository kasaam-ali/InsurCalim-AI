# InsurCalim AI

Multi-agent AI platform for investigating **auto insurance claims** — takes a claim
(documents + damage photos) and produces a **ranked, explainable investigator report**
(risk score, event timeline, flagged inconsistencies, source citations, recommended action).
Human-in-the-loop by design — it flags and ranks, it does not auto-deny.

## Status

**Working end to end.** The full pipeline runs a claim through four agents and returns an
explainable report, backed by a live PostgreSQL database and a fraud classifier trained on a
real 30,000-row dataset (ROC-AUC ≈ 0.74; ~67% fraud recall at a recall-favoring threshold).

See **[`DEMO.md`](./DEMO.md)** for a step-by-step live demo, and [`PLAN.md`](./PLAN.md) for the
full build plan.

## Architecture (4 agents, LangGraph state graph)

A shared `ClaimState` flows through the agents: `intake → timeline → fraud → report`.

1. **Intake & Extraction** — documents/photos → structured claim JSON (Claude).
2. **Timeline / Causal Reasoning** — order events, flag inconsistencies and gaps, run a light
   deterministic physics sanity check.
3. **Fraud & Anomaly** — hybrid: deterministic rules (policy/coverage/velocity) + image checks
   (perceptual-hash duplicate photos) + an ML fraud score + similar-past-claim retrieval (RAG)
   + LLM reasoning.
4. **Adjudication / Report** — synthesize a ranked, cited report with confidence scores and a
   recommended action.

## Tech stack

LangChain / LangGraph · Claude API via a multi-provider wrapper (OpenRouter → Claude → Gemini →
Groq) · PostgreSQL · Chroma (vector DB / RAG, Pinecone-ready) · fine-tuned DistilBERT for text +
a class-balanced Random Forest for tabular data · AWS deployment plan (RDS · S3 · ECS/EC2,
optional SageMaker / Bedrock).

## Data

- **Synthetic claims** — an LLM generator produces realistic narratives with injected fraud
  patterns and ground-truth labels, used by the LLM agents and the narrative fine-tuning.
- **Real dataset** — a public 30,000-row car-insurance fraud dataset is downloaded on demand
  and loaded into PostgreSQL to train and evaluate the tabular fraud classifier.

No real personal data is used; the real dataset is a public, anonymized research dataset.

## Quick start

```bash
# 1. Start PostgreSQL (Docker Desktop must be running)
docker compose -f infra/docker-compose.yml up -d db

# 2. Load the real dataset and train the fraud classifier
python -m insurclaim.data.load_real
python -m insurclaim.ml.train_tabular

# 3. Run the full pipeline on one claim
python -m insurclaim.main --claim 1
```

Configuration (API keys, database, model names) lives in `.env` — copy `.env.example` and fill
it in. See [`DEMO.md`](./DEMO.md) for the full walkthrough.
