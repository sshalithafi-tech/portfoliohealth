/**
 * LogoMark — PortfolioHealth Advisor brand mark.
 *
 * Concept: A premium deep-navy rounded tile with a gold "ascending pulse"
 * signature — a single flowing heartbeat-style line that rises from the
 * baseline to a peak dot in the top-right. A fine gold corner bracket adds
 * a subtle "crest" feel. Portfolio (ascending trajectory) + Health (pulse).
 *
 * Same palette as the app: Navy (#0A1628) + Gold (#C9A84C).
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
      {/* Deep navy background with subtle diagonal highlight */}
      <linearGradient id="lm-bg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor="#122240" />
        <stop offset="55%" stopColor="#0A1628" />
        <stop offset="100%" stopColor="#050B18" />
      </linearGradient>
      {/* Gold gradient for the pulse line */}
      <linearGradient id="lm-gold" x1="0" y1="1" x2="1" y2="0">
        <stop offset="0%" stopColor="#B8932F" />
        <stop offset="60%" stopColor="#C9A84C" />
        <stop offset="100%" stopColor="#E8C96A" />
      </linearGradient>
    </defs>

    {/* Navy rounded tile */}
    <rect x="0" y="0" width="100" height="100" rx={radius} ry={radius} fill="url(#lm-bg)" />

    {/* Inner gold hairline frame (very subtle) */}
    <rect
      x="2"
      y="2"
      width="96"
      height="96"
      rx={Math.max(0, radius - 2)}
      ry={Math.max(0, radius - 2)}
      fill="none"
      stroke="#C9A84C"
      strokeOpacity="0.18"
      strokeWidth="1"
    />

    {/* Top-right corner crest bracket */}
    <path
      d="M 72 8 L 92 8 L 92 28"
      fill="none"
      stroke="#C9A84C"
      strokeWidth="2"
      strokeLinecap="round"
    />

    {/* Faint gold baseline (portfolio axis) */}
    <line
      x1="12"
      y1="82"
      x2="88"
      y2="82"
      stroke="#C9A84C"
      strokeOpacity="0.22"
      strokeWidth="1.25"
      strokeLinecap="round"
    />

    {/* Gold ascending pulse signature — the hero element */}
    <path
      d="M 12 68 L 28 68 L 34 58 L 42 74 L 52 32 L 62 48 L 78 22"
      fill="none"
      stroke="url(#lm-gold)"
      strokeWidth="4.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />

    {/* Peak dot (the ascendant point) */}
    <circle cx="78" cy="22" r="5.5" fill="#C9A84C" />
    <circle cx="78" cy="22" r="2.2" fill="#0A1628" />
  </svg>
);

export default LogoMark;
