import { useRef, useState } from "react";
import { AnimatePresence } from "framer-motion";
import { ShieldAlert } from "lucide-react";
import { captureToken, clearToken, LANDING_URL } from "./api.js";
import IntroSequence from "./components/IntroSequence.jsx";
import AppShell from "./components/AppShell.jsx";
import OverviewSection from "./sections/OverviewSection.jsx";
import QueueSection from "./sections/QueueSection.jsx";
import AnalyticsSection from "./sections/AnalyticsSection.jsx";
import RingsSection from "./sections/RingsSection.jsx";
import SubmitSection from "./sections/SubmitSection.jsx";
import ReportSection from "./sections/ReportSection.jsx";
import ClaimantSection from "./sections/ClaimantSection.jsx";
import PolicySection from "./sections/PolicySection.jsx";
import ModelSection from "./sections/ModelSection.jsx";
import GuideSection from "./sections/GuideSection.jsx";

export default function App() {
  const [token] = useState(() => captureToken());
  const [intro, setIntro] = useState(true);
  const [section, setSection] = useState("overview");
  const [reportClaimId, setReportClaimId] = useState(null);
  const [lastResult, setLastResult] = useState(null);
  const [movedClaim, setMovedClaim] = useState(null); // live submit result handed to the investigator desk

  // Keep-alive: a section is mounted on first visit and then kept mounted (just
  // hidden) so in-progress work uploaded files, a running investigation, a
  // rendered report, case notes survives navigating away and back.
  const visited = useRef(new Set([section]));
  visited.current.add(section);

  // The IntroSequence drives its own timing and calls onDone when finished.

  function navigate(id) {
    setSection(id);
  }
  function openClaim(id) {
    setMovedClaim(null);
    setReportClaimId(id);
    setSection("report");
  }
  // "Move to investigator" from the submit-flow report: carry the live claim
  // into the Investigation report section (deep analysis + case handling).
  function moveToInvestigator(result, jobId) {
    setReportClaimId(null);
    setMovedClaim({ result, jobId });
    setSection("report");
  }
  function logout() {
    clearToken();
    window.location.href = LANDING_URL;
  }

  if (!token) return <Unauthorized />;

  return (
    <>
      <AnimatePresence>{intro && <IntroSequence key="intro" onDone={() => setIntro(false)} />}</AnimatePresence>
      <AppShell active={section} onNavigate={navigate} onLogout={logout}>
        {[...visited.current].map((id) => (
          <div key={id} hidden={id !== section} className={id === section ? "animate-fade-in" : undefined}>
            {renderSection(id, {
              openClaim, navigate, moveToInvestigator, setLastResult, setMovedClaim, setSection,
              reportClaimId, movedClaim, lastResult,
            })}
          </div>
        ))}
      </AppShell>
    </>
  );
}

// Render a section by id with the shared handlers/state. Kept out of the
// component body so the keep-alive map stays tidy.
function renderSection(id, ctx) {
  const {
    openClaim, navigate, moveToInvestigator, setLastResult, setMovedClaim, setSection,
    reportClaimId, movedClaim, lastResult,
  } = ctx;
  switch (id) {
    case "overview": return <OverviewSection onOpenClaim={openClaim} onNavigate={navigate} />;
    case "queue": return <QueueSection onOpenClaim={openClaim} />;
    case "analytics": return <AnalyticsSection />;
    case "rings": return <RingsSection onOpenClaim={openClaim} />;
    case "submit": return <SubmitSection onResult={(r) => setLastResult(r)} onMove={moveToInvestigator} />;
    case "report": return (
      <ReportSection initialClaimId={reportClaimId} moved={movedClaim} onClearMoved={() => setMovedClaim(null)} />
    );
    case "claimant": return <ClaimantSection result={lastResult} onGoSubmit={() => setSection("submit")} />;
    case "policy": return <PolicySection />;
    case "model": return <ModelSection />;
    case "guide": return <GuideSection onNavigate={navigate} />;
    default: return null;
  }
}

function Unauthorized() {
  return (
    <div className="grid min-h-dvh place-items-center bg-bg px-6">
      <div className="card max-w-md p-8 text-center">
        <ShieldAlert className="mx-auto h-10 w-10 text-warn" />
        <h1 className="mt-4 text-xl font-bold">Sign in required</h1>
        <p className="mt-2 text-sm text-muted">
          Open the dashboard from the InsurCalim sign-in page so it can hand off a secure session token.
        </p>
        <a className="btn-primary mx-auto mt-6" href={LANDING_URL}>Go to sign-in</a>
      </div>
    </div>
  );
}
