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

export const DecisionVulnerability = ({ report }) => (
  <div className="p-6 glass-surface-highlight rounded-xl">
    <div className="flex items-center gap-2 mb-4">
      <AlertTriangle size={20} className="text-[#C9A84C]" />
      <h2 className="text-lg font-semibold text-white font-['Outfit']">Decision-Type Vulnerability Analysis</h2>
    </div>
    <p className="text-white/60 text-sm leading-relaxed">{report.decision_vulnerability || "No analysis available."}</p>
  </div>
);

const PHASES = [
  { key: "immediate", title: "Phase 1 — Immediate (0–3 months)", subtitle: "Stabilise the Foundation", color: "#C9A84C" },
  { key: "short_term", title: "Phase 2 — Short-Term (3–12 months)", subtitle: "Build Capability", color: "#34D399" },
  { key: "strategic", title: "Phase 3 — Strategic (12+ months)", subtitle: "Optimise and Scale", color: "#A78BFA" },
];

export const ImprovementRoadmap = ({ report }) => (
  <div className="p-6 glass-surface-highlight rounded-xl">
    <div className="flex items-center gap-2 mb-6">
      <TrendingUp size={20} className="text-[#34D399]" />
      <h2 className="text-lg font-semibold text-white font-['Outfit']">Improvement Roadmap</h2>
    </div>
    <div className="space-y-4">
      {PHASES.map(phase => {
        const data = report.roadmap?.[phase.key];
        const actions = typeof data === 'object' && !Array.isArray(data) ? data.actions : (Array.isArray(data) ? data : []);
        const isRich = typeof data === 'object' && !Array.isArray(data);
        return (
          <div key={phase.key} className="p-4 glass-surface rounded-xl border-l-4" style={{ borderLeftColor: phase.color }}>
            <h3 className="text-sm font-semibold font-['Outfit'] mb-1" style={{ color: phase.color }}>{phase.title}</h3>
            <p className="text-xs text-white/40 mb-3 italic">{phase.subtitle}</p>
            <ul className="space-y-1.5 mb-3">
              {(actions || []).map((a, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-white/60"><span style={{ color: phase.color }}>-</span>{a}</li>
              ))}
            </ul>
            {isRich && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                {data.pillar_focus && <div className="text-white/40"><span className="text-white/60 font-medium">Pillar Focus:</span> {data.pillar_focus}</div>}
                {data.governance_milestone && <div className="text-white/40"><span className="text-white/60 font-medium">Governance:</span> {data.governance_milestone}</div>}
                {data.management_commitment && <div className="text-white/40"><span className="text-white/60 font-medium">Management:</span> {data.management_commitment}</div>}
                {data.expected_gain && <div className="text-white/40"><span className="text-white/60 font-medium">Expected Gain:</span> {data.expected_gain}</div>}
              </div>
            )}
          </div>
        );
      })}
    </div>
  </div>
);
