# Competitive Analysis & Positioning

How InsurClaim AI compares to leading insurance-AI vendors, what to borrow from
each, and where we can differentiate. Used to prioritize the roadmap.

## The landscape

| Vendor | Focus | Signature strength |
| --- | --- | --- |
| **Shift Technology** | Fraud detection + claims decisioning | Fraud reason codes at FNOL, coverage & liability analysis, subrogation, cross-carrier network (IDN) |
| **Tractable** | Computer vision for auto damage | Pixel-level damage assessment from photos with certainty scores; repair vs total-loss |
| **Cytora** | Risk/document digitization & intake | Unstructured documents → structured decision-ready data (140+ languages), agentic workflows, audit trails |
| **Lemonade** | Consumer insurer (D2C) | AI chatbot instant claims ("AI Jim"), ~3-second claims, app-first UX, behavioral-economics anti-fraud |
| **Yunke** | Digital insurance platform (China) | End-to-end policy/claims administration and distribution SaaS |

## What each does that we should match

- **Shift** → coverage & liability analysis (is the claim covered by the policy?),
  explainable reason codes, cross-claim network fraud. *We already have reason
  codes and RAG fraud-rings; we are adding a policy coverage engine.*
- **Tractable** → damage assessment from photos. *We hash photos for reuse; we are
  adding vision-based damage description and photo-vs-narrative consistency.*
- **Cytora** → ingest any document (FIR, police report, medical bill, PDF) into a
  structured claim. *We are adding document/photo upload + extraction.*
- **Lemonade** → frictionless claim submission UX. *We are adding an upload/submit
  flow; a conversational intake is a future option.*
- **Yunke** → policy administration. *Out of scope we are an investigation layer,
  not a full policy-admin core.*

## Where we already lead / can differentiate

1. **Explainable, multi-layer investigation in one report** deterministic rules
   + fine-tuned ML + similar-past-claim RAG + LLM narrative reasoning + timeline
   physics + coverage, each with an evidence pointer. Competitors specialize
   (Tractable = vision, Shift = fraud, Cytora = intake); we unify them.
2. **Fraud-ring detection from narrative similarity** link organized fraud by
   modus operandi, not just shared identifiers.
3. **Timeline physics / impossible-timeline detection** a differentiator few
   general fraud tools advertise.
4. **Open & self-hostable, bring-your-own-model** a multi-provider LLM layer
   (Claude / Gemini / Groq / OpenRouter) means an insurer can run it in their own
   environment for data privacy, versus closed SaaS.
5. **Human-in-the-loop by design** ranks and recommends, never auto-denies;
   audit-defensible exports.

## Feature roadmap (borrow + differentiate)

**Building now**
- [ ] Company policy upload + **coverage check** (is the claim within policy?).
- [ ] Claim **document/photo upload** → extract → run pipeline → report.
- [ ] **Vision damage analysis** describe damage from a photo, flag
      photo-vs-narrative inconsistencies.

**Next**
- [ ] Investigator case management: notes, status, assignment, audit log.
- [ ] Cross-carrier / shared-entity linking (phone, address, VIN) beyond narrative.
- [ ] Conversational claim intake (Lemonade-style).
- [ ] Confidence/uncertainty surfaced on every layer.
- [ ] Multi-language intake (Cytora-style).

## One-line pitch

> InsurClaim AI is an **open, explainable claim-investigation layer** that reads a
> claim's documents and photos, checks it against the insurer's own policy, and
> returns a ranked, evidence-cited fraud report combining rules, a fine-tuned
> model, similar-claim retrieval, and LLM reasoning, with a human always in the loop.
