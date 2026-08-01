import { motion } from "framer-motion";

// Sequenced sign-in intro:
//   1) the wordmark "InsurClaim AI" reveals letter-by-letter,
//   2) the magnifier logo strokes itself in above it (with a soft glow),
//   3) the whole thing fades away into the dashboard.
// Restrained, premium dark navy backdrop with a subtle radial glow.
const WORD = "InsurClaim AI";
const EASE = [0.16, 1, 0.3, 1];

export default function BrandedLoader() {
  return (
    <motion.div
      className="fixed inset-0 z-50 grid place-items-center overflow-hidden"
      initial={{ opacity: 1 }}
      exit={{ opacity: 0, transition: { duration: 0.5, ease: EASE } }}
      style={{
        backgroundColor: "#0B0F17",
        backgroundImage:
          "radial-gradient(600px 300px at 50% 42%, rgba(59,130,246,.16), transparent 60%)",
      }}
    >
      <div className="flex flex-col items-center gap-6">
        {/* 2) Logo appears AFTER the wordmark (delay 1.05s) */}
        <motion.svg
          viewBox="0 0 64 64" className="h-16 w-16" fill="none"
          initial={{ opacity: 0, scale: 0.6 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, ease: EASE, delay: 1.05 }}
        >
          <motion.circle
            cx="27" cy="27" r="17" stroke="#60A5FA" strokeWidth="4" strokeLinecap="round"
            initial={{ pathLength: 0 }} animate={{ pathLength: 1 }}
            transition={{ duration: 0.7, ease: "easeInOut", delay: 1.1 }}
          />
          <motion.line
            x1="39" y1="39" x2="52" y2="52" stroke="#8B5CF6" strokeWidth="4" strokeLinecap="round"
            initial={{ pathLength: 0 }} animate={{ pathLength: 1 }}
            transition={{ duration: 0.4, ease: "easeInOut", delay: 1.7 }}
          />
        </motion.svg>

        {/* 1) Wordmark reveals first, letter by letter */}
        <div className="flex items-end">
          {WORD.split("").map((ch, i) => (
            <motion.span
              key={i}
              className="gradient-text text-3xl font-bold tracking-tight sm:text-4xl"
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, ease: EASE, delay: 0.15 + i * 0.055 }}
              style={{ whiteSpace: "pre" }}
            >
              {ch}
            </motion.span>
          ))}
        </div>

        {/* underline sweep */}
        <motion.span
          className="h-[2px] rounded-full bg-grad-primary"
          initial={{ width: 0, opacity: 0 }}
          animate={{ width: 180, opacity: 1 }}
          transition={{ duration: 0.7, ease: EASE, delay: 0.9 }}
        />

        <motion.div
          className="text-xs tracking-[0.2em] text-sidebar-muted"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 1.9 }}
        >
          INVESTIGATOR DASHBOARD
        </motion.div>
      </div>
    </motion.div>
  );
}
