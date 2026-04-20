import { Shield, ArrowUpRight } from "lucide-react";
import { DIMENSIONS } from "./constants";

export const GovernanceObservations = ({ report }) => {
  const obs = report.governance_observations || {};
  const assessment = report.governance_assessment;
  const hasValid = Object.values(obs).some(v => v && !String(v).includes("N/A") && !String(v).toLowerCase().includes("below"));
  if (!hasValid && !assessment) return null;

  return (
    <div data-testid="governance-indicators" className="p-6 glass-surface-highlight rounded-xl border-l-4 border-[#C9A84C]">
      <div className="flex items-center gap-2 mb-2">
        <Shield size={20} className="text-[#C9A84C]" />
        <h2 className="text-lg font-semibold text-white font-['Outfit']">Governance Indicators</h2>
      </div>
      {assessment && (
        <p className="text-white/70 text-sm italic leading-relaxed mb-4 p-3 bg-white/[0.03] rounded-lg border border-white/[0.06]">
          {assessment}
        </p>
      )}
      {hasValid && (
        <div className="space-y-3">
          {DIMENSIONS.map(dim => {
            const v = obs[dim];
            if (!v || String(v).includes("N/A") || String(v).toLowerCase().includes("below")) return null;
            return (
              <div key={`gov-${dim}`} className="p-3 bg-[#C9A84C]/5 rounded-lg border border-[#C9A84C]/10">
                <span className="text-xs font-semibold text-[#C9A84C] uppercase tracking-wider">{dim}</span>
                <p className="text-white/70 text-sm mt-1">{v}</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

const GOVERNANCE_QUESTIONS = [
  "Who owns the product portfolio decision-making process?",
  "Are stage-gate reviews conducted with defined decision criteria and assigned owners?",
  "Is there a Product Manager or Portfolio Manager with cross-functional authority?",
  "Are portfolio priorities reviewed on a defined cadence (e.g. quarterly PPM reviews)?",
];

export const GovernanceOwnership = ({ report }) => (
  <div className="p-6 glass-surface-highlight rounded-xl">
    <div className="flex items-center gap-3 mb-4">
      <div className="w-10 h-10 rounded-lg bg-[#A78BFA]/15 flex items-center justify-center"><Shield size={22} className="text-[#A78BFA]" /></div>
      <h2 className="text-lg font-semibold text-white font-['Outfit']">Governance & Ownership</h2>
    </div>
    <p className="text-white/60 text-sm mb-4 leading-relaxed">
      Governance is the connective tissue between all four PPDT dimensions. High capability in People, Process, Data, or Technology without clear ownership and accountability still produces unreliable, inconsistent portfolio decisions.
    </p>
    <ul className="space-y-2 mb-4">
      {GOVERNANCE_QUESTIONS.map((q, i) => (
        <li key={i} className="flex items-start gap-2 text-sm text-white/50">
          <span className="text-[#A78BFA] mt-0.5">-</span>{q}
        </li>
      ))}
    </ul>
    {report.governance_assessment && (
      <p className="text-white/70 text-sm italic leading-relaxed p-3 bg-white/[0.03] rounded-lg border border-white/[0.06]">
        {report.governance_assessment}
      </p>
    )}
    <div className="mt-4 p-3 bg-[#EF4444]/5 border border-[#EF4444]/15 rounded-lg">
      <p className="text-[#EF4444] text-xs font-medium">
        "Without governance structures, even well-trained people and advanced technology produce fragmented decisions. Accountability must be assigned — not assumed."
      </p>
    </div>
  </div>
);

const MANAGEMENT_POINTS = [
  "Leadership sets the strategic priority for PPM — if portfolio management is not visibly championed at the executive level, it will be deprioritised at the operational level.",
  "Management commitment enables resource allocation: time, budget, and cross-functional cooperation needed for PPM improvement.",
  "In organisations where leadership actively participates in stage-gate reviews and portfolio prioritisation, maturity levels increase faster and more sustainably.",
];

const commitmentTone = (level) => {
  const k = String(level || "").toLowerCase();
  if (k === "high") return { color: "#34D399", label: "HIGH" };
  if (k === "medium") return { color: "#C9A84C", label: "MEDIUM" };
  if (k === "low") return { color: "#EF4444", label: "LOW" };
  return null;
};

export const ManagementCommitment = ({ report }) => {
  const rating = commitmentTone(report.management_commitment);
  return (
    <div data-testid="management-commitment-section" className="p-6 glass-surface-highlight rounded-xl">
      <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-[#34D399]/15 flex items-center justify-center"><ArrowUpRight size={22} className="text-[#34D399]" /></div>
          <div>
            <h2 className="text-lg font-semibold text-white font-['Outfit']">Management Commitment</h2>
            <p className="text-xs text-white/40 italic">The multiplier effect on all capability investments</p>
          </div>
        </div>
        {rating && (
          <div
            data-testid="management-commitment-badge"
            className="px-4 py-2 rounded-xl flex items-center gap-2 font-['Outfit']"
            style={{ backgroundColor: `${rating.color}18`, borderColor: `${rating.color}40`, borderWidth: 1 }}
          >
            <span className="text-[10px] uppercase tracking-wider" style={{ color: rating.color }}>Rating</span>
            <span className="text-base font-bold" style={{ color: rating.color }}>{rating.label}</span>
          </div>
        )}
      </div>
      <p className="text-white/60 text-sm mb-4 leading-relaxed">
        Management commitment acts as a multiplier on all capability investments. Without leadership buy-in, investments in People training and Process redesign produce limited, short-lived change. With it, even modest interventions can rapidly elevate maturity across all four PPDT dimensions.
      </p>
      <ul className="space-y-2 mb-4">
        {MANAGEMENT_POINTS.map((p, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-white/50"><span className="text-[#34D399] mt-0.5">-</span>{p}</li>
        ))}
      </ul>
      {report.management_commitment_assessment && (
        <p className="text-white/70 text-sm italic leading-relaxed p-3 bg-white/[0.03] rounded-lg border border-white/[0.06]">
          {report.management_commitment_assessment}
        </p>
      )}
      <div className="mt-4 p-3 bg-[#34D399]/5 border border-[#34D399]/15 rounded-lg">
      <p className="text-[#34D399] text-xs font-medium">
        "If management commitment is low, prioritise leadership alignment before investing in tools or training — otherwise capability improvements will not stick."
      </p>
    </div>
  </div>
  );
};
