/**
 * AssessmentDashboard.jsx
 *
 * Compact, scannable 2x2 dashboard that replaces the previous wall-of-text
 * R6 Bottleneck + R8 Decision Impact sections in the consultant report.
 *
 * Cards (always in this order, always rendered, never skipped):
 *   Row 1 — BottleneckCard           · PreconditionsCard
 *   Row 2 — PortfolioDecisionImpactCard · GovernanceReadinessCard
 *
 * Design rules:
 *   - All four cards share the same surface, radius, padding, label and chip styles.
 *   - Severity colors are driven by the global maturity band palette:
 *       Critical / very weak  = red   #DC2626 (--bn-critical)
 *       Moderate / partial    = amber #F59E0B (--bn-warning)
 *       Good / established    = green #10B981 (--bn-good)
 *       Advanced / strong     = sky   #0EA5E9 (--bn-advanced)
 *   - All long AI prose is normalised through `truncateInsight` / `extractFirstSentence`.
 *   - Backend `pdf_builder.py` still consumes the verbose fields untouched.
 */
import {
  AlertTriangle,
  Layers,
  Compass,
  ShieldCheck,
  CheckCircle2,
  CircleDot,
  XCircle,
} from "lucide-react";
import {
  scoreToBand,
  scoreToLevel,
  BAND_COLORS,
  LEVEL_TITLES,
} from "../../lib/reportData";

/* ============================================================
 * Small shared helpers
 * ============================================================ */

const SEVERITY_COLORS = {
  critical: "var(--bn-critical, #DC2626)",
  warning: "var(--bn-warning, #F59E0B)",
  good: "var(--bn-good, #10B981)",
  advanced: "var(--bn-advanced, #0EA5E9)",
  muted: "#94A3B8",
};

const PILLAR_LABELS = {
  people: "People",
  process: "Process",
  data: "Data",
  technology: "Technology",
};

/** First non-empty sentence; falls back to original text if no period present. */
export function extractFirstSentence(text = "") {
  const s = String(text || "").trim();
  if (!s) return "";
  const m = s.match(/[^.!?]+[.!?]/);
  return (m ? m[0] : s).trim();
}

/** Trim a long string to ~maxChars, breaking on word boundary, appending an ellipsis. */
export function truncateInsight(text = "", maxChars = 170) {
  const s = String(text || "").trim();
  if (s.length <= maxChars) return s;
  const cut = s.slice(0, maxChars);
  const space = cut.lastIndexOf(" ");
  return `${space > 60 ? cut.slice(0, space) : cut}…`;
}

/** Map a 0–5 score to one of the 4 severity buckets used in this dashboard. */
function severityFromScore(score) {
  const b = scoreToBand(score);
  if (b <= 1) return "critical";
  if (b === 2) return "warning";
  if (b === 3) return "good";
  return "advanced"; // 4 and 5
}

/** Map H/M/L impact strings to severity buckets. */
function severityFromImpact(level) {
  if (level === "High") return "critical";
  if (level === "Medium") return "warning";
  return "good";
}

/* ============================================================
 * Generic visual atoms
 * ============================================================ */

const StatusChip = ({ label, severity = "muted", testid }) => (
  <span
    className="bn-chip"
    data-severity={severity}
    data-testid={testid}
    style={{ "--c": SEVERITY_COLORS[severity] }}
  >
    {label}
  </span>
);

const SeverityBar = ({ severity = "muted" }) => (
  <span className="bn-sev" data-severity={severity} style={{ "--c": SEVERITY_COLORS[severity] }}>
    <span className="bn-sev-fill" />
  </span>
);

/** Circular SVG gauge — animates fill on mount via CSS keyframe. */
const RingGauge = ({ score = 0, color = SEVERITY_COLORS.critical, levelLabel = "" }) => {
  const safe = Math.max(0, Math.min(5, Number(score) || 0));
  const pct = safe / 5;
  const R = 52;
  const C = 2 * Math.PI * R;
  return (
    <div className="bn-ring">
      <svg viewBox="0 0 130 130" className="bn-ring-svg">
        <circle cx="65" cy="65" r={R} className="bn-ring-track" />
        <circle
          cx="65"
          cy="65"
          r={R}
          className="bn-ring-fill"
          style={{
            stroke: color,
            strokeDasharray: C,
            strokeDashoffset: C * (1 - pct),
          }}
        />
      </svg>
      <div className="bn-ring-center">
        <span className="bn-ring-score" style={{ color }}>
          {safe.toFixed(1)}
        </span>
        <span className="bn-ring-suffix">/ 5</span>
      </div>
      {levelLabel && <span className="bn-ring-level">{levelLabel}</span>}
    </div>
  );
};

/* ============================================================
 * CARD 1 — Bottleneck
 * ============================================================ */

function buildBottleneckInsight(data, pillarKey) {
  const chain = [
    data?.bottleneck_narrative,
    data?.decision_vulnerability_narrative,
    data?.pillar_interpretations?.[pillarKey],
    data?.dimension_summaries?.[pillarKey],
  ];
  for (const t of chain) {
    const v = (t || "").trim();
    if (v) return truncateInsight(extractFirstSentence(v) || v, 170);
  }
  // Pillar-specific fallback
  const fallbacks = {
    people: "Decision rights, ownership and stewardship are not yet established — portfolio choices remain personality-led rather than role-led.",
    process: "Portfolio is reviewed ad hoc rather than on a governed cadence with stage-gates — making intake, change and retirement decisions inconsistent.",
    data: "Master data and product profitability are fragmented across systems — every portfolio decision is reconciled manually before it can be made.",
    technology: "Business systems are not yet adapted to surface a live portfolio view — decisions wait on monthly extracts instead of live evidence.",
  };
  return truncateInsight(fallbacks[pillarKey] || "Bottleneck details are not yet narrated for this pillar.", 170);
}

const BottleneckCard = ({ data }) => {
  const pillarKey = data?.bottleneck;
  if (!pillarKey) return null;
  const score = Number(data?.scores?.[pillarKey] ?? 0);
  const level = scoreToLevel(score);
  const sev = severityFromScore(score);
  const band = scoreToBand(score);
  const color = BAND_COLORS[band];
  const insight = buildBottleneckInsight(data, pillarKey);
  const label = PILLAR_LABELS[pillarKey] || pillarKey;

  return (
    <div className="bn-card" data-testid="dashboard-card-bottleneck">
      <div className="bn-card-head">
        <span className="bn-card-eyebrow">
          <AlertTriangle size={13} /> Bottleneck
        </span>
        <StatusChip label={LEVEL_TITLES[level] || "—"} severity={sev} testid="bottleneck-status" />
      </div>
      <div className="bn-bn-body">
        <div className="bn-bn-left">
          <RingGauge score={score} color={color} levelLabel={LEVEL_TITLES[level]} />
        </div>
        <div className="bn-bn-right">
          <div className="bn-bn-pillar" data-testid="bottleneck-pillar">{label}</div>
          <div className="bn-bn-meta">
            {LEVEL_TITLES[level]} · {score.toFixed(1)} / 5.0
          </div>
          <p className="bn-bn-insight" data-testid="bottleneck-insight">{insight}</p>
          <div className="bn-bn-risks" data-testid="bottleneck-risks">
            <StatusChip label="Profit leakage" severity="critical" />
            <StatusChip label="Strategic drift" severity="warning" />
            <StatusChip label="Decision latency" severity="warning" />
          </div>
        </div>
      </div>
    </div>
  );
};

/* ============================================================
 * CARD 2 — Preconditions
 * ============================================================ */

const PRECONDITIONS = [
  {
    key: "shared_product",
    label: "Shared product understanding",
    keywordsMissing: [
      "product definition", "common language", "unclear product", "productisation",
      "no productisation", "inconsistent product", "product family", "no productiz",
      "no product structure",
    ],
    pillars: ["people", "process"],
  },
  {
    key: "structure",
    label: "Commercial + technical structure",
    keywordsMissing: [
      "bom", "fragment", "item hierarchy", "no product structure", "no link between",
      "commercial and technical", "no family", "no configuration",
    ],
    pillars: ["process", "data"],
  },
  {
    key: "classification",
    label: "Strategic product classification",
    keywordsMissing: [
      "strategic", "supportive", "non-strategic", "segmentation", "prioritisation",
      "no portfolio prioritisation", "no classification",
    ],
    pillars: ["process", "people"],
  },
  {
    key: "ownership",
    label: "Ownership + governance",
    keywordsMissing: [
      "no owner", "no accountability", "no stewardship", "no governance",
      "decision rights", "no governance body", "unclear ownership", "no steward",
    ],
    pillars: ["people"],
  },
  {
    key: "cadence",
    label: "PPM process + review cadence",
    keywordsMissing: [
      "stage-gate", "stage gate", "review cadence", "intake", "go-kill", "ad hoc",
      "ad-hoc", "portfolio review", "review rhythm", "no formal review",
    ],
    pillars: ["process"],
  },
  {
    key: "data_reporting",
    label: "Data + reporting readiness",
    keywordsMissing: [
      "fragmented", "single source", "manual profitability", "no dashboard",
      "isolated reporting", "manual reconciliation", "no live", "spreadsheets",
    ],
    pillars: ["data", "technology"],
  },
];

const PARTIAL_HINTS = ["inconsistent", "isolated", "manual", "incomplete", "partial", "limited", "ad hoc", "ad-hoc"];

function buildSignalCorpus(data) {
  const parts = [
    ...(data?.key_findings || []),
    ...(data?.critical_gaps || []),
    ...Object.values(data?.dimension_summaries || {}),
    ...Object.values(data?.pillar_interpretations || {}),
    data?.bottleneck_narrative || "",
    data?.decision_vulnerability_narrative || "",
  ];
  return parts.filter(Boolean).join(" \n ").toLowerCase();
}

function derivePreconditionStatus(precondition, corpus, scores) {
  const hits = precondition.keywordsMissing.filter((kw) => corpus.includes(kw));
  const avgScore =
    precondition.pillars.reduce((acc, p) => acc + (Number(scores?.[p]) || 0), 0) /
    precondition.pillars.length;
  // No textual evidence + decent score → Met
  if (hits.length === 0 && avgScore >= 3.5) return "Met";
  // Strong textual evidence of absence OR very low pillar avg → Missing
  if (hits.length >= 2 || avgScore < 2.0) return "Missing";
  // Soft signals or moderate score → Partial
  const partialHit = PARTIAL_HINTS.some((h) => corpus.includes(h));
  if (hits.length >= 1 || partialHit || avgScore < 3.0) return "Partial";
  return "Met";
}

const PRECON_SEVERITY = { Met: "good", Partial: "warning", Missing: "critical" };
const PRECON_ICON = {
  Met: <CheckCircle2 size={14} />,
  Partial: <CircleDot size={14} />,
  Missing: <XCircle size={14} />,
};

const PreconditionsCard = ({ data }) => {
  const corpus = buildSignalCorpus(data);
  const scores = data?.scores || {};

  const rows = PRECONDITIONS.map((p) => ({
    ...p,
    status: derivePreconditionStatus(p, corpus, scores),
  }));
  const metCount = rows.filter((r) => r.status === "Met").length;

  return (
    <div className="bn-card" data-testid="dashboard-card-preconditions">
      <div className="bn-card-head">
        <span className="bn-card-eyebrow">
          <Layers size={13} /> Preconditions
        </span>
        <StatusChip label={`${metCount} / ${rows.length} met`} severity={metCount >= 4 ? "good" : metCount >= 2 ? "warning" : "critical"} />
      </div>
      <ul className="bn-precon-list">
        {rows.map((row) => (
          <li key={row.key} className="bn-precon-row" data-testid={`precon-${row.key}`}>
            <span className="bn-precon-icon" style={{ color: SEVERITY_COLORS[PRECON_SEVERITY[row.status]] }}>
              {PRECON_ICON[row.status]}
            </span>
            <span className="bn-precon-label">{row.label}</span>
            <StatusChip label={row.status} severity={PRECON_SEVERITY[row.status]} />
          </li>
        ))}
      </ul>
    </div>
  );
};

/* ============================================================
 * CARD 3 — Portfolio Decision Impact
 * ============================================================ */

const DECISION_TYPES = [
  { key: "discontinuation", label: "Discontinuation" },
  { key: "new_launch", label: "New Product Launch" },
  { key: "product_change", label: "Product Change" },
  { key: "investment", label: "Portfolio Investment" },
  { key: "eol", label: "EOL / Retirement" },
  { key: "rationalisation", label: "Product Family Rationalisation" },
];

const FALLBACK_BY_PILLAR = {
  data: {
    investment: "High", rationalisation: "High", eol: "High",
    new_launch: "Medium", product_change: "Medium", discontinuation: "Medium",
  },
  process: {
    new_launch: "High", product_change: "High",
    investment: "Medium", discontinuation: "Medium", eol: "Medium", rationalisation: "Medium",
  },
  people: {
    investment: "High",
    rationalisation: "Medium", new_launch: "Medium", product_change: "Medium",
    eol: "Medium", discontinuation: "Medium",
  },
  technology: {
    product_change: "High", eol: "High",
    new_launch: "Medium", investment: "Medium", discontinuation: "Medium", rationalisation: "Medium",
  },
};

const IMPACT_LABELS = {
  discontinuation: ["discontinuation", "discontinue", "kill"],
  new_launch: ["new product launch", "npd", "new launch", "launch"],
  product_change: ["product change", "product modification", "configuration change"],
  investment: ["portfolio investment", "capability investment", "investment"],
  eol: ["eol", "end of life", "retirement"],
  rationalisation: ["rationalisation", "rationalization", "family rationalisation"],
};

const EXPLICIT_LEVELS = [
  { re: /high( risk)?/i, level: "High" },
  { re: /critical/i, level: "High" },
  { re: /medium( risk)?/i, level: "Medium" },
  { re: /moderate/i, level: "Medium" },
  { re: /low( risk)?/i, level: "Low" },
];

function deriveDecisionImpact(decisionKey, corpus, bottleneckPillar, bottleneckScore) {
  // Try to read explicit severity attached to this decision in the narrative.
  for (const kw of IMPACT_LABELS[decisionKey]) {
    const idx = corpus.indexOf(kw);
    if (idx === -1) continue;
    const window = corpus.slice(Math.max(0, idx - 60), idx + 120);
    for (const { re, level } of EXPLICIT_LEVELS) {
      if (re.test(window)) return level;
    }
  }
  // Fallback by bottleneck pillar.
  const byPillar = FALLBACK_BY_PILLAR[bottleneckPillar] || FALLBACK_BY_PILLAR.process;
  let level = byPillar[decisionKey] || "Medium";
  // Score-based softening / sharpening.
  if (bottleneckScore < 2.0 && level === "Medium") level = "High";
  if (bottleneckScore > 3.0 && level === "High") level = "Medium";
  if (bottleneckScore > 3.0 && level === "Medium") level = "Low";
  return level;
}

const PortfolioDecisionImpactCard = ({ data }) => {
  const corpus = buildSignalCorpus(data);
  const pillarKey = data?.bottleneck || "process";
  const pillarScore = Number(data?.scores?.[pillarKey] ?? 2.5);
  const rows = DECISION_TYPES.map((d) => ({
    ...d,
    level: deriveDecisionImpact(d.key, corpus, pillarKey, pillarScore),
  }));
  const worst = rows.find((r) => r.level === "High") || rows[0];

  return (
    <div className="bn-card" data-testid="dashboard-card-decision-impact">
      <div className="bn-card-head">
        <span className="bn-card-eyebrow">
          <Compass size={13} /> Portfolio Decision Impact
        </span>
        <StatusChip
          label={worst ? `${worst.label} most exposed` : "—"}
          severity={severityFromImpact(worst?.level || "Medium")}
        />
      </div>
      <p className="bn-card-sub">Decision types most exposed today</p>
      <ul className="bn-dec-list">
        {rows.map((row) => {
          const sev = severityFromImpact(row.level);
          const isWorst = row === worst && worst.level === "High";
          return (
            <li
              key={row.key}
              className={`bn-dec-row${isWorst ? " is-worst" : ""}`}
              data-testid={`decision-${row.key}`}
            >
              <span className="bn-dec-label">{row.label}</span>
              <SeverityBar severity={sev} />
              <StatusChip label={row.level} severity={sev} />
            </li>
          );
        })}
      </ul>
    </div>
  );
};

/* ============================================================
 * CARD 4 — PPM Governance Readiness
 * ============================================================ */

const GOVERNANCE_DIMS = [
  {
    key: "ownership",
    label: "Decision ownership",
    primaryPillar: "people",
    weak: ["no owner", "no accountability", "no stewardship", "no governance body", "unclear ownership", "no decision rights"],
    established: ["named owner", "governance body", "decision rights", "accountability"],
  },
  {
    key: "cadence",
    label: "Review cadence",
    primaryPillar: "process",
    weak: ["no review", "ad hoc", "ad-hoc", "no cadence", "no formal review", "no portfolio review"],
    established: ["monthly review", "quarterly review", "stage-gate", "stage gate", "review cadence", "portfolio review"],
  },
  {
    key: "kpi",
    label: "KPI discipline",
    primaryPillar: "data",
    weak: ["no kpi", "no metrics", "no target", "no profitability", "manual profitability", "no dashboard"],
    established: ["kpi", "metrics", "profitability", "dashboard", "scorecard", "renewal rate"],
  },
  {
    key: "alignment",
    label: "Cross-functional alignment",
    primaryPillar: "process",
    weak: ["siloed", "silos", "handoff", "no shared visibility", "no cross-functional", "no alignment"],
    established: ["cross-functional", "shared visibility", "joint review", "aligned"],
  },
];

function deriveGovernanceReadiness(dim, corpus, scores) {
  const score = Number(scores?.[dim.primaryPillar] ?? 0);
  const weakHits = dim.weak.filter((k) => corpus.includes(k)).length;
  const strongHits = dim.established.filter((k) => corpus.includes(k)).length;
  if (weakHits >= 2 || score < 2.0) return "Weak";
  if (strongHits >= 2 && score >= 3.5) return "Established";
  if (score >= 3.5 && weakHits === 0) return "Established";
  return "Emerging";
}

const GOV_SEVERITY = { Weak: "critical", Emerging: "warning", Established: "good" };
const GOV_BAR_STEPS = { Weak: 1, Emerging: 2, Established: 3 };

const GovernanceReadinessCard = ({ data }) => {
  const corpus = buildSignalCorpus(data);
  const scores = data?.scores || {};
  const rows = GOVERNANCE_DIMS.map((d) => ({
    ...d,
    status: deriveGovernanceReadiness(d, corpus, scores),
  }));
  const established = rows.filter((r) => r.status === "Established").length;

  return (
    <div className="bn-card" data-testid="dashboard-card-governance">
      <div className="bn-card-head">
        <span className="bn-card-eyebrow">
          <ShieldCheck size={13} /> PPM Governance Readiness
        </span>
        <StatusChip
          label={`${established} / ${rows.length} established`}
          severity={established >= 3 ? "good" : established >= 1 ? "warning" : "critical"}
        />
      </div>
      <p className="bn-card-sub">Operating-model readiness for repeatable PPM</p>
      <ul className="bn-gov-list">
        {rows.map((row) => {
          const sev = GOV_SEVERITY[row.status];
          const steps = GOV_BAR_STEPS[row.status];
          return (
            <li key={row.key} className="bn-gov-row" data-testid={`gov-${row.key}`}>
              <div className="bn-gov-top">
                <span className="bn-gov-label">{row.label}</span>
                <StatusChip label={row.status} severity={sev} />
              </div>
              <div className="bn-gov-steps" data-severity={sev} style={{ "--c": SEVERITY_COLORS[sev] }}>
                {[1, 2, 3].map((i) => (
                  <span key={i} className={`bn-gov-step${i <= steps ? " on" : ""}`} />
                ))}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
};

/* ============================================================
 * Section wrapper — renders the 2x2 dashboard grid
 * ============================================================ */

export const AssessmentDashboardSection = ({ data }) => {
  return (
    <section className="bn-dashboard" data-testid="report-assessment-dashboard">
      <div className="bn-grid">
        <BottleneckCard data={data} />
        <PreconditionsCard data={data} />
        <PortfolioDecisionImpactCard data={data} />
        <GovernanceReadinessCard data={data} />
      </div>
    </section>
  );
};

export default AssessmentDashboardSection;
