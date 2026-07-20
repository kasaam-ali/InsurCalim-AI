import { Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import Counter from "./Counter.jsx";
import { riskMeta, BAND_TONE, TONE_HEX } from "../lib/report.js";

// Shared, light-theme building blocks used across the dashboard sections.

export function SectionHeader({ eyebrow, title, subtitle, actions }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        {eyebrow && <div className="eyebrow mb-1">{eyebrow}</div>}
        <h1 className="text-xl font-bold sm:text-2xl">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-muted">{subtitle}</p>}
      </div>
      {actions}
    </div>
  );
}

export function Card({ className = "", children }) {
  return <div className={`card p-5 ${className}`}>{children}</div>;
}

export function StatCard({ label, value, sub, prefix = "", suffix = "", tone = "#2563EB", icon: Icon, delay = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.35 }}
      className="card p-5"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-muted">{label}</span>
        {Icon && (
          <span className="grid h-8 w-8 place-items-center rounded-lg" style={{ background: `${tone}14`, color: tone }}>
            <Icon className="h-4 w-4" />
          </span>
        )}
      </div>
      <div className="tnum mt-2 font-mono text-2xl font-bold text-ink">
        {typeof value === "number" ? <Counter value={value} prefix={prefix} suffix={suffix} /> : value}
      </div>
      {sub && <div className="mt-1 text-xs text-muted">{sub}</div>}
    </motion.div>
  );
}

export function RiskPill({ score, band }) {
  const meta = band ? { label: band, tone: BAND_TONE[band] } : riskMeta(score);
  const hex = TONE_HEX[meta.tone];
  return (
    <span className="pill" style={{ color: hex, background: `${hex}16`, border: `1px solid ${hex}33` }}>
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: hex }} />
      {score !== undefined ? `${Math.round(score)} ${meta.label}` : `${meta.label} RISK`}
    </span>
  );
}

export function Loading({ label = "Loading…" }) {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-sm text-muted">
      <Loader2 className="h-4 w-4 animate-spin" /> {label}
    </div>
  );
}

export function ErrorNote({ children }) {
  return (
    <div className="rounded-lg border border-bad/30 bg-bad-soft px-4 py-3 text-sm text-bad">{children}</div>
  );
}

// Horizontal labelled bar (for distributions / importances).
export function Bar({ label, value, max, tone = "#2563EB", suffix = "" }) {
  const pct = max ? Math.round((value / max) * 100) : 0;
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="text-ink-soft">{label}</span>
        <span className="tnum text-muted">
          {value}
          {suffix}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-line">
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
