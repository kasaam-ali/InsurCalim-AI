import { useTheme } from "./theme.js";

// Recharts styling that follows the active theme (Recharts needs literal colours,
// not CSS classes, so we resolve them from the current theme here).
const DARK = {
  grid: "#1C2434",
  axisTick: { fontSize: 11, fill: "#7B879B" },
  cursor: { fill: "rgba(59,130,246,0.08)" },
  tooltip: {
    background: "#141A24", border: "1px solid #222A38", borderRadius: 8,
    fontSize: 12, color: "#E7ECF3", boxShadow: "0 8px 24px rgba(0,0,0,.5)",
  },
};

const LIGHT = {
  grid: "#E8EEF6",
  axisTick: { fontSize: 11, fill: "#64748B" },
  cursor: { fill: "rgba(37,99,235,0.06)" },
  tooltip: {
    background: "#FFFFFF", border: "1px solid #E2E8F0", borderRadius: 8,
    fontSize: 12, color: "#0B1220", boxShadow: "0 8px 24px rgba(16,24,40,.12)",
  },
};

export function useChart() {
  return useTheme() === "light" ? LIGHT : DARK;
}

// Risk band colours (kept constant across themes; readable on both).
export const BAND_COLORS = { HIGH: "#EF4444", MEDIUM: "#F59E0B", LOW: "#22C55E" };
export const SERIES = ["#3B82F6", "#8B5CF6", "#22D3EE", "#F59E0B", "#22C55E"];
