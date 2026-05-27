/**
 * BottleneckSection — R6 Bottleneck Card
 *
 * Renders the full bottleneck card as shown in the assessment report:
 *   │ Header          — pillar label · score/level badge · RingGauge
 *   │ Narrative       — AI-generated decision-vulnerability summary
 *   │ Two-col findings — “What the assessment found” + “Why this constrains maturity”
 *   │ Risk pills      — Profit leakage, Strategic drift, Decision latency
 *   │ Academic footer  — Hannila et al. references
 *
 * Props:
 *   bottleneckPillar  {string}   e.g. "data"
 *   scores            {object}   dimension score map  { data: 1.5, ... }
 *   report            {object}   full AI report JSON
 */

import { AlertTriangle, TrendingDown, Target, Zap, Users, ClipboardCheck, Database, Monitor } from "lucide-react";
import RingGauge from "../ui/RingGauge";

// ── Pillar meta ──────────────────────────────────────────────────────────────
const PILLAR_ICONS   = { people: Users, process: ClipboardCheck, data: Database, technology: Monitor };
const PILLAR_LABELS  = { people: "People", process: "Process", data: "Data", technology: "Technology" };
const PILLAR_COLORS  = { people: "#60A5FA", process: "#34D399", data: "#C9A84C", technology: "#A78BFA" };

// ── Maturity level name from score ──────────────────────────────────────────
function levelName(score) {
  if (score >= 4.5) return "Predictive";
  if (score >= 3.5) return "Managed";
  if (score >= 2.5) return "Defined";
  if (score >= 1.5) return "Developing";
  return "Ad Hoc";
}

// ── Risk pill config ─────────────────────────────────────────────────────────
const RISK_PILLS = [
  { key: "profit_leakage",   label: "Profit leakage",  Icon: TrendingDown, fallback: "No corporate-level data model connecting product families to cost, profitability, or supportability." },
  { key: "strategic_drift",  label: "Strategic drift", Icon: Target,       fallback: "Product master data fragmented across systems — no single source of truth; critical decisions rely on manual reconstruction." },
  { key: "decision_latency", label: "Decision latency",Icon: Zap,          fallback: "No data ownership or stewardship roles defined — data quality issues addressed reactively with no accountability structure." },
];

/**
 * Resolve a risk pill description.
 * Priority: report.risk_pills[key] → report.critical_gaps filtered
 * → report.key_findings filtered → static fallback
 */
function resolvePillText(key, fallback, report) {
  if (report?.risk_pills?.[key]) return report.risk_pills[key];

  const label = key.replace(/_/g, " ").toLowerCase();
  const gaps = report?.critical_gaps ?? [];
  const findings = report?.key_findings ?? [];

  const match =
    gaps.find(g => g?.toLowerCase().includes(label)) ??
    findings.find(f => f?.toLowerCase().includes(label));

  return match ?? fallback;
}

// ── Main component ────────────────────────────────────────────────────────────
export const BottleneckSection = ({ bottleneckPillar, scores, report }) => {
  if (!bottleneckPillar) return null;

  const key    = String(bottleneckPillar).toLowerCase();
  const Icon   = PILLAR_ICONS[key]  ?? Database;
  const color  = PILLAR_COLORS[key] ?? "#EF4444";
  const label  = PILLAR_LABELS[key] ?? bottleneckPillar;
  const score  = typeof scores?.[key] === "number" ? scores[key] : null;
  const level  = score !== null ? levelName(score) : null;

  // Content fields — multiple fallback paths for different AI output shapes
  const narrative =
    report?.bottleneck_narrative ??
    report?.decision_vulnerability ??
    report?.pillar_interpretations?.[key] ??
    null;

  const foundText =
    report?.dimension_summaries?.[key] ??
    report?.pillar_findings?.[key]?.[0] ??
    null;

  const constrainText =
    report?.bottleneck_constraint ??
    report?.pillar_interpretations?.[key] ??
    report?.pillar_findings?.[key]?.[1] ??
    null;

  return (
    <div
      data-testid="bottleneck-section"
      className="rounded-2xl border overflow-hidden"
      style={{
        borderColor: `${color}40`,
        background: `linear-gradient(135deg, ${color}06 0%, transparent 60%)`,
      }}
    >
      {/* ── Header ── */}
      <div className="flex items-start justify-between gap-4 px-6 pt-6 pb-4 border-b" style={{ borderColor: `${color}20` }}>
        <div className="flex items-center gap-3 min-w-0">
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
            style={{ backgroundColor: `${color}18` }}
          >
            <AlertTriangle size={18} style={{ color }} />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-base font-semibold text-[#0C1B2A] font-['Outfit']">Bottleneck — {label}</h2>
              {score !== null && level && (
                <span
                  className="px-2 py-0.5 rounded-full text-xs font-medium font-['Outfit']"
                  style={{ backgroundColor: `${color}18`, color }}
                >
                  {score.toFixed(1)} / 5.0 · {level}
                </span>
              )}
            </div>
            <p className="text-xs text-[#8896A5] mt-0.5 italic">
              The weakest pillar caps real-world capability regardless of other scores.
            </p>
          </div>
        </div>

        {/* Ring gauge */}
        {score !== null && (
          <div className="shrink-0">
            <RingGauge score={score} size={88} thickness={8} showLevel={false} />
          </div>
        )}
      </div>

      {/* ── Narrative ── */}
      {narrative && (
        <div className="px-6 py-4 border-b" style={{ borderColor: `${color}20` }}>
          <p className="text-sm text-[#4A5568] leading-relaxed">{narrative}</p>
        </div>
      )}

      {/* ── Two-column findings ── */}
      {(foundText || constrainText) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-px border-b" style={{ borderColor: `${color}20` }}>
          {/* Left — What the assessment found */}
          {foundText && (
            <div className="px-5 py-4" style={{ background: `${color}05` }}>
              <p
                className="text-[10px] font-semibold uppercase tracking-widest mb-2"
                style={{ color }}
              >
                What the assessment found
              </p>
              <p className="text-xs text-[#4A5568] leading-relaxed">{foundText}</p>
            </div>
          )}

          {/* Right — Why this constrains maturity */}
          {constrainText && (
            <div className="px-5 py-4 bg-[#F8F9FA]">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-[#8896A5] mb-2">
                Why this constrains maturity
              </p>
              <p className="text-xs text-[#4A5568] leading-relaxed">{constrainText}</p>
            </div>
          )}
        </div>
      )}

      {/* ── Risk pills ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-px" style={{ background: `${color}10` }}>
        {RISK_PILLS.map(({ key: pillKey, label: pillLabel, Icon: PillIcon, fallback }) => {
          const text = resolvePillText(pillKey, fallback, report);
          return (
            <div key={pillKey} className="px-5 py-4 bg-white">
              <div className="flex items-center gap-1.5 mb-1.5">
                <PillIcon size={13} style={{ color }} />
                <p
                  className="text-[11px] font-semibold"
                  style={{ color }}
                >
                  {pillLabel}
                </p>
              </div>
              <p className="text-[11px] text-[#4A5568] leading-relaxed">{text}</p>
            </div>
          );
        })}
      </div>

      {/* ── Academic footer ── */}
      <div className="px-6 py-3 border-t" style={{ borderColor: `${color}20`, background: `${color}04` }}>
        <p className="text-[10px] text-[#8896A5] italic">
          Bottleneck principle: Hannila et al. (2022) · Hannila (2019) · Hannila, Koskinen, Härkönen &amp; Haapasalo (2020), JEIM 33(1).
        </p>
      </div>
    </div>
  );
};

export default BottleneckSection;
