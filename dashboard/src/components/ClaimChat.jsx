import { useState } from "react";
import { Send, Sparkles } from "lucide-react";
import { askAssistant } from "../api.js";

// Suggested starter questions a non-technical user might ask about a claim.
const SUGGESTED = [
  "Why is this claim risky?",
  "What should I check next?",
  "Is the amount being claimed fair?",
  "What does the recommendation mean?",
];

// Inline, per-claim Q&A. The user can ask anything about THIS claim and gets a
// plain-English answer; the report's key facts are passed along as context so
// the answer stays specific to this claim.
export default function ClaimChat({ context }) {
  const [msgs, setMsgs] = useState([]);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);

  async function ask(question) {
    const text = (question ?? q).trim();
    if (!text || busy) return;
    setQ("");
    setMsgs((m) => [...m, { role: "user", text }]);
    setBusy(true);
    try {
      const { answer } = await askAssistant(text, context);
      setMsgs((m) => [...m, { role: "bot", text: answer || "No answer was returned." }]);
    } catch (_) {
      setMsgs((m) => [...m, { role: "bot", text: "The assistant is unavailable right now please try again." }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="overflow-hidden rounded-xl border border-line bg-surface">
      <div className="flex items-center gap-2.5 border-b border-line px-4 py-3">
        <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary-soft text-primary">
          <Sparkles className="h-4 w-4" />
        </span>
        <div>
          <div className="text-sm font-semibold text-ink">Ask about this claim</div>
          <div className="text-xs text-muted">Not sure about something? Ask a question and get a plain-English answer.</div>
        </div>
      </div>

      <div className="px-4 py-4">
        {msgs.length === 0 ? (
          <div className="flex flex-wrap gap-2">
            {SUGGESTED.map((s) => (
              <button key={s} onClick={() => ask(s)}
                      className="rounded-full border border-line px-3 py-1.5 text-xs text-ink-soft transition hover:border-primary/40 hover:text-ink">
                {s}
              </button>
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {msgs.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-3.5 py-2 text-sm leading-relaxed ${
                  m.role === "user" ? "bg-primary text-white" : "border border-line bg-bg text-ink-soft"
                }`}>
                  {m.text}
                </div>
              </div>
            ))}
            {busy && <div className="text-xs text-muted">Thinking…</div>}
          </div>
        )}

        <div className="mt-4 flex gap-2">
          <input className="field" value={q} onChange={(e) => setQ(e.target.value)}
                 placeholder="Ask anything about this claim…"
                 onKeyDown={(e) => e.key === "Enter" && ask()} />
          <button className="btn-primary" onClick={() => ask()} disabled={busy}>
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
