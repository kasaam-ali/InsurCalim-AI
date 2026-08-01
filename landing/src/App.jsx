import { useEffect, useRef } from "react";
import Hero from "./components/Hero.jsx";
import Stats from "./components/Stats.jsx";
import Features from "./components/Features.jsx";
import Flow from "./components/Flow.jsx";
import Footer from "./components/Footer.jsx";

export default function App() {
  const spot = useRef(null);

  // A soft glow follows the cursor across the whole page (modern spotlight effect).
  useEffect(() => {
    const el = spot.current;
    if (!el) return;
    const reduce =
      window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) return;

    const onMove = (e) => {
      el.style.setProperty("--mx", `${e.clientX}px`);
      el.style.setProperty("--my", `${e.clientY}px`);
      el.classList.add("on");
    };
    const onLeave = () => el.classList.remove("on");

    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerleave", onLeave);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerleave", onLeave);
    };
  }, []);

  return (
    <>
      {/* Animated background layers sit behind all content. */}
      <div className="mesh" aria-hidden="true" />
      <div className="grain" aria-hidden="true" />
      <div className="spotlight" ref={spot} aria-hidden="true" />

      <nav className="nav">
        <div className="wrap nav-inner">
          <div className="brand">
            <span className="logo">🔎</span> InsurClaim AI
          </div>
          <div className="nav-links">
            <a href="#why">Why</a>
            <a href="#features">Features</a>
            <a href="#how">How it works</a>
            <a href="#signin">Sign in</a>
          </div>
        </div>
      </nav>

      <main>
        <Hero />
        <Stats />
        <Features />
        <Flow />
      </main>

      <Footer />
    </>
  );
}
