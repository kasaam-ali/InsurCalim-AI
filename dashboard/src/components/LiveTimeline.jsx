import { Check, Loader2, Search } from "lucide-react";
import { Card } from "./ui.jsx";

// Live step feed for a running investigation (light theme). Replaces Streamlit's
// st.status panel; each arrived step lights up, the newest one spins.
export default function LiveTimeline({ steps = [], done = false }) {
  return (
    <div className="mx-auto max-w-2xl animate-fade-up">
      <Card>
        <div className="mb-5 flex items-center gap-3">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-primary-soft text-primary">
            {done ? <Check className="h-5 w-5 text-good" /> : <Search className="h-5 w-5" />}
          </span>
          <div>
            <div className="font-semibold">{done ? "Investigation complete" : "Investigating the claim…"}</div>
            <div className="text-xs text-muted">
              {done ? "Compiling the report below." : "Watch each step as the system works."}
            </div>
          </div>
        </div>

        <ol className="space-y-1">
          {steps.map((s, i) => {
            const active = i === steps.length - 1 && !done;
            return (
              <li key={i} className="flex items-start gap-3 py-1.5 animate-fade-up">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center">
                  {active ? <Loader2 className="h-4 w-4 animate-spin text-primary" /> : <Check className="h-4 w-4 text-good" />}
                </span>
                <span className={active ? "text-ink" : "text-muted"}>{s.message}</span>
              </li>
            );
          })}
          {steps.length === 0 && (
            <li className="flex items-center gap-3 py-1.5 text-muted">
              <Loader2 className="h-4 w-4 animate-spin text-primary" /> Starting…
            </li>
          )}
        </ol>
      </Card>
    </div>
  );
}
