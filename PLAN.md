# ClaimChain AI — v1 Build Plan (Portfolio Demo)

## Context

Ahmed ek multi-agent AI platform bana raha hai jo insurance claims investigate karta hai
("ClaimChain AI"). Original idea mein 6 alag agents, fine-tuning, Pinecone, aur "damage
physics from photos" tha. Research (2026 multi-agent + insurance fraud best practices)
ke baad decide hua ke us design ka bahut hissa fuzool/over-engineered hai for a greenfield
demo. Yeh plan usko ek **leaner, actually-buildable, wow-worthy** system mein reshape karta hai.

**Confirmed scope (user se):**
- **Purpose:** Portfolio / demo / learning — koi real customer ya PII nahi, synthetic data.
- **Line:** Auto / motor insurance (isliye vision/photo analysis relevant hai).
- **Data:** Kuch nahi — synthetic data generate karenge.
- **v1:** Full end-to-end pipeline, **collapsed agents** (6 → 4).

**CV / Learning requirement (sir ne bola — non-negotiable):** Project mein yeh **6 technologies
cover honi chahiye** taake seekh bhi ho aur CV pe aa jaye:
LangChain/LangGraph, Named Vector DB (Chroma/Pinecone), Claude API, SQL/PostgreSQL,
**Fine-tuning**, aur **AWS**. Isliye pehle jo "cut list" tha usay reverse kar diya gaya hai —
ab har technology ko ek **asli, defensible role** milega (checkbox nahi).

**Intended outcome:** Ek claim (docs + photos) andar jaye, aur ek **ranked, explainable
investigator report** bahar aaye — risk score, timeline, flagged inconsistencies, source
citations, aur recommended action (auto-deny NAHI, human-in-the-loop). Saath hi 6-tech stack
end-to-end demonstrate ho.

---

## CV Technologies — har ek ka asli role (checkbox nahi)

| Technology | Kahan use hoga (meaningful role) |
|---|---|
| **LangChain / LangGraph** | Poora orchestration — 4-agent `StateGraph`, shared `ClaimState`, conditional/parallel steps. |
| **Named Vector DB (Chroma → Pinecone)** | RAG: policy documents + prior-claim narratives ke embeddings. **Chroma** local dev/seekhne ke liye; **Pinecone** managed-cloud swap (AWS phase mein) — dono CV pe. |
| **Claude API** | Vision extraction, causal/timeline reasoning, fraud narrative reasoning, report synthesis (Opus 4.8 / Haiku 4.5). |
| **SQL / PostgreSQL** | Relational store: claims, parties, vehicles, photo hashes, velocity queries (repeat-claimant/VIN). |
| **Fine-tuning** | Ek **chhota open model (LoRA/PEFT — e.g. DistilBERT ya Llama-3.x-8B)** ko synthetic labeled fraud data pe train karke **fraud/anomaly classifier** banao. Yeh Fraud Agent ka classic-ML brain hai — architecturally sahi *aur* CV bullet. |
| **AWS** | Deployment: **RDS** (Postgres), **S3** (docs/photos), **ECS/EC2** (dockerized app), optionally **SageMaker** (fine-tuned model host) ya **Bedrock** (Claude). Final phase. |

> Design principle: har tech project ko genuinely behtar banaye. Fine-tuning ko "classic-ML
> fraud scorer" bana ke woh LLM ki jagah numeric anomaly detection karta hai (jo sahi bhi hai),
> aur RAG ko real policy-context grounding deta hai. Koi bhi tech sirf CV ke liye zabardasti thoosi nahi.

---

## Refined Architecture — 4 Agents (LangGraph state graph)

Ek shared `ClaimState` (LangGraph state object) sab agents ke beech flow karta hai. Har agent
apna output state mein add karta hai; kuch steps parallel ho sakte hain.

1. **Intake & Extraction Agent** *(old 1+2+3 merged)*
   - Input: FNOL form, police report (PDF/text), damage photos.
   - Claude (vision + structured outputs) → structured `claim` JSON: parties, vehicles,
     dates, location, described sequence, policy number, claimed damages.
   - Model: `claude-haiku-4-5` (cheap extraction/classification) with structured
     `output_config.format` schema.

2. **Timeline / Causal Reasoning Agent** *(old 4 — the unique piece, KEEP)*
   - Extracted facts ko temporal sequence mein arrange karta hai (Event A → B → C).
   - Consistency checks: kya sequence physically/temporally possible hai? Contradictions?
     (e.g. damage described before impact time; two events same timestamp different places).
   - Model: `claude-opus-4-8` with `thinking: {type: "adaptive"}`, `effort: "high"`.
   - **Honesty note (docs/pitch):** yeh LLM-based temporal ordering + consistency reasoning
     hai — "causal inference" over-claim mat karna.

3. **Fraud & Anomaly Agent** *(old 5+6 merged — hybrid, 3 layers)*
   - **Deterministic (code, NOT LLM):** policy active on incident date? claim within
     coverage? claim velocity (same party/VIN repeat claims)? amount vs policy limit?
   - **Image checks (code):** EXIF/metadata sanity, perceptual-hash duplicate detection
     (same photo reused across claims), basic tampering signals.
   - **Fine-tuned ML classifier:** synthetic labeled fraud data pe trained chhota model
     (LoRA/DistilBERT) — structured claim features → fraud probability. **Yeh fine-tuning
     deliverable hai** aur numeric anomaly scoring LLM se better karta hai.
   - **LLM reasoning (Claude):** teenon layers ke signals + timeline inconsistencies ko weigh
     karke narrative-level red flags nikaalta hai. Model: `claude-opus-4-8`.
   - Output: structured risk signals list, each with evidence pointer.

4. **Adjudication / Report Agent** *(new — the differentiator)*
   - Sab signals synthesize → **ranked, explainable report**: overall risk score,
     top flags (most-severe first), timeline summary, **source citations** for every claim,
     recommended action (`route_to_investigator` / `fast_track_approve` / `request_more_info`).
   - **Human-in-the-loop:** report flag+rank karta hai, auto-deny nahi. Model: `claude-opus-4-8`.

---

## Tech Stack (v1)

- **Orchestration:** LangGraph (Python) — `StateGraph` with `ClaimState`.
- **LLM:** Claude API via `anthropic` SDK.
  - `claude-opus-4-8` — reasoning (timeline, fraud, report), adaptive thinking.
  - `claude-haiku-4-5` — cheap extraction/classification.
  - Structured outputs via `output_config.format` (JSON schema). Vision via base64 image blocks.
- **DB:** PostgreSQL — claims, parties/vehicles (entity table for velocity checks), photo hashes.
- **Vector DB:** **Chroma** (local dev) — policy docs + prior-claim narratives ke embeddings;
  AWS phase mein **Pinecone** (managed) swap. Interface abstract rakho taake swap easy ho.
- **Fine-tuning:** HuggingFace `transformers` + `peft` (LoRA) ya `sentence-transformers`/`sklearn`
  baseline — fraud classifier training script + saved model artifact.
- **Image:** `Pillow` (EXIF), `imagehash` (perceptual hash for duplicate detection).
- **Deploy:** local + `docker-compose` (Postgres + Chroma + app) → phir **AWS**
  (RDS + S3 + ECS/EC2, optional SageMaker/Bedrock/Pinecone).

---

## Data Strategy (synthetic)

- **Generator script:** Claude se realistic auto-claim sets generate karao — FNOL text,
  police report text, damage descriptions, party/vehicle records. Inject known fraud patterns:
  staged collision, duplicate/reused photos, policy-lapsed-then-backdated, impossible timeline,
  repeat-claimant velocity.
- Har generated claim pe ground-truth label (`legit` / `fraud` + fraud_type) rakho — yeh
  **do kaam karta hai:** (1) fine-tuning ke liye training set, aur (2) eval harness ka
  ground truth. (Zyada claims chahiye honge fine-tuning ke liye — generator ko scale karo.)

---

## Key Components / Files (proposed layout)

```
claimchain/
  graph.py              # LangGraph StateGraph wiring + ClaimState (TypedDict)
  agents/
    intake.py           # Extraction agent (Haiku, vision, structured output)
    timeline.py         # Causal/temporal reasoning agent (Opus + adaptive thinking)
    fraud.py            # Hybrid: deterministic rules + image checks + LLM
    report.py           # Adjudication/report agent (Opus)
  rules/
    deterministic.py    # policy-active, coverage, velocity, amount-vs-limit (pure code)
    image_checks.py     # EXIF + perceptual-hash duplicate detection
  ml/
    train.py            # fine-tune fraud classifier (LoRA/DistilBERT) on labeled synthetic data
    predict.py          # load artifact → fraud probability for a claim
  vectordb/
    store.py            # abstract RAG interface; Chroma impl (Pinecone impl for AWS phase)
    ingest.py           # embed + index policy docs + prior-claim narratives
  db/
    schema.sql          # claims, parties, vehicles, photo_hashes
    repo.py             # queries incl. velocity / duplicate lookups
  data/
    generate.py         # synthetic claim + fraud-pattern generator (Claude), with labels
  eval/
    harness.py          # run pipeline over labeled set → precision/recall/confusion
  llm.py                # thin Anthropic client wrapper (model routing, structured output helper)
  main.py               # CLI: run one claim → print report JSON
  infra/                # AWS phase: Dockerfile, docker-compose, IaC / deploy notes
```

Reuse: single `llm.py` client wrapper (prompt-cache friendly — stable system prompts,
volatile claim data last). Deterministic checks live in `rules/` so LLM never does math/policy logic.

---

## Explainability & Trust (the real differentiator, build from day 1)

- Har fraud signal aur report claim ke saath ek **evidence pointer** (source doc + field/line).
- Report Agent ko instruct karo: har assertion cite kare; koi bhi flag jiske paas evidence
  nahi, use "low confidence / unverified" mark kare.
- Deterministic rule outputs report mein alag "hard checks" section mein — LLM inko override na kare.

---

## Verification (end-to-end)

1. `docker-compose up` → Postgres + pgvector ready; `schema.sql` apply.
2. `python -m claimchain.data.generate --n 50` → 50 labeled synthetic claims (mix legit/fraud).
3. `python -m claimchain.main --claim <id>` → ek claim ka full report JSON, timeline +
   ranked flags + citations dikhna chahiye.
4. `python -m claimchain.eval.harness` → labeled set pe pipeline chalao; **precision/recall +
   confusion matrix** print ho. Yeh success metric hai (fine-tuning ki jagah).
5. Manual spot-check: ek injected-fraud claim (duplicate photo) sahi flag hui? Ek legit claim
   false-positive to nahi?

---

## Phased build (har phase pe ek CV-tech "unlock" hota hai)

1. **Foundation:** `llm.py` wrapper *(Claude API)* + `db/schema.sql` *(PostgreSQL)* +
   `docker-compose` + synthetic labeled generator (thoda data).
2. **Intake agent:** docs+photos → structured claim JSON *(Claude vision)*. Extraction verify.
3. **Vector DB + RAG:** Chroma mein policy docs + prior claims embed/index *(Vector DB)*;
   agents ko relevant context retrieve karna.
4. **Deterministic rules + image checks:** pure-code layer, testable without LLM.
5. **Fine-tuning:** synthetic labeled data pe fraud classifier train *(Fine-tuning)*;
   `ml/predict.py` se probability. Confusion matrix pe validate.
6. **Timeline agent:** causal/temporal reasoning (the showpiece).
7. **Fraud agent:** 3-layer hybrid wiring (rules + image + fine-tuned classifier + LLM).
8. **Report agent + LangGraph wiring:** full graph end-to-end *(LangGraph)*.
9. **Eval harness:** precision/recall over labeled synthetic set; iterate prompts.
10. **AWS deploy:** RDS + S3 + ECS/EC2 *(AWS)*; optionally Chroma→Pinecone swap +
    SageMaker/Bedrock. **Yeh phase 6 CV-techs ko "cloud-deployed" bana ke seal karta hai.**

Open choice for build-time: language confirm (plan assumes **Python** — LangGraph + HuggingFace
fine-tuning ka natural ghar; TS mein fine-tuning awkward hai). Agar zaroorat ho to discuss karenge.
