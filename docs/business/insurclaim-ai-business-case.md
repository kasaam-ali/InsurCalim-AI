# InsurCalim AI — Business Case & Investment Brief

**An AI platform for investigating auto-insurance claims: explainable, human-in-the-loop, and built to attack a multi-hundred-billion-dollar fraud problem.**

*Prepared for review · MVP working end-to-end · synthetic & public data only (no real PII).*

---

## 1. Executive Summary

Insurance claims are slow, expensive, and heavily exposed to fraud. Every claim arrives as a
pile of unstructured documents, photos, and videos that a human adjuster must read, cross-check,
and price — millions of times a year. Meanwhile, fraud drains **hundreds of billions of dollars
annually** and is now being supercharged by AI-generated fake images and documents.

**InsurCalim AI** is a working multi-agent platform that ingests a claim's documents, photos, and
videos and produces a **ranked, explainable investigator report** — risk score, event timeline,
flagged inconsistencies, coverage decision, a fair-cost (quantum) assessment, citations, and a
recommended action. It is **human-in-the-loop by design: it flags and ranks, it never
auto-denies.**

The MVP is complete and runs end-to-end. This document sets out the problem size, the market
opportunity, the solution, its architecture, its **operating cost**, and what funding unlocks.

**The opportunity in one line:** the AI-in-insurance market is growing at **~32–35% CAGR** toward
**$88–246B by 2030–2035**, and AI fraud detection can cut fraud losses by **up to 30%** — while
our cost to analyse a claim can be **as low as a few cents**.

---

## 2. The Problem and Its Size

Claims handling is the costliest, most fraud-exposed part of insurance, and it is still largely
manual.

- **Fraud is enormous.** Global insurance fraud is estimated to exceed **$80 billion per year**
  (2025). In the United States alone, fraud drains an estimated **$308.6 billion per year**, of
  which **$90–122 billion** comes from Property & Casualty (P&C) lines. [1][2]
- **It is widespread.** Fraud occurs in roughly **10% of P&C insurance losses**, and it costs the
  average US consumer about **$900 per year** in higher premiums. [1][2]
- **It is getting worse with AI.** An estimated **25–30% of claims** now involve GenAI-altered
  fake images, medical reports, or valuation certificates — a threat traditional tooling was
  never built to catch. [1]
- **Manual processing is slow and expensive.** Adjusters open individual scans and photos,
  analyse unstructured files, and re-key data into legacy systems — a bottleneck that limits
  growth and delays honest payouts. [3][4]

**Why this matters for InsurCalim AI:** the platform is built precisely around these pain points —
multi-format document intake, multi-signal fraud detection (including **AI-generated media
detection**), and an explainable score an investigator can defend.

---

## 3. Market Opportunity

Insurance is one of the largest and fastest-moving arenas for applied AI, and every major player
is investing.

- **AI in insurance** was valued at roughly **$10–20 billion in 2025** and is projected to reach
  **$88–246 billion by 2030–2035**, a CAGR of **~32–35%**. [5][6]
- **AI in claims processing** specifically is forecast to grow from **$0.46B (2025) to $0.97B by
  2030** (16.2% CAGR). [6]
- **AI fraud detection** could reduce insurance fraud losses by **up to 30%**, translating to
  billions in savings. [6]

The field is crowded with serious money and proven results, which validates the category:

| Player | What they did | Result |
| --- | --- | --- |
| **EY** (Nordic insurer) | Document Intelligence (OCR + NLP) | **70%** auto-extraction [3] |
| **PwC** (auto insurer) | Explainable-AI damage assessment | **29%** efficiency savings [7] |
| **McKinsey / Aviva** | 80+ AI models, human-in-the-loop claims | **£60M** saved in 2024 [8] |
| **Shift Technology** | Fraud & underwriting detection | **$30M+/yr** risk mitigation [9] |
| **AWS / EXL** | GenAI underwriting on Bedrock | **−80%** underwriting cost [10] |
| **Lemonade** | AI-native claims ("AI Jim") | **~3-second** settlements [11] |

InsurCalim AI applies the same patterns these leaders converged on — document intelligence,
explainability, and human-in-the-loop control — in a single, coherent, portfolio-ready product.

---

## 4. Our Solution — InsurCalim AI

A multi-agent system that turns a raw claim into a defensible investigator report.

- 🧠 **Four specialised agents** orchestrated by a LangGraph state machine:
  `intake → timeline → fraud → report`.
- 📎 **Multi-format intake** — TXT, PDF, DOCX, images, and video, with a vision-OCR fallback for
  scanned/image-only PDFs.
- 🕵️ **Multi-signal fraud detection** — deterministic rules, duplicate-photo hashing, a
  fine-tuned ML score, similar-past-claim retrieval (RAG), full-document narrative red-flag
  analysis, and **AI-generated (deepfake) media detection**.
- 🛡️ **Policy-driven coverage gate** — checks coverage and whether every policy-required document
  is present.
- 💰 **Claim-amount (quantum) assessment** — even when a claim is not fraud, it judges whether the
  demanded cost is justified and, if not, estimates the fair amount.
- 🧾 **Claimant overview** — a consolidated profile, summary, document checklist, and risk
  snapshot per uploaded claimant.
- 🧾 **Explainable, cited report** — a risk score that breaks down into weighted reason codes,
  with evidence and policy-clause citations; **human-in-the-loop — it never auto-denies.**
- 💬 **AI chat** — grounded, per-claim follow-up questions for the investigator.

---

## 5. Architecture

A shared `ClaimState` flows through the agent graph; supporting stores and models sit alongside.

<svg viewBox="0 0 900 420" xmlns="http://www.w3.org/2000/svg" font-family="Segoe UI, Arial, sans-serif" width="100%">
  <style>
    .box{rx:8;ry:8;stroke-width:1.5;}
    .lbl{font-size:13px;font-weight:600;fill:#14204a;}
    .sub{font-size:10px;fill:#5b6472;}
    .agent{fill:#e9eefb;stroke:#3a5bd0;}
    .store{fill:#eafaf2;stroke:#0f9d58;}
    .io{fill:#fdeee0;stroke:#e5820e;}
    .out{fill:#f3eefe;stroke:#4a3aa7;}
    .arrow{stroke:#8a93a5;stroke-width:2;marker-end:url(#a);}
  </style>
  <defs>
    <marker id="a" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="#8a93a5"/>
    </marker>
  </defs>
  <!-- Input -->
  <rect class="box io" x="20" y="170" width="130" height="70"/>
  <text class="lbl" x="85" y="200" text-anchor="middle">Claim intake</text>
  <text class="sub" x="85" y="218" text-anchor="middle">docs · photos · video</text>
  <!-- Agents -->
  <rect class="box agent" x="185" y="175" width="120" height="60"/>
  <text class="lbl" x="245" y="200" text-anchor="middle">1. Intake</text>
  <text class="sub" x="245" y="216" text-anchor="middle">extract JSON</text>
  <rect class="box agent" x="335" y="175" width="120" height="60"/>
  <text class="lbl" x="395" y="200" text-anchor="middle">2. Timeline</text>
  <text class="sub" x="395" y="216" text-anchor="middle">order · gaps</text>
  <rect class="box agent" x="485" y="175" width="120" height="60"/>
  <text class="lbl" x="545" y="200" text-anchor="middle">3. Fraud</text>
  <text class="sub" x="545" y="216" text-anchor="middle">6-layer hybrid</text>
  <rect class="box agent" x="635" y="175" width="120" height="60"/>
  <text class="lbl" x="695" y="200" text-anchor="middle">4. Report</text>
  <text class="sub" x="695" y="216" text-anchor="middle">rank · cite</text>
  <!-- Output -->
  <rect class="box out" x="785" y="170" width="95" height="70"/>
  <text class="lbl" x="832" y="198" text-anchor="middle">Investig-</text>
  <text class="lbl" x="832" y="214" text-anchor="middle">ator</text>
  <text class="sub" x="832" y="230" text-anchor="middle">human decides</text>
  <!-- Flow arrows -->
  <line class="arrow" x1="150" y1="205" x2="183" y2="205"/>
  <line class="arrow" x1="305" y1="205" x2="333" y2="205"/>
  <line class="arrow" x1="455" y1="205" x2="483" y2="205"/>
  <line class="arrow" x1="605" y1="205" x2="633" y2="205"/>
  <line class="arrow" x1="755" y1="205" x2="783" y2="205"/>
  <!-- Supporting stores (below) -->
  <rect class="box store" x="185" y="300" width="150" height="60"/>
  <text class="lbl" x="260" y="325" text-anchor="middle">PostgreSQL</text>
  <text class="sub" x="260" y="341" text-anchor="middle">claims · policies · cases</text>
  <rect class="box store" x="355" y="300" width="150" height="60"/>
  <text class="lbl" x="430" y="325" text-anchor="middle">Chroma (RAG)</text>
  <text class="sub" x="430" y="341" text-anchor="middle">similar-claim retrieval</text>
  <rect class="box store" x="525" y="300" width="150" height="60"/>
  <text class="lbl" x="600" y="325" text-anchor="middle">ML models</text>
  <text class="sub" x="600" y="341" text-anchor="middle">DistilBERT · RandomForest</text>
  <!-- LLM layer (top) -->
  <rect class="box out" x="185" y="70" width="570" height="55"/>
  <text class="lbl" x="470" y="93" text-anchor="middle">Multi-provider LLM layer (fallback + key rotation)</text>
  <text class="sub" x="470" y="111" text-anchor="middle">Z.AI GLM → Gemini → Groq → (Claude/OpenRouter) · vision for images</text>
  <!-- connectors to LLM + stores -->
  <line class="arrow" x1="395" y1="175" x2="410" y2="127"/>
  <line class="arrow" x1="545" y1="175" x2="530" y2="127"/>
  <line class="arrow" x1="545" y1="235" x2="590" y2="298"/>
  <line class="arrow" x1="545" y1="235" x2="440" y2="298"/>
  <line class="arrow" x1="245" y1="235" x2="258" y2="298"/>
  <text class="sub" x="470" y="30" text-anchor="middle" font-size="12" font-weight="700" fill="#14204a">Streamlit investigator dashboard (login-gated)</text>
</svg>

**Flow:** a claim enters intake, is extracted to structured JSON, ordered into a timeline,
scored for fraud across six layers, then synthesised into a ranked, cited report — with a human
investigator making the final call. PostgreSQL, Chroma (RAG), and the ML models support the
agents; a resilient multi-provider LLM layer powers extraction and reasoning; everything is
served through a login-gated Streamlit dashboard.

---

## 6. Technology Stack

| Layer | Technology |
| --- | --- |
| **Orchestration** | LangGraph · LangChain-core |
| **LLMs** | Multi-provider fallback + key rotation: **Z.AI (GLM) → OpenRouter → Gemini → Claude → Groq**; Gemini/OpenRouter for vision |
| **Vector DB / RAG** | Chroma (Pinecone-ready abstraction) |
| **Relational store** | PostgreSQL (claims, parties, vehicles, photo hashes, policies, cases) |
| **ML / fine-tuning** | DistilBERT (narrative) · class-balanced Random Forest (tabular, real 30k rows) |
| **Frontend** | Streamlit dashboard, custom CSS, login-gated |
| **Media** | pypdf · pdfplumber · pypdfium2 (vision-OCR) · python-docx · OpenCV · Pillow · imagehash |
| **Infra** | Docker Compose · AWS deployment plan (RDS · S3 · ECS/EC2, optional SageMaker / Bedrock) |

---

## 7. Cost Analysis — What It Costs to Analyse a Claim

This is the core operating-cost question: *how much does it cost to run document/claim analysis?*

**Per-claim workload.** A single claim runs roughly **7–8 text LLM calls** (intake extraction,
timeline, two fraud passes, report synthesis, coverage, amount assessment, document completeness)
plus **one vision call per image**. That is approximately **20,000–30,000 input tokens** and
**~5,000 output tokens** per claim in total.

**Cost per claim by provider** (using ~25K input + 5K output tokens):

| Provider (per 1M tokens in/out) | Cost per claim | Per 1,000 claims |
| --- | --- | --- |
| **Z.AI GLM-4.5-flash / Groq** — free tier *(current default)* | **~$0.00** | **~$0** |
| **Gemini 2.5 Flash** ($0.30 / $2.50) [12] | **~$0.02** | **~$20** |
| **Claude Sonnet 5** ($3 / $15) [13] | **~$0.15** | **~$150** |
| **Claude Opus 4.8** ($5 / $25) [13] | **~$0.25** | **~$250** |

> Illustrative math (Gemini Flash): 25K × $0.30/1M = $0.0075 input + 5K × $2.50/1M = $0.0125
> output ≈ **$0.02/claim**. Vision-heavy claims add a small per-image increment.

**Run-rate scenarios** (add fixed infrastructure — managed Postgres + app hosting ≈ **$50–150 /
month** at pilot scale):

| Scenario | LLM tier | 10,000 claims/month | + infra | Monthly total |
| --- | --- | --- | --- | --- |
| **Lean / demo** | free tier | ~$0 | ~$50 | **~$50** |
| **Balanced** | Gemini Flash | ~$200 | ~$100 | **~$300** |
| **Premium** | Claude Sonnet | ~$1,500 | ~$150 | **~$1,650** |

**The ROI framing.** Fraud costs the average consumer **~$900/year** and AI fraud detection can
cut fraud losses by **up to 30%**. [1][6] Even at the premium tier, analysing a claim costs
**cents**, while catching a single inflated or fraudulent claim saves **thousands** — an
order-of-magnitude return. The platform is deliberately built to start at near-zero cost on free
tiers and scale up to paid, higher-accuracy models only where the ROI justifies it.

### 7.1 Free vs. paid — the quality trade-off

Free-tier models produce acceptable extraction and summaries, but the **hardest and most
valuable task — reading the whole claim file and catching where different documents contradict
each other** (dates, damage descriptions, amounts) — is a deep-reasoning task where small free
models fall short. This is exactly where premium models earn their cost:

| Tier | What it catches | Typical use |
| --- | --- | --- |
| **Free** (GLM / Llama / Flash-free) | Extraction, summaries, obvious red flags. Misses subtle cross-document contradictions. | Demo, low-stakes triage |
| **Claude Sonnet 5** | Reasons over the full document set; reliably flags "document A says X, document B says Y"; much stronger summaries. **The sweet spot.** | Production |
| **Claude Opus 4.8** | Sonnet's quality plus the hardest, most ambiguous cases; deepest reasoning (incremental gain over Sonnet on most claims). | High-stakes / escalated |

**The smart architecture is a hybrid**, not one model for everything: keep cheap models for the
mechanical steps (intake, timeline, coverage, amount, documents) and spend on a premium model
**only for the reasoning-heavy fraud + report step** — where contradiction detection lives.

| Setup | Cost / claim | Per 1,000 | ~10,000 / month |
| --- | --- | --- | --- |
| Free tier (today) | ~$0 | ~$0 | ~$0 |
| **Hybrid — Flash + Sonnet for reasoning** *(recommended)* | ~$0.07 | ~$70 | ~$700 |
| Hybrid — Flash + Opus for reasoning | ~$0.12 | ~$120 | ~$1,200 |
| All Sonnet / all Opus | $0.15 / $0.25 | $150 / $250 | $1,500 / $2,500 |

The hybrid delivers roughly **90% of premium quality at under half the cost** — the recommended
path to production.

**On training.** For contradiction detection and summarisation, a strong base model with good
prompting **beats fine-tuning a small model**, and avoids the data-collection, labelling, and GPU
cost — so early funding is best spent on a **better base model, not on training an LLM**.
Fine-tuning is reserved for the **numeric fraud classifier** (the existing DistilBERT / Random
Forest layer), where more labelled real-world claims data directly improves the score — a Phase-2
investment once a pilot supplies that data.

---

## 8. Roadmap & The Ask

The MVP is complete and working end-to-end. Funding accelerates the path from demo to pilot:

- **Paid LLM tier** — move the primary path to a paid, higher-accuracy model for production
  reliability and consistency (a modest, usage-based cost per the table above).
- **Cloud deployment** — AWS (RDS · S3 · ECS), so an insurer can pilot on real infrastructure.
- **Pilot with real (permissioned) data** — validate accuracy and fraud-catch rate on a partner
  insurer's historical claims.
- **Hardening** — output-consistency controls, audit logging, and role-based access for
  multi-user investigator teams.

**The ask:** seed funding to run a paid-tier pilot and a cloud deployment, turning a working MVP
into a revenue-ready product in a market growing at ~32–35% per year.

---

## 9. References

1. Coalition Against Insurance Fraud / industry statistics — *Insurance fraud worldwide and US
   costs, P&C share, consumer impact, GenAI fake-media trend.*
   https://insurancefraud.org/fraud-stats/ ; https://www.iii.org/fact-statistic/facts-and-statistics-insurance-fraud
2. Insurance Information Institute — *Facts + Statistics: Fraud.*
   https://www.iii.org/fact-statistic/facts-and-statistics-insurance-fraud
3. EY — *How a Nordic insurance company automated claims processing.*
   https://www.ey.com/en_dk/insights/financial-services/emeia/how-a-nordic-insurance-company-automated-claims-processing
4. InsurCalim AI — companion research survey, `docs/research/ai-in-insurance-claims.md`.
5. Fortune Business Insights — *AI in Insurance Market Size, Share.*
   https://www.fortunebusinessinsights.com/ai-in-insurance-market-114760
6. *AI in Insurance Claims Processing Market* (GlobeNewswire) and Mordor Intelligence — market
   size, CAGR, and fraud-loss reduction.
   https://www.globenewswire.com/news-release/2026/07/06/3322187/28124/en/AI-in-Insurance-Claims-Processing-Market-Surges-to-0-97-Billion-by-2030-with-a-CAGR-of-16-2.html ; https://www.mordorintelligence.com/industry-reports/ai-in-insurance-market
7. PwC — *Auto insurance AI analytics case study (explainable AI damage estimation).*
   https://www.pwc.com/us/en/library/case-studies/auto-insurance-ai-analytics.html
8. McKinsey & Company — *Aviva: Rewiring the insurance claims journey with AI.*
   https://www.mckinsey.com/capabilities/tech-and-ai/how-we-help-clients/rewired-in-action/aviva-rewiring-the-insurance-claims-journey-with-ai
9. Shift Technology — *AI in underwriting: case examples from leading insurers.*
   https://www.shift-technology.com/resources/reports-and-insights/ai-in-underwriting-case-examples-from-leading-insurers
10. AWS / EXL — *EXL reduces underwriting costs by up to 80% using Amazon Bedrock.*
    https://aws.amazon.com/solutions/case-studies/exl-case-study/
11. Lemonade — *AI Jim claims automation.*
    https://www.claimsjournal.com/news/national/2025/03/07/327670.htm
12. Google — *Gemini 2.5 Flash API pricing ($0.30 input / $2.50 output per 1M tokens).*
    https://ai.google.dev/pricing
13. Anthropic — *Claude API pricing (Sonnet 5 $3/$15; Opus 4.8 $5/$25 per 1M tokens).*
    https://platform.claude.com/docs/en/pricing

---

*InsurCalim AI is a portfolio project built on synthetic and public data only — no real customer
information. All market and pricing figures are attributed to the public sources cited above.
Decision support for a human investigator, not an automated decision.*
