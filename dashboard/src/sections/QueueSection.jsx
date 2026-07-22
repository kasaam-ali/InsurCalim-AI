import { useEffect, useMemo, useState } from "react";
import { Search, Flag, ChevronRight } from "lucide-react";
import { fetchClaims } from "../api.js";
import { SectionHeader, RiskPill, Loading, ErrorNote } from "../components/ui.jsx";

const BANDS = ["All", "HIGH", "MEDIUM", "LOW"];

export default function QueueSection({ onOpenClaim }) {
  const [claims, setClaims] = useState(null);
  const [band, setBand] = useState("All");
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    fetchClaims().then(setClaims).catch((e) => setError(e.message));
  }, []);

  const rows = useMemo(() => {
    if (!claims) return [];
    const q = query.trim().toLowerCase();
    return claims.filter((c) => {
      if (band !== "All" && c.band !== band) return false;
      if (q && !`${c.description} ${c.location}`.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [claims, band, query]);

  return (
    <div>
      <SectionHeader eyebrow="Portfolio" title="Claims queue"
                     subtitle="Ranked by risk. Open a claim to see the full investigation." />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="flex gap-1 rounded-lg border border-line bg-surface p-1">
          {BANDS.map((b) => (
            <button key={b} onClick={() => setBand(b)}
                    className={`rounded-md px-3 py-1.5 text-xs font-medium transition ${
                      band === b ? "bg-primary text-white" : "text-muted hover:text-ink"
                    }`}>
              {b}
            </button>
          ))}
        </div>
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
          <input value={query} onChange={(e) => setQuery(e.target.value)}
                 placeholder="Search description or location…" className="field pl-9" />
        </div>
      </div>

      {error && <ErrorNote>{error}</ErrorNote>}
      {!claims && !error && <Loading label="Scoring the portfolio…" />}

      {claims && (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="border-b border-line bg-bg text-left text-xs uppercase tracking-wide text-muted">
              <tr>
                <th className="px-4 py-3">Claim</th>
                <th className="px-4 py-3">Risk</th>
                <th className="px-4 py-3">Type (label)</th>
                <th className="hidden px-4 py-3 md:table-cell">Location</th>
                <th className="px-4 py-3">Flags</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => (
                <tr key={c.id} onClick={() => onOpenClaim?.(c.id)}
                    className="cursor-pointer border-b border-line/70 transition last:border-0 hover:bg-primary-soft/50">
                  <td className="tnum px-4 py-3 font-mono font-medium">#{c.id}</td>
                  <td className="px-4 py-3"><RiskPill score={c.risk} band={c.band} /></td>
                  <td className="px-4 py-3 text-ink-soft">{c.fraud_type}</td>
                  <td className="hidden max-w-[240px] truncate px-4 py-3 text-muted md:table-cell">
                    {c.location || " "}
                  </td>
                  <td className="px-4 py-3">
                    {c.signals > 0 ? (
                      <span className="inline-flex items-center gap-1 text-warn"><Flag className="h-3.5 w-3.5" /> {c.signals}</span>
                    ) : <span className="text-muted">0</span>}
                  </td>
                  <td className="px-4 py-3 text-right text-muted"><ChevronRight className="ml-auto h-4 w-4" /></td>
                </tr>
              ))}
            </tbody>
          </table>
          {rows.length === 0 && <div className="px-4 py-8 text-center text-sm text-muted">No claims match.</div>}
        </div>
      )}
      {claims && <p className="mt-3 text-xs text-muted">{rows.length} claims shown.</p>}
    </div>
  );
}
