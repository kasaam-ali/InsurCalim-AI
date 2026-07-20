import { useId } from "react";

// Tiny gradient area sparkline (SVG) from a list of numbers. Purely decorative
// scale, but the shape is real data (a monthly series).
export default function Sparkline({ values = [], color = "#3B82F6", width = 120, height = 36 }) {
  const id = useId().replace(/:/g, "");
  if (!values.length) return <svg width={width} height={height} />;

  const max = Math.max(...values);
  const min = Math.min(...values);
  const span = max - min || 1;
  const stepX = width / Math.max(values.length - 1, 1);
  const pts = values.map((v, i) => [i * stepX, height - 4 - ((v - min) / span) * (height - 8)]);
  const line = pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");
  const area = `${line} L${width},${height} L0,${height} Z`;

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id={`sg-${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.35" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#sg-${id})`} />
      <path d={line} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
