import {
  FileText, ClipboardCheck, AlertTriangle, Camera, Coins, ShieldCheck,
  FolderCheck, Cpu, Gavel, Download, CheckCircle2, XCircle, Users, Car,
  MapPin, CalendarDays, Banknote,
} from "lucide-react";
import { fmtMoney, riskMeta } from "../lib/report.js";
import { pdfUrl } from "../api.js";
import AmountBlock from "./AmountBlock.jsx";

// A single, comprehensive, plain-English investigator report rendered from a
// live investigation result. Every section that has data is shown in full a
// proper report document, not a summary. Used by the submit-flow "Dive Deeper"
// panel and by the "moved to investigator" view so both read identically.

const ACTION_LABEL = {
  route_to_investigator: "Send to an investigator",
  request_more_info: "Ask for more information",
  fast_track_approve: "Fast-track for approval",
};

const ACTION_WHY = {
  route_to_investigator:
    "Enough warning signs came up that this claim should not be paid on trust. An investigator should examine the evidence and speak to the people involved before any money is released.",
  request_more_info:
    "The picture is mixed some things look fine, some do not. The safest next step is to ask the claimant for a few more documents so the doubts can be cleared before a decision is made.",
  fast_track_approve:
    "Almost nothing looked wrong with this claim. It can move quickly towards approval a person still gives the final yes; the system never approves on its own.",
};

const ACTION_STEPS = {
  route_to_investigator: [
    "Open a case file and assign it to an investigator.",
    "Re-check the flagged items below against the original documents and photos.",
    "Contact the claimant and any third parties to confirm the account.",
    "Hold any payment until the investigator signs the case off.",
  ],
  request_more_info: [
    "Send the claimant the list of missing documents below.",
    "Ask for clarification on each flagged point.",
    "Re-assess once the extra evidence arrives.",
  ],
  fast_track_approve: [
    "Do a final human check of the claim details.",
    "Confirm the amount against the fair-cost estimate below.",
    "Approve and process the payment.",
  ],
};

const VERDICT_MEANING = {
  overstated: "The amount being demanded is materially higher than a fair market repair cost a common sign of an inflated claim.",
  understated: "The amount being demanded is actually lower than the fair market repair cost.",
  fair: "The amount being demanded is in line with fair market repair costs.",
  reasonable: "The amount being demanded is in line with fair market repair costs.",
  insufficient_info: "There was not enough detail to estimate a fair repair cost with confidence.",
};

function confidenceWord(c) {
  const n = Number(c);
  if (Number.isNaN(n)) return "Indicator";
  if (n >= 80) return "Strong indicator";
  if (n >= 50) return "Moderate indicator";
  return "Minor indicator";
}

function formatCitation(c) {
  if (typeof c === "string") return c;
  if (c && typeof c === "object") {
    const name = c.doc_name || c.doc || c.source || "policy";
    const company = c.company ? ` · ${c.company}` : "";
    const sim = typeof c.similarity === "number" ? ` (match ${(c.similarity * 100).toFixed(0)}%)` : "";
    return `${name}${company}${sim}`;
  }
  return String(c);
}

export default function DeepReport({ result, jobId }) {
  const report = result?.final?.report || {};
  const extracted = result?.final?.extracted || {};
  const overview = result?.overview || {};
  const amount = result?.amount || null;
  const coverage = result?.coverage || null;
  const documents = result?.documents || null;
  const media = result?.media || [];
  const flags = (report.top_flags || []).filter((f) => f?.summary);

  const ccy = amount?.currency || "PKR";
  const meta = riskMeta(report.risk_score || 0);
  const action = report.recommended_action;
  const summaryText = (report.timeline_summary || overview.summary || "").trim();

  // Claim-fact rows (only those we actually have).
  const facts = [
    { Icon: Users, k: "Claimant", v: overview.claimant },
    { Icon: Car, k: "Vehicle", v: overview.vehicle },
    { Icon: CalendarDays, k: "Incident date", v: overview.incident_date },
    { Icon: CalendarDays, k: "Reported on", v: overview.report_date },
    { Icon: MapPin, k: "Location", v: overview.location },
    {
      Icon: Banknote, k: "Amount claimed",
      v: overview.claimed_amount != null ? fmtMoney(overview.claimed_amount, ccy) : null,
    },
  ].filter((f) => f.v && f.v !== "-");

  const parties = (overview.parties || []).filter((p) => p.full_name && p.full_name !== "-");
  const present = documents?.present || [];
  const missing = documents?.missing || [];

  // Amount gap (claimed vs fair), when both are known.
  let gap = null;
  if (amount && amount.claimed_amount != null && amount.fair_estimate) {
    const diff = Number(amount.claimed_amount) - Number(amount.fair_estimate);
    const pct = Math.round((diff / Number(amount.fair_estimate)) * 100);
    gap = { diff, pct };
  }

  return (
    <div className="space-y-6">
      {/* 1 Claim data sheet */}
      <Section n="1" title="Claim on file" Icon={FileText}>
        {facts.length === 0 && parties.length === 0 ? (
          <p className="text-sm text-muted">No structured claim details were extracted.</p>
        ) : (
          <>
            {facts.length > 0 && (
              <dl className="grid gap-x-8 gap-y-3 sm:grid-cols-2">
                {facts.map((f, i) => (
                  <div key={i} className="flex items-start gap-2.5">
                    <f.Icon className="mt-0.5 h-4 w-4 shrink-0 text-muted" />
                    <div>
                      <dt className="text-[11px] font-medium uppercase tracking-wide text-muted">{f.k}</dt>
                      <dd className="text-sm font-medium text-ink">{f.v}</dd>
                    </div>
                  </div>
                ))}
              </dl>
            )}
            {parties.length > 0 && (
              <div className="mt-4 border-t border-line pt-3">
                <div className="mb-2 text-[11px] font-medium uppercase tracking-wide text-muted">People involved</div>
                <ul className="space-y-1.5">
                  {parties.map((p, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm">
                      <Users className="h-3.5 w-3.5 text-muted" />
                      <span className="font-medium text-ink">{p.full_name}</span>
                      <span className="text-muted"> {p.role}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
      </Section>

      {/* 2 What happened */}
      {summaryText && (
        <Section n="2" title="What happened" Icon={ClipboardCheck}>
          <p className="text-sm leading-relaxed text-ink-soft">{summaryText}</p>
        </Section>
      )}

      {/* 3 Why this was flagged */}
      <Section n="3" title="Why this claim was flagged" Icon={AlertTriangle}
               badge={<Count n={flags.length} />}>
        <p className="mb-4 text-sm leading-relaxed text-muted">
          Each point below added to the overall concern. The bar shows how confident the system is
          in that specific finding.
        </p>
        {flags.length === 0 ? (
          <p className="text-sm text-muted">Nothing specific was flagged on this claim.</p>
        ) : (
          <ol className="space-y-4">
            {flags.map((f, i) => {
              const conf = Number(f.confidence);
              const hasConf = f.confidence !== undefined && f.confidence !== "" && !Number.isNaN(conf);
              return (
                <li key={i} className="rounded-lg border border-line p-4">
                  <div className="flex items-start gap-2.5">
                    <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-warn-soft text-[11px] font-bold text-warn">
                      {i + 1}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-sm font-semibold text-ink">{f.summary}</span>
                        {hasConf && (
                          <span className="pill" style={{ color: "#D97706", background: "#D9770616", border: "1px solid #D9770633" }}>
                            {confidenceWord(conf)}
                          </span>
                        )}
                      </div>
                      {f.evidence && <p className="mt-1.5 text-sm leading-relaxed text-ink-soft">{f.evidence}</p>}
                      {hasConf && (
                        <div className="mt-3">
                          <div className="mb-1 flex justify-between text-[11px] uppercase tracking-wide text-muted">
                            <span>How sure</span><span className="tnum">{Math.round(conf)}%</span>
                          </div>
                          <div className="h-1.5 overflow-hidden rounded-full bg-line">
                            <div className="h-full rounded-full bg-primary"
                                 style={{ width: `${Math.min(100, Math.max(0, conf))}%` }} />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </li>
              );
            })}
          </ol>
        )}
      </Section>

      {/* 4 Damage & media analysis */}
      {media.length > 0 && (
        <Section n="4" title="Damage & media analysis" Icon={Camera} badge={<Count n={media.length} />}>
          <div className="space-y-3">
            {media.map((m, i) => (
              <div key={i} className="rounded-lg border border-line p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-ink">
                  <Camera className="h-4 w-4 text-primary" />
                  {m.file_name || `${m.kind || "media"} ${i + 1}`}
                  <span className="pill border border-line text-muted">{m.kind || "media"}</span>
                </div>
                {m.damage && <p className="mt-2 text-sm leading-relaxed text-ink-soft">{m.damage}</p>}
                <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1.5 text-xs">
                  <Check ok={!m.synthetic}
                         yes="Looks like a genuine photo (no AI-generation signs)"
                         no={m.synthetic ? `Possible AI-generated media ${m.synthetic.evidence || m.synthetic.severity || "flagged"}` : ""} />
                  <Check ok={!m.duplicate_of}
                         yes="Not seen on any other claim"
                         no={m.duplicate_of ? `Reused same image is on claim #${m.duplicate_of.claim_id}` : ""} />
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* 5 Fair-cost assessment */}
      {amount && (
        <Section n="5" title="Is the amount being claimed fair?" Icon={Coins}>
          {gap && amount.verdict === "overstated" && (
            <p className="mb-3 text-sm leading-relaxed text-ink-soft">
              The demand of <strong>{fmtMoney(amount.claimed_amount, ccy)}</strong> is about
              {" "}<strong>{fmtMoney(gap.diff, ccy)}</strong> ({gap.pct}%) above the fair estimate of
              {" "}<strong>{fmtMoney(amount.fair_estimate, ccy)}</strong>.
            </p>
          )}
          <p className="mb-4 text-sm leading-relaxed text-muted">
            {VERDICT_MEANING[amount.verdict] || "A market-based estimate to guide the adjuster."}
          </p>
          <AmountBlock amount={amount} />
        </Section>
      )}

      {/* 6 Policy coverage */}
      {coverage && (
        <Section n="6" title="Policy coverage" Icon={ShieldCheck}>
          <p className="text-sm text-ink-soft">
            Coverage decision: <span className="font-semibold">{coverage.decision}</span>.
            {coverage.decision === "needs_review" && " The policy match was not conclusive, so a person should confirm cover."}
          </p>
          {(coverage.citations || []).length > 0 && (
            <>
              <div className="mt-3 text-[11px] font-medium uppercase tracking-wide text-muted">Clauses checked</div>
              <ul className="mt-1.5 list-disc space-y-1 pl-5 text-sm text-muted">
                {coverage.citations.map((c, i) => <li key={i}>{formatCitation(c)}</li>)}
              </ul>
            </>
          )}
        </Section>
      )}

      {/* 7 Document checklist */}
      {(present.length > 0 || missing.length > 0) && (
        <Section n="7" title="Document checklist" Icon={FolderCheck}
                 badge={<span className="text-xs text-muted">{present.length} on file · {missing.length} missing</span>}>
          <div className="grid gap-x-8 gap-y-2 sm:grid-cols-2">
            {present.map((d, i) => (
              <div key={`p${i}`} className="flex items-center gap-2 text-sm text-ink-soft">
                <CheckCircle2 className="h-4 w-4 shrink-0 text-good" /> {String(d)}
              </div>
            ))}
            {missing.map((d, i) => (
              <div key={`m${i}`} className="flex items-center gap-2 text-sm text-muted">
                <XCircle className="h-4 w-4 shrink-0 text-warn" /> {String(d)}
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* 8 How this was assessed */}
      <Section n="8" title="How this assessment was made" Icon={Cpu}>
        <p className="text-sm leading-relaxed text-ink-soft">
          This claim was checked in layers. First, fixed rules and cross-checks run automatically and
          always give the same answer for the same claim: duplicate-photo detection, comparison against
          thousands of past claims, and a machine-learning model trained on real fraud data. Then an
          AI assistant reads the documents and writes up the findings you see above. The concern score
          combines all of these signals.
        </p>
        <p className="mt-3 text-sm leading-relaxed text-muted">
          The system only ranks and explains it never approves or rejects a claim on its own. A person
          always makes the final decision.
        </p>
      </Section>

      {/* 9 Recommendation & next steps */}
      <Section n="9" title="Recommendation & next steps" Icon={Gavel}
               badge={<span className="pill" style={{ color: "#2563EB", background: "#2563EB16", border: "1px solid #2563EB33" }}>{ACTION_LABEL[action] || "Human review"}</span>}>
        <p className="text-sm leading-relaxed text-ink-soft">{ACTION_WHY[action] ||
          "A person should review this claim before any decision."}</p>
        {(ACTION_STEPS[action] || []).length > 0 && (
          <ol className="mt-3 list-decimal space-y-1.5 pl-5 text-sm text-ink-soft">
            {ACTION_STEPS[action].map((s, i) => <li key={i}>{s}</li>)}
          </ol>
        )}
        {jobId && (
          <a className="btn-ghost mt-4" href={pdfUrl(jobId)} target="_blank" rel="noreferrer">
            <Download className="h-4 w-4" /> Download the full PDF report
          </a>
        )}
      </Section>
    </div>
  );
}

// A numbered report section with a heading rule and visible content.
function Section({ n, title, Icon, badge, children }) {
  return (
    <section>
      <div className="mb-3 flex items-center gap-2.5">
        <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-primary-soft text-[11px] font-bold text-primary">{n}</span>
        {Icon && <Icon className="h-4 w-4 shrink-0 text-muted" />}
        <h4 className="text-sm font-semibold text-ink">{title}</h4>
        {badge && <span className="ml-auto">{badge}</span>}
      </div>
      <div className="border-l-2 border-line pl-4">{children}</div>
    </section>
  );
}

function Count({ n }) {
  return (
    <span className="tnum grid h-6 min-w-[24px] place-items-center rounded-full bg-primary-soft px-1.5 text-xs font-semibold text-primary">
      {n}
    </span>
  );
}

function Check({ ok, yes, no }) {
  return (
    <span className="flex items-center gap-1.5">
      {ok ? <CheckCircle2 className="h-3.5 w-3.5 text-good" /> : <AlertTriangle className="h-3.5 w-3.5 text-warn" />}
      <span className={ok ? "text-muted" : "text-warn"}>{ok ? yes : no}</span>
    </span>
  );
}
