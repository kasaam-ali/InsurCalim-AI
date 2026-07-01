# ClaimChain AI

Multi-agent AI platform for investigating **auto insurance claims** — takes a claim
(documents + damage photos) and produces a **ranked, explainable investigator report**
(risk score, event timeline, flagged inconsistencies, source citations, recommended action).
Human-in-the-loop by design — it flags and ranks, it does not auto-deny.

## Status
Greenfield — planning stage. See [`PLAN.md`](./PLAN.md) for the full v1 build plan.

## Architecture (v1 — 4 collapsed agents, LangGraph)
1. **Intake & Extraction** — docs + photos → structured claim JSON (Claude vision).
2. **Timeline / Causal Reasoning** — arrange events into a sequence, check temporal consistency.
3. **Fraud & Anomaly** — hybrid: deterministic rules + image checks + fine-tuned ML classifier + LLM reasoning.
4. **Adjudication / Report** — synthesize a ranked, cited, explainable report.

## Tech stack
LangChain / LangGraph · Claude API (Anthropic) · PostgreSQL · Chroma → Pinecone (vector DB / RAG) ·
Fine-tuned fraud classifier (LoRA / HuggingFace) · AWS (RDS · S3 · ECS/EC2, optional SageMaker/Bedrock)

## Data
Synthetic auto-claim generator with injected fraud patterns + ground-truth labels
(feeds both fine-tuning and the evaluation harness).
