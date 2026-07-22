import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import {
  MousePointerClick, UploadCloud, Bot, FileSearch, UserCheck, ArrowRight,
  LayoutDashboard, Inbox, TrendingUp, Network, FilePlus2, IdCard, ShieldCheck,
  Cpu, Eye, Layers, MessageSquare, FlaskConical, Rocket, ListChecks,
  Play, PlayCircle, X,
} from "lucide-react";
import { SectionHeader, Panel, Card, RiskPill } from "../components/ui.jsx";
import { BAND_COLORS } from "../lib/chartTheme.js";

// Demo video shown in the popup. Paste your link here (YouTube, Vimeo, or a
// direct .mp4 URL). Leave it empty to show a friendly placeholder instead.
const DEMO_VIDEO_URL = "";

// Normalise common share links into an embeddable player URL.
function toEmbed(url) {
  if (!url) return "";
  const yt = url.match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/))([\w-]{6,})/);
  if (yt) return `https://www.youtube.com/embed/${yt[1]}`;
  const vm = url.match(/vimeo\.com\/(?:video\/)?(\d+)/);
  if (vm) return `https://player.vimeo.com/video/${vm[1]}`;
  return url;
}

const IS_EMBED = /youtu\.?be|youtube\.com|vimeo\.com/.test(DEMO_VIDEO_URL);

// A centered popup that plays the product demo video.
function DemoModal({ open, onClose }) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  // Rendered into document.body so the fixed overlay is relative to the viewport
  // (ancestors here use transforms, which would otherwise trap position: fixed).
  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
         onClick={onClose}>
      <div className="w-full max-w-3xl overflow-hidden rounded-xl border border-line bg-surface shadow-pop animate-scale-in"
           onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-line px-4 py-3">
          <h3 className="text-[13px] font-semibold text-ink">InsurCalim AI product demo</h3>
          <button onClick={onClose} className="icon-btn" title="Close"><X className="h-[18px] w-[18px]" /></button>
        </div>
        <div className="aspect-video w-full bg-black">
          {DEMO_VIDEO_URL ? (
            IS_EMBED ? (
              <iframe src={toEmbed(DEMO_VIDEO_URL)} title="Product demo" className="h-full w-full"
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen />
            ) : (
              <video src={DEMO_VIDEO_URL} controls className="h-full w-full" />
            )
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-2 px-6 text-center text-white/70">
              <PlayCircle className="h-10 w-10" />
              <p className="text-sm font-medium text-white/90">Demo video link not added yet</p>
              <p className="text-xs">Paste your video URL into DEMO_VIDEO_URL near the top of GuideSection.jsx (YouTube, Vimeo, or a direct .mp4 link).</p>
            </div>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}

// A plain, friendly "how to use it" guide for a first-time user. It leads with a
// step-by-step walkthrough, then explains what each part is for in everyday
// language. Kept light on jargon on purpose.

const STEPS = [
  { n: "1", Icon: MousePointerClick, h: "Open New investigation", p: "In the left menu, under Investigate, click New investigation. Every case starts here." },
  { n: "2", Icon: UploadCloud, h: "Add the claim", p: "Upload the claimant's files: the claim form, police report, damage photos, even a video. Drag and drop or browse." },
  { n: "3", Icon: Bot, h: "Let the AI work", p: "Click Investigate and watch the live timeline. The AI reads everything and builds the case for you in about a minute." },
  { n: "4", Icon: FileSearch, h: "Read the result", p: "You get a risk score from 0 to 100 and a short list of what looked off, each one with the evidence behind it." },
  { n: "5", Icon: UserCheck, h: "Decide and record", p: "Open the full report, ask the built-in chat any question, add your notes, and make the call. The app never decides for you." },
];

const BANDS = [
  { key: "HIGH", range: "60 to 100", plain: "Likely fraud. Send it to an investigator for a full review." },
  { key: "MEDIUM", range: "30 to 59", plain: "Not sure yet. Ask the claimant for the missing document or detail." },
  { key: "LOW", range: "0 to 29", plain: "Looks fine. Safe to approve quickly. It is still logged for the record." },
];

const SECTIONS = [
  { id: "overview", Icon: LayoutDashboard, label: "Command center", desc: "Your home screen. The big numbers and the riskiest claims, the moment you log in." },
  { id: "queue", Icon: Inbox, label: "Investigation queue", desc: "The full list of claims. Sort or search, then click any row to open it." },
  { id: "submit", Icon: FilePlus2, label: "New investigation", desc: "Start here. Upload a new claim and watch it get analyzed live." },
  { id: "report", Icon: FileSearch, label: "Investigation report", desc: "The full write-up for one claim. Read the score and flags, add notes, and decide." },
  { id: "claimant", Icon: IdCard, label: "Claimant profile", desc: "A simple profile of the person: their summary, who was involved, and which documents are in." },
  { id: "rings", Icon: Network, label: "Fraud rings", desc: "Shows claims that are secretly connected, which is how organized fraud usually hides." },
  { id: "analytics", Icon: TrendingUp, label: "Fraud analytics", desc: "Charts of the trends: how many claims, what kinds of fraud, and how much money is at risk." },
  { id: "policy", Icon: ShieldCheck, label: "Policies & coverage", desc: "Add your policy rules, then check whether a claim is actually covered." },
  { id: "model", Icon: Cpu, label: "Model health", desc: "For the curious: how well the AI performs. You do not need this to do your job." },
];

const TIPS = [
  { Icon: ShieldCheck, tone: "#22C55E", h: "It never decides for you", p: "The app ranks and explains. A human always makes the final approve or deny call." },
  { Icon: Eye, tone: "#3B82F6", h: "Every flag shows its proof", p: "Open any red flag to see the exact evidence, so you can trust it or overrule it." },
  { Icon: Layers, tone: "#7C3AED", h: "It checks fraud many ways", p: "Simple rules, repeated-photo checks, past similar claims, and an AI that reads the whole story." },
  { Icon: MessageSquare, tone: "#0EA5E9", h: "You can ask it questions", p: "Every report has a chat. Ask things like 'why is this high risk?' in plain English." },
  { Icon: FlaskConical, tone: "#D97706", h: "Safe demo data", p: "All claims here are made-up samples. No real customer information is used anywhere." },
];

/* -------------------------------------------------------------------------- */

function IconChip({ Icon, tone }) {
  return (
    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-md"
          style={{ background: `${tone}1a`, color: tone }}>
      <Icon className="h-[18px] w-[18px]" />
    </span>
  );
}

export default function GuideSection({ onNavigate }) {
  const [showDemo, setShowDemo] = useState(false);

  return (
    <div className="animate-fade-up">
      <SectionHeader
        eyebrow="Getting started"
        title="How to use InsurCalim AI"
        subtitle="New here? Just follow the steps below. It is simpler than it looks, and the app never makes a decision for you."
        actions={
          <button className="btn-primary" onClick={() => setShowDemo(true)}>
            <Play className="h-4 w-4" /> Watch the demo
          </button>
        }
      />

      <DemoModal open={showDemo} onClose={() => setShowDemo(false)} />

      {/* 1. Use it in 5 steps ---------------------------------------------- */}
      <Panel title="Use it in 5 simple steps" subtitle="From a new claim to a decision" icon={Rocket}>
        <ol className="space-y-3">
          {STEPS.map((s) => (
            <li key={s.n} className="flex items-start gap-3.5 rounded-lg border border-line bg-surface-2 p-3.5">
              <span className="tnum grid h-8 w-8 shrink-0 place-items-center rounded-full bg-primary/12 text-sm font-bold text-primary">
                {s.n}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <s.Icon className="h-4 w-4 text-muted" />
                  <h4 className="text-[13px] font-semibold text-ink">{s.h}</h4>
                </div>
                <p className="mt-1 text-xs leading-relaxed text-muted">{s.p}</p>
              </div>
            </li>
          ))}
        </ol>
        <div className="mt-4 flex flex-wrap gap-2">
          <button className="btn-primary" onClick={() => onNavigate?.("submit")}>
            <ArrowRight className="h-4 w-4" /> Try step 1 now
          </button>
          <button className="btn-ghost" onClick={() => onNavigate?.("overview")}>
            <LayoutDashboard className="h-4 w-4" /> Go to Command center
          </button>
        </div>
      </Panel>

      {/* 2. What each part is for ------------------------------------------ */}
      <Panel className="mt-4" title="What each part is for" subtitle="Click any row to open that screen" icon={ListChecks}>
        <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
          {SECTIONS.map((s) => (
            <button
              key={s.id}
              onClick={() => onNavigate?.(s.id)}
              className="group flex items-start gap-3 rounded-md border border-line bg-surface-2 px-3 py-2.5 text-left transition-colors hover:border-primary/30 hover:bg-surface"
            >
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-md bg-primary/10 text-primary">
                <s.Icon className="h-4 w-4" />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <span className="text-[13px] font-semibold text-ink">{s.label}</span>
                  <ArrowRight className="h-3.5 w-3.5 text-muted opacity-0 transition-opacity group-hover:opacity-100" />
                </div>
                <p className="mt-0.5 text-xs leading-relaxed text-muted">{s.desc}</p>
              </div>
            </button>
          ))}
        </div>
      </Panel>

      {/* 3. What the risk score means -------------------------------------- */}
      <Panel className="mt-4" title="What the risk score means" subtitle="Every claim gets a number from 0 to 100" icon={TrendingUp}>
        <div className="flex h-2.5 overflow-hidden rounded-full">
          <div style={{ width: "30%", background: BAND_COLORS.LOW }} />
          <div style={{ width: "30%", background: BAND_COLORS.MEDIUM }} />
          <div style={{ width: "40%", background: BAND_COLORS.HIGH }} />
        </div>
        <div className="tnum mt-1.5 flex justify-between text-[10px] text-muted">
          <span>0</span><span>30</span><span>60</span><span>100</span>
        </div>

        <div className="mt-4 space-y-2.5">
          {BANDS.map((b) => (
            <div key={b.key} className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-md border border-line bg-surface-2 px-3 py-2.5">
              <span className="w-24 shrink-0"><RiskPill band={b.key} /></span>
              <span className="tnum w-20 shrink-0 text-xs text-muted">{b.range}</span>
              <span className="text-[13px] text-ink-soft sm:flex-1">{b.plain}</span>
            </div>
          ))}
        </div>
        <p className="mt-3 text-xs text-muted">Simple rule: the higher the number, the more you should look closely.</p>
      </Panel>

      {/* 4. Good to know --------------------------------------------------- */}
      <Panel className="mt-4" title="Good to know" subtitle="A few friendly things that make it easier to trust" icon={MessageSquare}>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {TIPS.map((t) => (
            <div key={t.h} className="rounded-lg border border-line bg-surface-2 p-3.5">
              <div className="flex items-center gap-2.5">
                <IconChip Icon={t.Icon} tone={t.tone} />
                <h4 className="text-[13px] font-semibold text-ink">{t.h}</h4>
              </div>
              <p className="mt-2 text-xs leading-relaxed text-muted">{t.p}</p>
            </div>
          ))}
        </div>
      </Panel>

      {/* 5. Try it --------------------------------------------------------- */}
      <Card className="mt-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <IconChip Icon={Rocket} tone="#2563EB" />
            <div>
              <h3 className="text-[13px] font-semibold text-ink">That is all you need to start.</h3>
              <p className="text-xs text-muted">Upload your first claim and let the AI do the heavy lifting.</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button className="btn-ghost" onClick={() => setShowDemo(true)}>
              <Play className="h-4 w-4" /> Watch the demo
            </button>
            <button className="btn-primary" onClick={() => onNavigate?.("submit")}>
              <ArrowRight className="h-4 w-4" /> Start a new investigation
            </button>
          </div>
        </div>
      </Card>
    </div>
  );
}
