import { Sun, Moon } from "lucide-react";
import { useTheme, toggleTheme } from "../lib/theme.js";

// Dark ↔ light theme switch. One click re-themes the whole app via CSS variables.
export default function ThemeToggle() {
  const theme = useTheme();
  const isDark = theme !== "light";
  return (
    <button
      onClick={toggleTheme}
      title={isDark ? "Switch to light theme" : "Switch to dark theme"}
      aria-label="Toggle theme"
      className="grid h-9 w-9 place-items-center rounded-lg border border-line bg-surface-2 text-ink-soft transition hover:border-primary/50 hover:text-primary"
    >
      {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </button>
  );
}
