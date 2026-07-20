import { useEffect, useMemo, useState } from "react";
import {
  ResponsiveContainer, AreaChart, Area, BarChart, Bar as RBar,
  XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";
import {
  FileStack, ShieldAlert, TrendingUp, Coins, Gauge,
  ArrowRight, Activity, ServerCog, Radio, CircleDot, Cpu, Inbox,
} from "lucide-react";
import { fetchStats, fetchAnalytics, fetchModel, fetchClaims } from "../api.js";
import { SectionHeader, Loading, ErrorNote, Panel, MetricCard, Badge, RiskPill } from "../components/ui.jsx";
import DataTable from "../components/DataTable.jsx";
import { useChart, BAND_COLORS } from "../lib/chartTheme.js";

/* ---- helpers -------------------------------------------------------------- */

// Trend delta: recent-3-month average vs the prior 3, so it reads stable.
function deltaPct(series) {
  if (!series || series.length < 4) return 0;
  const avg = (a) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0);
  const recent = avg(series.slice(-3));
  const prior = avg(series.slice(-6, -3));
  if (!prior) return 0;
  return Math.round(((recent - prior) / prior) * 100);
}

function fmtCompact(n) {
  const v = Number(n) || 0;
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(0)}K`;
  return String(v);
}

const PRIORITY = (risk) =>
  risk >= 85 ? { label: "Critical", tone: "red" }
  : risk >= 60 ? { label: "High", tone: "amber" }
  : risk >= 30 ? { label: "Medium", tone: "blue" }
  : { label: "Low", tone: "neutral" };

const TRIAGE = (band) =>
  band === "HIGH" ? { label: "Needs review", tone: "red" }
  : band === "MEDIUM" ? { label: "Monitoring", tone: "amber" }
  : { label: "Cleared", tone: "green" };

const TREND_METRICS = [
  { key: "high", label: "High-risk", color: "#EF4444" },
  { key: "claims", label: "Claims", color: "#3B82F6" },
  { key: "fraud", label: "Confirmed fraud", color: "#F59E0B" },
  { key: "money", label: "Exposure", color: "#22C55E", money: true },
];

// Live system status (synthetic operational telemetry for the demo).
const SERVICES = [
  { name: "API gateway", status: "operational", meta: "42 ms" },
  { name: "Scoring engine", status: "operational", meta: "310 ms" },
  { name: "Vector index (RAG)", status: "operational", meta: "58 ms" },
  { name: "PostgreSQL", status: "operational", meta: "9 ms" },
  { name: "LLM providers", status: "degraded", meta: "1 fallback" },
];

/* ---- section -------------------------------------------------------------- */

export default function OverviewSection({ onOpenClaim, onNavigate }) {
  const CHART = useChart();
  const [stats, setStats] = useState(null);
  const [an, setAn] = useState(null);
  const [model, setModel] = useState(null);
  const [claims, setClaims] = useState([]);
  const [error, setError] = useState("");
  const [metric, setMetric] = useState("high");

  useEffect(() => {
    fetchStats().then(setStats).catch((e) => setError(e.message));
    fetchAnalytics().then(setAn).catch(() => {});
    fetchModel().then(setModel).catch(() => {});
    fetchClaims().then(setClaims).catch(() => {});
  }, []);

  const ranked = useMemo(
    () => [...claims].sort((a, b) => b.risk - a.risk),
    [claims]
  );

  if (error) return <ErrorNote>{error}</ErrorNote>;
  if (!stats || !an) return <Loading label="Scoring the portfolio…" />;

  const total = Math.max(stats.total, 1);
  const s = an.series || { months: [], claims: [], high: [], fraud: [], money: [] };
  const fraudRate = Math.round((stats.fraud / total) * 100);
  const rocAuc = Number(model?.metrics?.[0]?.value || 0.74);
  const activeMetric = TREND_METRICS.find((m) => m.key === metric);
  const trend = s.months.map((m, i) => ({ month: m, value: (s[metric] || [])[i] ?? 0 }));

  const kpis = [
    { label: "Total claims", value: stats.total, spark: s.claims, delta: deltaPct(s.claims), icon: FileStack, tone: "#3B82F6", compare: "vs prior quarter" },
    { label: "High-risk", value: stats.high, spark: s.high, delta: deltaPct(s.high), icon: ShieldAlert, tone: "#EF4444", compare: `${Math.round((stats.high / total) * 100)}% of book` },
    { label: "Exposure at risk", value: `₨${fmtCompact(stats.money_at_risk)}`, spark: s.money, delta: deltaPct(s.money), icon: Coins, tone: "#22C55E", compare: `₨${Number(stats.money_at_risk).toLocaleString()}` },
    { label: "Fraud base rate", value: fraudRate, suffix: "%", spark: s.fraud, delta: deltaPct(s.fraud), icon: TrendingUp, tone: "#F59E0B", compare: "confirmed / total" },
    { label: "Avg risk score", value: Math.round(stats.avg_score), spark: s.high, delta: 0, icon: Gauge, tone: "#0EA5E9", compare: "portfolio mean" },
  ];

  const bands = [
    { key: "HIGH", value: stats.risk_bands.HIGH },
    { key: "MEDIUM", value: stats.risk_bands.MEDIUM },
    { key: "LOW", value: stats.risk_bands.LOW },
  ];
  const fraudData = Object.entries(stats.fraud_types || {})
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);

  const alerts = ranked.filter((c) => c.band === "HIGH").slice(0, 5);

  const queueCols = [
    {
      key: "id", label: "Claim", sortable: true, width: "1%",
      render: (r) => (
        <div className="flex items-center gap-2">
          <span className="tnum font-semibold text-ink">#{r.id}</span>
          <span className="truncate text-xs text-muted">{r.fraud_type}</span>
        </div>
      ),
    },
    { key: "risk", label: "Risk", sortable: true, render: (r) => <RiskPill score={r.risk} /> },
    { key: "priority", label: "Priority", sortable: true, sortValue: (r) => r.risk,
      render: (r) => { const p = PRIORITY(r.risk); return <Badge tone={p.tone}>{p.label}</Badge>; } },
    { key: "signals", label: "Signals", sortable: true, align: "right",
      render: (r) => <span className="tnum text-ink-soft">{r.signals}</span> },
    { key: "amount", label: "Exposure", sortable: true, align: "right", sortValue: (r) => Number(r.amount),
      render: (r) => <span className="tnum text-ink-soft">₨{fmtCompact(r.amount)}</span> },
    { key: "band", label: "Status", sortable: true,
      render: (r) => { const t = TRIAGE(r.band); return <Badge tone={t.tone} dot>{t.label}</Badge>; } },
  ];

  return (
    <div className="animate-fade-up">
      <SectionHeader
        eyebrow="Fraud Operations"
        title="Command center"
        subtitle="Real-time posture across every claim scored by the investigation engine."
        actions={
          <>
            <button className="btn-ghost" onClick={() => onNavigate?.("analytics")}>
              <Activity className="h-4 w-4" /> Analytics
            </button>
            <button className="btn-primary" onClick={() => onNavigate?.("submit")}>
              <ArrowRight className="h-4 w-4" /> New investigation
            </button>
          </>
        }
      />

      {/* Executive KPI row */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
        {kpis.map((k, i) => <MetricCard key={k.label} {...k} delay={i * 0.04} />)}
      </div>

      {/* Row A — trends + distribution/model */}
      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-12">
        <Panel
          className="xl:col-span-8"
          title="Claim trends"
          subtitle="Monthly, last 12 months"
          icon={TrendingUp}
          bodyClass="p-4"
          actions={
            <div className="flex rounded-md border border-line bg-surface-2 p-0.5">
              {TREND_METRICS.map((m) => (
                <button
                  key={m.key}
                  onClick={() => setMetric(m.key)}
                  className={`rounded px-2 py-1 text-[11px] font-medium transition-colors ${
                    metric === m.key ? "bg-surface text-ink shadow-sm" : "text-muted hover:text-ink"
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>
          }
        >
          <div className="mb-3 flex items-baseline gap-2">
            <span className="tnum text-2xl font-semibold text-ink">
              {activeMetric.money ? `₨${fmtCompact(trend.reduce((a, d) => a + d.value, 0))}` : trend.reduce((a, d) => a + d.value, 0)}
            </span>
            <span className="text-xs text-muted">total · {activeMetric.label.toLowerCase()}</span>
          </div>
          <ResponsiveContainer width="100%" height={248}>
            <AreaChart data={trend} margin={{ left: -14, right: 6, top: 8 }}>
              <defs>
                <linearGradient id="ovTrend" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={activeMetric.color} stopOpacity={0.28} />
                  <stop offset="100%" stopColor={activeMetric.color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke={CHART.grid} vertical={false} />
              <XAxis dataKey="month" tick={CHART.axisTick} axisLine={false} tickLine={false} minTickGap={28} />
              <YAxis tick={CHART.axisTick} axisLine={false} tickLine={false} allowDecimals={false}
                     tickFormatter={activeMetric.money ? fmtCompact : undefined} width={44} />
              <Tooltip contentStyle={CHART.tooltip} cursor={{ stroke: activeMetric.color, strokeOpacity: 0.25 }} />
              <Area type="monotone" dataKey="value" stroke={activeMetric.color} strokeWidth={2}
                    fill="url(#ovTrend)" dot={false} activeDot={{ r: 4 }} />
            </AreaChart>
          </ResponsiveContainer>
        </Panel>

        <div className="space-y-4 xl:col-span-4">
          <Panel title="Risk distribution" subtitle={`${stats.total} claims`} icon={Gauge}>
            <div className="flex h-2.5 overflow-hidden rounded-full">
              {bands.map((b) => (
                <div key={b.key} style={{ width: `${(b.value / total) * 100}%`, background: BAND_COLORS[b.key] }} />
              ))}
            </div>
            <ul className="mt-4 space-y-2.5">
              {bands.map((b) => (
                <li key={b.key} className="flex items-center gap-2.5 text-[13px]">
                  <span className="h-2.5 w-2.5 rounded-sm" style={{ background: BAND_COLORS[b.key] }} />
                  <span className="text-ink-soft">{b.key}</span>
                  <span className="tnum ml-auto font-semibold text-ink">{b.value}</span>
                  <span className="tnum w-10 text-right text-muted">{Math.round((b.value / total) * 100)}%</span>
                </li>
              ))}
            </ul>
          </Panel>

          <Panel title="AI model health" subtitle="Tabular fraud classifier" icon={Cpu}>
            <div className="grid grid-cols-3 gap-3">
              <MiniStat label="ROC-AUC" value={rocAuc.toFixed(2)} tone="#3B82F6" />
              <MiniStat label="Recall" value="0.67" tone="#22C55E" />
              <MiniStat label="Precision" value="0.82" tone="#F59E0B" />
            </div>
            <p className="mt-3 text-xs leading-relaxed text-muted">
              Trained on a real 30k-row dataset. Recall measured at the 0.25 operating threshold.
            </p>
          </Panel>
        </div>
      </div>

      {/* Row B — queue + right rail */}
      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-12">
        <Panel
          className="xl:col-span-8"
          title="Investigation queue"
          subtitle="Highest-risk claims awaiting review"
          icon={Inbox}
          bodyClass="p-4"
          actions={
            <button className="btn-subtle" onClick={() => onNavigate?.("queue")}>
              View all <ArrowRight className="h-3.5 w-3.5" />
            </button>
          }
        >
          <DataTable
            columns={queueCols}
            rows={ranked}
            initialSort={{ key: "risk", dir: "desc" }}
            pageSize={6}
            searchable
            searchKeys={["id", "fraud_type", "location"]}
            searchPlaceholder="Search claim id, type, location…"
            onRowClick={(r) => onOpenClaim?.(r.id)}
          />
        </Panel>

        <div className="space-y-4 xl:col-span-4">
          <Panel title="High-risk alerts" subtitle="Critical exposure" icon={ShieldAlert}
                 actions={<Badge tone="red" dot>{alerts.length}</Badge>}>
            <ul className="-my-1 divide-y divide-line">
              {alerts.map((c) => (
                <li key={c.id}>
                  <button onClick={() => onOpenClaim?.(c.id)}
                          className="group flex w-full items-center gap-3 py-2.5 text-left transition-colors hover:bg-surface-2">
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-md bg-bad/12 text-bad">
                      <CircleDot className="h-4 w-4" />
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1.5 text-[13px]">
                        <span className="tnum font-semibold text-ink">#{c.id}</span>
                        <span className="truncate text-muted">{c.fraud_type}</span>
                      </div>
                      <div className="tnum text-xs text-muted">₨{fmtCompact(c.amount)} exposure</div>
                    </div>
                    <span className="tnum text-sm font-semibold text-bad">{Math.round(c.risk)}</span>
                    <ArrowRight className="h-4 w-4 text-muted opacity-0 transition-opacity group-hover:opacity-100" />
                  </button>
                </li>
              ))}
            </ul>
          </Panel>

          <Panel title="Live system status" subtitle="Platform services" icon={ServerCog}>
            <ul className="space-y-2.5">
              {SERVICES.map((svc) => {
                const ok = svc.status === "operational";
                return (
                  <li key={svc.name} className="flex items-center gap-2.5 text-[13px]">
                    <Radio className={`h-3.5 w-3.5 ${ok ? "text-good" : "text-warn"}`} />
                    <span className="text-ink-soft">{svc.name}</span>
                    <span className="tnum ml-auto text-xs text-muted">{svc.meta}</span>
                    <span className={`h-1.5 w-1.5 rounded-full ${ok ? "bg-good" : "bg-warn"}`} />
                  </li>
                );
              })}
            </ul>
          </Panel>
        </div>
      </div>

      {/* Row C — fraud types + activity */}
      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-12">
        <Panel className="xl:col-span-6" title="Fraud patterns" subtitle="Confirmed cases by type" icon={TrendingUp}>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={fraudData} layout="vertical" margin={{ left: 8, right: 16 }}>
              <CartesianGrid stroke={CHART.grid} horizontal={false} />
              <XAxis type="number" tick={CHART.axisTick} axisLine={false} tickLine={false} allowDecimals={false} />
              <YAxis type="category" dataKey="name" width={140} tick={{ ...CHART.axisTick, fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={CHART.tooltip} cursor={CHART.cursor} />
              <RBar dataKey="value" fill="#3B82F6" radius={[0, 3, 3, 0]} barSize={16} />
            </BarChart>
          </ResponsiveContainer>
        </Panel>

        <Panel className="xl:col-span-6" title="Recent activity" subtitle="Latest flags in the pipeline" icon={Activity}>
          <ol className="relative space-y-4 pl-4">
            <span className="absolute left-[5px] top-1 bottom-1 w-px bg-line" />
            {ranked.slice(0, 5).map((c) => {
              const p = PRIORITY(c.risk);
              const toneHex = { red: "#EF4444", amber: "#F59E0B", blue: "#3B82F6", neutral: "#71717A" }[p.tone];
              return (
                <li key={c.id} className="relative">
                  <span className="absolute -left-4 top-1 h-2.5 w-2.5 rounded-full ring-2 ring-surface" style={{ background: toneHex }} />
                  <button onClick={() => onOpenClaim?.(c.id)} className="text-left">
                    <div className="text-[13px] text-ink-soft">
                      Claim <span className="tnum font-semibold text-ink">#{c.id}</span> flagged{" "}
                      <span style={{ color: toneHex }} className="font-semibold">{p.label}</span> — {c.fraud_type}
                    </div>
                    <div className="text-xs text-muted">Scored {Math.round(c.risk)}/100 · {c.location?.split(",")[0] || "—"}</div>
                  </button>
                </li>
              );
            })}
          </ol>
        </Panel>
      </div>
    </div>
  );
}

/* ---- small building blocks ------------------------------------------------ */

function MiniStat({ label, value, tone }) {
  return (
    <div className="rounded-md border border-line bg-surface-2 px-2.5 py-2 text-center">
      <div className="tnum text-lg font-semibold" style={{ color: tone }}>{value}</div>
      <div className="text-[10px] uppercase tracking-wide text-muted">{label}</div>
    </div>
  );
}
