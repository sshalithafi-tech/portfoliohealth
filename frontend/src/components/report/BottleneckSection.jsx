/**
 * BottleneckSection — R6 Bottleneck Card
 *
 * Five zones:
 *   1. Header          — AlertTriangle · pillar label · score/level badge
 *   2. Narrative       — AI-generated decision-vulnerability summary
 *   3. Two-col findings — "What the assessment found" + "Why this constrains maturity"
 *   4. Risk pills      — Profit leakage · Strategic drift · Decision latency
 *   5. Academic footer — Hannila et al. references
 *
 * Props:
 *   bottleneckPillar  {string}   e.g. "data"
 *   scores            {object}   { data: 1.5, people: 2.0, ... }
 *   report            {object}   full AI report JSON
 */

import { AlertTriangle, TrendingDown, Target, Zap, Users, ClipboardCheck, Database, Monitor } from "lucide-react";

// ── Pillar meta ──────────────────────────────────────────────────────────────
const PILLAR_ICONS  = { people: Users, process: ClipboardCheck, data: Database, technology: Monitor };
const PILLAR_LABELS = { people: "People", process: "Process", data: "Data", technology: "Technology" };

// ── Maturity level names ─────────────────────────────────────────────────────
function levelName(score) {
  if (score >= 4.5) return "Predictive";
  if (score >= 3.5) return "Managed";
  if (score >= 2.5) return "Defined";
  if (score >= 1.5) return "Developing";
  return "Ad Hoc";
}

// ── Level pill CSS class ─────────────────────────────────────────────────────
function levelClass(score) {
  if (score >= 4.5) return "l5";
  if (score >= 3.5) return "l4";
  if (score >= 2.5) return "l3";
  if (score >= 1.5) return "l2";
  return "l1";
}

// ── Risk pills config ────────────────────────────────────────────────────────
const RISK_PILLS = [
  {
    key: "profit_leakage",
    label: "Profit leakage",
    Icon: TrendingDown,
    fallback: "No corporate-level data model connecting product families to cost, profitability, or supportability — capability view requires manual reconstruction; no standing financial model of through-life value.",
  },
  {
    key: "strategic_drift",
    label: "Strategic drift",
    Icon: Target,
    fallback: "Product master data fragmented across multiple systems — no single source of truth; critical cost estimating models held in personal spreadsheets; non-engineering functions cannot access product data without intermediation.",
  },
  {
    key: "decision_latency",
    label: "Decision latency",
    Icon: Zap,
    fallback: "No data ownership or stewardship roles defined — data quality issues addressed reactively when noticed by senior individuals; no accountability structure, no SLA, no governance.",
  },
];

/**
 * Resolve a risk pill's description text.
 * Priority chain:
 *   report.risk_pills[key]
 *   → report.critical_gaps matching the label
 *   → report.key_findings matching the label
 *   → static fallback
 */
function resolvePillText(key, fallback, report) {
  if (report?.risk_pills?.[key]) return report.risk_pills[key];

  const label = key.replace(/_/g, " ").toLowerCase();
  const gaps     = Array.isArray(report?.critical_gaps)  ? report.critical_gaps  : [];
  const findings = Array.isArray(report?.key_findings)   ? report.key_findings   : [];

  const match =
    gaps.find(g     => typeof g === "string" && g.toLowerCase().includes(label)) ??
    findings.find(f => typeof f === "string" && f.toLowerCase().includes(label));

  return match ?? fallback;
}

// ── Main component ────────────────────────────────────────────────────────────
export const BottleneckSection = ({ bottleneckPillar, scores, report }) => {
  if (!bottleneckPillar) return null;

  const key   = String(bottleneckPillar).toLowerCase();
  const label = PILLAR_LABELS[key] ?? bottleneckPillar;
  const score = typeof scores?.[key] === "number" ? scores[key] : null;
  const level = score !== null ? levelName(score) : null;
  const lc    = score !== null ? levelClass(score) : "l1";

  // ── Zone 2: Narrative
  const narrative =
    report?.bottleneck_narrative ??
    report?.decision_vulnerability ??
    report?.pillar_interpretations?.[key] ??
    null;

  // ── Zone 3 left: What the assessment found
  const foundText =
    report?.dimension_summaries?.[key] ??
    report?.pillar_findings?.[key]?.[0] ??
    null;

  // ── Zone 3 right: Why this constrains maturity
  const constrainText =
    report?.bottleneck_constraint ??
    report?.pillar_interpretations?.[key] ??
    report?.pillar_findings?.[key]?.[1] ??
    null;

  return (
    <section className="ph-report r6">
      <span className="section-label">R6 — Bottleneck Analysis</span>

      <div className="r6-card">

        {/* ── Zone 1: Header ───────────────────────────────────────────── */}
        <div className="r6-head">
          <span className="ico"><AlertTriangle size={20} /></span>
          <div className="r6-head-text">
            <h3 className="r6-title">Bottleneck — {label}</h3>
            {score !== null && level && (
              <span className={`r6-capped-pill level-pill ${lc}`}>
                {score.toFixed(1)} / 5.0 &middot; {level}
              </span>
            )}
          </div>
        </div>

        {/* ── Zone 2: AI narrative ─────────────────────────────────────── */}
        {narrative && (
          <p className="r6-body">{narrative}</p>
        )}

        {/* ── Zone 3: Two-column findings ──────────────────────────────── */}
        {(foundText || constrainText) && (
          <div className="r6-two-col">
            {foundText && (
              <div className="r6-col r6-col--cause">
                <span className="r6-col-label">What the assessment found</span>
                <p className="r6-col-body">{foundText}</p>
              </div>
            )}
            {constrainText && (
              <div className="r6-col r6-col--consequence">
                <span className="r6-col-label">Why this constrains maturity</span>
                <p className="r6-col-body">{constrainText}</p>
              </div>
            )}
          </div>
        )}

        {/* ── Zone 4: Risk pills ───────────────────────────────────────── */}
        <div className="r6-risks">
          {RISK_PILLS.map(({ key: pillKey, label: pillLabel, Icon, fallback }) => (
            <div key={pillKey} className="r6-risk-pill">
              <span className="r6-risk-icon"><Icon size={15} /></span>
              <div>
                <span className="r6-risk-pill-label">{pillLabel}</span>
                <span className="r6-risk-pill-desc">
                  {resolvePillText(pillKey, fallback, report)}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* ── Zone 5: Academic footer ──────────────────────────────────── */}
        <p className="section-footer">
          Bottleneck principle: Hannila et al. (2022) &middot; Hannila (2019) &middot; Hannila, Koskinen, H&#228;rk&#246;nen &amp; Haapasalo (2020), JEIM 33(1).
        </p>

      </div>
    </section>
  );
};

export default BottleneckSection;
