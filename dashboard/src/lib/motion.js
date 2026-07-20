// Shared framer-motion variants so every section moves with the same rhythm.
// Easing is a soft "expo-out" (ui-ux-pro-max motion guidance) for a premium feel.
export const EASE = [0.16, 1, 0.3, 1];

export const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: EASE } },
};

export const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } },
};

export const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.55, ease: EASE } },
};

// Section swap (route-like) transition used with AnimatePresence.
export const sectionSwap = {
  initial: { opacity: 0, y: 18, filter: "blur(6px)" },
  animate: { opacity: 1, y: 0, filter: "blur(0px)", transition: { duration: 0.5, ease: EASE } },
  exit: { opacity: 0, y: -12, filter: "blur(6px)", transition: { duration: 0.3, ease: EASE } },
};
