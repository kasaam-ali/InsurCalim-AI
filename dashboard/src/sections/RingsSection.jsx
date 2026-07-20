import { useEffect, useState } from "react";
import { Network } from "lucide-react";
import { fetchRings } from "../api.js";
import { SectionHeader, Card, Loading, ErrorNote, RiskPill } from "../components/ui.jsx";

export default function RingsSection({ onOpenClaim }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchRings().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorNote>{error}</ErrorNote>;
  if (!data) return <Loading label="Linking related claims…" />;

  return (
    <div>
      <SectionHeader eyebrow="Organized fraud" title="Fraud rings"
                     subtitle="Groups of claims linked by similar known-fraud patterns (RAG similarity ≥ 0.40)." />

      {data.rings.length === 0 ? (
        <Card><p className="text-sm text-muted">No fraud rings of size 3+ detected in the current portfolio.</p></Card>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {data.rings.map((ring, i) => (
            <Card key={i}>
              <div className="mb-3 flex items-center justify-between">
                <h3 className="flex items-center gap-2 font-semibold">
                  <Network className="h-4 w-4 text-primary" /> Ring #{i + 1}
                </h3>
                <span className="pill" style={{ color: "#7C3AED", background: "#7C3AED14", border: "1px solid #7C3AED33" }}>
                  {ring.size} claims
                </span>
              </div>
              <RingGraph ring={ring} />
              <ul className="mt-3 divide-y divide-line">
                {ring.members.map((m) => (
                  <li key={m.id} onClick={() => onOpenClaim?.(m.id)}
                      className="flex cursor-pointer items-center gap-3 py-2 text-sm hover:text-primary">
                    <span className="tnum font-mono font-medium">#{m.id}</span>
                    <span className="text-ink-soft">{m.fraud_type}</span>
                    <span className="ml-auto"><RiskPill score={m.risk} /></span>
                  </li>
                ))}
              </ul>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// Simple circular node-link layout of a ring's claims.
function RingGraph({ ring, size = 220 }) {
  const R = size / 2 - 26;
  const cx = size / 2;
  const cy = size / 2;
  const nodes = ring.members.slice(0, 14); // cap for legibility
  const pos = {};
  nodes.forEach((m, i) => {
    const a = (i / nodes.length) * 2 * Math.PI - Math.PI / 2;
    pos[m.id] = { x: cx + R * Math.cos(a), y: cy + R * Math.sin(a) };
  });

  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="mx-auto" style={{ width: size, maxWidth: "100%" }}>
      {ring.edges.map(([a, b], i) =>
        pos[a] && pos[b] ? (
          <line key={i} x1={pos[a].x} y1={pos[a].y} x2={pos[b].x} y2={pos[b].y} stroke="#CBD5E1" strokeWidth="1" />
        ) : null
      )}
      {nodes.map((m) => (
        <g key={m.id}>
          <circle cx={pos[m.id].x} cy={pos[m.id].y} r="13" fill="#EFF4FF" stroke="#2563EB" strokeWidth="1.5" />
          <text x={pos[m.id].x} y={pos[m.id].y + 3} textAnchor="middle"
                style={{ fontSize: 9, fill: "#1D4ED8", fontWeight: 600 }}>
            {m.id}
          </text>
        </g>
      ))}
    </svg>
  );
}
