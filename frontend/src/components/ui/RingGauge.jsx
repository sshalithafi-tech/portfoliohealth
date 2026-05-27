/**
 * RingGauge — shared SVG ring score component.
 *
 * Props
 *   score      {number}   0–5 value to display
 *   size       {number}   Overall pixel size of the SVG (default 96)
 *   thickness  {number}   Stroke width of the ring track (default 9)
 *   label      {string}   Optional sub-label under the level name (e.g. "bottleneck")
 *   showLevel  {boolean}  Show maturity level name below the number (default true)
 *   animate    {boolean}  Animate the ring fill on mount (default true)
 *
 * Colour banding (matches constants.js MATURITY_LEVELS)
 *   < 2.0  →  #EF4444  (Ad Hoc — red)
 *   < 3.0  →  #C9A84C  (Developing — amber)
 *   < 4.0  →  #C9A84C  (Defined — amber/gold)
 *   ≥ 4.0  →  #34D399  (Managed / Predictive — green)
 */

import { useEffect, useRef, useState } from "react";

const LEVEL_NAMES = ["", "Ad Hoc", "Developing", "Defined", "Managed", "Predictive"];

function getColor(score) {
  if (score >= 4.0) return "#34D399";
  if (score >= 2.0) return "#C9A84C";
  return "#EF4444";
}

function getLevelName(score) {
  if (score >= 4.5) return "Predictive";
  if (score >= 3.5) return "Managed";
  if (score >= 2.5) return "Defined";
  if (score >= 1.5) return "Developing";
  return "Ad Hoc";
}

export function RingGauge({
  score = 0,
  size = 96,
  thickness = 9,
  label,
  showLevel = true,
  animate = true,
}) {
  const clampedScore = Math.max(0, Math.min(5, score));
  const color = getColor(clampedScore);
  const levelName = getLevelName(clampedScore);

  const center = size / 2;
  const radius = center - thickness / 2 - 2;
  const circumference = 2 * Math.PI * radius;
  const targetDash = (clampedScore / 5) * circumference;

  const [currentDash, setCurrentDash] = useState(animate ? 0 : targetDash);
  const rafRef = useRef(null);

  useEffect(() => {
    if (!animate) {
      setCurrentDash(targetDash);
      return;
    }
    const duration = 900;
    const start = performance.now();
    const from = 0;

    function step(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setCurrentDash(from + (targetDash - from) * eased);
      if (progress < 1) rafRef.current = requestAnimationFrame(step);
    }

    rafRef.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(rafRef.current);
  }, [targetDash, animate]);

  // Font sizes scale with the outer dimension
  const scoreFontSize = size * 0.22;
  const maxFontSize = size * 0.10;
  const levelFontSize = size * 0.085;
  const labelFontSize = size * 0.08;

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      aria-label={`Score ${clampedScore.toFixed(1)} out of 5 — ${levelName}`}
      role="img"
    >
      {/* Track ring */}
      <circle
        cx={center}
        cy={center}
        r={radius}
        fill="none"
        stroke={`${color}22`}
        strokeWidth={thickness}
      />

      {/* Value ring — starts at 12 o'clock (−90°) */}
      <circle
        cx={center}
        cy={center}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={thickness}
        strokeLinecap="round"
        strokeDasharray={`${currentDash} ${circumference}`}
        transform={`rotate(-90 ${center} ${center})`}
        style={{ transition: animate ? "none" : "stroke-dasharray 0.6s ease-out" }}
      />

      {/* Score number */}
      <text
        x={center}
        y={center - (showLevel ? size * 0.04 : 0)}
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize={scoreFontSize}
        fontWeight="700"
        fontFamily="'JetBrains Mono', monospace"
        fill={color}
      >
        {clampedScore.toFixed(1)}
      </text>

      {/* /5 sub-text */}
      <text
        x={center + scoreFontSize * 0.62}
        y={center - (showLevel ? size * 0.04 : 0) + scoreFontSize * 0.18}
        textAnchor="start"
        dominantBaseline="middle"
        fontSize={maxFontSize}
        fontFamily="'JetBrains Mono', monospace"
        fill="#8896A5"
      >
        /5
      </text>

      {/* Level name */}
      {showLevel && (
        <text
          x={center}
          y={center + size * 0.16}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize={levelFontSize}
          fontWeight="600"
          fontFamily="'Outfit', sans-serif"
          fill="#8896A5"
        >
          {levelName}
        </text>
      )}

      {/* Optional sub-label (e.g. "bottleneck") */}
      {label && (
        <text
          x={center}
          y={center + size * 0.28}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize={labelFontSize}
          fontFamily="'Outfit', sans-serif"
          fill="#8896A5"
          style={{ textTransform: "uppercase", letterSpacing: "0.05em" }}
        >
          {label}
        </text>
      )}
    </svg>
  );
}

export default RingGauge;
