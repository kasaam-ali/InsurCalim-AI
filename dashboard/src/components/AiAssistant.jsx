import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, Send, X, Loader2 } from "lucide-react";
import { askAssistant } from "../api.js";

const SUGGESTED = [
  "What are the top fraud patterns in this portfolio?",
  "How is the risk score calculated?",
  "What should I check first on a high-risk claim?",
  "Explain the fair-cost estimate.",
];

// Right-side AI assistant drawer. Chats about the portfolio / current claim via
// the existing LLM (POST /api/chat). Restrained "InsightAI"-style header orb.
export default function AiAssistant({ open, onClose, context = "" }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  async function send(text) {
    const q = (text ?? input).trim();
    if (!q || busy) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setBusy(true);
    try {
      const { answer } = await askAssistant(q, context);
      setMessages((m) => [...m, { role: "assistant", text: answer }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", text: `Sorry ${e.message}` }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div className="fixed inset-0 z-40 bg-black/40" initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose} />
          <motion.aside
            className="fixed inset-y-0 right-0 z-50 flex w-[min(92vw,380px)] flex-col border-l border-line bg-surface"
            initial={{ x: "100%" }} animate={{ x: 0 }} exit={{ x: "100%" }}
            transition={{ type: "spring", stiffness: 300, damping: 32 }}
          >
            {/* Header */}
            <div className="flex items-center gap-3 border-b border-line px-4 py-3.5">
              <span className="relative grid h-9 w-9 place-items-center rounded-full bg-grad-violet shadow-glow-violet">
                <span className="absolute inset-0 animate-spin-slow rounded-full opacity-60"
                      style={{ background: "conic-gradient(from 0deg,#8b5cf6,#22d3ee,#3b82f6,#8b5cf6)", mask: "radial-gradient(circle, transparent 55%, black 57%)", WebkitMask: "radial-gradient(circle, transparent 55%, black 57%)" }} />
                <Sparkles className="relative h-4 w-4 text-white" />
              </span>
              <div className="leading-tight">
                <div className="text-sm font-semibold">InsurCalim Assistant</div>
                <div className="text-[11px] text-muted">AI investigator analyst</div>
              </div>
              <button className="btn-subtle ml-auto" onClick={onClose} aria-label="Close assistant">
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Body */}
            <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
              {messages.length === 0 && (
                <div>
                  <div className="rounded-lg border border-line bg-bg p-3 text-sm text-ink-soft">
                    Hi 👋 I can explain flags, risk scores and the fair-cost estimate, or suggest what to
                    check next. Ask me anything about this portfolio.
                  </div>
                  <div className="mt-3 text-xs font-medium uppercase tracking-wide text-muted">Suggested</div>
                  <div className="mt-2 space-y-2">
                    {SUGGESTED.map((q) => (
                      <button key={q} onClick={() => send(q)}
                              className="w-full rounded-lg border border-line bg-bg px-3 py-2 text-left text-sm text-ink-soft transition hover:border-primary/50 hover:text-ink">
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((m, i) => (
                <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-3.5 py-2.5 text-sm ${
                    m.role === "user" ? "bg-primary text-white" : "border border-line bg-bg text-ink-soft"
                  }`}>
                    {m.text}
                  </div>
                </div>
              ))}
              {busy && (
                <div className="flex items-center gap-2 text-sm text-muted">
                  <Loader2 className="h-4 w-4 animate-spin" /> Thinking…
                </div>
              )}
              <div ref={endRef} />
            </div>

            {/* Input */}
            <div className="border-t border-line p-3">
              <div className="flex items-end gap-2">
                <textarea
                  rows={1}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      send();
                    }
                  }}
                  placeholder="Type your message…"
                  className="field max-h-32 resize-none"
                />
                <button className="btn-primary !px-3" disabled={busy || !input.trim()} onClick={() => send()}>
                  <Send className="h-4 w-4" />
                </button>
              </div>
              <div className="mt-2 text-center text-[10px] text-muted">Powered by InsurCalim AI</div>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
