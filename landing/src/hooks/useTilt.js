import { useRef, useCallback } from "react";

/**
 * Lightweight 3D tilt-on-hover for a card. Returns a ref plus pointer handlers.
 * The card rotates toward the cursor and a radial glow follows it. Disabled for
 * users who prefer reduced motion.
 *
 * @param {number} max maximum rotation in degrees.
 */
export function useTilt(max = 9) {
  const ref = useRef(null);
  const reduce =
    typeof window !== "undefined" &&
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const onMove = useCallback(
    (e) => {
      const el = ref.current;
      if (!el || reduce) return;
      const r = el.getBoundingClientRect();
      const px = (e.clientX - r.left) / r.width; // 0..1
      const py = (e.clientY - r.top) / r.height; // 0..1
      const rx = (0.5 - py) * max * 2;
      const ry = (px - 0.5) * max * 2;
      el.style.transform = `rotateX(${rx.toFixed(2)}deg) rotateY(${ry.toFixed(2)}deg) translateZ(0)`;
      const glow = el.querySelector(".glow");
      if (glow) {
        glow.style.left = `${px * 100}%`;
        glow.style.top = `${py * 100}%`;
      }
    },
    [max, reduce]
  );

  const onLeave = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    el.style.transform = "rotateX(0deg) rotateY(0deg)";
  }, []);

  return { ref, onMove, onLeave };
}
