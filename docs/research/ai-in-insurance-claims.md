# AI in Insurance Claims: Big-Tech Case Studies, Challenges, and Solutions

**A survey of how leading consultancies, cloud platforms, and insurtechs apply artificial intelligence to insurance claims — and the design lessons for InsurCalim AI.**

---

## Abstract

Insurance is one of the largest and fastest-moving arenas for applied artificial intelligence. Claims handling in particular — high in volume, rich in unstructured documents, exposed to fraud, and sensitive to customer waiting time — has become the prime target for automation across the industry. This paper surveys concrete, publicly documented deployments from three groups of players: global consultancies (EY, PwC, McKinsey), cloud platforms (Amazon Web Services and its partner ecosystem), and insurtechs and specialist vendors (Lemonade, Shift Technology, Ping An, Tractable). For each we describe the business problem, the AI solution and how it works, the challenge that had to be overcome, and the measurable results reported. We then distil the challenges common to every deployment — unstructured intake, the "black-box" trust problem, regulatory defensibility, over-automation risk, and fraud — and the solutions the industry has converged on: intelligent document processing, explainable AI, audit trails and citations, and human-in-the-loop control. Finally we map these lessons onto **InsurCalim AI**, a multi-agent, explainable, human-in-the-loop claims-investigation system, showing that its design mirrors the patterns the market leaders have independently arrived at.

---

## 1. Introduction

Claims are where an insurer's promise is actually paid out, and where most of its operating cost and customer friction live. A single motor claim can arrive as a mix of photographs, PDF scans, invoices, medical notes, police reports, and free-text statements, each of which a human adjuster must open, read, cross-check, and key into a legacy system. Multiplied across millions of claims a year, this manual work is slow, expensive, inconsistent, and vulnerable to fraud.

Artificial intelligence attacks every part of that chain at once:

- **Document understanding** — optical character recognition (OCR) and natural-language processing (NLP) turn unstructured files into structured data.
- **Damage and cost assessment** — computer vision estimates repair scope from photographs.
- **Fraud detection** — machine-learning models and network analysis flag suspicious patterns a human would miss.
- **Triage and routing** — models decide which claims can be fast-tracked and which need a specialist.
- **Customer interaction** — conversational agents handle first notice of loss (FNOL) and status updates.

The prize is large. Industry deployments now report cost reductions of 30–80%, processing times cut from weeks to seconds, and tens of millions of dollars in prevented fraud. That is why, as one supervisor framed it, "insurance is a huge field, and every company is racing to work on it." The remainder of this paper documents *who* is doing *what*, *how* they overcame the hard parts, and *what results* they achieved.

---

## 2. The Landscape

The organisations bringing AI to claims fall into three broad types, each with a different business model:

| Type | Representative players | What they bring |
| --- | --- | --- |
| **Consultancies / professional services** | EY, PwC, McKinsey | Bespoke transformation programmes, proprietary tooling, change management inside large incumbents |
| **Cloud platforms & their partners** | AWS (with EXL, HCLTech, Generali) | Reusable AI building blocks — document AI, generative AI, ML infrastructure — assembled into solutions |
| **Insurtechs & specialist vendors** | Lemonade, Shift Technology, Ping An, Tractable | AI-native products, either full digital insurers or focused engines (fraud, damage, chat) sold to carriers |

The following section examines representative case studies from each.

---

## 3. Case Studies

### 3.1 EY — Automating claims processing for a Nordic insurer

- **Problem.** A leading Nordic insurance firm processed every claim manually: agents opened individual images and PDF scans of invoices, pharmacy receipts, and medical documents, analysed them, and re-keyed the relevant data into the claims system. The volume and variety of unstructured data overwhelmed existing infrastructure and slowed customer service. [1]
- **Solution — how it works.** EY deployed **EY Fabric Document Intelligence**, a machine-learning and Python platform that "converts semi-structured and unstructured documents into actionable structured data." It runs in stages: image cleansing (background removal, rotation correction, noise reduction), data processing via OCR and NLP, classification into structured formats, and integration back into the insurer's legacy claims system. [1]
- **Challenge overcome.** The design was deliberately **human-centred and transparent** — EY explicitly avoided a "black-box implementation of AI," giving the insurer the control and auditability it required.
- **Results.** Roughly **70% of documents are correctly extracted and interpreted** automatically, enabling near real-time processing and freeing agents to focus on customer relationships; the project became a springboard for enterprise-wide modernisation. [1]

### 3.2 PwC — Explainable AI for auto damage estimation

- **Problem.** An auto-insurance client relied on experienced estimators to analyse photographs and produce preliminary damage assessments. As the business grew, a shortage of qualified estimators threatened to cap growth, so the client asked PwC to speed up estimation. [2]
- **Solution — how it works.** PwC built **image-recognition AI models to detect and classify vehicle damage**, using an **explainable AI (XAI)** technique that shows *visually why* the model reached each prediction at every stage of the process. [2]
- **Challenge overcome.** Trust and defensibility. Because estimators must stand behind their numbers, PwC made the model's reasoning inspectable rather than opaque — and the AI even caught damage details that the manual process had missed.
- **Results.** The proof of concept identified **29% efficiency savings** achievable with full roll-out across the estimator team, while improving consistency and trust. [2]

### 3.3 McKinsey — Aviva: rewiring the claims journey with AI

- **Problem.** Aviva's motor-claims journey was slow and fragmented, with complex liability decisions taking weeks and customers frequently dissatisfied. [3]
- **Solution — how it works.** Working with McKinsey, Aviva rolled out **more than 80 AI models** across the claims function and adopted a **"double-helix" operating model** in which the journey can switch seamlessly between digital and human tracks — cases involving personal injury, for example, default to human handling. The transformation spanned six dimensions: strategy, talent, agile operating model, technology, data, and adoption/scaling. [3][4]
- **Challenge overcome.** Balancing automation with judgement and empathy. The double-helix keeps a human in the loop exactly where stakes are highest, rather than forcing full automation.
- **Results.** Liability assessment for complex cases became **23 days faster**, routing accuracy improved **30%**, customer complaints fell **65%**, net promoter score climbed **more than seven-fold**, employee engagement more than doubled to an all-time high, and Aviva told investors the motor-claims transformation **saved more than £60 million (~$82 million) in 2024**; use of recycled parts tripled, cutting cost and environmental impact. [3][4]

### 3.4 Shift Technology — AI for underwriting and fraud detection

- **Problem.** Insurers renew or bind risky and fraudulent policies through legacy systems with few safeguards, and manual reviews cannot scale. [5]
- **Solution — how it works.** Shift Technology applies **fraud and misrepresentation detection, network analysis, and entity resolution** to spot hidden risk — for example identifying "ghost broker" networks (which average 500% loss ratios) and policyholders concealing their claims history, and firing prioritised alerts into underwriting workflows. [5]
- **Challenge overcome.** Catching fraud *before* it becomes a costly claim, without adding headcount, and doing so with alerts specific enough for humans to act on.
- **Results.** For a top-5 US personal-auto insurer: a **40% impact rate on policy alerts**, **$30M+ in annual projected underwriting risk mitigation**, and **$15 of prevented losses per new policy**. For a major European P&C insurer: **3× the expected relevant alerts**, accuracy beyond the 50% benchmark, **100+ risky policies** that manual review had missed, and **$1M in annual projected risk mitigation**. [5]

### 3.5 Amazon Web Services and partners — building blocks for claims and underwriting

AWS supplies reusable components — **Amazon Textract** (document extraction), **Amazon Comprehend** (NLP), **Amazon Bedrock** (generative AI, including Anthropic's Claude models), **Amazon Kendra** (enterprise search), and **Amazon SageMaker** (ML) — that partners assemble into claims and underwriting solutions. [6]

- **EXL — Underwriting Assist.** Built on Amazon Bedrock (using **Claude 3 Sonnet**) with Kendra, Textract, and Comprehend, EXL's Life Digital Suite Underwriting Assist was delivered in **60 days** and **cut underwriting costs by up to 80%**, compressing processing from days to hours. [6]
- **HCLTech — intelligent intake.** A serverless solution using Textract and Amazon Nova Pro behind Bedrock agents achieved a **20× efficiency improvement** on ACORD-130 form processing and **95% accuracy** with automated validation. [6]
- **Generali** uses Bedrock and SageMaker to automate data processing and decision-making across pricing, underwriting, claims, and operations. [6]
- **Challenge overcome.** Speed and scale of deployment. Rather than building models from scratch, carriers compose pre-trained, managed services — reaching production in weeks while keeping data governance on the cloud platform.

### 3.6 Lemonade — AI-native claims ("AI Jim")

- **Problem.** Legacy claims processes take days or weeks; a digital-native insurer set out to settle in seconds. [7]
- **Solution — how it works.** Lemonade's claims bot **"AI Jim"** receives the FNOL — often a short video or text — and performs multi-layered analysis: conversational triage with clarifying questions, rules-based checks against policy and coverage, and fraud signals, before making a payout decision. [7]
- **Challenge overcome.** Automating end-to-end payout while controlling fraud and keeping customers satisfied — with clear escalation to humans when needed.
- **Results.** By end of 2025, **96% of FNOLs are taken by AI without human intervention**, **55% of claims are fully automated end-to-end**, the fastest settlements complete in **~3 seconds**, customer satisfaction with AI Jim exceeds **90%**, and AI-driven automation contributed to roughly a **30% reduction in claims-processing costs**. [7]

### 3.7 Ping An and Tractable — scale and specialist vision

- **Ping An (China)** handles enormous inquiry and claims volumes with AI, including the **"AskBob"** assistant that delivers real-time, personalised responses — an example of AI deployed at population scale. [7]
- **Tractable** is a specialist computer-vision vendor whose models estimate vehicle (and property) damage directly from photographs to accelerate motor-claim appraisal, illustrating the "focused engine sold to carriers" model. [8]

---

## 4. Cross-Cutting Challenges and How the Industry Solved Them

Across every case study, the same handful of obstacles recur — and the industry has converged on a consistent set of answers.

| Challenge | Why it matters | Solution the industry adopted | Seen in |
| --- | --- | --- | --- |
| **Unstructured intake** | Claims arrive as photos, scans, invoices, medical notes, free text | Intelligent document processing: OCR + NLP to extract structured data | EY [1], AWS/HCLTech [6] |
| **The "black-box" problem** | Opaque decisions are hard to trust or defend | **Explainable AI (XAI)** — show *why* each prediction was made | PwC [2], EY [1], [9] |
| **Regulatory & legal defensibility** | Every decision must stand up to auditors, regulators, and courts | **Audit trails and citations** — a transparent, traceable evidence chain | [9], regulatory literature |
| **Over-automation risk** | Wrong automated denials harm customers and create liability | **Human-in-the-loop as a baseline** — AI assists, flags uncertainty, routes edge cases to people | McKinsey/Aviva [3], [9] |
| **Fraud** | Fraud inflates loss ratios and premiums | Fuse structured data + document/image analysis + NL statements, then route prioritised cases to investigators with **explainable risk scores, not black-box flags** | Shift [5], [9] |

Two themes dominate. First, **explainability is not optional** in insurance: because outcomes affect customers, money, and compliance, leaders build systems whose reasoning a human can inspect and a regulator can audit. Second, **human-in-the-loop is a baseline requirement, not a best-practice nicety** — the recurring pattern is AI that *ranks and recommends* while a person decides, especially for high-stakes cases such as personal injury or outright denial.

---

## 5. Synthesis: How InsurCalim AI Applies These Lessons

**InsurCalim AI** is a multi-agent auto-claims investigation system: it ingests a claim's documents, photos, and videos and produces a ranked, explainable investigator report — risk score, event timeline, flagged inconsistencies, coverage and amount assessment, citations, and a recommended action — with a human always making the final call. Its design maps directly onto the industry patterns above.

| Industry lesson | Where it came from | How InsurCalim AI implements it |
| --- | --- | --- |
| Turn unstructured files into structured data | EY [1], AWS [6] | Multi-format intake (documents, DOCX, images, video, scanned-PDF OCR) that extracts structured claim data |
| Explainable AI, not black-box scores | PwC [2], EY [1] | An explainable fraud/risk score with per-signal reasons and evidence, plus a written narrative |
| Audit trails and citations | Regulatory practice [9] | Policy-clause citations and document-level evidence attached to every finding |
| Human-in-the-loop, never auto-deny | McKinsey/Aviva [3] | Positioned explicitly as "ranks and recommends, never auto-denies"; high-risk cases route to a senior investigator |
| Multi-signal fraud fusion | Shift [5] | Combines narrative red flags, document-level fraud, image/AI-generated-media detection, and similar-known-fraud retrieval |
| Cost/quantum discipline | Industry damage-estimation work [2] | A claim-amount (quantum) assessment judging whether the demanded amount is justified, and if not, the fair estimate |

In short, InsurCalim AI is not an outlier: it embodies the same design principles — document intelligence, explainability, auditability, human-in-the-loop control, and multi-signal fraud analysis — that EY, PwC, McKinsey, AWS's ecosystem, and the leading insurtechs have independently converged on.

---

## 6. Conclusion

AI in insurance claims has moved from pilot to production, and the evidence is concrete: 70% automated document extraction (EY), 29% estimation efficiency (PwC), £60M annual savings and a seven-fold NPS gain (Aviva/McKinsey), $30M+ in prevented fraud (Shift), 80% lower underwriting cost (EXL on AWS), and three-second settlements (Lemonade). Just as striking is the convergence in *how* these results were achieved — every serious deployment pairs automation with **explainability, auditability, and a human in the loop**, because insurance decisions must be trusted, defended, and, when necessary, overruled by a person. A claims-investigation system built today should therefore be judged not only on speed and accuracy but on whether it can *explain itself* and *defer to human judgement*. InsurCalim AI is designed on exactly those principles.

---

## References

1. EY. *How a Nordic insurance company automated claims processing.* https://www.ey.com/en_dk/insights/financial-services/emeia/how-a-nordic-insurance-company-automated-claims-processing
2. PwC. *Insurance claims estimator uses AI for efficiency (auto insurance AI analytics case study).* https://www.pwc.com/us/en/library/case-studies/auto-insurance-ai-analytics.html
3. McKinsey & Company. *Aviva: Rewiring the insurance claims journey with AI.* https://www.mckinsey.com/capabilities/tech-and-ai/how-we-help-clients/rewired-in-action/aviva-rewiring-the-insurance-claims-journey-with-ai
4. McKinsey & Company. *Rewired in action — case collection (2025).* https://www.mckinsey.com/capabilities/tech-and-ai/how-we-help-clients/rewired-in-action
5. Shift Technology. *AI in underwriting: case examples from leading insurers.* https://www.shift-technology.com/resources/reports-and-insights/ai-in-underwriting-case-examples-from-leading-insurers
6. Amazon Web Services. *Solutions for insurance*, and partner case studies — EXL (*Underwriting Assist on Amazon Bedrock*), HCLTech (*insurance intake with Amazon Nova Pro and Bedrock agents*), Generali. https://aws.amazon.com/solutions/financial-services/insurance/ ; https://aws.amazon.com/solutions/case-studies/exl-case-study/ ; https://aws.amazon.com/blogs/machine-learning/automate-the-insurance-claim-lifecycle-using-amazon-bedrock-agents-and-knowledge-bases/
7. Lemonade / Ping An coverage. *AI Jim claims automation* and *Ping An "AskBob"*. https://www.claimsjournal.com/news/national/2025/03/07/327670.htm ; https://getperspective.ai/blog/lemonade-case-study-conversational-ai-insurance
8. Tractable. *AI for accident and disaster recovery (vehicle and property damage appraisal).* https://tractable.ai/
9. Explainable AI and human-in-the-loop in insurance — industry analysis. https://brisc.ai/blog/explainable-ai-xai-in-insurance-moving-beyond-the-black-box ; https://owl.co/resources/explainable-ai-in-insurance

---

*Prepared as a research survey for the InsurCalim AI project. All figures are drawn from the publicly available sources cited above; company names and results are attributed to their respective publishers.*
