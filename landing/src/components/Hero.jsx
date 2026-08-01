import LoginCard from "./LoginCard.jsx";

// Hero video asset (downloaded into public/assets). If it is missing, the
// <video> simply shows its poster / the CSS gradient behind it, so the hero
// still looks premium offline.
const HERO_VIDEO = "/assets/hero-cars.mp4";
const HERO_POSTER = "/assets/hero-poster.svg";

export default function Hero() {
  return (
    <header className="hero">
      {/* Background: video with graceful fallback to a cinematic gradient. */}
      <div className="hero-poster" aria-hidden="true" />
      <div className="hero-video" aria-hidden="true">
        <video
          autoPlay
          muted
          loop
          playsInline
          poster={HERO_POSTER}
          preload="metadata"
        >
          <source src={HERO_VIDEO} type="video/mp4" />
        </video>
      </div>
      <div className="hero-scrim" aria-hidden="true" />

      <div className="hero-grid">
        <div>
          <span className="eyebrow rise" style={{ animationDelay: "0.05s" }}>
            <span className="dot" /> Explainable · Human-in-the-loop
          </span>

          <h1 className="rise" style={{ animationDelay: "0.15s" }}>
            Investigate every <span className="gradient-text">auto claim</span> with confidence.
          </h1>

          <p className="lede rise" style={{ animationDelay: "0.28s" }}>
            InsurClaim AI reads the documents, photos and video, reconstructs the timeline,
            flags inconsistencies and prices the damage then hands a ranked, cited report to
            a human. It flags and recommends; it never auto-denies.
          </p>

          <div className="hero-cta rise" style={{ animationDelay: "0.4s" }}>
            <a href="#signin" className="btn btn-primary">Sign in to the dashboard →</a>
            <a href="#features" className="btn btn-ghost">See how it works</a>
          </div>

          <div className="hero-trust rise" style={{ animationDelay: "0.52s" }}>
            <span><b>4</b> specialised agents</span>
            <span><b>Live</b> market-price damage estimates</span>
            <span><b>Cited</b> evidence on every flag</span>
          </div>
        </div>

        <div className="rise" style={{ animationDelay: "0.34s" }}>
          <LoginCard />
        </div>
      </div>
    </header>
  );
}
