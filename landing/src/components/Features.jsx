import { useTilt } from "../hooks/useTilt.js";
import Reveal from "./Reveal.jsx";

const FEATURES = [
  {
    icon: "🕵️",
    title: "Fraud & inconsistency detection",
    body:
      "A narrative agent cross-checks the story against every document and photo, surfacing the exact contradictions dates that don't line up, damage that doesn't match the report.",
  },
  {
    icon: "🧭",
    title: "Reconstructed event timeline",
    body:
      "The incident is rebuilt into an ordered sequence with the facts behind each step, so gaps and impossible orderings become obvious at a glance.",
  },
  {
    icon: "💸",
    title: "Live market-price amount check",
    body:
      "The amount agent searches real parts and repair prices on the web, builds a line-item estimate and tells you whether the demanded figure is reasonable or overstated.",
  },
  {
    icon: "🔍",
    title: "Explainable, cited decisions",
    body:
      "Every risk score, flag and recommendation carries its evidence and a citation. Nothing is a black box an adjuster can defend each call.",
  },
];

function FeatureCard({ f, i }) {
  const { ref, onMove, onLeave } = useTilt();
  return (
    <Reveal className="tilt" delay={i * 90}>
      <article
        ref={ref}
        className="feature"
        onMouseMove={onMove}
        onMouseLeave={onLeave}
      >
        <span className="glow" aria-hidden="true" />
        <div className="icon">{f.icon}</div>
        <h3>{f.title}</h3>
        <p>{f.body}</p>
      </article>
    </Reveal>
  );
}

export default function Features() {
  return (
    <section className="section" id="features">
      <div className="wrap">
        <Reveal className="section-head">
          <span className="eyebrow"><span className="dot" /> What it does</span>
          <h2>Four agents, one investigator report.</h2>
          <p>
            Each agent handles one part of the investigation and writes to a shared case file.
            The result is a single ranked, explainable report not a black-box score.
          </p>
        </Reveal>
        <div className="features">
          {FEATURES.map((f, i) => (
            <FeatureCard key={f.title} f={f} i={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
