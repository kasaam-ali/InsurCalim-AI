import { useEffect, useState } from "react";
import { Check, Loader2, Search } from "lucide-react";
import { Card } from "./ui.jsx";

// How long each step spins before the next one is revealed. Keeps the feed
// paced even when the backend sends several steps at once.
const REVEAL_MS = 600;

// Live step feed for a running investigation (light theme). Replaces Streamlit's
// st.status panel. Steps are revealed one at a time: the newest spins, then turns
// into a green tick as the next one lands, so the user watches steady progress
// instead of a burst of items appearing together.
export default function LiveTimeline({ steps = [], done = false }) {
  const [shown, setShown] = useState(0);

  // Reveal one more step after a short delay whenever the backend is ahead of
  // what we have displayed. The first step shows almost immediately.
  useEffect(() => {
    if (shown >= steps.length) return;
    const delay = shown === 0 ? 150 : REVEAL_MS;
    const t = setTimeout(() => setShown((n) => Math.min(n + 1, steps.length)), delay);
    return () => clearTimeout(t);
  }, [shown, steps.length]);

  const visible = steps.slice(0, shown);
  const allShown = shown >= steps.length;
  const finished = done && allShown;

  return (
    <div className="mx-auto max-w-2xl animate-fade-up">
      <Card>
        <div className="mb-5 flex items-center gap-3">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-primary-soft text-primary">
            {finished ? <Check className="h-5 w-5 text-good" /> : <Search className="h-5 w-5" />}
          </span>
          <div>
            <div className="font-semibold">{finished ? "Investigation complete" : "Investigating the claim…"}</div>
            <div className="text-xs text-muted">
              {finished ? "Compiling the report below." : "Watch each step as the system works."}
            </div>
          </div>
        </div>

        <ol className="space-y-1">
          {visible.map((s, i) => {
            // The last revealed step spins until the next one lands (or, for the
            // final step, until the whole run is done); the rest are ticks.
            const isLast = i === visible.length - 1;
            const active = isLast && !finished;
            return (
              <li key={i} className="flex items-start gap-3 py-1.5 animate-fade-up">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center">
                  {active ? <Loader2 className="h-4 w-4 animate-spin text-primary" /> : <Check className="h-4 w-4 text-good" />}
                </span>
                <span className={active ? "text-ink" : "text-muted"}>{s.message}</span>
              </li>
            );
          })}
          {visible.length === 0 && (
            <li className="flex items-center gap-3 py-1.5 text-muted">
              <Loader2 className="h-4 w-4 animate-spin text-primary" /> Starting…
            </li>
          )}
        </ol>
      </Card>
    </div>
  );
}
