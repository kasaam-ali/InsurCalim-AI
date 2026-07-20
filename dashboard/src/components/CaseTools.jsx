import { useMemo, useState } from "react";
import { CheckSquare, Square, User, ArrowRight } from "lucide-react";
import { fmtMoney } from "../lib/report.js";

// Investigator-desk tools that live only in the Investigation report (not in the
// quick submit view): a verification checklist derived from the case, and a
// register of the people involved.

export function InvestigatorChecklist({ result }) {
  const report = result?.final?.report || {};
  const amount = result?.amount || null;
  const coverage = result?.coverage || null;
  const documents = result?.documents || null;
  const flags = (report.top_flags || []).filter((f) => f?.summary);
  const ccy = amount?.currency || "PKR";

  const tasks = useMemo(() => {
    const t = [];
    flags.forEach((f) => t.push({ group: "Findings", label: `Verify: ${f.summary}` }));
    (documents?.missing || []).forEach((d) => t.push({ group: "Documents", label: `Obtain the ${String(d).toLowerCase()}` }));
    if (amount?.verdict === "overstated" && amount.fair_estimate != null) {
      t.push({ group: "Cost", label: `Reconcile the claimed amount against the fair estimate (${fmtMoney(amount.fair_estimate, ccy)})` });
    }
    if (coverage?.decision === "needs_review") {
      t.push({ group: "Coverage", label: "Confirm the policy was active and covers this loss" });
    }
    t.push({ group: "General", label: "Contact the claimant and any third parties to corroborate the account" });
    return t;
  }, [flags, documents, amount, coverage, ccy]);

  const [done, setDone] = useState(() => new Set());
  const pct = tasks.length ? Math.round((done.size / tasks.length) * 100) : 0;
  const toggle = (i) =>
    setDone((s) => {
      const n = new Set(s);
      n.has(i) ? n.delete(i) : n.add(i);
      return n;
    });

  return (
    <div className="overflow-hidden rounded-xl border border-line bg-surface">
      <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
        <div>
          <div className="text-[13px] font-semibold text-ink">Verification checklist</div>
          <div className="text-xs text-muted">Work items generated from this case</div>
        </div>
        <div className="text-right">
          <div className="tnum text-sm font-semibold text-ink">{done.size}/{tasks.length}</div>
          <div className="text-[11px] text-muted">{pct}% complete</div>
        </div>
      </div>
      <div className="h-1 bg-surface-2">
        <div className="h-full bg-primary transition-all" style={{ width: `${pct}%` }} />
      </div>
      <ul className="divide-y divide-line">
        {tasks.map((t, i) => {
          const checked = done.has(i);
          return (
            <li key={i}>
              <button onClick={() => toggle(i)}
                      className="flex w-full items-start gap-3 px-4 py-2.5 text-left transition-colors hover:bg-surface-2">
                {checked
                  ? <CheckSquare className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                  : <Square className="mt-0.5 h-4 w-4 shrink-0 text-muted" />}
                <span className={`flex-1 text-[13px] ${checked ? "text-muted line-through" : "text-ink-soft"}`}>
                  {t.label}
                </span>
                <span className="mt-0.5 shrink-0 text-[10px] font-semibold uppercase tracking-wide text-muted">{t.group}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export function PartiesRegister({ result }) {
  const ov = result?.overview || {};
  let parties = (ov.parties || []).filter((p) => p.full_name && p.full_name !== "-");
  // Fall back to the named claimant when the structured party list is empty.
  if (parties.length === 0 && ov.claimant && ov.claimant !== "-") {
    parties = [{ full_name: ov.claimant, role: "claimant" }];
  }
  if (parties.length === 0) return null;
  return (
    <div className="overflow-hidden rounded-xl border border-line bg-surface">
      <ul className="divide-y divide-line">
        {parties.map((p, i) => (
          <li key={i} className="flex items-center gap-3 px-4 py-3">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-primary/12 text-primary">
              <User className="h-4 w-4" />
            </span>
            <div className="min-w-0 flex-1">
              <div className="truncate text-[13px] font-semibold text-ink">{p.full_name}</div>
              <div className="text-xs capitalize text-muted">{p.role}</div>
            </div>
            <button className="btn-subtle h-8" disabled title="Demo — contact action">
              Contact <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
