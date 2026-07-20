import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown } from "lucide-react";

// A professional, button-style collapsible section: an icon tile, a title +
// subtitle, an optional badge, and a chevron. Hovering highlights it; clicking
// reveals the detail with a smooth height animation. Shared by the report views.
export default function Disclosure({ title, subtitle, icon: Icon, badge, defaultOpen = false, children }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="overflow-hidden rounded-xl border border-line bg-surface transition hover:border-primary/40">
      <button onClick={() => setOpen((o) => !o)}
              className="flex w-full items-center gap-3 px-4 py-3.5 text-left transition hover:bg-surface-2">
        {Icon && (
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-primary-soft text-primary">
            <Icon className="h-4 w-4" />
          </span>
        )}
        <span className="min-w-0 flex-1">
          <span className="block text-sm font-semibold text-ink">{title}</span>
          {subtitle && <span className="block truncate text-xs text-muted">{subtitle}</span>}
        </span>
        {badge}
        <ChevronDown className={`h-4 w-4 shrink-0 text-muted transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div key="body" initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}>
            <div className="border-t border-line px-4 py-4">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
