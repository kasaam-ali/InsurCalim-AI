import { useTheme } from "./theme.js";

// Recharts styling that follows the active theme (Recharts needs literal colours,
// not CSS classes, so we resolve them from the current theme here). Muted grids,
// tabular tick labels, restrained tooltips enterprise, not decorative.
const DARK = {
  grid: "#212127",
  axisTick: { fontSize: 11, fill: "#71717A", fontFamily: "JetBrains Mono, monospace" },
  cursor: { fill: "rgba(59,130,246,0.07)" },
  tooltip: {
    background: "#171719", border: "1px solid #2E2E33", borderRadius: 8,
    fontSize: 12, color: "#F4F4F5", boxShadow: "0 12px 32px rgba(0,0,0,.55)",
    padding: "8px 10px",
  },
};

const LIGHT = {
  grid: "#ECECEE",
  axisTick: { fontSize: 11, fill: "#71717A", fontFamily: "JetBrains Mono, monospace" },
  cursor: { fill: "rgba(37,99,235,0.05)" },
  tooltip: {
    background: "#FFFFFF", border: "1px solid #E4E4E7", borderRadius: 8,
    fontSize: 12, color: "#18181B", boxShadow: "0 12px 32px rgba(16,24,40,.12)",
    padding: "8px 10px",
  },
};

export function useChart() {
  return useTheme() === "light" ? LIGHT : DARK;
}

// Risk band colours (constant across themes; readable on both).
export const BAND_COLORS = { HIGH: "#EF4444", MEDIUM: "#F59E0B", LOW: "#22C55E" };
// Categorical series blue-led, a single hue family with restrained support colours.
export const SERIES = ["#3B82F6", "#60A5FA", "#0EA5E9", "#F59E0B", "#22C55E"];
