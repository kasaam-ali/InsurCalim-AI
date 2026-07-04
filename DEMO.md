# InsurCalim AI — Live Demo Guide

A step-by-step walkthrough to demonstrate that the system works end to end.
Each step lists the command, what to expect, and **which capability it proves**.

Run the commands from the project root (`InsurCalim AI/`) in a terminal
(PowerShell on Windows). Lines starting with `#` are comments — do not type them.

---

## What this project is

A multi-agent AI platform that investigates **auto-insurance claims**. A claim
goes in; a ranked, explainable **investigator report** comes out — risk score,
timeline, flagged inconsistencies, source citations, and a recommended action
(human-in-the-loop; it never auto-denies).

**Six technologies are demonstrated:**

| Technology | Where it runs | Proven by step |
| --- | --- | --- |
| Claude API (multi-provider) | `insurclaim/llm.py` | 4 |
| PostgreSQL | `insurclaim/db/` | 1, 2 |
| Vector DB + RAG (Chroma) | `insurclaim/vectordb/` | 4 (inside the pipeline) |
| LangGraph orchestration | `insurclaim/graph.py` | 4 |
| Fine-tuning (DistilBERT) | `insurclaim/ml/` | 5 |
| AWS deployment plan | `infra/deploy.md` | 6 |

---

## Prerequisites (one-time)

1. **Docker Desktop** must be running (the whale icon in the tray should be green).
2. The Python virtual environment (`.venv`) is already set up with all packages.
3. API access is configured in `.env` (git-ignored). During development the app
   routes LLM calls through OpenRouter to keep costs low.

Start the database if it is not already running:

```powershell
docker compose -f infra/docker-compose.yml up -d db
```

---

## Step 1 — The database is live (PostgreSQL)

```powershell
docker compose -f infra/docker-compose.yml ps
docker exec infra-db-1 psql -U insurclaim -d insurclaim -c "\dt"
```

**Expect:** the `infra-db-1` container is `Up (healthy)`, and five tables are
listed: `policies`, `claims`, `parties`, `vehicles`, `photo_hashes`.

**Proves:** a real relational store, with a schema designed for velocity checks
(repeat claimant / repeat VIN) and duplicate-photo detection.

---

## Step 2 — Real claim data with ground-truth labels

```powershell
docker exec infra-db-1 psql -U insurclaim -d insurclaim -c "SELECT id, is_fraud, fraud_type, claimed_amount FROM claims ORDER BY id;"
```

**Expect:** claims with `is_fraud` labels and a `fraud_type` (e.g.
`staged_collision`) for the fraudulent ones.

**Proves:** labeled data exists — used both as the training set for the ML
classifier and as ground truth for evaluation.

---

## Step 3 — Generate new synthetic claims (Claude)

```powershell
.venv\Scripts\python.exe -m insurclaim.data.generate --n 2 --fraud-ratio 0.5
```

**Expect:** `Generated and stored N claims ...`. New rows appear in the `claims`
table (re-run Step 2 to see them).

**Proves:** the data generator uses the LLM to invent realistic claims and
deliberately injects known fraud patterns, each with a ground-truth label.

> Note: on the free LLM tier this can take a minute or two per claim because of
> upstream rate limits. This is a hosting limit, not a code problem.

---

## Step 4 — The full investigation pipeline (the headline)

```powershell
.venv\Scripts\python.exe -m insurclaim.main --claim 1
```

**Expect:** a JSON investigator report containing `risk_score`, `top_flags`
(each with a confidence value), `timeline_summary`, `citations`, and
`recommended_action`.

**Proves the core of the project:** one claim flows through four agents wired in
a LangGraph state graph — `intake -> timeline -> fraud -> report` — combining
LLM reasoning, deterministic rules, similar-past-claim retrieval (RAG), and the
ML fraud score into a single explainable report. The result is also written back
to the claim record in PostgreSQL.

---

## Step 5 — Fine-tune the fraud classifier (optional, heavier)

```powershell
.venv\Scripts\python.exe -m insurclaim.ml.train
```

**Expect:** DistilBERT trains on the labeled claims and is saved to
`models/fraud_classifier/`. After this, Step 4 reports a numeric
`fraud_probability` instead of `null`.

**Proves:** a real fine-tuning deliverable — a small transformer specialised on
the project's own labeled fraud data.

> Requires enough labeled claims to be useful; generate more with Step 3 first.

---

## Step 6 — Measure accuracy (evaluation)

```powershell
.venv\Scripts\python.exe -m insurclaim.eval.harness
```

**Expect:** a confusion matrix plus precision, recall, and a classification
report over all labeled claims.

**Proves:** the project's success metric — accuracy measured against ground
truth, not just anecdotes.

> Most meaningful with 20+ claims and the ML model trained.

---

## Step 7 — Clean, professional history

```powershell
git log --oneline
```

**Proves:** the work was built in reviewable, well-described commits.

---

## Deployment story (no cloud account needed to explain)

The whole stack runs locally with Docker Compose. `infra/deploy.md` maps every
local piece to a managed AWS service (RDS, S3, ECS/Fargate, Pinecone, SageMaker,
Bedrock) with least-privilege secrets in AWS Secrets Manager. The code is already
cloud-ready: configuration comes from environment variables, and the vector store
is behind an interface so Chroma can be swapped for Pinecone without touching the
agents.

---

## Honest current status

- The end-to-end pipeline works and produces explainable reports.
- Fraud-detection strength scales with populated layers: generate more claims,
  index prior claims for retrieval (`python -m insurclaim.vectordb.ingest`), and
  train the classifier (Step 5). With those active, fraudulent claims score
  much higher.
- No real personal data is used anywhere — the dataset is synthetic by design.
