import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

// Cinematic sign-in intro, in two acts:
//   1) a sleek sedan drives in from the right (auto-insurance context),
//   2) it drives off as the "InsurCalim AI" wordmark + logo reveal,
// then the whole thing fades into the dashboard.
const EASE = [0.16, 1, 0.3, 1];
const WORD = "InsurCalim AI";

// Drop a real car at dashboard/public/video/car.mp4 (best) or dashboard/public/
// img/car-hero.png|jpg to replace the vector fallback it is used automatically.
const CAR_VIDEO = "/video/car.mp4";
const CAR_IMAGE = "/img/car-hero.png";

export default function IntroSequence({ onDone }) {
  const [media, setMedia] = useState("svg"); // svg fallback until a real asset is found
  const [showBrand, setShowBrand] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const v = await fetch(CAR_VIDEO, { method: "HEAD" });
        if (alive && v.ok) return setMedia("video");
        const im = await fetch(CAR_IMAGE, { method: "HEAD" });
        if (alive && im.ok) return setMedia("image");
      } catch (_) {}
    })();
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    // Let the clip play, then reveal the brand ON TOP of it; fade out together.
    const t1 = setTimeout(() => setShowBrand(true), 2600);
    const t2 = setTimeout(() => onDone?.(), 6900);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [onDone]);

  const hasVideo = media === "video";

  return (
    <motion.div
      className="fixed inset-0 z-[100] overflow-hidden"
      initial={{ opacity: 1 }}
      exit={{ opacity: 0, transition: { duration: 0.6, ease: EASE } }}
      style={{
        backgroundColor: "#0B0F17",
        backgroundImage: hasVideo
          ? undefined
          : "radial-gradient(700px 320px at 50% 45%, rgba(59,130,246,.14), transparent 60%)",
      }}
    >
      {/* Full-bleed cinematic backdrop (plays the whole time) */}
      {hasVideo ? (
        <motion.div
          className="absolute inset-0"
          initial={{ opacity: 0, scale: 1.04 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1.1, ease: EASE }}
        >
          <video src={CAR_VIDEO} autoPlay muted playsInline
                 onError={() => setMedia("image")}
                 className="absolute inset-0 h-full w-full object-cover" />
          {/* Light vignette middle stays clear/bright, gentle fade at edges. */}
          <div className="pointer-events-none absolute inset-0"
               style={{ background: "linear-gradient(180deg, rgba(5,7,12,.28) 0%, transparent 18%, transparent 80%, rgba(5,7,12,.42) 100%)" }} />
          {/* When the brand takes over, blur + darken the clip and wash it in the
              InsurCalim navy/blue so the wordmark reads on a deeper, branded backdrop. */}
          <motion.div className="pointer-events-none absolute inset-0 backdrop-blur-[3px]"
                      initial={{ opacity: 0 }} animate={{ opacity: showBrand ? 1 : 0 }}
                      transition={{ duration: 0.8, ease: EASE }}
                      style={{
                        background:
                          "radial-gradient(680px 340px at 50% 48%, rgba(59,130,246,.22), transparent 62%)," +
                          "linear-gradient(180deg, rgba(11,15,23,.68), rgba(15,23,42,.78))",
                      }} />
        </motion.div>
      ) : (
        <FallbackCar media={media} onFail={() => setMedia("svg")} showBrand={showBrand} />
      )}

      {/* Caption while the clip plays alone; hides once the brand takes over. */}
      {hasVideo && (
        <AnimatePresence>
          {!showBrand && (
            <motion.div key="cap"
                        className="absolute inset-x-0 bottom-10 text-center text-xs tracking-[0.3em] text-white/85"
                        initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, transition: { duration: 0.4 } }}
                        transition={{ delay: 0.7, duration: 0.6 }}
                        style={{ textShadow: "0 2px 12px rgba(0,0,0,.6)" }}>
              AUTO-INSURANCE INTELLIGENCE
            </motion.div>
          )}
        </AnimatePresence>
      )}

      {/* Brand animation overlaid on top of the still-playing video */}
      <AnimatePresence>
        {showBrand && (
          <motion.div key="brand" className="absolute inset-0 grid place-items-center"
                      initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                      exit={{ opacity: 0, transition: { duration: 0.4 } }}
                      transition={{ duration: 0.5 }}>
            <BrandOverlay />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// Vector / image fallback path (only used when no real video is present).
function FallbackCar({ media, onFail, showBrand }) {
  return (
    <div className="absolute inset-0 grid place-items-center">
      {!showBrand && (
        <div className="relative w-[min(84vw,760px)]">
          {[0, 1, 2].map((i) => (
            <motion.span
              key={i}
              className="absolute rounded-full"
              style={{ height: 2, background: "linear-gradient(90deg, transparent, #3b82f6)", top: 34 + i * 20, right: 0 }}
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: [0, 160, 0], opacity: [0, 0.8, 0] }}
              transition={{ duration: 0.8, delay: 0.1 + i * 0.08, ease: "easeOut" }}
            />
          ))}
          <motion.div initial={{ x: 420, opacity: 0 }} animate={{ x: 0, opacity: 1 }}
                      transition={{ duration: 1.1, ease: EASE }}>
            {media === "image" ? (
              <img src={CAR_IMAGE} alt="" onError={onFail}
                   className="w-full rounded-xl drop-shadow-2xl" />
            ) : (
              <CarSilhouette />
            )}
          </motion.div>
        </div>
      )}
    </div>
  );
}

function BrandOverlay() {
  return (
    <div className="flex flex-col items-center gap-6">
      <motion.svg viewBox="0 0 64 64" className="h-16 w-16 drop-shadow-[0_2px_16px_rgba(0,0,0,.6)]" fill="none"
                  initial={{ opacity: 0, scale: 0.6 }} animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.6, ease: EASE, delay: 0.15 }}>
        <motion.circle cx="27" cy="27" r="17" stroke="#60A5FA" strokeWidth="4" strokeLinecap="round"
                       initial={{ pathLength: 0 }} animate={{ pathLength: 1 }}
                       transition={{ duration: 0.7, ease: "easeInOut", delay: 0.2 }} />
        <motion.line x1="39" y1="39" x2="52" y2="52" stroke="#8B5CF6" strokeWidth="4" strokeLinecap="round"
                     initial={{ pathLength: 0 }} animate={{ pathLength: 1 }}
                     transition={{ duration: 0.4, ease: "easeInOut", delay: 0.75 }} />
      </motion.svg>

      {/* Each letter pops in one-by-one, then the full wordmark stands complete. */}
      <div className="flex items-end" style={{ filter: "drop-shadow(0 2px 14px rgba(0,0,0,.6))" }}>
        {WORD.split("").map((ch, i) => (
          <motion.span key={i} className="text-3xl font-bold tracking-tight text-white sm:text-5xl"
                       initial={{ opacity: 0, y: 18, scale: 0.7 }}
                       animate={{ opacity: 1, y: 0, scale: 1 }}
                       transition={{ duration: 0.32, ease: EASE, delay: 0.3 + i * 0.13 }}
                       style={{ whiteSpace: "pre" }}>
            {ch}
          </motion.span>
        ))}
      </div>

      <motion.span className="h-[2px] rounded-full bg-primary"
                   initial={{ width: 0, opacity: 0 }} animate={{ width: 180, opacity: 1 }}
                   transition={{ duration: 0.7, ease: EASE, delay: 2.15 }} />
      <motion.div className="text-xs tracking-[0.2em] text-white/70"
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5, delay: 2.45 }}>
        INVESTIGATOR DASHBOARD
      </motion.div>
    </div>
  );
}

// A stylised metallic sedan (side profile) with spinning alloy wheels + headlight glow.
function CarSilhouette() {
  return (
    <svg viewBox="0 0 300 130" className="w-full">
      <defs>
        <linearGradient id="carBody" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#4b5568" />
          <stop offset="55%" stopColor="#2b3346" />
          <stop offset="100%" stopColor="#161c29" />
        </linearGradient>
        <linearGradient id="carGlass" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#1f2a3d" />
          <stop offset="100%" stopColor="#0c121d" />
        </linearGradient>
        <radialGradient id="hlGlow">
          <stop offset="0%" stopColor="#dbeafe" stopOpacity="0.95" />
          <stop offset="100%" stopColor="#dbeafe" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* ground shadow */}
      <ellipse cx="150" cy="120" rx="132" ry="7" fill="rgba(0,0,0,.45)" />

      {/* body */}
      <path d="M18,90 L18,74 Q20,66 30,64 L70,58 Q82,36 108,33 L176,33 Q206,35 224,58 L272,64 Q285,66 287,77 L287,90 Z"
            fill="url(#carBody)" stroke="#5b6577" strokeWidth="1" />
      {/* greenhouse / windows */}
      <path d="M84,57 L110,37 L172,37 Q192,40 202,57 Z" fill="url(#carGlass)" />
      {/* beltline highlight */}
      <path d="M30,63 L268,66" stroke="#7c8598" strokeWidth="1" opacity=".5" fill="none" />
      {/* door split + handle */}
      <line x1="150" y1="40" x2="150" y2="86" stroke="#1a2230" strokeWidth="1.5" />
      <rect x="128" y="60" width="14" height="3" rx="1.5" fill="#0f1622" />
      {/* headlight + glow */}
      <ellipse cx="22" cy="70" rx="6" ry="3.4" fill="#e6f0ff" />
      <circle cx="14" cy="70" r="22" fill="url(#hlGlow)" />
      {/* taillight */}
      <rect x="279" y="70" width="6" height="6" rx="1.5" fill="#f45b69" />

      <Wheel cx={86} cy={94} />
      <Wheel cx={222} cy={94} />
    </svg>
  );
}

function Wheel({ cx, cy, r = 24 }) {
  const spokes = Array.from({ length: 8 }, (_, i) => (i / 8) * 360);
  return (
    <g>
      <circle cx={cx} cy={cy} r={r} fill="#0d1218" stroke="#2a3140" strokeWidth="6" />
      <motion.g style={{ transformBox: "fill-box", transformOrigin: "center" }}
                animate={{ rotate: 360 }} transition={{ duration: 0.9, ease: "linear", repeat: Infinity }}>
        <circle cx={cx} cy={cy} r={r - 8} fill="#c9d3e0" />
        {spokes.map((a, i) => (
          <line key={i} x1={cx} y1={cy} x2={cx + (r - 9) * Math.cos((a * Math.PI) / 180)}
                y2={cy + (r - 9) * Math.sin((a * Math.PI) / 180)} stroke="#8f9bb0" strokeWidth="2.5" strokeLinecap="round" />
        ))}
        <circle cx={cx} cy={cy} r="4" fill="#5b6577" />
      </motion.g>
    </g>
  );
}
