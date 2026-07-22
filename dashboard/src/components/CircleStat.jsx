// Circular progress "donut" with a centered label like the reference's
// accuracy dial. Pure SVG.
export default function CircleStat({ value = 0, max = 100, size = 132, color = "#3B82F6", label, sub }) {
  const pct = Math.max(0, Math.min(1, value / max));
  const r = size / 2 - 10;
  const c = 2 * Math.PI * r;
  const cx = size / 2;

  return (
    <div className="flex items-center gap-4">
      <svg width={size} height={size} className="shrink-0">
        <circle cx={cx} cy={cx} r={r} fill="none" className="stroke-line" strokeWidth="10" />
        <circle cx={cx} cy={cx} r={r} fill="none" stroke={color} strokeWidth="10" strokeLinecap="round"
                strokeDasharray={`${c * pct} ${c}`} transform={`rotate(-90 ${cx} ${cx})`}
                style={{ transition: "stroke-dasharray 900ms cubic-bezier(0.16,1,0.3,1)", filter: `drop-shadow(0 0 6px ${color}55)` }} />
        <text x={cx} y={cx - 2} textAnchor="middle" className="tnum fill-ink font-mono"
              style={{ fontSize: size * 0.2, fontWeight: 700 }}>
          {typeof value === "number" ? value : value}
        </text>
        {sub && (
          <text x={cx} y={cx + size * 0.15} textAnchor="middle" className="fill-muted" style={{ fontSize: 10 }}>
            {sub}
          </text>
        )}
      </svg>
      {label && <div className="text-sm text-ink-soft">{label}</div>}
    </div>
  );
}
