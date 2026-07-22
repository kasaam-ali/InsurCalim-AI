import { useEffect, useState } from "react";
import { Network, ChevronDown, Info } from "lucide-react";
import { fetchRings } from "../api.js";
import { SectionHeader, Card, Loading, ErrorNote, RiskPill, Badge } from "../components/ui.jsx";

// Turn a raw fraud_type key like "staged_collision" into "Staged collision".
function prettyType(t) {
  const s = (t || "").replace(/_/g, " ").trim();
  return s ? s[0].toUpperCase() + s.slice(1) : "Mixed pattern";
}

// The most common fraud type in a ring, used as its human label.
function dominantType(members) {
  const counts = {};
  members.forEach((m) => {
    const t = m.fraud_type || "unknown";
    counts[t] = (counts[t] || 0) + 1;
  });
  const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
  return top ? top[0] : "";
}

// Plain-language, per-type detail used to describe one specific ring.
const TYPE_DETAIL = {
  staged_collision: "crashes that look deliberately arranged, with stories that line up too neatly to be separate accidents",
  exaggerated_damage: "damage that looks inflated well beyond what the incident would realistically cause",
  exaggerated: "damage that looks inflated well beyond what the incident would realistically cause",
  policy_lapsed_backdated: "incidents that appear backdated to a time when the policy was not actually active",
  impossible_timeline: "timelines that do not physically add up, repeated across the group",
};

// A short one-line description of what this specific ring is.
function ringDescription(members) {
  const detail = TYPE_DETAIL[dominantType(members)]
    || "a shared pattern that suggests they were filed by the same group";
  return `These ${members.length} claims are linked by ${detail}.`;
}

export default function RingsSection({ onOpenClaim }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchRings().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorNote>{error}</ErrorNote>;
  if (!data) return <Loading label="Linking related claims…" />;

  return (
    <div className="animate-fade-up">
      <SectionHeader eyebrow="Organized fraud" title="Fraud rings"
                     subtitle="Claims that look connected to each other, grouped automatically." />

      {/* Plain-language explainer of what this section is and why it matters. */}
      <Card className="mb-4">
        <div className="flex items-start gap-3">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-md bg-primary/10 text-primary">
            <Info className="h-[18px] w-[18px]" />
          </span>
          <div className="space-y-1.5 text-[13px] leading-relaxed text-muted">
            <p><span className="font-semibold text-ink">What this is:</span> a view that automatically groups claims that seem connected to one another.</p>
            <p><span className="font-semibold text-ink">What a ring means:</span> when 3 or more claims share the same story or pattern, they were likely staged together by the same people, not separate real accidents.</p>
            <p><span className="font-semibold text-ink">Why it helps:</span> catching a whole group at once stops organized fraud that is easy to miss when you look at one claim at a time.</p>
            <p><span className="font-semibold text-ink">How to use it:</span> open a ring to see its linked claims, then click any claim to investigate it.</p>
          </div>
        </div>
      </Card>

      {data.rings.length === 0 ? (
        <Card><p className="text-sm text-muted">No fraud rings of size 3+ detected in the current portfolio.</p></Card>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {data.rings.map((ring, i) => (
            <RingCard key={i} ring={ring} index={i} onOpenClaim={onOpenClaim} />
          ))}
        </div>
      )}
    </div>
  );
}

// A single ring: a label header that is always visible, with the graph and the
// member claims tucked into a collapsible dropdown (closed by default).
function RingCard({ ring, index, onOpenClaim }) {
  const [open, setOpen] = useState(false);
  const label = prettyType(dominantType(ring.members));
  const avg = Math.round(
    ring.members.reduce((a, m) => a + (Number(m.risk) || 0), 0) / Math.max(ring.members.length, 1)
  );

  return (
    <Card>
      <button onClick={() => setOpen((o) => !o)} className="flex w-full items-center gap-3 text-left">
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-md bg-primary/10 text-primary">
          <Network className="h-[18px] w-[18px]" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold text-ink">Ring #{index + 1}</h3>
            <Badge tone="blue">{label}</Badge>
          </div>
          <p className="mt-0.5 text-xs text-muted">{ring.size} linked claims · avg risk {avg}</p>
        </div>
        <span className="pill shrink-0" style={{ color: "#7C3AED", background: "#7C3AED14", border: "1px solid #7C3AED33" }}>
          {ring.size} claims
        </span>
        <ChevronDown className={`h-4 w-4 shrink-0 text-muted transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open && (
        <div className="mt-3 animate-fade-in border-t border-line pt-3">
          <p className="mb-3 text-xs leading-relaxed text-muted">{ringDescription(ring.members)}</p>
          <RingGraph ring={ring} />
          <ul className="mt-3 divide-y divide-line">
            {ring.members.map((m) => (
              <li key={m.id} onClick={() => onOpenClaim?.(m.id)}
                  className="flex cursor-pointer items-center gap-3 py-2 text-sm hover:text-primary">
                <span className="tnum font-mono font-medium">#{m.id}</span>
                <span className="text-ink-soft">{prettyType(m.fraud_type)}</span>
                <span className="ml-auto"><RiskPill score={m.risk} /></span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
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
