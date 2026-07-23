import { useEffect, useRef, useState } from "react";
import { Loader2, ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";
import { motion } from "framer-motion";
import Counter from "./Counter.jsx";
import Sparkline from "./Sparkline.jsx";
import { riskMeta, BAND_TONE, TONE_HEX } from "../lib/report.js";

// Shared building blocks for the "precision console" system.

/* -------------------------------------------------------------------------- */
/*  Headers & panels                                                          */
/* -------------------------------------------------------------------------- */

export function SectionHeader({ eyebrow, title, subtitle, actions }) {
  return (
    <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
      <div className="min-w-0">
        {eyebrow && <div className="eyebrow mb-1.5">{eyebrow}</div>}
        <h1 className="text-lg font-semibold tracking-tight text-ink">{title}</h1>
        {subtitle && <p className="mt-1 text-[13px] text-muted">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}

// A titled panel with an optional header row (title + subtitle + actions).
export function Panel({ title, subtitle, icon: Icon, actions, className = "", bodyClass = "p-4", children }) {
  return (
    <section className={`panel ${className}`}>
      {(title || actions) && (
        <header className="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
          <div className="flex min-w-0 items-center gap-2.5">
            {Icon && (
              <span className="grid h-7 w-7 shrink-0 place-items-center rounded-md bg-surface-2 text-muted">
                <Icon className="h-4 w-4" />
              </span>
            )}
            <div className="min-w-0">
              <h3 className="truncate text-[13px] font-semibold text-ink">{title}</h3>
              {subtitle && <p className="truncate text-xs text-muted">{subtitle}</p>}
            </div>
          </div>
          {actions && <div className="flex shrink-0 items-center gap-1.5">{actions}</div>}
        </header>
      )}
      <div className={bodyClass}>{children}</div>
    </section>
  );
}

export function Card({ className = "", children }) {
  return <div className={`panel p-4 ${className}`}>{children}</div>;
}

/* -------------------------------------------------------------------------- */
/*  Metric / KPI card                                                         */
/* -------------------------------------------------------------------------- */

// Enterprise KPI tile: icon, label, big mono value, trend delta, mini sparkline,
// and a comparison line. Subtle hover lift.
export function MetricCard({
  label, value, prefix = "", suffix = "", delta, lowerIsBetter = false, compare, spark = [],
  icon: Icon, tone = "#3B82F6", delay = 0,
}) {
  // A long name, location or vehicle gets cut off with an ellipsis. Measure it
  // and, only when it really is cut off, offer the full text on hover.
  const valueRef = useRef(null);
  const compareRef = useRef(null);
  const [clipped, setClipped] = useState(false);

  useEffect(() => {
    const check = () => {
      const isCut = (el) => !!el && el.scrollWidth > el.clientWidth + 1;
      setClipped(isCut(valueRef.current) || isCut(compareRef.current));
    };
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, [value, compare]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
      className="panel group relative p-4 transition-shadow hover:shadow-md"
    >
      {clipped && (
        <div className="pointer-events-none absolute bottom-full left-1/2 z-30 mb-2 hidden w-max max-w-[280px] -translate-x-1/2 group-hover:block">
          <div className="rounded-md bg-ink px-2.5 py-1.5 text-xs font-medium leading-snug text-surface shadow-pop">
            <div className="break-words">{value}</div>
            {compare && <div className="mt-0.5 break-words opacity-70">{compare}</div>}
          </div>
          <div className="mx-auto h-0 w-0 border-x-4 border-t-4 border-x-transparent border-t-ink" />
        </div>
      )}
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted">{label}</span>
        {Icon && (
          <span className="grid h-7 w-7 place-items-center rounded-md" style={{ background: `${tone}1a`, color: tone }}>
            <Icon className="h-3.5 w-3.5" />
          </span>
        )}
      </div>

      <div className="mt-2.5 flex items-end justify-between gap-2 overflow-hidden">
        <div ref={valueRef} className="tnum min-w-0 truncate text-[26px] font-semibold leading-none text-ink">
          {typeof value === "number" ? <Counter value={value} prefix={prefix} suffix={suffix} /> : value}
        </div>
        {spark && spark.length > 1 && (
          <div className="shrink-0 opacity-80 transition-opacity group-hover:opacity-100">
            <Sparkline values={spark} color={tone} width={64} height={34} />
          </div>
        )}
      </div>

      <div className="mt-2.5 flex items-center gap-2 text-xs">
        {delta !== undefined && <Delta delta={delta} lowerIsBetter={lowerIsBetter} />}
        {compare && <span ref={compareRef} className="truncate text-muted">{compare}</span>}
      </div>
    </motion.div>
  );
}

// Kept for backward-compat with older sections.
export function StatCard({ label, value, sub, prefix = "", suffix = "", tone = "#3B82F6", icon }) {
  return <MetricCard label={label} value={value} prefix={prefix} suffix={suffix} tone={tone} icon={icon} compare={sub} />;
}

// The arrow always points the way the number moved. The colour says whether that
// move is good news, which is not always "up": falling exposure or a falling
// fraud rate are wins, so those callers pass lowerIsBetter.
export function Delta({ delta, lowerIsBetter = false }) {
  const d = Number(delta) || 0;
  if (!d) return <span className="inline-flex items-center gap-0.5 text-muted"><Minus className="h-3 w-3" /> 0%</span>;
  const up = d > 0;
  const Icon = up ? ArrowUpRight : ArrowDownRight;
  const good = lowerIsBetter ? !up : up;
  const hex = good ? "#22C55E" : "#EF4444";
  return (
    <span className="inline-flex items-center gap-0.5 font-semibold" style={{ color: hex }}>
      <Icon className="h-3.5 w-3.5" /> {Math.abs(d)}%
    </span>
  );
}

/* -------------------------------------------------------------------------- */
/*  Badges                                                                    */
/* -------------------------------------------------------------------------- */

const BADGE_TONE = {
  neutral: { c: "var(--c-muted)", chan: "--c-muted" },
  blue: { chan: "--c-primary" },
  green: { chan: "--c-good" },
  amber: { chan: "--c-warn" },
  red: { chan: "--c-bad" },
};

// A status/priority badge. `tone` in {neutral, blue, green, amber, red}. Set
// `dot` for a leading status dot, `solid` for a filled variant.
export function Badge({ tone = "neutral", dot = false, solid = false, className = "", children }) {
  const chan = (BADGE_TONE[tone] || BADGE_TONE.neutral).chan;
  const style = solid
    ? { background: `rgb(var(${chan}))`, color: "#fff", borderColor: "transparent" }
    : { color: `rgb(var(${chan}))`, background: `rgb(var(${chan}) / 0.12)`, borderColor: `rgb(var(${chan}) / 0.25)` };
  return (
    <span className={`badge ${className}`} style={style}>
      {dot && <span className="h-1.5 w-1.5 rounded-full" style={{ background: solid ? "#fff" : `rgb(var(${chan}))` }} />}
      {children}
    </span>
  );
}

const BAND_BADGE = { HIGH: "red", MEDIUM: "amber", LOW: "green" };

export function RiskPill({ score, band }) {
  const meta = band ? { label: band } : riskMeta(score);
  const tone = BAND_BADGE[meta.label] || "neutral";
  return (
    <Badge tone={tone} dot>
      {score !== undefined ? `${Math.round(score)} · ${meta.label}` : meta.label}
    </Badge>
  );
}

/* -------------------------------------------------------------------------- */
/*  Feedback                                                                  */
/* -------------------------------------------------------------------------- */

export function Loading({ label = "Loading…" }) {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-[13px] text-muted">
      <Loader2 className="h-4 w-4 animate-spin" /> {label}
    </div>
  );
}

// Skeleton block for loading states.
export function Skeleton({ className = "" }) {
  return <div className={`shimmer rounded-md ${className}`} />;
}

export function ErrorNote({ children }) {
  return (
    <div className="rounded-md border border-bad/30 bg-bad-soft px-4 py-3 text-[13px] text-bad">{children}</div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Horizontal labelled bar (distributions / importances)                     */
/* -------------------------------------------------------------------------- */

export function Bar({ label, value, max, tone = "#3B82F6", suffix = "" }) {
  const pct = max ? Math.round((value / max) * 100) : 0;
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between text-[13px]">
        <span className="text-ink-soft">{label}</span>
        <span className="tnum text-muted">{value}{suffix}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-surface-2">
        <motion.div
          className="h-full rounded-full"
          style={{ background: tone }}
          initial={{ width: 0 }}
          whileInView={{ width: `${pct}%` }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        />
      </div>
    </div>
  );
}
