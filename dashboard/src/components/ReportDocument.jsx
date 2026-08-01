import { useState } from "react";
import { createPortal } from "react-dom";
import { X, Printer, ChevronDown } from "lucide-react";
import { fmtMoney } from "../lib/report.js";

// A professional, monochrome, print-ready investigation report expository
// prose in a proper sequence, no charts or colour. Each section is a button you
// open for detail; the fair-cost figure appears exactly once. "Download PDF"
// prints this same document (all sections expanded) via the browser.

const RISK_WORD = (s) => (s >= 60 ? "high" : s >= 30 ? "medium" : "low");

const ACTION_LABEL = {
  route_to_investigator: "refer the claim to a human investigator",
  request_more_info: "request further information from the claimant",
  fast_track_approve: "fast-track the claim towards approval",
};

const ACTION_STEPS = {
  route_to_investigator: [
    "Open a case file and assign a named investigator.",
    "Re-examine each finding below against the original documents and photographs.",
    "Interview the claimant and any third parties to corroborate the account.",
    "Withhold settlement until the investigator formally signs off.",
  ],
  request_more_info: [
    "Issue the claimant a request for the outstanding documents listed below.",
    "Seek written clarification on each point raised under Findings.",
    "Re-assess the claim once the additional evidence is received.",
  ],
  fast_track_approve: [
    "Perform a final manual review of the claim particulars.",
    "Confirm the demanded amount against the fair-cost assessment below.",
    "Approve and release settlement.",
  ],
};

const VERDICT_SENTENCE = {
  overstated: "materially exceeds a fair market repair cost and appears inflated",
  understated: "falls below a fair market repair cost",
  fair: "is consistent with a fair market repair cost",
  reasonable: "is consistent with a fair market repair cost",
  insufficient_info: "could not be assessed for want of sufficient detail",
};

export default function ReportDocument({ result, onClose }) {
  const report = result?.final?.report || {};
  const overview = result?.overview || {};
  const amount = result?.amount || null;
  const coverage = result?.coverage || null;
  const documents = result?.documents || null;
  const flags = (report.top_flags || []).filter((f) => f?.summary);

  const score = Math.round(Number(report.risk_score) || 0);
  const ccy = amount?.currency || "PKR";
  const action = report.recommended_action;
  const ref = `IC-${String(Math.abs(hash(overview.claimant + (overview.incident_date || "") + score)) % 100000).padStart(5, "0")}`;
  const today = new Date().toLocaleDateString("en-GB", { day: "2-digit", month: "long", year: "numeric" });

  const particulars = [
    ["Claimant", overview.claimant],
    ["Vehicle", overview.vehicle],
    ["Date of incident", overview.incident_date],
    ["Date reported", overview.report_date],
    ["Location", overview.location],
    ["Amount claimed", overview.claimed_amount != null ? fmtMoney(overview.claimed_amount, ccy) : null],
  ].filter(([, v]) => v && v !== "-");

  const present = documents?.present || [];
  const missing = documents?.missing || [];

  const doc = (
    <div className="min-h-full w-full bg-neutral-700/60 px-4 py-8 backdrop-blur-sm">
      {/* Toolbar */}
      <div className="no-print mx-auto mb-4 flex max-w-[820px] items-center justify-between">
        <div className="text-[13px] font-medium text-white/90">Report preview</div>
        <div className="flex items-center gap-2">
          <button onClick={() => window.print()}
                  className="inline-flex h-9 items-center gap-2 rounded-md bg-white px-3.5 text-[13px] font-semibold text-neutral-900 transition hover:bg-neutral-200">
            <Printer className="h-4 w-4" /> Download PDF
          </button>
          <button onClick={onClose}
                  className="grid h-9 w-9 place-items-center rounded-md bg-white/10 text-white transition hover:bg-white/20">
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Paper sheet */}
      <article id="report-print"
               className="mx-auto max-w-[820px] rounded-md bg-white px-10 py-12 text-[13.5px] leading-relaxed text-neutral-800 shadow-2xl"
               style={{ fontFamily: "Inter, system-ui, sans-serif" }}>
        {/* Masthead */}
        <header className="border-b border-neutral-300 pb-5">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-neutral-500">
                InsurClaim AI · Fraud Operations
              </div>
              <h1 className="mt-1 text-2xl font-bold tracking-tight text-neutral-900">Investigation Report</h1>
            </div>
            <div className="text-right text-[11px] leading-5 text-neutral-500">
              <div>Ref&nbsp;<span className="font-mono font-semibold text-neutral-700">{ref}</span></div>
              <div>{today}</div>
              <div className="font-semibold uppercase tracking-wide text-neutral-600">Confidential</div>
            </div>
          </div>
          <p className="mt-3 text-[12px] text-neutral-500">
            Prepared by the automated investigation engine for human review. This document explains and
            recommends; it does not decide. A person retains the final decision on this claim.
          </p>
        </header>

        {/* 1 Executive summary (open) */}
        <Section n="1" title="Executive summary" defaultOpen>
          <p>
            This claim has been assessed at an overall concern score of{" "}
            <strong className="text-neutral-900">{score} out of 100</strong> ({RISK_WORD(score)} concern).
            {flags.length > 0 && <> The assessment surfaced {flags.length} matter{flags.length > 1 ? "s" : ""} warranting attention, the most significant being “{flags[0].summary}”.</>}
            {amount?.verdict && amount.verdict !== "insufficient_info" && (
              <> The amount demanded {VERDICT_SENTENCE[amount.verdict]}.</>
            )}
            {" "}On the balance of the evidence, the recommended course of action is to{" "}
            <strong className="text-neutral-900">{ACTION_LABEL[action] || "have the claim reviewed by a person"}</strong>.
          </p>
        </Section>

        {/* 2 Claim particulars */}
        {particulars.length > 0 && (
          <Section n="2" title="Claim particulars" hint="the facts on record" defaultOpen>
            <dl className="grid grid-cols-1 gap-x-10 gap-y-2 sm:grid-cols-2">
              {particulars.map(([k, v]) => (
                <div key={k} className="flex justify-between gap-4 border-b border-neutral-100 py-1">
                  <dt className="text-neutral-500">{k}</dt>
                  <dd className="text-right font-medium text-neutral-900">{v}</dd>
                </div>
              ))}
            </dl>
            {(overview.parties || []).filter((p) => p.full_name && p.full_name !== "-").length > 0 && (
              <p className="mt-3 text-[12.5px] text-neutral-600">
                <span className="font-semibold text-neutral-700">Parties: </span>
                {overview.parties.filter((p) => p.full_name && p.full_name !== "-")
                  .map((p) => `${p.full_name} (${p.role})`).join("; ")}.
              </p>
            )}
          </Section>
        )}

        {/* 3 Narrative of the incident */}
        {(report.timeline_summary || overview.summary) && (
          <Section n="3" title="Narrative of the incident" hint="what is said to have happened">
            <p>{report.timeline_summary || overview.summary}</p>
          </Section>
        )}

        {/* 4 Findings */}
        <Section n="4" title="Findings" hint={`${flags.length} matter${flags.length === 1 ? "" : "s"} raised`} defaultOpen={flags.length > 0}>
          {flags.length === 0 ? (
            <p>No specific concerns were raised against this claim during the automated assessment.</p>
          ) : (
            <ol className="space-y-3">
              {flags.map((f, i) => (
                <li key={i}>
                  <p>
                    <strong className="text-neutral-900">{i + 1}. {f.summary}.</strong>
                    {f.evidence && <> {f.evidence}</>}
                    {f.confidence !== undefined && f.confidence !== "" && !Number.isNaN(Number(f.confidence)) && (
                      <span className="text-neutral-500"> (confidence {Math.round(Number(f.confidence))}%)</span>
                    )}
                  </p>
                </li>
              ))}
            </ol>
          )}
        </Section>

        {/* 5 Cost assessment (fair estimate appears exactly once) */}
        {amount && (
          <Section
            n="5"
            title="Cost assessment"
            hint={amount.fair_estimate != null ? `fair estimate ${fmtMoney(amount.fair_estimate, ccy)}` : "estimate"}
          >
            <p>
              The claimant demands <strong className="text-neutral-900">{fmtMoney(amount.claimed_amount, ccy)}</strong>.
              {amount.verdict && amount.verdict !== "insufficient_info" && (
                <> Measured against current market repair costs, this amount {VERDICT_SENTENCE[amount.verdict]}.</>
              )}
              {(amount.line_items || []).length > 0 && <> The fair-cost estimate stated above is built up as follows:</>}
            </p>
            {(amount.line_items || []).length > 0 && (
              <table className="mt-4 w-full border-collapse text-[12.5px]">
                <thead>
                  <tr className="border-y border-neutral-300 text-left text-[11px] uppercase tracking-wide text-neutral-500">
                    <th className="py-1.5 font-semibold">Item</th>
                    <th className="py-1.5 text-right font-semibold">Estimate</th>
                    <th className="hidden py-1.5 font-semibold sm:table-cell">Source</th>
                  </tr>
                </thead>
                <tbody>
                  {amount.line_items.map((li, i) => (
                    <tr key={i} className="border-b border-neutral-100">
                      <td className="py-1.5 text-neutral-800">{li.item}</td>
                      <td className="py-1.5 text-right font-medium text-neutral-900">{fmtMoney(li.estimate, ccy)}</td>
                      <td className="hidden py-1.5 text-neutral-500 sm:table-cell">{li.source || " "}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            {amount.fair_low != null && amount.fair_high != null && amount.fair_low !== amount.fair_high && (
              <p className="mt-2.5 text-[12.5px] text-neutral-600">
                Reasonable settlement range: {fmtMoney(amount.fair_low, ccy)} – {fmtMoney(amount.fair_high, ccy)}.
              </p>
            )}
            {amount.rationale && <p className="mt-1.5 text-[12.5px] text-neutral-600">{amount.rationale}</p>}
          </Section>
        )}

        {/* 6 Coverage position */}
        {coverage && (
          <Section n="6" title="Coverage position" hint={coverage.decision}>
            <p>
              The policy coverage position is recorded as{" "}
              <strong className="text-neutral-900">{coverage.decision}</strong>.
              {coverage.decision === "needs_review" && " The policy match was not conclusive; a person should confirm that the loss is covered before settlement."}
            </p>
            {(coverage.citations || []).length > 0 && (
              <ul className="mt-2 list-disc space-y-1 pl-5 text-[12.5px] text-neutral-600">
                {coverage.citations.map((c, i) => <li key={i}>{citation(c)}</li>)}
              </ul>
            )}
          </Section>
        )}

        {/* 7 Documentation status */}
        {(present.length > 0 || missing.length > 0) && (
          <Section n="7" title="Documentation status" hint={`${missing.length} outstanding`}>
            {present.length > 0 && (
              <p><span className="font-semibold text-neutral-700">On file: </span>{present.map(String).join(", ")}.</p>
            )}
            {missing.length > 0 && (
              <p className="mt-1.5"><span className="font-semibold text-neutral-700">Outstanding: </span>{missing.map(String).join(", ")}.</p>
            )}
          </Section>
        )}

        {/* 8 Recommendation */}
        <Section n="8" title="Recommendation" hint="next steps" defaultOpen>
          <p>
            It is recommended that the insurer {ACTION_LABEL[action] || "have this claim reviewed by a person"}.
            The automated engine ranks and explains only; it does not approve or reject claims. Suggested next steps:
          </p>
          <ol className="mt-2 list-decimal space-y-1 pl-5">
            {(ACTION_STEPS[action] || ACTION_STEPS.route_to_investigator).map((s, i) => <li key={i}>{s}</li>)}
          </ol>
        </Section>

        <footer className="mt-8 border-t border-neutral-300 pt-4 text-[11px] text-neutral-400">
          End of report · {ref} · Generated {today} · InsurClaim AI · Synthetic demonstration data.
        </footer>
      </article>
    </div>
  );

  return createPortal(
    <div className="fixed inset-0 z-[120] overflow-y-auto" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      {doc}
    </div>,
    document.body
  );
}

// A collapsible, numbered report section styled as a heading button.
function Section({ n, title, hint, defaultOpen = false, children }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section className="doc-section border-b border-neutral-200 py-4 last:border-0">
      <button onClick={() => setOpen((o) => !o)}
              className="flex w-full items-center gap-3 text-left">
        <span className="font-mono text-[12px] font-bold text-neutral-400">{String(n).padStart(2, "0")}</span>
        <h2 className="text-[15px] font-bold tracking-tight text-neutral-900">{title}</h2>
        {hint && <span className="no-print truncate text-[11px] italic text-neutral-400"> {hint}</span>}
        <ChevronDown className={`no-print ml-auto h-4 w-4 shrink-0 text-neutral-400 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      <div className={`doc-body mt-2.5 pl-8 text-neutral-800 ${open ? "" : "hidden"}`}>
        {children}
      </div>
    </section>
  );
}

function citation(c) {
  if (typeof c === "string") return c;
  if (c && typeof c === "object") {
    const name = c.doc_name || c.doc || c.source || "policy";
    const company = c.company ? ` · ${c.company}` : "";
    const sim = typeof c.similarity === "number" ? ` (match ${(c.similarity * 100).toFixed(0)}%)` : "";
    return `${name}${company}${sim}`;
  }
  return String(c);
}

function hash(str) {
  let h = 0;
  const s = String(str || "");
  for (let i = 0; i < s.length; i++) h = (h << 5) - h + s.charCodeAt(i) | 0;
  return h;
}
