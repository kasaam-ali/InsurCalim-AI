import Reveal from "./Reveal.jsx";

const STEPS = [
  { n: "1", h: "Upload the case", p: "Drop in the claim documents, damage photos and video for one claimant." },
  { n: "2", h: "Agents investigate", p: "Intake, timeline, fraud and amount agents read everything and write to a shared case file." },
  { n: "3", h: "Ranked report", p: "You get a risk score, flagged inconsistencies, coverage view and a priced amount check — all cited." },
  { n: "4", h: "Human decides", p: "The adjuster reviews, asks the built-in chat follow-ups, and makes the call. Never auto-denied." },
];

export default function Flow() {
  return (
    <section className="section" id="how" style={{ paddingTop: 0 }}>
      <div className="wrap">
        <Reveal className="section-head">
          <span className="eyebrow"><span className="dot" /> How it works</span>
          <h2>From raw evidence to a defensible decision.</h2>
        </Reveal>
        <div className="flow">
          {STEPS.map((s, i) => (
            <Reveal key={s.n} className="step" delay={i * 80}>
              <div className="n">{s.n}</div>
              <h4>{s.h}</h4>
              <p>{s.p}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
