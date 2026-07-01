import { useEffect, useRef, useState } from "react";

/**
 * Scroll-triggered fade-in-and-slide-up wrapper.
 * - Uses IntersectionObserver, triggers once per element (unobserves after).
 * - Respects prefers-reduced-motion: shows content immediately, no animation.
 * - opacity/transform only (no layout-affecting properties), so no reflow/jank.
 * - `delay` (ms) lets callers stagger items in a grid (e.g. i * 90).
 */
const prefersReducedMotion = () =>
  typeof window !== "undefined" &&
  typeof window.matchMedia === "function" &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

export const Reveal = ({ children, as: Tag = "div", delay = 0, className = "", ...rest }) => {
  const ref = useRef(null);
  const [visible, setVisible] = useState(prefersReducedMotion);

  useEffect(() => {
    if (visible) return;
    const el = ref.current;
    if (!el || typeof IntersectionObserver === "undefined") {
      setVisible(true);
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setVisible(true);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -60px 0px" }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [visible]);

  return (
    <Tag
      ref={ref}
      className={`ph-reveal${visible ? " is-visible" : ""}${className ? ` ${className}` : ""}`}
      style={{ transitionDelay: visible && delay ? `${delay}ms` : "0ms" }}
      {...rest}
    >
      {children}
    </Tag>
  );
};

export default Reveal;
