import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
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

export default function App() {
  const [token] = useState(() => captureToken());
  const [intro, setIntro] = useState(true);
  const [section, setSection] = useState("overview");
  const [reportClaimId, setReportClaimId] = useState(null);
  const [lastResult, setLastResult] = useState(null);
  const [movedClaim, setMovedClaim] = useState(null); // live submit result handed to the investigator desk

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
        <AnimatePresence mode="wait">
          <motion.div
            key={section === "report" ? `report:${movedClaim ? `moved:${movedClaim.jobId}` : reportClaimId}` : section}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
          >
            {section === "overview" && <OverviewSection />}
            {section === "queue" && <QueueSection onOpenClaim={openClaim} />}
            {section === "analytics" && <AnalyticsSection />}
            {section === "rings" && <RingsSection onOpenClaim={openClaim} />}
            {section === "submit" && (
              <SubmitSection onResult={(r) => setLastResult(r)} onMove={moveToInvestigator} />
            )}
            {section === "report" && (
              <ReportSection
                initialClaimId={reportClaimId}
                moved={movedClaim}
                onClearMoved={() => setMovedClaim(null)}
              />
            )}
            {section === "claimant" && (
              <ClaimantSection result={lastResult} onGoSubmit={() => setSection("submit")} />
            )}
            {section === "policy" && <PolicySection />}
            {section === "model" && <ModelSection />}
          </motion.div>
        </AnimatePresence>
      </AppShell>
    </>
  );
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
