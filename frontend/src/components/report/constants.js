// ── Dimension list ────────────────────────────────────────────────────────────
export const DIMENSIONS = ["people", "process", "data", "technology"];

// ── Pillar labels & icon keys ────────────────────────────────────────────────
export const PILLAR_LABELS = {
  people:     "People",
  process:    "Process",
  data:       "Data",
  technology: "Technology",
};

/** Key → Lucide icon name (resolved in BottleneckSection to avoid importing
 *  Lucide in this non-JSX module). */
export const PILLAR_ICONS_MAP = {
  people:     "Users",
  process:    "ClipboardCheck",
  data:       "Database",
  technology: "Monitor",
};

// ── Maturity levels ───────────────────────────────────────────────────────────
export const MATURITY_LEVELS = [
  {
    level: 1,
    name: "Ad Hoc",
    desc: "No structured approach. Decisions are reactive, informal, and based on individual intuition. Data is fragmented; processes are undefined.",
    color: "#EF4444",
  },
  {
    level: 2,
    name: "Developing",
    desc: "Some processes are defined but inconsistently applied. Basic data collection exists but lacks integration. People have varying levels of PPM understanding.",
    color: "#C9A84C",
  },
  {
    level: 3,
    name: "Defined",
    desc: "Structured processes and roles are established. Data is accessible but not fully integrated. A common language around portfolio management is forming.",
    color: "#C9A84C",
  },
  {
    level: 4,
    name: "Managed",
    desc: "Data-driven decisions are supported by integrated systems. Metrics and KPIs are actively tracked and used in governance. Decisions are traceable.",
    color: "#34D399",
  },
  {
    level: 5,
    name: "Predictive",
    desc: "Predictive, evidence-based decisions. Continuous-improvement culture embedded. All four PPDT dimensions fully aligned; AI-assisted analytics, scenario modelling, and automated lifecycle alerts drive portfolio choices in real time.",
    color: "#C9A84C",
  },
];

/**
 * LEVEL_THRESHOLDS — ordered high→low so the first match wins.
 * Used by levelName() in BottleneckSection.jsx.
 */
export const LEVEL_THRESHOLDS = [
  { min: 4.5, name: "Predictive" },
  { min: 3.5, name: "Managed" },
  { min: 2.5, name: "Defined" },
  { min: 1.5, name: "Developing" },
  { min: 0,   name: "Ad Hoc" },
];

// ── R6 Bottleneck: per-pillar fallback text ───────────────────────────────────

/**
 * BN_ROOT_CAUSE_FALLBACK — Zone 3L ("What the assessment found")
 * Used only when the AI report does not supply dimension_summaries[key]
 * or pillar_findings[key][0].
 * Source: Hannila (2019) doctoral dissertation framework;
 *         Hannila et al. (2020) 8-company study findings.
 */
export const BN_ROOT_CAUSE_FALLBACK = {
  people:
    "Roles, competencies, and decision-making accountability required for data-driven PPM are not yet formally established. Portfolio decisions default to individuals with informal authority rather than defined governance structures.",
  process:
    "Portfolio review cadences and decision gates are absent or inconsistently applied. No formal Stage-Gate or equivalent intake process exists to structure go/kill criteria at each development milestone.",
  data:
    "Product-level master data — cost, revenue, margin, lifecycle stage, and capability family contribution — is incomplete, fragmented across systems, or not trusted by decision-makers as a reliable basis for action.",
  technology:
    "Systems supporting portfolio management are fragmented or manually reconciled. Product data cannot be aggregated to a portfolio view without bespoke effort, preventing product-level insights from surfacing at the point of decision.",
};

/**
 * BN_CONSEQUENCE_FALLBACK — Zone 3R ("Why this constrains maturity")
 * Used only when the AI report does not supply bottleneck_constraint,
 * pillar_interpretations[key], or pillar_findings[key][1].
 * Source: Hannila et al. (2022) bottleneck-capping principle;
 *         Hannila et al. (2020) empirical evidence.
 */
export const BN_CONSEQUENCE_FALLBACK = {
  people:
    "Hannila et al. (2022): people-capability gaps are the most common reason portfolio data initiatives stall — without a named owner and defined mandate, tool investments do not translate into improved decision quality.",
  process:
    "Hannila (2019): companies with weak portfolio governance retain up to 30% more low-margin products than peers at equivalent revenue scale. Process gaps allow under-performing initiatives to persist unchallenged.",
  data:
    "Hannila et al. (2020) 8-company study: data quality was the single most-cited barrier to data-driven PPM. Every participating company reported that portfolio decisions were made on estimated rather than verified figures.",
  technology:
    "Silvola (2018) and Hannila et al. (2022): technology gaps force portfolio managers into spreadsheet workarounds that introduce lag, version conflicts, and decision latency — eroding the value of even well-designed processes.",
};

// ── R6 Bottleneck: risk pill definitions ─────────────────────────────────────

/**
 * RISK_PILL_DEFS — drives Zone 4 of BottleneckSection.
 * Icon is the Lucide component name (string); resolved in the JSX layer.
 * fallback is used only when the AI report provides no matching sentence.
 *
 * Priority chain in buildRiskItems():
 *   report.risk_pills[pillarKey][key]
 *   → critical_gaps sentence containing label
 *   → key_findings sentence containing label
 *   → fallback
 */
export const RISK_PILL_DEFS = [
  {
    key:      "profit_leakage",
    label:    "Profit leakage",
    Icon:     "TrendingDown",
    fallback: "No corporate-level data model connecting product families to cost, profitability, or supportability — capability view requires manual reconstruction; no standing financial model of through-life value (Precondition 3: holistic, corporate-level data model).",
  },
  {
    key:      "strategic_drift",
    label:    "Strategic drift",
    Icon:     "ShieldAlert",
    fallback: "Product master data fragmented across multiple systems with no single source of truth; critical cost estimating models held in personal spreadsheets; non-engineering functions cannot access product data without intermediation (Precondition 3: holistic, corporate-level data model).",
  },
  {
    key:      "decision_latency",
    label:    "Decision latency",
    Icon:     "Zap",
    fallback: "No data ownership or stewardship roles defined — data quality issues addressed reactively when noticed by senior individuals; no accountability structure, no SLA, no governance (Precondition 4: data governance ensuring quality, ownership, and accessibility).",
  },
];

// ── Misc ──────────────────────────────────────────────────────────────────────
export const CONTACT_EMAIL = "shalitha.samarakoonmudiyanselage@student.oulu.fi";
