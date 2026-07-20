import { useState } from "react";
import {
  LayoutDashboard, ListChecks, FileSearch, Network, BarChart3, FilePlus2,
  UserSquare, ShieldCheck, Cpu, LogOut, PanelLeft, X,
} from "lucide-react";
import ThemeToggle from "./ThemeToggle.jsx";

// Nav model. Grouped like a classic admin sidebar. `id` matches the section keys
// rendered by App.jsx.
export const NAV_GROUPS = [
  {
    heading: "Monitor",
    items: [
      { id: "overview", label: "Overview", Icon: LayoutDashboard },
      { id: "queue", label: "Claims queue", Icon: ListChecks },
      { id: "analytics", label: "Analytics", Icon: BarChart3 },
      { id: "rings", label: "Fraud rings", Icon: Network },
    ],
  },
  {
    heading: "Investigate",
    items: [
      { id: "submit", label: "Submit a claim", Icon: FilePlus2 },
      { id: "report", label: "Investigation report", Icon: FileSearch },
      { id: "claimant", label: "Claimant overview", Icon: UserSquare },
    ],
  },
  {
    heading: "Configure",
    items: [
      { id: "policy", label: "Policy & coverage", Icon: ShieldCheck },
      { id: "model", label: "Model performance", Icon: Cpu },
    ],
  },
];

const ALL_ITEMS = NAV_GROUPS.flatMap((g) => g.items);

export default function AppShell({ active, onNavigate, onLogout, children }) {
  // Sidebar open by default on desktop, collapsed on small screens.
  const [navOpen, setNavOpen] = useState(() =>
    typeof window !== "undefined" ? window.innerWidth >= 1024 : true
  );
  const activeItem = ALL_ITEMS.find((i) => i.id === active);

  return (
    <div className="min-h-dvh bg-bg">
      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-ink transition-transform
          ${navOpen ? "translate-x-0" : "-translate-x-full"}`}
      >
        <div className="flex items-center gap-2.5 px-5 py-5">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-primary-soft">
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" strokeWidth="2.4">
              <circle cx="10.5" cy="10.5" r="6.5" className="stroke-primary" />
              <line x1="15.5" y1="15.5" x2="21" y2="21" strokeLinecap="round" className="stroke-accent" />
            </svg>
          </span>
          <div className="leading-tight">
            <div className="text-sm font-bold text-sidebar-strong">InsurCalim AI</div>
            <div className="text-[11px] text-sidebar-muted">Fraud investigation</div>
          </div>
          <button className="ml-auto text-sidebar-muted hover:text-sidebar-strong" onClick={() => setNavOpen(false)}
                  aria-label="Collapse navigation">
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 pb-4">
          {NAV_GROUPS.map((group) => (
            <div key={group.heading} className="mb-4">
              <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-sidebar-muted">
                {group.heading}
              </div>
              {group.items.map(({ id, label, Icon }) => {
                const on = active === id;
                return (
                  <button
                    key={id}
                    onClick={() => {
                      onNavigate(id);
                      if (window.innerWidth < 1024) setNavOpen(false);
                    }}
                    className={`relative mb-0.5 flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition ${
                      on ? "bg-primary text-white shadow-glow" : "text-sidebar-ink hover:bg-sidebar-hover hover:text-sidebar-strong"
                    }`}
                  >
                    <Icon className="h-[18px] w-[18px] shrink-0" />
                    <span className="font-medium">{label}</span>
                  </button>
                );
              })}
            </div>
          ))}
        </nav>

        <div className="border-t border-sidebar-border p-3">
          <button
            onClick={onLogout}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-sidebar-ink transition hover:bg-sidebar-hover hover:text-sidebar-strong"
          >
            <LogOut className="h-[18px] w-[18px]" /> Log out
          </button>
        </div>
      </aside>

      {/* Backdrop (mobile only, when the sidebar overlays content) */}
      {navOpen && (
        <div className="fixed inset-0 z-30 bg-black/40 lg:hidden" onClick={() => setNavOpen(false)} />
      )}

      {/* Main column */}
      <div className={`transition-[padding] duration-300 ${navOpen ? "lg:pl-64" : "lg:pl-0"}`}>
        <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-line bg-surface/90 px-4 py-3 backdrop-blur sm:px-6">
          <button className="btn-subtle" onClick={() => setNavOpen((o) => !o)}
                  aria-label={navOpen ? "Collapse navigation" : "Open navigation"}
                  title={navOpen ? "Collapse navigation" : "Open navigation"}>
            <PanelLeft className="h-5 w-5" />
          </button>
          <div>
            <div className="text-sm font-semibold text-ink">{greeting()}, Investigator</div>
            <div className="text-xs text-muted">{activeItem ? activeItem.label : ""}</div>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <span className="hidden items-center gap-2 rounded-full border border-line px-3 py-1.5 text-xs text-muted sm:flex">
              <span className="h-1.5 w-1.5 rounded-full bg-good" /> Synthetic data · demo
            </span>
            <ThemeToggle />
            <span className="grid h-9 w-9 place-items-center rounded-full bg-primary-soft font-semibold text-primary">
              KA
            </span>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1200px] px-4 py-6 sm:px-6 sm:py-8">{children}</main>
      </div>
    </div>
  );
}

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}
