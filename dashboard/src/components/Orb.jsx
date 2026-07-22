import { motion } from "framer-motion";

// A glossy, glowing "AI" sphere radial-gradient highlight + soft glow + a slow
// rotating conic ring. The premium accent from the reference, kept tasteful.
export default function Orb({ size = 84, label = "AI" }) {
  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }}>
      {/* outer glow */}
      <div className="absolute inset-0 rounded-full blur-xl"
           style={{ background: "radial-gradient(circle, rgba(139,92,246,.55), transparent 65%)" }} />
      {/* rotating conic ring */}
      <motion.div
        className="absolute rounded-full"
        style={{
          inset: 2,
          background: "conic-gradient(from 0deg,#8b5cf6,#22d3ee,#3b82f6,#8b5cf6)",
          mask: "radial-gradient(circle, transparent 62%, black 64%)",
          WebkitMask: "radial-gradient(circle, transparent 62%, black 64%)",
        }}
        animate={{ rotate: 360 }}
        transition={{ duration: 10, ease: "linear", repeat: Infinity }}
      />
      {/* glossy sphere */}
      <div className="relative grid place-items-center rounded-full"
           style={{
             width: size * 0.68, height: size * 0.68,
             background: "radial-gradient(circle at 32% 28%, #c4b5fd 0%, #8b5cf6 42%, #4c1d95 100%)",
             boxShadow: "inset 0 -6px 12px rgba(0,0,0,.35), 0 6px 20px rgba(139,92,246,.5)",
           }}>
        {/* specular highlight */}
        <span className="absolute rounded-full"
              style={{ width: "34%", height: "24%", top: "16%", left: "22%",
                       background: "radial-gradient(circle, rgba(255,255,255,.9), transparent 70%)", filter: "blur(1px)" }} />
        <span className="relative text-sm font-bold tracking-wide text-white">{label}</span>
      </div>
    </div>
  );
}
