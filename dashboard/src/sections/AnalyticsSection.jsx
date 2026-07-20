import { useEffect, useState } from "react";
import {
  ResponsiveContainer, AreaChart, Area, BarChart, Bar as RBar, XAxis, YAxis, Tooltip, CartesianGrid, Cell,
} from "recharts";
import { fetchAnalytics } from "../api.js";
import { SectionHeader, Card, Loading, ErrorNote } from "../components/ui.jsx";
import { useChart, BAND_COLORS } from "../lib/chartTheme.js";

export default function AnalyticsSection() {
  const CHART = useChart();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchAnalytics().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorNote>{error}</ErrorNote>;
  if (!data) return <Loading label="Aggregating claims…" />;

  const bandData = ["HIGH", "MEDIUM", "LOW"].map((b) => ({ name: b, value: data.risk_bands[b] }));
  const fraudData = Object.entries(data.fraud_types || {}).map(([name, value]) => ({ name, value }));
  const avgData = ["HIGH", "MEDIUM", "LOW"].map((b) => ({ name: b, value: data.avg_claimed_by_band[b] }));

  return (
    <div>
      <SectionHeader eyebrow="Trends" title="Analytics" subtitle="How the book of claims moves over time and by risk." />

      <Card className="mb-4">
        <h3 className="mb-3 font-semibold">Claims per month</h3>
        <ResponsiveContainer width="100%" height={240}>
          <AreaChart data={data.claims_per_month} margin={{ left: 0, right: 12, top: 4 }}>
            <defs>
              <linearGradient id="claimsArea" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.45} />
                <stop offset="100%" stopColor="#3B82F6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke={CHART.grid} vertical={false} />
            <XAxis dataKey="month" tick={CHART.axisTick} axisLine={false} tickLine={false} />
            <YAxis tick={CHART.axisTick} axisLine={false} tickLine={false} allowDecimals={false} />
            <Tooltip contentStyle={CHART.tooltip} />
            <Area type="monotone" dataKey="claims" stroke="#3B82F6" strokeWidth={2.5}
                  fill="url(#claimsArea)" dot={{ r: 2.5, fill: "#3B82F6" }} activeDot={{ r: 5 }} />
          </AreaChart>
        </ResponsiveContainer>
      </Card>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <h3 className="mb-3 font-semibold">Claims by risk band</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={bandData} margin={{ left: -16, right: 8 }}>
              <CartesianGrid stroke={CHART.grid} vertical={false} />
              <XAxis dataKey="name" tick={CHART.axisTick} axisLine={false} tickLine={false} />
              <YAxis tick={CHART.axisTick} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip contentStyle={CHART.tooltip} cursor={CHART.cursor} />
              <RBar dataKey="value" radius={[4, 4, 0, 0]} barSize={44}>
                {bandData.map((d) => <Cell key={d.name} fill={BAND_COLORS[d.name]} />)}
              </RBar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="mb-3 font-semibold">Labeled fraud types</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={fraudData} layout="vertical" margin={{ left: 8, right: 12 }}>
              <defs>
                <linearGradient id="fraudBar2" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#3B82F6" />
                  <stop offset="100%" stopColor="#8B5CF6" />
                </linearGradient>
              </defs>
              <CartesianGrid stroke={CHART.grid} horizontal={false} />
              <XAxis type="number" tick={CHART.axisTick} axisLine={false} tickLine={false} allowDecimals={false} />
              <YAxis type="category" dataKey="name" width={130} tick={CHART.axisTick} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={CHART.tooltip} cursor={CHART.cursor} />
              <RBar dataKey="value" fill="url(#fraudBar2)" radius={[0, 4, 4, 0]} barSize={14} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="mb-3 font-semibold">Avg claimed by band (PKR)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={avgData} margin={{ left: 4, right: 8 }}>
              <defs>
                <linearGradient id="avgBar" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#22D3EE" />
                  <stop offset="100%" stopColor="#3B82F6" />
                </linearGradient>
              </defs>
              <CartesianGrid stroke={CHART.grid} vertical={false} />
              <XAxis dataKey="name" tick={CHART.axisTick} axisLine={false} tickLine={false} />
              <YAxis tick={CHART.axisTick} axisLine={false} tickLine={false} width={54}
                     tickFormatter={(v) => (v >= 1000 ? `${Math.round(v / 1000)}k` : v)} />
              <Tooltip contentStyle={CHART.tooltip} cursor={CHART.cursor}
                       formatter={(v) => `PKR ${Number(v).toLocaleString()}`} />
              <RBar dataKey="value" fill="url(#avgBar)" radius={[4, 4, 0, 0]} barSize={44} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  );
}
