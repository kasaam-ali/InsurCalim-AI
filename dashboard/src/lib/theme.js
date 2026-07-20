import { useEffect, useState } from "react";

// Theme management via a `data-theme` attribute on <html> and CSS variables.
// Two themes: "dark" (default) and "light" (white + black + light blue).
const KEY = "insurclaim_theme";
const EVENT = "insur:theme";

export function getTheme() {
  return document.documentElement.getAttribute("data-theme") || "dark";
}

export function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  try {
    localStorage.setItem(KEY, theme);
  } catch (_) {}
  window.dispatchEvent(new CustomEvent(EVENT, { detail: theme }));
}

export function toggleTheme() {
  applyTheme(getTheme() === "dark" ? "light" : "dark");
}

// Subscribe a component to the current theme.
export function useTheme() {
  const [theme, setTheme] = useState(getTheme());
  useEffect(() => {
    const on = () => setTheme(getTheme());
    window.addEventListener(EVENT, on);
    return () => window.removeEventListener(EVENT, on);
  }, []);
  return theme;
}
