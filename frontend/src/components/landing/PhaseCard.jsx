import { useState } from "react";
import { ChevronDown } from "lucide-react";

/**
 * Collapsible "How It Works" phase card. Body text is clamped to 2 lines and
 * the evidence list is hidden until expanded, keeping all 4 cards in the row
 * a uniform height by default (grid + flex both stretch/pin consistently),
 * with a "Show details" toggle for the full content.
 */
const PhaseCard = ({ n, title, body, items, style, dark }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`ph-glass-card ph-phase-card ph-animate-in${dark ? " ph-liquid-glass dark" : ""}`} style={style}>
      <div className="ph-num">{n}</div>
      <h3>{title}</h3>
      <p className={`ph-phase-body${expanded ? "" : " clamped"}`}>{body}</p>
      {expanded && (
        <ul className="ph-phase-list">
          {items.map((it) => (
            <li key={it}>{it}</li>
          ))}
        </ul>
      )}
      <button
        type="button"
        className="ph-phase-toggle"
        aria-expanded={expanded}
        onClick={() => setExpanded((v) => !v)}
      >
        {expanded ? "Show less" : "Show details"}
        <ChevronDown size={14} className={`ph-nav-dropdown-chevron${expanded ? " open" : ""}`} />
      </button>
    </div>
  );
};

export default PhaseCard;
