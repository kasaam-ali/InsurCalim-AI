# InsurClaim AI Live Demo Guide

A step-by-step walkthrough to demonstrate that the system works end to end.
Each step lists the command, what to expect, and **which capability it proves**.

Run the commands from the project root (`InsurCalim AI/`) in a terminal
(PowerShell on Windows). Lines starting with `#` are comments do not type them.

---

## What this project is

A multi-agent AI platform that investigates **auto-insurance claims**. A claim
goes in; a ranked, explainable **investigator report** comes out risk score,
timeline, flagged inconsistencies, source citations, and a recommended action
(human-in-the-loop; it never auto-denies).

**Six technologies are demonstrated:**

| Technology | Where it runs | Proven by step |
| --- | --- | --- |
| Claude API (multi-provider) | `insurclaim/llm.py` | 4 |
| PostgreSQL | `insurclaim/db/` | 1, 2, 5 |
| Vector DB + RAG (Chroma) | `insurclaim/vectordb/` | 4 (inside the pipeline) |
| LangGraph orchestration | `insurclaim/graph.py` | 4 |
| Fine-tuning + classic ML | `insurclaim/ml/` | 6, 7 |
| AWS deployment plan | `infra/deploy.md` | Deployment section |

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

## Step 1 The database is live (PostgreSQL)

```powershell
docker compose -f infra/docker-compose.yml ps
docker exec infra-db-1 psql -U insurclaim -d insurclaim -c "\dt"
```

**Expect:** the `infra-db-1` container is `Up (healthy)`, and the tables are
listed: `policies`, `claims`, `parties`, `vehicles`, `photo_hashes`, and
`real_claims`.

**Proves:** a real relational store, with a schema designed for velocity checks
(repeat claimant / repeat VIN) and duplicate-photo detection.

---

## Step 2 Synthetic claim data with ground-truth labels

```powershell
docker exec infra-db-1 psql -U insurclaim -d insurclaim -c "SELECT id, is_fraud, fraud_type, claimed_amount FROM claims ORDER BY id;"
```

**Expect:** claims with `is_fraud` labels and a `fraud_type` (e.g.
`staged_collision`) for the fraudulent ones.

**Proves:** labeled narrative data exists for the LLM agents and for evaluation.

---

## Step 3 Generate new synthetic claims (Claude)

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

## Step 4 The full investigation pipeline (headline #1)

```powershell
.venv\Scripts\python.exe -m insurclaim.main --claim 1
```

**Expect:** a JSON investigator report containing `risk_score`, `top_flags`
(each with a confidence value), `timeline_summary`, `citations`, and
`recommended_action`.

**Proves the core of the project:** one claim flows through four agents wired in
a LangGraph state graph `intake -> timeline -> fraud -> report` combining
LLM reasoning, deterministic rules, similar-past-claim retrieval (RAG), and the
ML fraud score into a single explainable report. The result is also written back
to the claim record in PostgreSQL.

---

## Step 5 Load a real-world dataset (30,000 real claims)

```powershell
.venv\Scripts\python.exe -m insurclaim.data.load_real
docker exec infra-db-1 psql -U insurclaim -d insurclaim -c "SELECT is_fraud, COUNT(*) FROM real_claims GROUP BY is_fraud;"
```

**Expect:** `Loaded 30000 real claims ...`, then a count showing ~26,560 legit
and ~3,440 fraud (a realistic ~11% fraud rate).

**Proves:** the project is not limited to synthetic data it downloads a real,
public, labeled 30,000-row car-insurance fraud dataset (Kaggle) into PostgreSQL
for training and evaluation.

---

## Step 6 Measured performance on real data (headline #2)

```powershell
.venv\Scripts\python.exe -m insurclaim.ml.train_tabular
```

**Expect:** threshold-free quality scores plus a confusion matrix and
classification report on a held-out 20% split, roughly:

```
PR-AUC (average precision): 0.30
ROC-AUC:                    0.74

Operating point at threshold 0.25:
              precision    recall  f1-score   support
       legit       0.95      0.76      0.84      5312
       fraud       0.26      0.67      0.38       688
```

**Proves:** a real, defensible result on realistic data a class-balanced
Random Forest with a ROC-AUC of ~0.74 that catches ~67% of fraud at a
recall-favoring decision threshold. It also tells a genuine ML story: fraud is
rare (~11%), so the default 0.5 cutoff misses most of it; lowering the threshold
trades precision for recall. Flagged claims go to a human investigator, never an
automatic denial so higher recall is the right call here.

---

## Step 7 Score an individual real claim with the model

```powershell
.venv\Scripts\python.exe -m insurclaim.main --real-claim 1
```

**Expect:** a JSON report for that real claim `fraud_probability`, `risk_score`,
`recommended_action`, a few key facts, and the `ground_truth_is_fraud` label so
you can see whether the model was right. Claim 1 (a fraud) scores ~0.99 and is
routed to an investigator.

**Proves:** the trained classifier is wired into the CLI and scores a specific
real claim end to end, not just aggregate metrics. (The held-out ROC-AUC from
Step 6 is the honest overall measure; this shows the model in action on one case.)

---

## Step 8 Fine-tune DistilBERT on narratives (optional)

```powershell
.venv\Scripts\python.exe -m insurclaim.ml.train --source narrative
```

**Expect:** DistilBERT fine-tunes on the synthetic narrative claims and is saved
to `models/fraud_classifier/`. After this, Step 4 reports a numeric
`fraud_probability` for narrative claims instead of `null`.

**Proves:** the fine-tuning deliverable a transformer specialised on free-text
claim narratives, complementing the tabular model from Step 6.

> Needs enough labeled narrative claims to be useful; generate more with Step 3.

---

## Step 9 Clean, professional history

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

- The end-to-end pipeline works and produces explainable reports (Step 4).
- The fraud classifier reaches ~0.84 recall on real held-out data (Step 6).
- Fraud-detection strength in the LLM pipeline scales with populated layers:
  generate more claims, index prior claims for retrieval
  (`python -m insurclaim.vectordb.ingest`), and train the narrative model
  (Step 7).
- No real personal data is used in the synthetic parts; the real dataset is a
  public, anonymized research dataset used only for training and evaluation.
