/** @type {import('tailwindcss').Config} */
// Dark "enterprise premium" palette (Linear/Vercel-leaning, InsightAI-inspired):
// deep near-black navy, elevated cards, a blue primary with subtle violet + teal
// accents for gradients. Restrained glow — serious, not a neon toy. Token names
// are kept from the light theme so components re-theme automatically.
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // All colours are CSS variables (space-separated RGB channels) so a
        // single [data-theme] switch re-themes the whole app, and Tailwind
        // opacity modifiers (e.g. bg-primary/15) keep working.
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
        sans: ['"IBM Plex Sans"', "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "SFMono-Regular", "monospace"],
      },
      borderRadius: {
        card: "14px",
      },
      backgroundImage: {
        "grad-primary": "linear-gradient(135deg, #3B82F6, #8B5CF6)",
        "grad-teal": "linear-gradient(135deg, #22D3EE, #3B82F6)",
        "grad-violet": "linear-gradient(135deg, #8B5CF6, #6366F1)",
      },
      boxShadow: {
        card: "0 1px 2px rgba(0,0,0,.4), 0 1px 3px rgba(0,0,0,.3)",
        "card-hover": "0 8px 24px rgba(0,0,0,.5)",
        glow: "0 0 24px rgba(59,130,246,.25)",
        "glow-violet": "0 0 30px rgba(139,92,246,.28)",
      },
      keyframes: {
        "fade-in": { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        float: { "0%,100%": { transform: "translateY(0)" }, "50%": { transform: "translateY(-6px)" } },
        "spin-slow": { to: { transform: "rotate(360deg)" } },
      },
      animation: {
        "fade-in": "fade-in .3s ease-out both",
        "fade-up": "fade-up .35s ease-out both",
        float: "float 6s ease-in-out infinite",
        "spin-slow": "spin-slow 18s linear infinite",
      },
    },
  },
  plugins: [],
};
