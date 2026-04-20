import { Target, AlertTriangle, TrendingUp } from "lucide-react";

export const FindingsAndGaps = ({ report }) => (
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div className="p-6 glass-surface-highlight rounded-xl">
      <div className="flex items-center gap-2 mb-4">
        <Target size={20} className="text-[#C9A84C]" />
        <h2 className="text-lg font-semibold text-white font-['Outfit']">Key Findings</h2>
      </div>
      <ul className="space-y-3">
        {(report.key_findings || []).map((f, i) => (
          <li key={i} className="flex items-start gap-3">
            <span className="w-5 h-5 rounded-full bg-[#C9A84C]/15 text-[#C9A84C] flex items-center justify-center text-[10px] shrink-0 mt-0.5">{i + 1}</span>
            <p className="text-white/60 text-sm">{f}</p>
          </li>
        ))}
      </ul>
    </div>
    <div className="p-6 glass-surface-highlight rounded-xl">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle size={20} className="text-[#EF4444]" />
        <h2 className="text-lg font-semibold text-white font-['Outfit']">Critical Capability Gaps</h2>
      </div>
      <ul className="space-y-3">
        {(report.critical_gaps || []).map((g, i) => (
          <li key={i} className="flex items-start gap-3">
            <span className="w-5 h-5 rounded-full bg-[#EF4444]/15 text-[#EF4444] flex items-center justify-center text-[10px] shrink-0 mt-0.5">!</span>
            <p className="text-white/60 text-sm">{g}</p>
          </li>
        ))}
      </ul>
    </div>
  </div>
);

const DECISION_TYPES = [
  { key: "discontinuation", label: "Discontinuation" },
  { key: "new_launch", label: "New Launch" },
  { key: "product_change", label: "Product Change" },
  { key: "portfolio_investment", label: "Portfolio Investment" },
];

const RISK_TONE = {
  low: { color: "#34D399", bg: "rgba(52,211,153,0.10)", border: "rgba(52,211,153,0.30)" },
  medium: { color: "#C9A84C", bg: "rgba(201,168,76,0.12)", border: "rgba(201,168,76,0.30)" },
  high: { color: "#F97316", bg: "rgba(249,115,22,0.12)", border: "rgba(249,115,22,0.30)" },
  critical: { color: "#EF4444", bg: "rgba(239,68,68,0.14)", border: "rgba(239,68,68,0.35)" },
};

const RiskBadge = ({ risk }) => {
  const key = String(risk || "").toLowerCase();
  const tone = RISK_TONE[key];
  if (!tone) {
    return <span className="text-xs text-white/30 font-medium">–</span>;
  }
  return (
    <span
      className="inline-flex items-center justify-center px-2.5 py-1 rounded text-[11px] font-bold font-['Outfit'] uppercase tracking-wider"
      style={{ color: tone.color, backgroundColor: tone.bg, borderColor: tone.border, borderWidth: 1 }}
    >
      {String(risk)}
    </span>
  );
};

export const DecisionVulnerability = ({ report }) => {
  const ratings = report.decision_vulnerability_ratings || {};
  const hasRatings = Object.keys(ratings).length > 0;
  return (
    <div data-testid="decision-vulnerability-section" className="p-6 glass-surface-highlight rounded-xl">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle size={20} className="text-[#C9A84C]" />
        <h2 className="text-lg font-semibold text-white font-['Outfit']">Decision-Type Vulnerability Analysis</h2>
      </div>
      {hasRatings && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-3 mb-4">
          {DECISION_TYPES.map(({ key, label }) => (
            <div key={key} data-testid={`decision-${key}`} className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
              <p className="text-[11px] text-white/50 mb-1.5">{label}</p>
              <RiskBadge risk={ratings[key]} />
            </div>
          ))}
        </div>
      )}
      <p className="text-white/60 text-sm leading-relaxed">{report.decision_vulnerability || "No narrative available."}</p>
    </div>
  );
};

const PHASES = [
  { key: "immediate", title: "Phase 1 — Immediate (0–3 months)", subtitle: "Stabilise the Foundation", color: "#C9A84C" },
  { key: "short_term", title: "Phase 2 — Short-Term (3–12 months)", subtitle: "Build Capability", color: "#34D399" },
  { key: "strategic", title: "Phase 3 — Strategic (12+ months)", subtitle: "Optimise and Scale", color: "#A78BFA" },
];

const toActionList = (val) => {
  if (!val) return [];
  if (Array.isArray(val)) return val;
  if (typeof val === "string") {
    // Split on semicolons, newlines, or numbered markers — keep single-string fallback safe
    const parts = val.split(/\n|;| \u2022 |\. (?=[A-Z])/).map(s => s.trim()).filter(Boolean);
    return parts.length > 1 ? parts : [val];
  }
  return [];
};

export const ImprovementRoadmap = ({ report }) => (
  <div data-testid="improvement-roadmap" className="p-6 glass-surface-highlight rounded-xl">
    <div className="flex items-center gap-2 mb-6">
      <TrendingUp size={20} className="text-[#34D399]" />
      <h2 className="text-lg font-semibold text-white font-['Outfit']">Improvement Roadmap</h2>
    </div>
    <div className="space-y-4">
      {PHASES.map(phase => {
        const data = report.roadmap?.[phase.key];
        const isObj = data && typeof data === 'object' && !Array.isArray(data);
        const actions = toActionList(isObj ? data.actions : data);
        // Support both old (management_commitment) and new (management_required) field names
        const mgmt = isObj ? (data.management_required || data.management_commitment) : null;
        return (
          <div key={phase.key} data-testid={`roadmap-phase-${phase.key}`} className="p-4 glass-surface rounded-xl border-l-4" style={{ borderLeftColor: phase.color }}>
            <div className="flex flex-wrap items-baseline gap-2 mb-1">
              <h3 className="text-sm font-semibold font-['Outfit']" style={{ color: phase.color }}>{phase.title}</h3>
              {isObj && data.timeframe && (
                <span className="text-[10px] uppercase tracking-wider text-white/40">{data.timeframe}</span>
              )}
            </div>
            <p className="text-xs text-white/40 mb-3 italic">{phase.subtitle}</p>
            <ul className="space-y-1.5 mb-3">
              {actions.map((a, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-white/60"><span style={{ color: phase.color }}>-</span>{a}</li>
              ))}
            </ul>
            {isObj && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                {data.pillar_focus && <div className="text-white/40"><span className="text-white/60 font-medium">Pillar Focus:</span> {data.pillar_focus}</div>}
                {data.governance_milestone && <div className="text-white/40"><span className="text-white/60 font-medium">Governance:</span> {data.governance_milestone}</div>}
                {mgmt && <div className="text-white/40"><span className="text-white/60 font-medium">Management:</span> {mgmt}</div>}
                {data.expected_gain && <div className="text-white/40"><span className="text-white/60 font-medium">Expected Gain:</span> {data.expected_gain}</div>}
              </div>
            )}
          </div>
        );
      })}
    </div>
  </div>
);
