import { riskMeta, TONE_HEX } from "../lib/report.js";

// Semicircular risk gauge (light theme). The arc sweeps 0 → score over 180°,
// coloured by risk band. Score shown in tabular mono.
export default function RiskGauge({ score = 0, size = 240 }) {
  const s = Math.max(0, Math.min(100, Number(score) || 0));
  const { label, tone } = riskMeta(s);
  const color = TONE_HEX[tone];

  const r = 80;
  const cx = 100;
  const cy = 100;
  const circumference = Math.PI * r;
  const dash = (s / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 200 118" style={{ width: size, maxWidth: "100%" }} role="img"
           aria-label={`Risk score ${Math.round(s)} out of 100, ${label} risk`}>
        <path d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
              fill="none" className="stroke-line" strokeWidth="13" strokeLinecap="round" />
        <path d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
              fill="none" stroke={color} strokeWidth="13" strokeLinecap="round"
              strokeDasharray={`${dash} ${circumference}`}
              style={{ transition: "stroke-dasharray 900ms cubic-bezier(0.16,1,0.3,1)", filter: `drop-shadow(0 0 6px ${color}55)` }} />
        <text x={cx} y={cy - 16} textAnchor="middle" className="tnum fill-ink font-mono"
              style={{ fontSize: 32, fontWeight: 700 }}>
          {Math.round(s)}
        </text>
        <text x={cx} y={cy + 2} textAnchor="middle" className="fill-muted" style={{ fontSize: 10, letterSpacing: 1 }}>
          / 100 RISK
        </text>
      </svg>
      <span className="pill -mt-1" style={{ color, background: `${color}16`, border: `1px solid ${color}33` }}>
        <span className="h-1.5 w-1.5 rounded-full" style={{ background: color }} />
        {label} RISK
      </span>
    </div>
  );
}
