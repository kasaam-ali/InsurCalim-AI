import { useState } from "react";
import {
  AlertTriangle, CheckCircle2, Info, Camera, RotateCcw, ArrowRight,
  FileSearch, FileText, Coins,
} from "lucide-react";
import { plainSummary, twoLine, riskMeta, fmtMoney } from "../lib/report.js";
import RiskGauge from "./RiskGauge.jsx";
import AmountBlock from "./AmountBlock.jsx";
import Disclosure from "./Disclosure.jsx";
import DeepReport from "./DeepReport.jsx";
import ReportDocument from "./ReportDocument.jsx";

const NOTICE_STYLE = {
  success: { Icon: CheckCircle2, hex: "#16A34A" },
  warning: { Icon: AlertTriangle, hex: "#D97706" },
  error: { Icon: AlertTriangle, hex: "#DC2626" },
};

const ACTION_LABEL = {
  route_to_investigator: "Send to an investigator",
  request_more_info: "Ask for more information",
  fast_track_approve: "Fast-track for approval",
};

// The recommended-action button ("move to ..."), with a done-state confirmation.
const ACTION_CTA = {
  route_to_investigator: { label: "Move to investigator", done: "Moved to investigator" },
  request_more_info: { label: "Request more information", done: "Request sent" },
  fast_track_approve: { label: "Fast-track for approval", done: "Fast-tracked" },
};

export default function ReportView({ result, jobId, onNewClaim, onMove }) {
  const [sent, setSent] = useState(false);
  const [preview, setPreview] = useState(false);
  const report = result?.final?.report || {};
  const amount = result?.amount || null;
  const media = result?.media || [];
  const documents = result?.documents || null;
  const coverage = result?.coverage || null;
  const notices = result?.notices || [];
  const flags = (report.top_flags || []).filter((f) => f?.summary);
  const photos = media.filter((m) => m.damage);
  const cta = ACTION_CTA[report.recommended_action] || { label: "Move to investigator", done: "Actioned" };

  return (
    <div className="mx-auto max-w-4xl space-y-5 animate-fade-up">
      <div className="flex items-center justify-between">
        <div className="eyebrow">Investigator report</div>
        <div className="flex items-center gap-2">
          <button className="btn-primary" onClick={() => setPreview(true)}>
            <FileText className="h-4 w-4" /> Preview report
          </button>
          <button className="btn-ghost" onClick={onNewClaim}><RotateCcw className="h-4 w-4" /> New claim</button>
        </div>
      </div>

      {preview && <ReportDocument result={result} onClose={() => setPreview(false)} />}

      {notices.length > 0 && (
        <div className="flex flex-col gap-1.5">
          {notices.map((n, i) => {
            const st = NOTICE_STYLE[n.level] || NOTICE_STYLE.warning;
            const Icon = st.Icon;
            return (
              <div key={i} className="flex items-start gap-2 text-sm" style={{ color: st.hex }}>
                <Icon className="mt-0.5 h-4 w-4 shrink-0" /><span>{n.message}</span>
              </div>
            );
          })}
        </div>
      )}

      {/* Headline professional report panel */}
      <div className="rounded-xl border border-line bg-surface">
        <div className="flex items-center justify-between border-b border-line px-5 py-2.5">
          <span className="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted">Investigation report</span>
          <span className="text-[11px] uppercase tracking-wide text-muted">For human review</span>
        </div>
        <div className="grid grid-cols-1 gap-6 p-5 md:grid-cols-[240px_1fr]">
          <div className="flex flex-col items-center justify-center md:border-r md:border-line md:pr-6">
            <RiskGauge score={report.risk_score} />
            <div className="mt-2 text-center text-xs text-muted">
              Recommended: <span className="text-ink">{ACTION_LABEL[report.recommended_action] || "Human review"}</span>
            </div>
          </div>
          <div className="min-w-0">
            <h3 className="font-semibold">Key findings what stands out about this claim</h3>
            {flags.length > 0 ? (
              <ul className="mt-3 space-y-2">
                {flags.map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                    <span>{f.summary}</span>
                  </li>
                ))}
              </ul>
            ) : <p className="mt-3 text-sm text-muted">No specific red flags surfaced for this claim.</p>}

            {photos.length > 0 && (
              <div className="mt-5">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <Camera className="h-4 w-4 text-primary" /> What the photos show
                </div>
                <ul className="mt-2 space-y-2">
                  {photos.map((m, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                      <span><span className="font-medium">{m.file_name}</span>
                        <span className="text-muted"> {twoLine(m.damage)}</span></span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* In plain English left-rule accent, no box */}
      <div className="flex items-start gap-3 border-l-2 border-primary pl-4">
        <Info className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-primary">In plain English</div>
          <p className="mt-1 text-sm leading-relaxed text-ink-soft">{plainSummary(report, amount)}</p>
        </div>
      </div>

      {/* Fair-cost estimate collapsible box (price on the button, detail inside) */}
      {amount && (
        <Disclosure
          title="Fair-cost estimate"
          subtitle="Is the amount being claimed fair?"
          icon={Coins}
          badge={amount.fair_estimate != null ? (
            <span className="pill" style={{ color: "rgb(var(--c-primary))", background: "rgb(var(--c-primary) / .12)", border: "1px solid rgb(var(--c-primary) / .25)" }}>
              {fmtMoney(amount.fair_estimate, amount.currency || "PKR")}
            </span>
          ) : null}
        >
          <AmountBlock amount={amount} bare />
        </Disclosure>
      )}

      {/* Dive Deeper one button that opens the full, detailed report */}
      <Disclosure title="Dive Deeper full investigator report"
                  subtitle="The complete, plain-English breakdown of this claim" icon={FileSearch}>
        <DeepReport result={result} jobId={jobId} />
      </Disclosure>

      {/* Decision bar hand this claim to the investigator desk (deep analysis + case handling) */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-line bg-surface p-4">
        <div>
          <div className="text-sm font-semibold text-ink">Ready to act on this claim?</div>
          <div className="text-xs text-muted">Opens the full Investigation report deep analysis, comparable claims, and case handling. A person always makes the final call.</div>
        </div>
        <button
          onClick={() => {
            setSent(true);
            if (onMove) onMove(result, jobId);
          }}
          className="btn-primary"
        >
          {cta.label} <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
