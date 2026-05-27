/**
 * BottleneckSection — R6 Bottleneck Card
 *
 * Layer 1 of 3: React component
 *
 * Five render zones
 *   Zone 1  Header          AlertTriangle · pillar label · score/level pill · capped badge
 *   Zone 2  Narrative       AI bottleneck_narrative (falls back to formula string)
 *   Zone 3  Two-col         "What the assessment found" | "Why this constrains maturity"
 *   Zone 4  Risk pills      Profit leakage · Strategic drift · Decision latency
 *   Zone 5  Academic footer Hannila et al. citation line
 *
 * Data priority chain per zone
 *   Zone 2: report.bottleneck_narrative → report.decision_vulnerability
 *            → report.pillar_interpretations[key] → formula string
 *   Zone 3L: report.dimension_summaries[key] → report.pillar_findings[key][0] → BN_ROOT_CAUSE_FALLBACK[key]
 *   Zone 3R: report.bottleneck_constraint → report.pillar_interpretations[key]
 *            → report.pillar_findings[key][1] → BN_CONSEQUENCE_FALLBACK[key]
 *   Zone 4:  buildRiskItems() — report.risk_pills[key] → critical_gaps match
 *            → key_findings match → RISK_PILL_DEFS[i].fallback
 *
 * Props
 *   bottleneckPillar  {string}   lowercase pillar key e.g. "data"
 *   scores            {object}   { data: 1.5, people: 2.0, process: 3.0, technology: 2.5 }
 *   report            {object}   full AI report JSON stored in assessment.report
 *   bottleneckCapped  {boolean}  true when overall score was capped by this pillar
 */

import {
  AlertTriangle, TrendingDown, ShieldAlert, Zap,
  Users, ClipboardCheck, Database, Monitor,
} from "lucide-react";
import {
  PILLAR_LABELS, PILLAR_ICONS_MAP,
  BN_ROOT_CAUSE_FALLBACK, BN_CONSEQUENCE_FALLBACK,
  RISK_PILL_DEFS, LEVEL_THRESHOLDS,
} from "./constants";
import "./bottleneck.css";

// ── Helpers ──────────────────────────────────────────────────────────────────

/** Map a numeric score to a maturity level name. */
function levelName(score) {
  for (const { min, name } of LEVEL_THRESHOLDS) {
    if (score >= min) return name;
  }
  return "Ad Hoc";
}

/** Map a numeric score to a CSS band class (l1–l5). */
function levelClass(score) {
  if (score >= 4.5) return "l5";
  if (score >= 3.5) return "l4";
  if (score >= 2.5) return "l3";
  if (score >= 1.5) return "l2";
  return "l1";
}

/**
 * Build the three risk-pill objects.
 * Priority per pill:
 *   1. report.risk_pills[pillar_key]  (AI-keyed to the bottleneck pillar)
 *   2. report.critical_gaps sentence that includes the pill label
 *   3. report.key_findings sentence that includes the pill label
 *   4. Static fallback from RISK_PILL_DEFS
 */
function buildRiskItems(report, pillarKey) {
  const gaps     = Array.isArray(report?.critical_gaps)  ? report.critical_gaps  : [];
  const findings = Array.isArray(report?.key_findings)   ? report.key_findings   : [];

  return RISK_PILL_DEFS.map(({ key, label, Icon, fallback }) => {
    // 1. Dedicated risk_pills field keyed by pillar
    if (report?.risk_pills?.[pillarKey]?.[key]) {
      return { Icon, label, desc: report.risk_pills[pillarKey][key] };
    }
    // 2/3. Scan gaps then findings for a sentence mentioning the label
    const needle = label.toLowerCase();
    const match =
      gaps.find(g     => typeof g === "string" && g.toLowerCase().includes(needle)) ??
      findings.find(f => typeof f === "string" && f.toLowerCase().includes(needle));
    return { Icon, label, desc: match ?? fallback };
  });
}

// ── Component ─────────────────────────────────────────────────────────────────

export const BottleneckSection = ({ bottleneckPillar, scores, report, bottleneckCapped }) => {
  if (!bottleneckPillar) return null;

  const key   = String(bottleneckPillar).toLowerCase();
  const label = PILLAR_LABELS[key] ?? bottleneckPillar;
  const score = typeof scores?.[key] === "number" ? scores[key] : null;
  const level = score !== null ? levelName(score) : null;
  const lc    = score !== null ? levelClass(score) : "l1";

  // ── Zone 2 — Narrative
  const narrative =
    report?.bottleneck_narrative ??
    report?.decision_vulnerability ??
    report?.pillar_interpretations?.[key] ??
    (score !== null && level
      ? `${label} scores ${score.toFixed(1)}/5.0 (${level}) — the lowest of the four pillars and the binding constraint on overall maturity. Investments in the other pillars will not lift the overall score until this gap is closed.`
      : null);

  // ── Zone 3L — What the assessment found
  const foundText =
    report?.dimension_summaries?.[key] ??
    report?.pillar_findings?.[key]?.[0] ??
    BN_ROOT_CAUSE_FALLBACK[key] ??
    null;

  // ── Zone 3R — Why this constrains maturity
  const constrainText =
    report?.bottleneck_constraint ??
    report?.pillar_interpretations?.[key] ??
    report?.pillar_findings?.[key]?.[1] ??
    BN_CONSEQUENCE_FALLBACK[key] ??
    null;

  // ── Zone 4 — Risk pills
  const riskItems = buildRiskItems(report, key);

  return (
    <section className="ph-report r6" data-testid="report-r6">

      <div className="r6-card">

        {/* Zone 1 ── Header */}
        <div className="r6-head">
          <span className="r6-head-ico"><AlertTriangle size={22} /></span>
          <div className="r6-head-text">
            <span className="r6-title">Bottleneck — {label}</span>
            {score !== null && level && (
              <span className={`r6-capped-pill level-pill ${lc}`}>
                {score.toFixed(1)} / 5.0
                <span className="r6-dot"> &middot; </span>
                {level}
                {bottleneckCapped && (
                  <span className="r6-cap-badge">&nbsp;&middot; Score capped</span>
                )}
              </span>
            )}
          </div>
        </div>

        {/* Zone 2 ── AI narrative */}
        {narrative && <p className="r6-body">{narrative}</p>}

        {/* Zone 3 ── Two-column findings */}
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

        {/* Zone 4 ── Risk pills */}
        <div className="r6-risks">
          {riskItems.map(({ Icon, label: pillLabel, desc }) => (
            <div key={pillLabel} className="r6-risk-pill">
              <Icon size={15} className="r6-risk-icon" />
              <div className="r6-risk-text">
                <span className="r6-risk-pill-label">{pillLabel}</span>
                <span className="r6-risk-pill-desc">{desc}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Zone 5 ── Academic footer */}
        <p className="section-footer">
          Bottleneck principle: Hannila et al. (2022)&nbsp;&middot;&nbsp;Hannila (2019)&nbsp;&middot;&nbsp;Hannila, Koskinen, H&#228;rk&#246;nen &amp; Haapasalo (2020), JEIM 33(1).
        </p>

      </div>
    </section>
  );
};

export default BottleneckSection;
