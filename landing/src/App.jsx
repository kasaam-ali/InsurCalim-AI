import Hero from "./components/Hero.jsx";
import Stats from "./components/Stats.jsx";
import Features from "./components/Features.jsx";
import Flow from "./components/Flow.jsx";
import Footer from "./components/Footer.jsx";

export default function App() {
  return (
    <>
      {/* Animated background layers sit behind all content. */}
      <div className="mesh" aria-hidden="true" />
      <div className="grain" aria-hidden="true" />

      <nav className="nav">
        <div className="wrap nav-inner">
          <div className="brand">
            <span className="logo">🔎</span> InsurCalim AI
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
