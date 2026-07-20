import { useEffect, useRef, useState } from "react";
import { useInView } from "framer-motion";

// Counts up to `value` when it scrolls into view. Uses tabular figures so the
// width stays stable while the number animates.
export default function Counter({ value = 0, duration = 1.2, prefix = "", suffix = "", format }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (!inView) return;
    let raf;
    const start = performance.now();
    const from = 0;
    const to = Number(value) || 0;
    const tick = (now) => {
      const t = Math.min(1, (now - start) / (duration * 1000));
      // easeOutExpo
      const eased = t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
      setDisplay(from + (to - from) * eased);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, value, duration]);

  const shown = format ? format(display) : Math.round(display).toLocaleString("en-US");
  return (
    <span ref={ref} className="tnum">
      {prefix}
      {shown}
      {suffix}
    </span>
  );
}
