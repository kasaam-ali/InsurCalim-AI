import Reveal from "./Reveal.jsx";

const STATS = [
  { num: "$80B+", lbl: "Fraud drained / year", cap: "across insurance, globally (2025)" },
  { num: "~10%", lbl: "Claims with fraud", cap: "of property & casualty losses" },
  { num: "25–30%", lbl: "AI-faked media", cap: "share of manipulated claim evidence" },
  { num: "~$0.02", lbl: "Cost per claim", cap: "on the balanced model tier" },
];

export default function Stats() {
  return (
    <section className="section" id="why" style={{ paddingTop: 0 }}>
      <div className="wrap">
        <Reveal className="section-head">
          <span className="eyebrow"><span className="dot" /> Why it matters</span>
          <h2>Claims fraud is a multi-billion-dollar problem.</h2>
          <p>
            Manual review can't keep pace, and AI-generated evidence is rising fast. InsurClaim AI
            triages the queue so investigators spend their time where it counts.
          </p>
        </Reveal>
        <div className="stats">
          {STATS.map((s, i) => (
            <Reveal key={s.lbl} delay={i * 80}>
              <div className="stat">
                <div className="num gradient-text">{s.num}</div>
                <div className="lbl">{s.lbl}</div>
                <div className="cap">{s.cap}</div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
