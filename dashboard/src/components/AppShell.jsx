import { useEffect, useState } from "react";
import {
  LayoutDashboard, Inbox, TrendingUp, Network, FilePlus2, FileSearch,
  IdCard, ShieldCheck, Cpu, LogOut, PanelLeft, ChevronsUpDown, Search,
  Bell, MessageSquare, Plus, ChevronRight, Check, Menu, X, ShieldAlert, BookOpen,
} from "lucide-react";
import ThemeToggle from "./ThemeToggle.jsx";

// Grouped navigation. `id` matches the section keys rendered by App.jsx.
export const NAV_GROUPS = [
  {
    heading: "Monitor",
    items: [
      { id: "overview", label: "Command center", Icon: LayoutDashboard },
      { id: "queue", label: "Investigation queue", Icon: Inbox },
      { id: "analytics", label: "Fraud analytics", Icon: TrendingUp },
      { id: "rings", label: "Fraud rings", Icon: Network },
    ],
  },
  {
    heading: "Investigate",
    items: [
      { id: "submit", label: "New investigation", Icon: FilePlus2 },
      { id: "report", label: "Investigation report", Icon: FileSearch },
      { id: "claimant", label: "Claimant profile", Icon: IdCard },
    ],
  },
  {
    heading: "Configure",
    items: [
      { id: "policy", label: "Policies & coverage", Icon: ShieldCheck },
      { id: "model", label: "Model health", Icon: Cpu },
      { id: "guide", label: "How it works", Icon: BookOpen },
    ],
  },
];

const ALL_ITEMS = NAV_GROUPS.flatMap((g) => g.items);
const COLLAPSE_KEY = "insurclaim_nav_collapsed";

// Representative operational notifications (synthetic demo data).
const NOTICES = [
  { tone: "#EF4444", title: "3 high-risk claims flagged", meta: "Investigation queue · just now" },
  { tone: "#F59E0B", title: "Fraud ring #4 gained a new member", meta: "Ring detection · 12m ago" },
  { tone: "#3B82F6", title: "Model recalibrated on 30k rows", meta: "Model health · 1h ago" },
];

export default function AppShell({ active, onNavigate, onLogout, children }) {
  const [collapsed, setCollapsed] = useState(() => {
    try { return localStorage.getItem(COLLAPSE_KEY) === "1"; } catch { return false; }
  });
  const [mobileOpen, setMobileOpen] = useState(false);
  const activeItem = ALL_ITEMS.find((i) => i.id === active);
  const activeGroup = NAV_GROUPS.find((g) => g.items.some((i) => i.id === active));

  useEffect(() => {
    try { localStorage.setItem(COLLAPSE_KEY, collapsed ? "1" : "0"); } catch {}
  }, [collapsed]);

  function go(id) {
    onNavigate(id);
    setMobileOpen(false);
  }

  const railW = collapsed ? "lg:w-[60px]" : "lg:w-[240px]";
  const padL = collapsed ? "lg:pl-[60px]" : "lg:pl-[240px]";

  return (
    <div className="min-h-dvh bg-bg">
      {/* ------------------------------------------------------------------ */}
      {/*  Sidebar                                                            */}
      {/* ------------------------------------------------------------------ */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-[240px] flex-col border-r border-sidebar-border bg-sidebar
          transition-[width,transform] duration-200 ${railW}
          ${mobileOpen ? "translate-x-0" : "-translate-x-full"} lg:translate-x-0`}
      >
        <Workspace collapsed={collapsed} onClose={() => setMobileOpen(false)} />

        <nav className="flex-1 overflow-y-auto px-2.5 py-3">
          {NAV_GROUPS.map((group) => (
            <div key={group.heading} className="mb-4 last:mb-0">
              {!collapsed && (
                <div className="px-2 pb-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-sidebar-muted">
                  {group.heading}
                </div>
              )}
              {collapsed && <div className="mx-2 mb-1.5 h-px bg-sidebar-border" />}
              <div className="space-y-0.5">
                {group.items.map(({ id, label, Icon }) => {
                  const on = active === id;
                  return (
                    <button
                      key={id}
                      onClick={() => go(id)}
                      title={collapsed ? label : undefined}
                      className={`group relative flex w-full items-center gap-2.5 rounded-md px-2 py-[7px] text-[13px] transition-colors
                        ${collapsed ? "justify-center" : ""}
                        ${on
                          ? "bg-surface-2 font-semibold text-sidebar-strong"
                          : "font-medium text-sidebar-ink hover:bg-sidebar-hover hover:text-sidebar-strong"}`}
                    >
                      {on && (
                        <span className="absolute left-0 top-1/2 h-4 w-[3px] -translate-y-1/2 rounded-r-full bg-primary" />
                      )}
                      <Icon className={`h-[17px] w-[17px] shrink-0 ${on ? "text-primary" : ""}`} />
                      {!collapsed && <span className="truncate">{label}</span>}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Footer system status + user */}
        <div className="border-t border-sidebar-border p-2.5">
          {!collapsed && (
            <div className="mb-2 flex items-center gap-2 rounded-md px-2 py-1.5 text-[11px] text-sidebar-muted">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-good opacity-60" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-good" />
              </span>
              All systems operational
            </div>
          )}
          <div className={`flex items-center gap-2.5 rounded-md px-2 py-1.5 ${collapsed ? "justify-center" : ""}`}>
            <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-primary/15 text-[11px] font-bold text-primary">
              KA
            </span>
            {!collapsed && (
              <div className="min-w-0 flex-1 leading-tight">
                <div className="truncate text-[12px] font-semibold text-sidebar-strong">Kasaam Ali</div>
                <div className="truncate text-[11px] text-sidebar-muted">Senior Investigator</div>
              </div>
            )}
            {!collapsed && (
              <button onClick={onLogout} title="Log out"
                      className="grid h-7 w-7 place-items-center rounded-md text-sidebar-muted transition-colors hover:bg-sidebar-hover hover:text-sidebar-strong">
                <LogOut className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </aside>

      {/* Mobile backdrop */}
      {mobileOpen && <div className="fixed inset-0 z-40 bg-black/50 lg:hidden" onClick={() => setMobileOpen(false)} />}

      {/* ------------------------------------------------------------------ */}
      {/*  Main column                                                        */}
      {/* ------------------------------------------------------------------ */}
      <div className={`transition-[padding] duration-200 ${padL}`}>
        <TopBar
          collapsed={collapsed}
          onToggleRail={() => setCollapsed((c) => !c)}
          onOpenMobile={() => setMobileOpen(true)}
          groupLabel={activeGroup?.heading}
          sectionLabel={activeItem?.label}
          onNavigate={go}
        />
        <main className="mx-auto w-full max-w-[1360px] px-4 py-6 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Workspace selector                                                        */
/* -------------------------------------------------------------------------- */
function Workspace({ collapsed, onClose }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative border-b border-sidebar-border p-2.5">
      <button
        onClick={() => setOpen((o) => !o)}
        className={`flex w-full items-center gap-2.5 rounded-md px-1.5 py-1.5 transition-colors hover:bg-sidebar-hover
          ${collapsed ? "justify-center" : ""}`}
      >
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-md bg-ink text-bg">
          <ShieldAlert className="h-[18px] w-[18px]" />
        </span>
        {!collapsed && (
          <>
            <span className="min-w-0 flex-1 text-left leading-tight">
              <span className="block truncate text-[13px] font-semibold text-sidebar-strong">InsurClaim AI</span>
              <span className="block truncate text-[11px] text-sidebar-muted">Fraud Operations</span>
            </span>
            <ChevronsUpDown className="h-3.5 w-3.5 shrink-0 text-sidebar-muted" />
          </>
        )}
      </button>

      {/* Mobile close */}
      <button onClick={onClose} className="absolute right-2.5 top-2.5 grid h-7 w-7 place-items-center rounded-md text-sidebar-muted hover:bg-sidebar-hover lg:hidden">
        <X className="h-4 w-4" />
      </button>

      {open && !collapsed && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute left-2.5 right-2.5 top-full z-20 mt-1 animate-scale-in rounded-lg border border-line bg-surface p-1.5 shadow-pop">
            <div className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted">Workspace</div>
            <div className="flex items-center gap-2.5 rounded-md bg-surface-2 px-2 py-1.5">
              <span className="grid h-7 w-7 place-items-center rounded-md bg-ink text-bg"><ShieldAlert className="h-4 w-4" /></span>
              <div className="min-w-0 flex-1 leading-tight">
                <div className="truncate text-[12px] font-semibold text-ink">InsurClaim AI</div>
                <div className="truncate text-[11px] text-muted">Fraud Operations · Synthetic demo</div>
              </div>
              <Check className="h-4 w-4 text-primary" />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Top bar                                                                   */
/* -------------------------------------------------------------------------- */
function TopBar({ collapsed, onToggleRail, onOpenMobile, groupLabel, sectionLabel, onNavigate }) {
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-line bg-bg/80 px-4 backdrop-blur-md sm:px-6 lg:px-8">
      {/* Mobile menu */}
      <button onClick={onOpenMobile} className="icon-btn lg:hidden"><Menu className="h-[18px] w-[18px]" /></button>
      {/* Desktop rail toggle */}
      <button onClick={onToggleRail} title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
              className="icon-btn hidden lg:grid"><PanelLeft className="h-[18px] w-[18px]" /></button>

      {/* Breadcrumb */}
      <nav className="hidden min-w-0 items-center gap-1.5 text-[13px] sm:flex">
        <span className="text-muted">{groupLabel || "Monitor"}</span>
        <ChevronRight className="h-3.5 w-3.5 text-muted/60" />
        <span className="truncate font-semibold text-ink">{sectionLabel || "Command center"}</span>
      </nav>

      {/* Global search */}
      <div className="ml-auto hidden max-w-sm flex-1 md:block">
        <label className="group flex h-9 items-center gap-2 rounded-md border border-line bg-surface px-2.5 text-muted transition-colors focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20">
          <Search className="h-4 w-4 shrink-0" />
          <input
            className="w-full bg-transparent text-[13px] text-ink placeholder:text-muted/70 focus:outline-none"
            placeholder="Search claims, policies, cases…"
          />
          <span className="hidden items-center gap-0.5 lg:flex">
            <span className="kbd">⌘</span><span className="kbd">K</span>
          </span>
        </label>
      </div>

      {/* Right cluster */}
      <div className="ml-auto flex items-center gap-1 md:ml-0">
        <span className="mr-1 hidden items-center gap-1.5 rounded-full border border-line bg-surface px-2.5 py-1 text-[11px] font-medium text-muted xl:flex">
          <span className="h-1.5 w-1.5 rounded-full bg-good" /> Operational
        </span>

        <QuickActions onNavigate={onNavigate} />
        <Notifications />
        <button className="icon-btn hidden sm:grid" title="Messages">
          <MessageSquare className="h-[18px] w-[18px]" />
          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-primary" />
        </button>
        <ThemeToggle />
        <UserMenu />
      </div>
    </header>
  );
}

function QuickActions({ onNavigate }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button onClick={() => setOpen((o) => !o)} className="btn-primary hidden h-8 px-2.5 sm:inline-flex">
        <Plus className="h-4 w-4" /> <span className="hidden lg:inline">New</span>
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full z-20 mt-1.5 w-52 animate-scale-in rounded-lg border border-line bg-surface p-1.5 shadow-pop">
            <MenuItem icon={FilePlus2} label="New investigation" onClick={() => { setOpen(false); onNavigate("submit"); }} />
            <MenuItem icon={ShieldCheck} label="Add policy" onClick={() => { setOpen(false); onNavigate("policy"); }} />
            <MenuItem icon={FileSearch} label="Open a report" onClick={() => { setOpen(false); onNavigate("report"); }} />
          </div>
        </>
      )}
    </div>
  );
}

function Notifications() {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button onClick={() => setOpen((o) => !o)} className="icon-btn" title="Notifications">
        <Bell className="h-[18px] w-[18px]" />
        <span className="absolute right-1 top-1 grid h-3.5 min-w-[14px] place-items-center rounded-full bg-bad px-0.5 text-[9px] font-bold text-white">3</span>
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full z-20 mt-1.5 w-80 animate-scale-in overflow-hidden rounded-lg border border-line bg-surface shadow-pop">
            <div className="flex items-center justify-between border-b border-line px-3 py-2.5">
              <span className="text-[13px] font-semibold text-ink">Notifications</span>
              <span className="pill" style={{ color: "rgb(var(--c-bad))", background: "rgb(var(--c-bad) / .12)" }}>3 new</span>
            </div>
            <ul className="max-h-80 overflow-y-auto">
              {NOTICES.map((n, i) => (
                <li key={i} className="flex items-start gap-2.5 border-b border-line px-3 py-2.5 last:border-0 hover:bg-surface-2">
                  <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: n.tone }} />
                  <div className="min-w-0">
                    <div className="text-[13px] font-medium text-ink">{n.title}</div>
                    <div className="text-[11px] text-muted">{n.meta}</div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </div>
  );
}

function UserMenu() {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button onClick={() => setOpen((o) => !o)}
              className="ml-1 grid h-8 w-8 place-items-center rounded-full bg-primary/15 text-[11px] font-bold text-primary ring-1 ring-line transition hover:ring-primary/40">
        KA
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full z-20 mt-1.5 w-60 animate-scale-in rounded-lg border border-line bg-surface p-1.5 shadow-pop">
            <div className="flex items-center gap-2.5 rounded-md px-2 py-2">
              <span className="grid h-9 w-9 place-items-center rounded-full bg-primary/15 text-[12px] font-bold text-primary">KA</span>
              <div className="min-w-0">
                <div className="truncate text-[13px] font-semibold text-ink">Kasaam Ali</div>
                <div className="truncate text-[11px] text-muted">investigator@insurcalim.ai</div>
              </div>
            </div>
            <div className="my-1 h-px bg-line" />
            <div className="flex items-center justify-between rounded-md px-2 py-1.5 text-[13px] text-ink-soft">
              <span>Appearance</span><ThemeToggle />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function MenuItem({ icon: Icon, label, onClick }) {
  return (
    <button onClick={onClick}
            className="flex w-full items-center gap-2.5 rounded-md px-2 py-1.5 text-[13px] text-ink-soft transition-colors hover:bg-surface-2 hover:text-ink">
      <Icon className="h-4 w-4 text-muted" /> {label}
    </button>
  );
}
