import { useState } from "react";
import { Globe, ChevronDown } from "lucide-react";
import { fmtMoney } from "../lib/report.js";
import { Card } from "./ui.jsx";

const VERDICT_TONE = {
  overstated: { text: "Demand looks overstated", hex: "#DC2626" },
  understated: { text: "Demand looks understated", hex: "#D97706" },
  fair: { text: "Demand looks fair", hex: "#16A34A" },
  reasonable: { text: "Demand looks fair", hex: "#16A34A" },
};

// Fair-cost estimate: verdict, claimed vs fair, per-item price + source, sources.
// `bare` drops the outer card and the internal title row so it can live inside a
// collapsible section that already provides its own header.
export default function AmountBlock({ amount, bare = false }) {
  const [showSources, setShowSources] = useState(false);
  if (!amount) return null;

  const ccy = amount.currency || "PKR";
  const verdict = VERDICT_TONE[amount.verdict] || { text: amount.verdict || "Assessed", hex: "#64748B" };
  const items = amount.line_items || [];

  const body = (
    <>
      {!bare && (
        <>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="font-semibold">Fair-cost estimate</div>
            <span className="pill" style={{ color: verdict.hex, background: `${verdict.hex}16`, border: `1px solid ${verdict.hex}33` }}>
              {verdict.text}
            </span>
          </div>
          <p className="mt-1 text-xs text-muted">
            A fair-cost <strong>estimate</strong> to guide a human adjuster — not a final settlement.
          </p>
        </>
      )}

      <div className={`grid grid-cols-2 gap-3 sm:grid-cols-3 ${bare ? "" : "mt-4"}`}>
        <Stat label="Claimed" value={fmtMoney(amount.claimed_amount, ccy)} />
        <Stat label="Fair estimate" value={fmtMoney(amount.fair_estimate, ccy)} accent />
        {amount.fair_low != null && amount.fair_high != null && amount.fair_low !== amount.fair_high && (
          <Stat label="Fair range" value={`${fmtMoney(amount.fair_low, ccy)} – ${fmtMoney(amount.fair_high, ccy)}`} />
        )}
      </div>

      {items.length > 0 && (
        <ul className="mt-4 space-y-1.5">
          {items.map((li, i) => (
            <li key={i} className="flex flex-wrap items-baseline gap-x-2 text-sm">
              <span className="text-ink">{li.item}</span>
              <span className="tnum font-mono font-medium text-primary">{fmtMoney(li.estimate, ccy)}</span>
              {li.source && <span className="text-xs italic text-muted">· {li.source}</span>}
            </li>
          ))}
        </ul>
      )}

      {amount.rationale && <p className="mt-3 text-sm text-muted">{amount.rationale}</p>}

      {amount.sources_text && (
        <div className="mt-4">
          <button onClick={() => setShowSources((v) => !v)}
                  className="flex items-center gap-2 text-xs font-medium text-primary hover:underline">
            <Globe className="h-3.5 w-3.5" /> Sources (live web search)
            <ChevronDown className={`h-3.5 w-3.5 transition ${showSources ? "rotate-180" : ""}`} />
          </button>
          {showSources && (
            <pre className="mt-2 whitespace-pre-wrap rounded-lg border border-line bg-bg p-3 text-xs text-muted">
              {amount.sources_text}
            </pre>
          )}
        </div>
      )}
    </>
  );

  return bare ? <div>{body}</div> : <Card>{body}</Card>;
}

function Stat({ label, value, accent = false }) {
  return (
    <div className="rounded-lg border border-line bg-bg px-3 py-2">
      <div className="text-[11px] uppercase tracking-wide text-muted">{label}</div>
      <div className={`tnum mt-0.5 font-mono text-sm ${accent ? "text-primary" : "text-ink"}`}>{value}</div>
    </div>
  );
}
