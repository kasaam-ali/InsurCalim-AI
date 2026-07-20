/** @type {import('tailwindcss').Config} */
// "Precision console" system — neutral zinc surfaces, one blue accent, hairline
// structure. All colours are CSS variables (space-separated RGB) so a single
// [data-theme] switch re-themes the app and Tailwind opacity modifiers work.
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg: "rgb(var(--c-bg) / <alpha-value>)",
        surface: "rgb(var(--c-surface) / <alpha-value>)",
        "surface-2": "rgb(var(--c-surface-2) / <alpha-value>)",
        sidebar: "rgb(var(--c-sidebar) / <alpha-value>)",
        "sidebar-hover": "rgb(var(--c-sidebar-hover) / <alpha-value>)",
        "sidebar-ink": "rgb(var(--c-sidebar-ink) / <alpha-value>)",
        "sidebar-strong": "rgb(var(--c-sidebar-strong) / <alpha-value>)",
        "sidebar-muted": "rgb(var(--c-sidebar-muted) / <alpha-value>)",
        "sidebar-border": "rgb(var(--c-sidebar-border) / <alpha-value>)",
        ink: "rgb(var(--c-ink) / <alpha-value>)",
        "ink-soft": "rgb(var(--c-ink-soft) / <alpha-value>)",
        muted: "rgb(var(--c-muted) / <alpha-value>)",
        line: "rgb(var(--c-line) / <alpha-value>)",
        "line-strong": "rgb(var(--c-line-strong) / <alpha-value>)",
        primary: "rgb(var(--c-primary) / <alpha-value>)",
        "primary-dark": "rgb(var(--c-primary-dark) / <alpha-value>)",
        "primary-soft": "rgb(var(--c-primary-soft) / <alpha-value>)",
        accent: "rgb(var(--c-accent) / <alpha-value>)",
        "accent-soft": "rgb(var(--c-accent-soft) / <alpha-value>)",
        teal: "rgb(var(--c-teal) / <alpha-value>)",
        good: "rgb(var(--c-good) / <alpha-value>)",
        "good-soft": "rgb(var(--c-good-soft) / <alpha-value>)",
        warn: "rgb(var(--c-warn) / <alpha-value>)",
        "warn-soft": "rgb(var(--c-warn-soft) / <alpha-value>)",
        bad: "rgb(var(--c-bad) / <alpha-value>)",
        "bad-soft": "rgb(var(--c-bad-soft) / <alpha-value>)",
      },
      fontFamily: {
        sans: ['Inter', "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "SFMono-Regular", "monospace"],
      },
      fontSize: {
        "2xs": ["0.6875rem", { lineHeight: "1rem" }],
      },
      borderRadius: {
        card: "10px",
      },
      boxShadow: {
        sm: "var(--shadow-sm)",
        md: "var(--shadow-md)",
        pop: "var(--shadow-pop)",
      },
      keyframes: {
        "fade-in": { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.97)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
      },
      animation: {
        "fade-in": "fade-in .25s ease-out both",
        "fade-up": "fade-up .3s ease-out both",
        "scale-in": "scale-in .16s ease-out both",
      },
    },
  },
  plugins: [],
};
