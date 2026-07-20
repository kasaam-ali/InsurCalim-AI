import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  AlertTriangle, Download, Gauge, ScanSearch, GitCompare,
  Gavel, ClipboardList, ShieldCheck, ArrowLeft, CheckCircle2, Coins, Sparkles,
} from "lucide-react";
import { fetchClaims, fetchClaimDetail, fetchCase, setCase, addCaseNote, pdfUrl } from "../api.js";
import { SectionHeader, Loading, ErrorNote, RiskPill } from "../components/ui.jsx";
import { TONE_HEX, riskMeta } from "../lib/report.js";
import RiskGauge from "../components/RiskGauge.jsx";
import AmountBlock from "../components/AmountBlock.jsx";
import DeepReport from "../components/DeepReport.jsx";
import ClaimChat from "../components/ClaimChat.jsx";
import Disclosure from "../components/Disclosure.jsx";

const ACTION_LABEL = {
  route_to_investigator: "Send to an investigator",
  request_more_info: "Ask for more information",
  fast_track_approve: "Fast-track for approval",
};

const ACTION_WHY = {
  route_to_investigator:
    "Enough warning signs came up that this claim should not be paid on trust. An investigator should look at the evidence and speak to the people involved before any money is paid out.",
  request_more_info:
    "The picture is mixed — some things look fine, some don't. The safest next step is to ask the claimant for a few more documents so the doubts can be cleared up before deciding.",
  fast_track_approve:
    "Almost nothing looked wrong with this claim. It can move quickly towards approval — a person still gives the final yes, the system never approves on its own.",
};

const BAND_WHY = {
  HIGH: "This is treated as high concern. It should be looked at by a person before anything is paid.",
  MEDIUM: "This sits in the middle — not clearly fine, not clearly wrong. It needs a second look.",
  LOW: "Very little looked wrong here. It is low concern, but a person still confirms it.",
};

// Every check the system can raise, written for a NON-technical reader:
// what it found, and why that is a concern — in everyday words.
const SIGNAL_INFO = {
  policy_inactive: { label: "Accident date not covered",
    meaning: "The accident happened on a date the policy did not actually cover.",
    why: "If the policy wasn't active that day, the claim may not be payable at all." },
  amount_over_limit: { label: "Asking for more than the policy allows",
    meaning: "The amount being claimed is higher than the maximum this policy pays.",
    why: "Demands above the agreed limit often mean the loss is being exaggerated." },
  late_report: { label: "Reported very late",
    meaning: "The claim was reported a long time after the accident happened.",
    why: "Long, unexplained delays give time to add or worsen the damage before reporting." },
  repeat_claimant: { label: "Same person on other claims",
    meaning: "The same person also appears on several other claims in the system.",
    why: "The same people turning up again and again is a classic sign of organised fraud." },
  repeat_vin: { label: "Same vehicle on other claims",
    meaning: "This exact vehicle has been claimed on several other claims too.",
    why: "One car being claimed over and over usually means old damage is being re-used." },
  physics_mismatch: { label: "The account doesn't add up",
    meaning: "The speed, distance and timing described in the account don't fit together.",
    why: "When the story is physically impossible, it usually means it was made up." },
  duplicate_photo: { label: "A photo copied from another claim",
    meaning: "One of the damage photos here is the same photo already used on a different claim.",
    why: "Re-using the same damage photo is direct, hard proof that something is wrong." },
  similar_to_known_fraud: { label: "Looks like a known fraud",
    meaning: "This claim's story closely matches a past claim that was confirmed as fraud.",
    why: "When a new claim is nearly identical to a proven fraud, the chance it's fraud jumps." },
  narrative_red_flag: { label: "Something in the paperwork doesn't fit",
    meaning: "While reading the claim documents, the system spotted a detail that contradicts the rest.",
    why: "The concern comes straight from the claimant's own documents, not from guesswork." },
  ml_fraud_probability: { label: "The system's own fraud estimate",
    meaning: "On its own, the fraud-detection model — trained on thousands of past claims — rated this claim as risky.",
    why: "It's a data-driven second opinion that has learned what fraud tends to look like." },
};

function signalInfo(code) {
  return SIGNAL_INFO[code] || { label: code, meaning: "A factor that added to the concern.", why: "" };
}

function strength(points) {
  if (points >= 40) return "Strong factor";
  if (points >= 25) return "Moderate factor";
  return "Minor factor";
}

const SEV_WORD = { high: "Serious", medium: "Notable", low: "Minor" };
const SEV_TONE = { high: "bad", medium: "warn", low: "good" };

export default function ReportSection({ initialClaimId, moved, onClearMoved }) {
  const [claims, setClaims] = useState([]);
  const [selected, setSelected] = useState(initialClaimId || null);
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState("");

  // A claim just handed over from the submit flow — show its live deep report
  // (with case handling) instead of the stored-claim browser.
  if (moved) return <MovedInvestigation moved={moved} onBrowse={onClearMoved} />;

  return <StoredClaimReport
    initialClaimId={initialClaimId} claims={claims} setClaims={setClaims}
    selected={selected} setSelected={setSelected} detail={detail} setDetail={setDetail}
    error={error} setError={setError} />;
}

function StoredClaimReport({
  initialClaimId, claims, setClaims, selected, setSelected, detail, setDetail, error, setError,
}) {
  useEffect(() => {
    fetchClaims()
      .then((cs) => {
        setClaims(cs);
        setSelected((prev) => prev || (cs[0] && cs[0].id));
      })
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (initialClaimId) setSelected(initialClaimId);
  }, [initialClaimId]);

  useEffect(() => {
    if (selected == null) return;
    setDetail(null);
    fetchClaimDetail(selected).then(setDetail).catch((e) => setError(e.message));
  }, [selected]);

  return (
    <div>
      <SectionHeader
        eyebrow="Investigate"
        title="Investigation report"
        subtitle="A plain-English report on any claim — what was found, why, and what to do next."
        actions={
          <select className="field w-auto" value={selected ?? ""} onChange={(e) => setSelected(Number(e.target.value))}>
            {claims.map((c) => (
              <option key={c.id} value={c.id}>#{c.id} · {c.fraud_type}</option>
            ))}
          </select>
        }
      />

      {error && <ErrorNote>{error}</ErrorNote>}
      {selected != null && !detail && !error && <Loading label="Preparing the report…" />}
      {detail && <Report detail={detail} />}
    </div>
  );
}

function Report({ detail }) {
  const meta = riskMeta(detail.risk);
  const color = TONE_HEX[meta.tone];
  const total = Math.max(1, detail.reason_codes.reduce((a, r) => a + r.points, 0));
  const drivers = [...detail.reason_codes].sort((a, b) => b.points - a.points);
  const topTwo = drivers.slice(0, 2).map((d) => signalInfo(d.code).label.toLowerCase());

  const assessment =
    `This claim has been rated ${meta.label} concern (${Math.round(detail.risk)} out of 100). ` +
    (topTwo.length ? `The two biggest reasons are “${topTwo.join("” and “")}”. ` : "") +
    (detail.prob != null ? `The system's fraud-detection model also rated it ${Math.round(detail.prob * 100)}% likely to be fraud. ` : "") +
    `Recommended next step: ${(ACTION_LABEL[detail.recommended_action] || "human review").toLowerCase()}. ` +
    `This report only flags and explains — a person always makes the final decision.`;

  // Claim-specific context the AI assistant answers against.
  const chatContext = [
    `Claim #${detail.id}. Risk score: ${Math.round(detail.risk)}/100 (${meta.label} concern).`,
    `Recommended next step: ${ACTION_LABEL[detail.recommended_action] || "human review"}.`,
    detail.prob != null ? `Model fraud likelihood: ${Math.round(detail.prob * 100)}%.` : "",
    drivers.length ? `Main factors: ${drivers.map((r) => signalInfo(r.code).label).join("; ")}.` : "",
    detail.amount != null ? `Amount claimed: PKR ${Number(detail.amount).toLocaleString()}.` : "",
    detail.description ? `Claim description: ${detail.description}` : "",
  ].filter(Boolean).join("\n");

  return (
    <div className="space-y-4">
      {/* Report header — case summary, always visible */}
      <div className="rounded-xl border border-line bg-surface">
        <div className="flex items-center justify-between border-b border-line px-5 py-2.5">
          <span className="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted">
            Investigation report · Claim #{detail.id}
          </span>
          <span className="text-[11px] uppercase tracking-wide text-muted">For human review</span>
        </div>
        <div className="grid gap-6 p-5 md:grid-cols-[220px_1fr]">
          <div className="flex flex-col items-center justify-center gap-2 md:border-r md:border-line md:pr-6">
            <RiskGauge score={detail.risk} />
            <RiskPill score={detail.risk} />
          </div>
          <div className="min-w-0">
            <div className="text-sm font-semibold text-ink">Case summary</div>
            <p className="mt-1.5 text-sm leading-relaxed text-ink-soft">{assessment}</p>
            <div className="mt-4 flex flex-wrap items-center gap-x-8 gap-y-3 border-t border-line pt-4">
              <Fact k="Overall concern" v={`${meta.label} (${Math.round(detail.risk)}/100)`} />
              <Fact k="Fraud likelihood" v={detail.prob != null ? `${Math.round(detail.prob * 100)}%` : "n/a"} />
              <Fact k="Recommended step" v={ACTION_LABEL[detail.recommended_action] || "Human review"} />
              <Fact k="Actual outcome (demo)" v={detail.is_fraud ? "Fraud" : "Genuine"} />
            </div>
            <button onClick={() => exportSummary(detail)} className="btn-ghost mt-4">
              <Download className="h-4 w-4" /> Export summary
            </button>
          </div>
        </div>
      </div>

      {/* Go-deeper sections — professional report pattern */}
      <SectionLabel n="1" text="Risk assessment" />
      <Disclosure title="Why this claim was rated the way it was" subtitle="What pushed the concern up, and by how much"
                  icon={Gauge} defaultOpen>
        <p className="mb-4 text-sm leading-relaxed text-ink-soft">
          Every claim is put through dozens of automatic checks and compared against thousands of past claims.
          Each concern below added to the overall rating. The bar shows how big a part each one played —
          the same claim always produces the same result.
        </p>
        <div className="space-y-4">
          {drivers.map((r, i) => {
            const info = signalInfo(r.code);
            const pct = Math.round((r.points / total) * 100);
            return (
              <div key={i}>
                <div className="mb-1 flex items-baseline justify-between gap-3">
                  <span className="text-sm font-semibold text-ink">{info.label}</span>
                  <span className="shrink-0 text-xs text-muted">{strength(r.points)} · {pct}% of the concern</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-line">
                  <motion.div className="h-full rounded-full" style={{ background: color }}
                              initial={{ width: 0 }} animate={{ width: `${pct}%` }}
                              transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }} />
                </div>
                {info.meaning && <p className="mt-1.5 text-xs leading-relaxed text-muted">{info.meaning}</p>}
              </div>
            );
          })}
        </div>
        <p className="mt-4 border-t border-line pt-3 text-xs text-muted">{BAND_WHY[meta.label]}</p>
      </Disclosure>

      <SectionLabel n="2" text="Findings" />
      <Disclosure title="What was found, in detail" subtitle="Each concern explained, with the proof behind it"
                  icon={ScanSearch} badge={<CountBadge n={detail.flags.length} tone={color} />}>
        {detail.flags.length === 0 ? (
          <p className="text-sm text-muted">Nothing was flagged on this claim by the automatic checks.</p>
        ) : (
          <div className="space-y-3">
            {detail.flags.map((f, i) => {
              const info = signalInfo(f.code);
              const hex = TONE_HEX[SEV_TONE[f.severity] || "warn"];
              return (
                <div key={i} className="rounded-lg border border-line p-4">
                  <div className="flex items-start gap-2.5">
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" style={{ color: hex }} />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-ink">{info.label}</span>
                        <span className="pill" style={{ color: hex, background: `${hex}16`, border: `1px solid ${hex}33` }}>
                          {SEV_WORD[f.severity] || "Notable"}
                        </span>
                      </div>
                      <p className="mt-1.5 text-sm leading-relaxed text-ink-soft">{info.meaning}</p>
                      {info.why && (
                        <p className="mt-2 text-sm leading-relaxed text-ink-soft">
                          <span className="font-semibold">Why this matters: </span>{info.why}
                        </p>
                      )}
                      {f.evidence && (
                        <p className="mt-2 border-t border-line pt-2 text-[11px] text-muted">
                          <span className="uppercase tracking-wide">Reference</span> · {f.evidence}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Disclosure>

      <SectionLabel n="3" text="Comparable claims" />
      <Disclosure title="Past claims that look like this one" subtitle="Where we've seen a similar story before"
                  icon={GitCompare} badge={<CountBadge n={detail.similar_claims.length} tone={color} />}>
        {detail.similar_claims.length === 0 ? (
          <p className="text-sm text-muted">No earlier claims closely resembled this one.</p>
        ) : (
          <>
            <p className="mb-3 text-sm leading-relaxed text-ink-soft">
              These older claims tell a very similar story to this one. A close match to a claim that was already
              proven to be fraud is itself a warning sign — fraud rings tend to re-use the same script.
            </p>
            <div className="overflow-hidden rounded-lg border border-line">
              {detail.similar_claims.map((m, i) => (
                <div key={i} className={`flex items-center gap-3 px-4 py-2.5 text-sm ${i ? "border-t border-line" : ""}`}>
                  <span className="tnum font-mono font-medium text-ink">#{m.claim_id}</span>
                  <span className="text-ink-soft">{m.fraud_type || "—"}</span>
                  {m.is_fraud && (
                    <span className="pill" style={{ color: "#DC2626", background: "#DC262614", border: "1px solid #DC262633" }}>
                      confirmed fraud
                    </span>
                  )}
                  <span className="tnum ml-auto text-muted">{Math.round(m.similarity * 100)}% alike</span>
                </div>
              ))}
            </div>
          </>
        )}
      </Disclosure>

      <SectionLabel n="4" text="Recommendation" />
      <Disclosure title="What to do next" subtitle="The suggested step, and the reason for it"
                  icon={Gavel} defaultOpen
                  badge={<span className="pill" style={{ color, background: `${color}16`, border: `1px solid ${color}33` }}>{ACTION_LABEL[detail.recommended_action] || "Review"}</span>}>
        <div className="flex items-start gap-2.5 rounded-lg border border-line p-4">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
          <p className="text-sm leading-relaxed text-ink-soft">
            {ACTION_WHY[detail.recommended_action] ||
              "A person should review this claim. The system only ranks and explains — it never approves or rejects a claim by itself."}
          </p>
        </div>
      </Disclosure>

      <SectionLabel n="5" text="Claim record" />
      <Disclosure title="The claim on file" subtitle="The basic facts this report is based on" icon={ClipboardList}>
        <dl className="grid gap-x-8 gap-y-2 text-sm sm:grid-cols-2">
          <Row k="Claim number" v={`#${detail.id}`} />
          <Row k="Location" v={detail.location || "—"} />
          <Row k="Amount claimed" v={detail.amount != null ? `PKR ${Number(detail.amount).toLocaleString()}` : "—"} />
          <Row k="Type on record" v={detail.fraud_type || "—"} />
        </dl>
        {detail.description && (
          <p className="mt-3 border-t border-line pt-3 text-sm leading-relaxed text-ink-soft">{detail.description}</p>
        )}
      </Disclosure>

      <SectionLabel n="6" text="Case handling" />
      <CaseManagement claimRef={`claim-${detail.id}`} />

      <SectionLabel n="7" text="AI assistant" />
      <ClaimChat context={chatContext} />
    </div>
  );
}

// A claim handed over from the submit flow. Renders the same professional,
// numbered deep-report layout — driven by the live investigation result — plus
// case handling. The case is opened as "investigating" automatically.
function MovedInvestigation({ moved, onBrowse }) {
  const { result, jobId } = moved;
  const report = result?.final?.report || {};
  const amount = result?.amount || null;
  const coverage = result?.coverage || null;
  const documents = result?.documents || null;
  const flags = (report.top_flags || []).filter((f) => f?.summary);
  const meta = riskMeta(report.risk_score || 0);
  const color = TONE_HEX[meta.tone];
  const claimRef = `job-${jobId}`;

  // Claim-specific context the AI assistant answers against.
  const chatContext = [
    `Risk score: ${Math.round(report.risk_score || 0)}/100 (${meta.label} concern).`,
    `Recommended next step: ${ACTION_LABEL[report.recommended_action] || "human review"}.`,
    flags.length ? `Key findings: ${flags.map((f) => f.summary).join("; ")}.` : "",
    report.timeline_summary ? `Summary: ${report.timeline_summary}` : "",
    amount ? `Amount — claimed: ${amount.claimed_amount ?? "n/a"}, fair estimate: ${amount.fair_estimate ?? "n/a"}, verdict: ${amount.verdict ?? "n/a"}.` : "",
    coverage ? `Policy coverage decision: ${coverage.decision}.` : "",
  ].filter(Boolean).join("\n");

  const assessment =
    `This claim was just moved to the investigator desk from a live submission. ` +
    `It has been rated ${meta.label} concern (${Math.round(report.risk_score || 0)} out of 100). ` +
    (flags.length ? `The biggest concern is “${flags[0].summary}”. ` : "") +
    `Recommended next step: ${(ACTION_LABEL[report.recommended_action] || "human review").toLowerCase()}. ` +
    `This report only flags and explains — a person always makes the final decision.`;

  return (
    <div>
      <SectionHeader
        eyebrow="Investigate"
        title="Investigation report"
        subtitle="A claim moved here from the submit flow — full analysis and case handling."
        actions={
          <button className="btn-ghost" onClick={onBrowse}>
            <ArrowLeft className="h-4 w-4" /> Browse stored claims
          </button>
        }
      />

      <div className="space-y-4">
        {/* Moved-in confirmation */}
        <div className="flex items-start gap-2.5 rounded-xl border border-good/30 bg-good-soft px-4 py-3 text-sm text-good">
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
          <span>Moved to the investigator desk. A case has been opened with status <strong>investigating</strong> — set the assignee and add notes below.</span>
        </div>

        {/* Report header — case summary */}
        <div className="rounded-xl border border-line bg-surface">
          <div className="flex items-center justify-between border-b border-line px-5 py-2.5">
            <span className="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted">
              Investigation report · Moved claim
            </span>
            <span className="text-[11px] uppercase tracking-wide text-muted">For human review</span>
          </div>
          <div className="grid gap-6 p-5 md:grid-cols-[220px_1fr]">
            <div className="flex flex-col items-center justify-center gap-2 md:border-r md:border-line md:pr-6">
              <RiskGauge score={report.risk_score} />
              <RiskPill score={report.risk_score} />
            </div>
            <div className="min-w-0">
              <div className="text-sm font-semibold text-ink">Case summary</div>
              <p className="mt-1.5 text-sm leading-relaxed text-ink-soft">{assessment}</p>
              <div className="mt-4 flex flex-wrap items-center gap-x-8 gap-y-3 border-t border-line pt-4">
                <Fact k="Overall concern" v={`${meta.label} (${Math.round(report.risk_score || 0)}/100)`} />
                <Fact k="Recommended step" v={ACTION_LABEL[report.recommended_action] || "Human review"} />
                {amount?.claimed_amount != null && (
                  <Fact k="Amount claimed" v={`PKR ${Number(amount.claimed_amount).toLocaleString()}`} />
                )}
                {amount?.fair_estimate != null && (
                  <Fact k="Fair estimate" v={`PKR ${Number(amount.fair_estimate).toLocaleString()}`} />
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Full, detailed investigator report (same as the submit-flow Dive Deeper) */}
        <div className="rounded-xl border border-line bg-surface p-5">
          <DeepReport result={result} jobId={jobId} />
        </div>

        {/* Case handling — opened as "investigating" automatically */}
        <div className="flex items-center gap-2.5 pt-2">
          <ClipboardList className="h-4 w-4 text-muted" />
          <span className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Case handling</span>
          <span className="h-px flex-1 bg-line" />
        </div>
        <CaseManagement claimRef={claimRef} autoStatus="investigating" />

        {/* AI assistant — ask anything about this claim */}
        <div className="flex items-center gap-2.5 pt-2">
          <Sparkles className="h-4 w-4 text-muted" />
          <span className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">AI assistant</span>
          <span className="h-px flex-1 bg-line" />
        </div>
        <ClaimChat context={chatContext} />
      </div>
    </div>
  );
}

// Render a coverage citation (string or {doc_name, company, similarity}).
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

// Small numbered report-section label above each disclosure.
function SectionLabel({ n, text }) {
  return (
    <div className="flex items-center gap-2.5 pt-2">
      <span className="grid h-5 w-5 place-items-center rounded-full bg-primary-soft text-[11px] font-bold text-primary">{n}</span>
      <span className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">{text}</span>
      <span className="h-px flex-1 bg-line" />
    </div>
  );
}

function Fact({ k, v }) {
  return (
    <div>
      <div className="text-[11px] font-medium uppercase tracking-wide text-muted">{k}</div>
      <div className="mt-0.5 text-sm font-semibold text-ink">{v}</div>
    </div>
  );
}

function Row({ k, v }) {
  return (
    <div className="flex justify-between gap-4 border-b border-line py-1.5">
      <dt className="text-muted">{k}</dt>
      <dd className="font-medium text-ink">{v}</dd>
    </div>
  );
}

function CountBadge({ n, tone }) {
  return (
    <span className="tnum grid h-6 min-w-[24px] place-items-center rounded-full px-1.5 text-xs font-semibold"
          style={{ color: tone, background: `${tone}16`, border: `1px solid ${tone}33` }}>
      {n}
    </span>
  );
}

function exportSummary(detail) {
  const lines = [
    "InsurCalim AI - investigation report",
    `Claim #${detail.id}  |  concern: ${Math.round(detail.risk)}/100 (${riskMeta(detail.risk).label})  |  next step: ${ACTION_LABEL[detail.recommended_action] || "review"}`,
    `System fraud likelihood: ${detail.prob != null ? Math.round(detail.prob * 100) + "%" : "n/a"}`,
    "",
    "Why it was rated this way:",
    ...detail.reason_codes.map((r) => `  - ${signalInfo(r.code).label} (${strength(r.points)})`),
    "",
    "What was found:",
    ...detail.flags.map((f) => `  - [${SEV_WORD[f.severity] || "Notable"}] ${signalInfo(f.code).label}: ${signalInfo(f.code).meaning}`),
    "",
    `Claim on file: ${detail.description}`,
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `claim_${detail.id}_report.txt`;
  a.click();
  URL.revokeObjectURL(a.href);
}

const STATUSES = ["open", "investigating", "cleared", "confirmed_fraud"];

function CaseManagement({ claimRef, autoStatus }) {
  const [status, setStatus] = useState("open");
  const [assignee, setAssignee] = useState("");
  const [notes, setNotes] = useState([]);
  const [note, setNote] = useState("");
  const [saved, setSaved] = useState(false);

  function load() {
    fetchCase(claimRef).then((c) => {
      const existing = c.status?.status || "open";
      // When a claim is moved in from the submit flow, open the case
      // automatically (only if it hasn't been set to something else already).
      if (autoStatus && existing === "open") {
        setStatus(autoStatus);
        setCase(claimRef, autoStatus, c.status?.assignee || "").catch(() => {});
      } else {
        setStatus(existing);
      }
      setAssignee(c.status?.assignee || "");
      setNotes(c.notes || []);
    }).catch(() => {
      if (autoStatus) {
        setStatus(autoStatus);
        setCase(claimRef, autoStatus, "").catch(() => {});
      }
    });
  }
  useEffect(load, [claimRef]);

  async function save() {
    await setCase(claimRef, status, assignee);
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  }
  async function submitNote() {
    if (!note.trim()) return;
    const updated = await addCaseNote(claimRef, note.trim());
    setNotes(updated);
    setNote("");
  }

  return (
    <Disclosure title="Track this case" subtitle="Set the status, assign it, and add notes" icon={ClipboardList} defaultOpen>
      <div className="grid gap-3 sm:grid-cols-[180px_1fr_auto] sm:items-end">
        <label className="text-sm">
          <span className="mb-1 block text-muted">Status</span>
          <select className="field" value={status} onChange={(e) => setStatus(e.target.value)}>
            {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-muted">Assignee</span>
          <input className="field" value={assignee} onChange={(e) => setAssignee(e.target.value)} placeholder="name" />
        </label>
        <button className="btn-primary" onClick={save}>{saved ? "Saved ✓" : "Save case"}</button>
      </div>

      <div className="mt-4">
        <div className="mb-2 flex gap-2">
          <input className="field" value={note} onChange={(e) => setNote(e.target.value)}
                 placeholder="Add an investigation note…" onKeyDown={(e) => e.key === "Enter" && submitNote()} />
          <button className="btn-ghost" onClick={submitNote}>Add note</button>
        </div>
        {notes.length > 0 && (
          <ul className="space-y-1.5 text-sm">
            {notes.map((n, i) => (
              <li key={i} className="rounded-lg border border-line bg-bg px-3 py-2">
                {n.note}
                <span className="ml-2 text-xs text-muted">{String(n.created_at).slice(0, 16)}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Disclosure>
  );
}
