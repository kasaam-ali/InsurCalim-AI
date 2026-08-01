<div align="center">

# 🔎 InsurClaim AI

### Multi-agent AI platform for investigating auto-insurance claims

Takes a claim (documents · photos · videos) and produces a **ranked, explainable investigator report**
risk score, event timeline, flagged inconsistencies, source citations, and a recommended action.
**Human-in-the-loop by design: it flags and ranks, it never auto-denies.**

<br/>

![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-multi--agent-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
![Claude](https://img.shields.io/badge/Claude_API-multi--provider-D97757?style=for-the-badge&logo=anthropic&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-relational_store-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Chroma](https://img.shields.io/badge/Chroma-vector_DB_/_RAG-FF6F61?style=for-the-badge&logo=databricks&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-RandomForest-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)
![Transformers](https://img.shields.io/badge/DistilBERT-fine--tuned-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

<br/>

![Status](https://img.shields.io/badge/status-working_end--to--end-2ea44f?style=flat-square)
![Data](https://img.shields.io/badge/data-synthetic_%2B_public_(no_PII)-blue?style=flat-square)
![Human in the loop](https://img.shields.io/badge/decisioning-human--in--the--loop-8A2BE2?style=flat-square)
![Explainable](https://img.shields.io/badge/AI-explainable_reason_codes-0f9d58?style=flat-square)
![Portfolio](https://img.shields.io/badge/type-portfolio_project-lightgrey?style=flat-square)

</div>

---

## ✨ Highlights

- 🧠 **Four specialized agents** orchestrated with a **LangGraph** state machine (`intake → timeline → fraud → report`).
- 🕵️ **Document-level fraud detection** reads the *whole* claim file and surfaces concrete inconsistencies (location/GPS mismatch, timeline gaps, physically-impossible damage, airbags-but-no-medical, repeat claims, inflated cost).
- 🧾 **Explainable reason codes** every risk score breaks down into weighted signals with an evidence pointer; nothing is a black box.
- 📎 **Multi-format intake** TXT · PDF · **DOCX** · images · **video** (frame sampling). Scanned/image-only PDFs are read with a **vision-OCR fallback**.
- 🧪 **AI-generated (deepfake) media detection** metadata/EXIF/C2PA forensics + a vision-model artifact check flag synthetic damage photos/videos.
- 🛡️ **Policy-driven coverage gate** pick which policy a claim falls under; the system checks coverage **and** whether every document that *policy* requires is present before fraud runs.
- 🕸️ **Fraud-ring detection** connected components over the RAG similarity graph reveal organized rings.
- 💬 **AI chat + case management** ask grounded follow-up questions per claim, set status/assignee, and keep an audit-trail of notes.
- 🔁 **Resilient LLM layer** a 5-provider fallback chain with key rotation; the pipeline degrades gracefully instead of crashing when quotas are exhausted.

---

## 🏗️ Architecture 4 agents, one shared state

A shared `ClaimState` flows through the graph: **`intake → timeline → fraud → report`**.

| # | Agent | What it does |
|---|-------|--------------|
| 1 | **Intake & Extraction** | Documents / photos / videos → structured claim JSON (degrades to raw text if the LLM is unavailable). |
| 2 | **Timeline / Causal Reasoning** | Orders events A→B→C, flags inconsistencies and gaps, runs a light deterministic physics-sanity check. |
| 3 | **Fraud & Anomaly** | Hybrid of 6 layers: deterministic rules · duplicate-photo hashing · fine-tuned ML score · similar-past-claim RAG · **full-document narrative red-flag analysis** · LLM synthesis. |
| 4 | **Adjudication / Report** | Synthesizes a ranked, cited report with confidence scores and a recommended action (`route_to_investigator` · `request_more_info` · `fast_track_approve`). |

---

## 🧰 Tech stack

| Layer | Technology |
|-------|-----------|
| **Orchestration** | LangGraph · LangChain-core |
| **LLMs** | Multi-provider wrapper with fallback + key rotation: **Z.AI (GLM) → OpenRouter → Gemini → Claude → Groq**; Gemini/OpenRouter for vision |
| **Vector DB / RAG** | Chroma (Pinecone-ready abstraction) |
| **Relational store** | PostgreSQL (claims, parties, vehicles, photo hashes, policies, cases) |
| **Fine-tuning / ML** | DistilBERT (narrative) · class-balanced Random Forest (tabular, real 30k rows) |
| **Frontend** | Streamlit dashboard with custom CSS (8 pages) |
| **Media** | pypdf · pdfplumber · pypdfium2 (vision-OCR) · python-docx · OpenCV · Pillow · imagehash |
| **Infra** | Docker Compose · AWS deployment plan (RDS · S3 · ECS/EC2, optional SageMaker / Bedrock) |

---

## 📊 Data

- **Synthetic claims** an LLM generator produces realistic narratives with injected fraud patterns and ground-truth labels (used by the LLM agents and narrative fine-tuning).
- **Real dataset** a public **30,000-row** car-insurance fraud dataset, downloaded on demand and loaded into PostgreSQL to train and evaluate the tabular classifier
  (**ROC-AUC ≈ 0.74**, ~**67%** fraud recall at a recall-favoring threshold).

> No real personal data is used the real dataset is a public, anonymized research dataset.

---

## 🚀 Quick start

```bash
# 1. Start PostgreSQL (Docker Desktop must be running)
docker compose -f infra/docker-compose.yml up -d db

# 2. Load the real dataset and train the fraud classifier
python -m insurclaim.data.load_real
python -m insurclaim.ml.train_tabular

# 3a. Run the full pipeline on one claim (CLI)
python -m insurclaim.main --claim 1

# 3b. …or launch the investigator dashboard
streamlit run frontend/app.py        # → http://localhost:8501
```

Configuration (API keys, database, model names) lives in **`.env`** copy `.env.example` and fill it in.
See **[`DEMO.md`](./DEMO.md)** for a full walkthrough, **[`PLAN.md`](./PLAN.md)** for the build plan, and
**[`COMPETITORS.md`](./COMPETITORS.md)** for market positioning.

---

<div align="center">

**Built as a portfolio project** · synthetic & public data only · human-in-the-loop, never auto-deny.

</div>
