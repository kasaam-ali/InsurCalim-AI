import { useEffect, useState } from "react";
import { fetchPolicies, startInvestigation, streamInvestigation } from "../api.js";
import { ErrorNote } from "../components/ui.jsx";
import SubmitView from "../components/SubmitView.jsx";
import LiveTimeline from "../components/LiveTimeline.jsx";
import ReportView from "../components/ReportView.jsx";

// Orchestrates the flagship flow: form → live timeline → report. Lifts the final
// result up via onResult so the Claimant-overview section can reuse it.
export default function SubmitSection({ onResult, onMove }) {
  const [policies, setPolicies] = useState([]);
  const [flow, setFlow] = useState("form"); // form | investigating | report
  const [steps, setSteps] = useState([]);
  const [done, setDone] = useState(false);
  const [result, setResult] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchPolicies().then(setPolicies).catch(() => {});
  }, []);

  async function handleSubmit({ files, text, docIds }) {
    setError("");
    setSteps([]);
    setDone(false);
    setResult(null);
    setFlow("investigating");
    try {
      const id = await startInvestigation({ files, text, docIds });
      setJobId(id);
      const payload = await streamInvestigation(id, (s) => setSteps((prev) => [...prev, s]));
      setDone(true);
      setResult(payload);
      onResult?.(payload, id);
      setTimeout(() => setFlow("report"), 450);
    } catch (e) {
      setError(e.message || "Something went wrong.");
      setFlow("form");
    }
  }

  function newClaim() {
    setResult(null);
    setJobId(null);
    setSteps([]);
    setDone(false);
    setFlow("form");
  }

  return (
    <div>
      {error && <div className="mx-auto mb-4 max-w-3xl"><ErrorNote>{error}</ErrorNote></div>}
      {flow === "form" && <SubmitView policies={policies} onSubmit={handleSubmit} />}
      {flow === "investigating" && <LiveTimeline steps={steps} done={done} />}
      {flow === "report" && result && (
        <ReportView result={result} jobId={jobId} onNewClaim={newClaim} onMove={onMove} />
      )}
    </div>
  );
}
