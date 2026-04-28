/**
 * LogoMark — PortfolioHealth Advisor brand mark.
 *
 * Concept: A clean navy rounded tile with a single cyan ascending-curve
 * signature. The curve rises from a stable base into a peak point —
 * "Portfolio" (ascending trajectory) + "Health" (vital pulse) condensed
 * into a single confident gesture. Modern SaaS aesthetic, no clutter.
 *
 * Palette: Navy `#0C1B2A` + Deep Cyan `#0891B2` accent.
 *
 * Usage:
 *   <LogoMark className="w-10 h-10" />
 *   <LogoMark className="w-20 h-20" radius={22} />
 */
export const LogoMark = ({
  className = "w-10 h-10",
  radius = 22,
  ariaLabel = "PortfolioHealth Advisor",
}) => (
  <svg
    viewBox="0 0 100 100"
    className={className}
    xmlns="http://www.w3.org/2000/svg"
    role="img"
    aria-label={ariaLabel}
  >
    <defs>
      {/* Navy tile gradient */}
      <linearGradient id="lm-bg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor="#162333" />
        <stop offset="55%" stopColor="#0C1B2A" />
        <stop offset="100%" stopColor="#050D18" />
      </linearGradient>
      {/* Cyan stroke gradient */}
      <linearGradient id="lm-cyan" x1="0" y1="1" x2="1" y2="0">
        <stop offset="0%" stopColor="#0E7490" />
        <stop offset="55%" stopColor="#0891B2" />
        <stop offset="100%" stopColor="#67E8F9" />
      </linearGradient>
      {/* Peak dot soft glow */}
      <radialGradient id="lm-glow">
        <stop offset="0%" stopColor="#67E8F9" stopOpacity="0.55" />
        <stop offset="100%" stopColor="#67E8F9" stopOpacity="0" />
      </radialGradient>
    </defs>

    {/* Navy rounded tile */}
    <rect x="0" y="0" width="100" height="100" rx={radius} ry={radius} fill="url(#lm-bg)" />

    {/* Inner cyan hairline */}
    <rect
      x="3"
      y="3"
      width="94"
      height="94"
      rx={Math.max(0, radius - 3)}
      ry={Math.max(0, radius - 3)}
      fill="none"
      stroke="#0891B2"
      strokeOpacity="0.20"
      strokeWidth="1"
    />

    {/* Subtle baseline */}
    <line
      x1="18"
      y1="76"
      x2="82"
      y2="76"
      stroke="#FFFFFF"
      strokeOpacity="0.10"
      strokeWidth="1"
      strokeLinecap="round"
    />

    {/* Soft glow behind peak */}
    <circle cx="78" cy="26" r="14" fill="url(#lm-glow)" />

    {/* The signature — clean ascending curve (smooth, confident) */}
    <path
      d="M 18 70 C 30 70, 38 64, 44 54 S 58 30, 78 26"
      fill="none"
      stroke="url(#lm-cyan)"
      strokeWidth="5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />

    {/* Peak vertex — the ascendant dot */}
    <circle cx="78" cy="26" r="5" fill="#67E8F9" />
    <circle cx="78" cy="26" r="2" fill="#0C1B2A" />

    {/* Small base anchor — grounds the curve */}
    <circle cx="18" cy="70" r="3.2" fill="#0891B2" opacity="0.85" />
  </svg>
);

export default LogoMark;
