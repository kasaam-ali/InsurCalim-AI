# InsurClaim AI: Project Overview

A source document for generating a narrated overview video. It explains what the
product is, the problem it solves, how a claim moves through the system, and how
each part works, in plain, professional language.

## What it is

InsurClaim AI is a multi-agent decision-support system for auto-insurance claims.
When a new claim arrives, it reads the whole case, checks it for signs of fraud,
and hands the investigator a single ranked, explainable report. It is a triage and
assistance tool, not an automated judge.

The one-line pitch: InsurClaim AI reads a claim the way a careful investigator
would, flags what looks off, ranks how risky it is, and always leaves the final
decision to a human.

## The problem it solves

Insurance teams receive far more claims than they can review closely. Genuine
claims and fraudulent ones sit in the same queue, so honest customers wait while
investigators spend time on cases that turn out to be fine. Reviewing everything by
hand is slow, and simple automated rules miss the cleverer fraud.

InsurClaim AI closes that gap. It does the first pass of reading and cross-checking
in about a minute, then surfaces the claims that deserve a human's attention first,
with the evidence attached so the investigator can trust it or overrule it.

## The golden rule

The system flags and ranks. It never auto-denies and never auto-approves. Every
claim still ends with a person making the final call. The report is written to
support that decision, not to replace it. This human-in-the-loop design is central
to the product.

## How a claim flows

A claim moves through four specialist agents, in order, each adding to a shared case
file. This pipeline is built on LangGraph, a framework for wiring AI agents into a
clear step-by-step flow.

1. Intake. The system takes the raw inputs: the claim narrative, a police report or
   FIR, damage photos, and even dashcam video. It reads documents in several formats
   and pulls out the structured facts: the vehicle, the incident, the damage, the
   amount being claimed, and which documents are present or missing.

2. Timeline. It reconstructs the order of events and checks them for physical and
   logical consistency. Impossible dates, gaps, and sequences that could not have
   happened in real life are flagged here.

3. Fraud. This is the core of the system. It runs several independent fraud checks,
   scores the claim, and finds similar past claims for context.

4. Report. It combines everything into one ranked, plain-English report with a risk
   score, the key findings, the evidence behind each finding, a fair-cost estimate,
   and a clear recommendation for the human reviewer.

## The risk score and its bands

Every claim receives a single risk score from 0 to 100. The higher the number, the
more closely a human should look. The score falls into one of three bands, and each
band maps to a suggested action:

- HIGH, 60 to 100. Likely fraud. Route the claim to an investigator for a full
  review.
- MEDIUM, 30 to 59. Not certain yet. Ask the claimant for the missing document or
  detail before deciding.
- LOW, 0 to 29. Looks fine. Safe to fast-track for approval, and it is still logged
  for the record.

## How fraud is detected

InsurClaim AI does not rely on a single trick. It combines several layers of
checking, so a claim has to pass many different tests. The layers are:

1. Deterministic rules. Straightforward checks for known red flags, such as an
   impossible incident date or a claimed amount far above a fair repair cost.

2. Duplicate-photo detection. Image hashing catches damage photos that have been
   reused across claims, a common sign of staged or recycled fraud.

3. Machine-learning classifier. A trained model estimates the probability that a
   claim is fraudulent based on patterns learned from historical claims.

4. Similar-claims retrieval. Using a vector search over past claims, the system
   finds cases that closely resemble the current one, which helps spot organized or
   repeated fraud.

5. Narrative red flags. A language model reads the claim story itself and points out
   inconsistencies, exaggerations, and phrasing that often appears in false claims.

6. Synthesis. A final language-model step weighs all the signals together and writes
   the human-readable summary and recommendation.

Every flag is explainable. Each one comes with the finding, the evidence for it, and
the action it suggests, so nothing in the report is a black box.

## The report and the built-in assistant

The report is designed for a busy human reviewer. It leads with the risk score and
band, then lists the key findings, gives a plain-English summary, and shows a
fair-cost estimate that compares what the claimant is demanding against a reasonable
repair cost.

Each report also has a built-in chat assistant. The investigator can ask questions
in plain language, such as why a claim is high risk or what document is missing. The
assistant answers only from that one claim's file. It does not answer questions that
are unrelated to the claim in front of it, which keeps it focused and trustworthy.

## What it is built with

InsurClaim AI pairs a Python backend with a modern web dashboard.

- The backend uses LangGraph to orchestrate the four agents, a machine-learning
  model for fraud probability, a vector store for similar-claims retrieval, and a
  language model for reading narratives and writing the report. A resilient
  multi-provider setup keeps the language-model calls working even if one provider
  is unavailable.

- The frontend is a React investigator dashboard. It has a command center with the
  key numbers and the riskiest claims, an investigation queue, fraud analytics, a
  fraud-rings view that reveals connected claims, the new-investigation screen, the
  full report view, a claimant profile, policy and coverage tools, and a model-health
  page.

## Who it is for and the key takeaway

InsurClaim AI is for insurance investigators and claims teams who need to review more
claims, more consistently, without losing human judgment. It speeds up the first
pass and points attention where it matters most.

The key takeaway: it reads every claim, explains what it finds, ranks the risk, and
hands a clear report to a person, who always makes the final decision.
