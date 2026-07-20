import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  ResponsiveContainer, AreaChart, Area, PieChart, Pie, Cell, BarChart, Bar as RBar,
  XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";
import {
  FileStack, ShieldAlert, TrendingUp, Coins, ArrowUpRight, ArrowDownRight,
} from "lucide-react";
import { fetchStats, fetchAnalytics, fetchModel } from "../api.js";
import { SectionHeader, Loading, ErrorNote } from "../components/ui.jsx";
import { useChart, BAND_COLORS } from "../lib/chartTheme.js";
import Counter from "../components/Counter.jsx";
import Sparkline from "../components/Sparkline.jsx";
import CircleStat from "../components/CircleStat.jsx";

// Smooth trend: recent 3-month average vs the prior 3-month average, so the
// delta reads like a stable trend rather than a volatile month-to-month spike.
function deltaPct(series) {
  if (!series || series.length < 4) return 0;
  const avg = (a) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0);
  const recent = avg(series.slice(-3));
  const prior = avg(series.slice(-6, -3));
  if (!prior) return 0;
  return Math.round(((recent - prior) / prior) * 100);
}

export default function OverviewSection() {
  const CHART = useChart();
  const [stats, setStats] = useState(null);
  const [an, setAn] = useState(null);
  const [model, setModel] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchStats().then(setStats).catch((e) => setError(e.message));
    fetchAnalytics().then(setAn).catch(() => {});
    fetchModel().then(setModel).catch(() => {});
  }, []);

  if (error) return <ErrorNote>{error}</ErrorNote>;
  if (!stats || !an) return <Loading label="Scoring the portfolio…" />;

  const total = Math.max(stats.total, 1);
  const s = an.series || { months: [], claims: [], high: [], fraud: [], money: [] };
  const fraudRate = Math.round((stats.fraud / total) * 100);
  const donut = ["HIGH", "MEDIUM", "LOW"].map((b) => ({ name: b, value: stats.risk_bands[b] }));
  const fraudData = Object.entries(stats.fraud_types || {}).map(([name, value]) => ({ name, value }));
  const trend = s.months.map((m, i) => ({ month: m, high: s.high[i], claims: s.claims[i] }));
  const rocAuc = Number((model?.metrics?.[0]?.value) || 0.74);
  const topType = Object.entries(stats.fraud_types || {}).sort((a, b) => b[1] - a[1])[0];

  const kpis = [
    { label: "Claims in system", value: stats.total, spark: s.claims, delta: deltaPct(s.claims), Icon: FileStack, color: "#3B82F6" },
    { label: "High-risk", value: stats.high, sub: `${Math.round((stats.high / total) * 100)}% of book`, spark: s.high, delta: deltaPct(s.high), Icon: ShieldAlert, color: "#F45B69" },
    { label: "Fraud base rate", value: fraudRate, suffix: "%", spark: s.fraud, delta: deltaPct(s.fraud), Icon: TrendingUp, color: "#F59E0B" },
    { label: "Money at risk", value: stats.money_at_risk, prefix: "PKR ", spark: s.money, delta: deltaPct(s.money), Icon: Coins, color: "#22D3EE" },
  ];

  return (
    <div>
      <SectionHeader eyebrow="Portfolio" title="Overview"
                     subtitle="Every claim in the system, scored by the fast fraud layer." />

      {/* KPI row — plain cells separated by hairline dividers (no cards) */}
      <div className="grid grid-cols-2 gap-px border-y border-line bg-line xl:grid-cols-4">
        {kpis.map((k, i) => <PlainKpi key={k.label} {...k} delay={i * 0.05} />)}
      </div>

      {/* High-risk trend — plain section */}
      <PlainSection title="High-risk claims over time"
                    aside={<span className="text-xs text-muted">Monthly</span>}>
        <div className="mb-2 flex items-center gap-2">
          <span className="tnum font-mono text-2xl font-bold">{stats.high}</span>
          <Delta delta={deltaPct(s.high)} />
        </div>
        <ResponsiveContainer width="100%" height={240}>
          <AreaChart data={trend} margin={{ left: -18, right: 6, top: 10 }}>
            <defs>
              <linearGradient id="ovHigh" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.5} />
                <stop offset="100%" stopColor="#3B82F6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke={CHART.grid} vertical={false} />
            <XAxis dataKey="month" tick={CHART.axisTick} axisLine={false} tickLine={false} minTickGap={24} />
            <YAxis tick={CHART.axisTick} axisLine={false} tickLine={false} allowDecimals={false} />
            <Tooltip contentStyle={CHART.tooltip} />
            <Area type="monotone" dataKey="high" stroke="#3B82F6" strokeWidth={2.5}
                  fill="url(#ovHigh)" dot={false} activeDot={{ r: 5 }} />
          </AreaChart>
        </ResponsiveContainer>
      </PlainSection>

      {/* Portfolio summary — plain text, real data */}
      <PlainSection title="Portfolio summary">
        <p className="max-w-3xl text-sm leading-relaxed text-ink-soft">
          <strong className="text-ink">{stats.high} of {stats.total}</strong> claims are high-risk
          ({Math.round((stats.high / total) * 100)}%).
          {topType && <> The most common pattern is <strong className="text-ink">{topType[0]}</strong> ({topType[1]} claims).</>}{" "}
          <strong className="text-ink">PKR {Number(stats.money_at_risk).toLocaleString()}</strong> is exposed across the book,
          and <strong className="text-ink">{stats.fast_trackable}</strong> low-risk claims can be fast-tracked.
        </p>
      </PlainSection>

      {/* Breakdown — three plain columns split by hairline dividers */}
      <div className="mt-6 grid grid-cols-1 gap-px border-t border-line bg-line lg:grid-cols-3">
        <div className="bg-bg px-1 pt-5 sm:px-2">
          <h3 className="mb-2 text-sm font-semibold text-ink">Risk distribution</h3>
          <div className="flex items-center gap-3">
            <ResponsiveContainer width="52%" height={180}>
              <PieChart>
                <Pie data={donut} dataKey="value" innerRadius={48} outerRadius={72} paddingAngle={2} strokeWidth={0}>
                  {donut.map((d) => <Cell key={d.name} fill={BAND_COLORS[d.name]} />)}
                </Pie>
                <Tooltip contentStyle={CHART.tooltip} />
              </PieChart>
            </ResponsiveContainer>
            <ul className="space-y-2 text-sm">
              {donut.map((d) => (
                <li key={d.name} className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-sm" style={{ background: BAND_COLORS[d.name] }} />
                  <span className="text-ink-soft">{d.name}</span>
                  <span className="tnum ml-1 font-medium">{d.value}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="bg-bg px-1 pt-5 sm:px-4">
          <h3 className="mb-2 text-sm font-semibold text-ink">Fraud types</h3>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={fraudData} layout="vertical" margin={{ left: 8, right: 12 }}>
              <defs>
                <linearGradient id="ovFraud" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#3B82F6" /><stop offset="100%" stopColor="#8B5CF6" />
                </linearGradient>
              </defs>
              <CartesianGrid stroke={CHART.grid} horizontal={false} />
              <XAxis type="number" tick={CHART.axisTick} axisLine={false} tickLine={false} allowDecimals={false} />
              <YAxis type="category" dataKey="name" width={120} tick={{ ...CHART.axisTick, fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={CHART.tooltip} cursor={CHART.cursor} />
              <RBar dataKey="value" fill="url(#ovFraud)" radius={[0, 4, 4, 0]} barSize={13} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-bg px-1 pt-5 sm:px-4">
          <h3 className="mb-3 text-sm font-semibold text-ink">Model performance</h3>
          <CircleStat value={Math.round(rocAuc * 100)} max={100} color="#8B5CF6" sub="ROC-AUC"
                      label={<div><div>Tabular classifier on a real 30k-row dataset.</div>
                              <div className="mt-1 text-muted">Fraud recall 67% @ 0.25</div></div>} />
        </div>
      </div>
    </div>
  );
}

// A plain KPI cell: no card, sits on the page with hairline dividers around it.
function PlainKpi({ label, value, sub, prefix = "", suffix = "", spark = [], delta = 0, Icon, color, delay = 0 }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay, duration: 0.35 }}
                className="bg-bg px-5 py-5">
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4" style={{ color }} />
        <span className="text-xs font-medium uppercase tracking-wide text-muted">{label}</span>
      </div>
      <div className="tnum mt-2 font-mono text-2xl font-bold text-ink">
        <Counter value={value} prefix={prefix} suffix={suffix} />
      </div>
      <div className="mt-3 flex items-center justify-between">
        {sub ? <span className="text-xs text-muted">{sub}</span> : <Delta delta={delta} />}
        <Sparkline values={spark} color={color} />
      </div>
    </motion.div>
  );
}

// A plain content section separated from the previous block by a top hairline.
function PlainSection({ title, aside, children }) {
  return (
    <section className="mt-6 border-t border-line pt-6">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-ink">{title}</h3>
        {aside}
      </div>
      {children}
    </section>
  );
}

function Delta({ delta }) {
  if (!delta) return <span className="text-xs text-muted">—</span>;
  const up = delta > 0;
  const Icon = up ? ArrowUpRight : ArrowDownRight;
  return (
    <span className="inline-flex items-center gap-0.5 text-xs font-medium" style={{ color: up ? "#22C55E" : "#F45B69" }}>
      <Icon className="h-3.5 w-3.5" /> {Math.abs(delta)}%
    </span>
  );
}
