/**
 * AssessmentDashboard.jsx — v2
 *
 * Layout:
 *   Row 1 — Bottleneck (full width, hero)
 *   Row 2 — Preconditions (half) · Portfolio Decision Impact (half)
 *   Row 3 — Portfolio Renewal Radar (full width)
 *
 * Design language is shared across every card (same surface, radius, padding,
 * eyebrow, chip, and severity palette). All AI prose is normalised through a
 * deterministic composer so dashboard structure stays stable across companies.
 *
 * Severity palette (aliased to maturity bands):
 *   red    #DC2626 (--bn-critical)  · Weak / Critical / High
 *   amber  #F59E0B (--bn-warning)   · Partial / Medium / Moderate
 *   green  #10B981 (--bn-good)      · Met / Established / Low
 *   sky    #0EA5E9 (--bn-advanced)  · Advanced / Strong (band 4)
 *
 * The PDF export pipeline in `/app/backend/pdf_builder.py` is intentionally
 * untouched — the verbose narrative still ships in downloads.
 */
import {
  AlertTriangle,
  Layers,
  Compass,
  Radar,
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

/* =====================================================================
 * Tokens & tiny helpers
 * ===================================================================== */

const SEVERITY_COLORS = {
  critical: "var(--bn-critical, #DC2626)",
  warning: "var(--bn-warning, #F59E0B)",
  good: "var(--bn-good, #10B981)",
  advanced: "var(--bn-advanced, #0EA5E9)",
  muted: "#94A3B8",
};

// Qualitative label shown for the always-visible Bottleneck Severity line.
// DBI itself is a derived/conceptual metric — we surface a plain-language
// label here rather than the raw index number.
const SEVERITY_LABELS = {
  critical: "Critical",
  warning: "High",
  good: "Moderate",
  advanced: "Low",
};

const PILLAR_LABELS = {
  people: "People",
  process: "Process",
  data: "Data",
  technology: "Technology",
};

export function extractFirstSentence(text = "") {
  const s = String(text || "").trim();
  if (!s) return "";
  const m = s.match(/[^.!?]+[.!?]/);
  return (m ? m[0] : s).trim();
}

export function truncateInsight(text = "", maxChars = 170) {
  const s = String(text || "").trim();
  if (s.length <= maxChars) return s;
  const cut = s.slice(0, maxChars);
  const space = cut.lastIndexOf(" ");
  return `${space > 60 ? cut.slice(0, space) : cut}…`;
}

function severityFromScore(score) {
  const b = scoreToBand(score);
  if (b <= 1) return "critical";
  if (b === 2) return "warning";
  if (b === 3) return "good";
  return "advanced";
}

function severityFromImpact(level) {
  if (level === "High") return "critical";
  if (level === "Medium") return "warning";
  return "good";
}

/* =====================================================================
 * Atoms — shared across every card so spacing/typography stay consistent
 * ===================================================================== */

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

const CardHead = ({ icon: Icon, eyebrow, chip, sub }) => (
  <header className="bn-card-head-block">
    <div className="bn-card-head">
      <span className="bn-card-eyebrow">
        <Icon size={13} /> {eyebrow}
      </span>
      {chip}
    </div>
    {sub && <p className="bn-card-sub">{sub}</p>}
  </header>
);

const CardFooter = ({ children }) =>
  children ? <p className="bn-card-foot">{children}</p> : null;

const RingGauge = ({ score = 0, color = SEVERITY_COLORS.critical, levelLabel = "" }) => {
  const safe = Math.max(0, Math.min(5, Number(score) || 0));
  const pct = safe / 5;
  const R = 62;
  const C = 2 * Math.PI * R;
  return (
    <div className="bn-ring bn-ring--lg">
      <svg viewBox="0 0 150 150" className="bn-ring-svg">
        <circle cx="75" cy="75" r={R} className="bn-ring-track" />
        <circle
          cx="75"
          cy="75"
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

/* =====================================================================
 * Signal corpus (lowercased AI text used by all derivation helpers)
 * ===================================================================== */

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

/* =====================================================================
 * CARD 1 — Bottleneck (full width, hero)
 * ===================================================================== */

const BOTTLENECK_DEFINITIONS = {
  people: "the People pillar captures decision rights, ownership, and the human governance through which portfolio choices actually get made.",
  process: "the Process pillar captures stage-gate discipline, review cadence, and the formal mechanics through which portfolio decisions move from intake to closure.",
  data: "the Data pillar captures master-data integrity, product profitability visibility, and the evidence base every portfolio decision is supposed to rest on.",
  technology: "the Technology pillar captures whether business IT systems can surface a live, integrated portfolio view at the moment a decision must be made.",
};

const BOTTLENECK_CONSEQUENCE = {
  people: "Until ownership is named and decision rights are explicit, portfolio choices remain personality-led and inconsistent across the lifecycle.",
  process: "Until a governed cadence exists, intake, change, and retirement decisions stay reactive and the portfolio drifts.",
  data: "Until master data and profitability are integrated, every portfolio decision waits on manual reconciliation before it can be made.",
  technology: "Until business IT supports a live portfolio view, leadership reviews lag the reality of the market by weeks or months.",
};

function composeBottleneckExplanation(data, pillarKey) {
  const def = `In this assessment, ${BOTTLENECK_DEFINITIONS[pillarKey] || ""}`;
  const cons = BOTTLENECK_CONSEQUENCE[pillarKey] || "";
  // Pull a short "why" signal from the AI fields. We lowercase only the
  // first character (so the clause flows after "because") and preserve any
  // acronyms / proper-nouns intact.
  const sourceChain = [
    data?.dimension_summaries?.[pillarKey],
    data?.pillar_interpretations?.[pillarKey],
    data?.bottleneck_narrative,
    data?.decision_vulnerability_narrative,
  ];
  let why = "";
  for (const t of sourceChain) {
    const s = extractFirstSentence(t || "");
    if (s && s.length >= 20) {
      const stripped = s.replace(/[.!?]+$/, "");
      // Only lowercase the very first character so acronyms (SAP, BI, ERP…)
      // keep their casing.
      const flowed = stripped.charAt(0).toLowerCase() + stripped.slice(1);
      why = `It is the binding constraint here because ${truncateInsight(flowed, 110)}.`;
      break;
    }
  }

  const sentences = [def, why, cons].filter(Boolean);
  let out = sentences.join(" ").replace(/\s+/g, " ").trim();
  // If the full 3-sentence version overflows, drop the (optional) "why"
  // sentence before truncating — we never want to lose the consequence.
  if (out.length > 360 && why) {
    out = [def, cons].join(" ").replace(/\s+/g, " ").trim();
  }
  if (out.length > 360) out = truncateInsight(out, 358);
  return out;
}

const BottleneckCard = ({ data }) => {
  const pillarKey = data?.bottleneck;
  if (!pillarKey) return null;
  const score = Number(data?.scores?.[pillarKey] ?? 0);
  const level = scoreToLevel(score);
  const sev = severityFromScore(score);
  const band = scoreToBand(score);
  const color = BAND_COLORS[band];
  const label = PILLAR_LABELS[pillarKey] || pillarKey;
  const explanation = composeBottleneckExplanation(data, pillarKey);

  // Decision Bottleneck Index — computed by the backend from
  // scores × contextual_weights. Rendered as a compact secondary chip so it
  // sits alongside the classical bottleneck (lowest-scoring pillar) without
  // competing with it. Falls back gracefully when the report predates DBI or
  // uses equal weights (contextual == equal → DBI is null).
  const dbi = data?.decision_bottleneck_index || null;
  const dbiSameAsBottleneck = dbi && dbi.pillar === pillarKey;
  const dbiSeverity = dbi
    ? dbi.direction === "above-baseline" ? "good" : "warning"
    : "muted";

  return (
    <article className="bn-card" data-testid="dashboard-card-bottleneck">
      <CardHead
        icon={AlertTriangle}
        eyebrow="Bottleneck"
        chip={<StatusChip label={LEVEL_TITLES[level] || "—"} severity={sev} testid="bottleneck-status" />}
      />
      <div className="bn-bn-body">
        <div className="bn-bn-left">
          <RingGauge score={score} color={color} levelLabel={LEVEL_TITLES[level]} />
        </div>
        <div className="bn-bn-right">
          <h3 className="bn-bn-pillar" data-testid="bottleneck-pillar">
            {label}
            <span className="bn-bn-pillar-meta"> · {LEVEL_TITLES[level]} · {score.toFixed(1)} / 5.0</span>
          </h3>
          {dbi && (
            <div className="bn-bn-dbi" data-testid="bottleneck-dbi">
              <span className="bn-bn-dbi-key">DBI</span>
              <span className="bn-bn-dbi-val">
                {PILLAR_LABELS[dbi.pillar] || dbi.pillar}
                <span className="bn-bn-dbi-delta"> ({dbi.gap > 0 ? "+" : ""}{Number(dbi.gap).toFixed(2)})</span>
              </span>
              <StatusChip label={dbi.direction.replace("-", " ")} severity={dbiSeverity} />
              {dbiSameAsBottleneck && (
                <span className="bn-bn-dbi-note">· matches capability bottleneck</span>
              )}
            </div>
          )}
          <div className="bn-bn-severity" data-testid="bottleneck-severity">
            <span className="bn-bn-severity-label">Bottleneck Severity</span>
            <StatusChip label={SEVERITY_LABELS[sev] || "—"} severity={sev} />
          </div>
          <p className="bn-bn-explanation" data-testid="bottleneck-insight">{explanation}</p>
        </div>
      </div>
      <div className="bn-bn-risks-wrap">
        <div className="bn-bn-risks" data-testid="bottleneck-risks">
          <StatusChip label="Profit leakage" severity="critical" />
          <StatusChip label="Strategic drift" severity="warning" />
          <StatusChip label="Decision latency" severity="warning" />
        </div>
        <p className="bn-bn-risks-note">
          Together, these capture how the bottleneck weakens value capture, strategic clarity, and decision speed.
        </p>
      </div>
    </article>
  );
};

/* =====================================================================
 * CARD 2 — Preconditions (half width, theory-grounded)
 * Hannila et al. (2020); Hannila (2019)
 * ===================================================================== */

const PRECONDITIONS = [
  {
    n: 1,
    key: "p1_understanding",
    title: "Mutual understanding of company products",
    blurb: "A shared definition of what counts as a product across functions.",
    pillars: ["people", "process"],
    weak: ["product definition", "common language", "unclear product", "no productisation", "no productization", "inconsistent product", "no product structure", "no productiz"],
  },
  {
    n: 2,
    key: "p2_structure",
    title: "Commercial and technical product structure",
    blurb: "Linked commercial families and technical BOM hierarchy.",
    pillars: ["process", "data"],
    weak: ["bom", "fragment", "item hierarchy", "no product structure", "no link between", "commercial and technical", "no family", "no configuration"],
  },
  {
    n: 3,
    key: "p3_data_model",
    title: "Holistic corporate-level data model",
    blurb: "Master data connected to the key business processes.",
    pillars: ["data", "technology"],
    weak: ["fragmented", "single source", "no single source", "siloed data", "manual reconciliation", "data silos", "isolated", "no master data", "no integrated data"],
  },
  {
    n: 4,
    key: "p4_classification",
    title: "Product classification and strategic role visibility",
    blurb: "Strategic, supportive, and non-strategic categorisation in active use.",
    pillars: ["process", "people"],
    weak: ["no strategic", "no classification", "no segmentation", "no portfolio prioritisation", "no prioritization", "no supportive", "non-strategic", "no strategic role"],
  },
  {
    n: 5,
    key: "p5_governance_it",
    title: "Data governance and business IT support",
    blurb: "Ownership of data quality plus IT able to surface a live portfolio view.",
    pillars: ["data", "technology"],
    weak: ["no governance", "no data owner", "no data ownership", "no stewardship", "manual profitability", "no dashboard", "no live", "no real-time", "spreadsheets"],
  },
];

const PARTIAL_HINTS = ["inconsistent", "isolated", "manual", "incomplete", "partial", "limited", "ad hoc", "ad-hoc"];

function derivePreconditionStatus(precondition, corpus, scores) {
  const hits = precondition.weak.filter((kw) => corpus.includes(kw));
  const avgScore =
    precondition.pillars.reduce((acc, p) => acc + (Number(scores?.[p]) || 0), 0) /
    precondition.pillars.length;
  if (hits.length === 0 && avgScore >= 3.5) return "Met";
  if (hits.length >= 2 || avgScore < 2.0) return "Missing";
  const partial = PARTIAL_HINTS.some((h) => corpus.includes(h));
  if (hits.length >= 1 || partial || avgScore < 3.0) return "Partial";
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
  const rows = PRECONDITIONS.map((p) => ({ ...p, status: derivePreconditionStatus(p, corpus, scores) }));
  const metCount = rows.filter((r) => r.status === "Met").length;

  return (
    <article className="bn-card" data-testid="dashboard-card-preconditions">
      <CardHead
        icon={Layers}
        eyebrow="Preconditions"
        chip={
          <StatusChip
            label={`${metCount} / ${rows.length} met`}
            severity={metCount >= 4 ? "good" : metCount >= 2 ? "warning" : "critical"}
          />
        }
        sub="Five preconditions for fact-based, data-driven PPM."
      />
      <ul className="bn-precon-list bn-precon-list--theory">
        {rows.map((row) => (
          <li key={row.key} className="bn-precon-row" data-testid={`precon-${row.key}`}>
            <span className="bn-precon-num">P{row.n}</span>
            <div className="bn-precon-text">
              <span className="bn-precon-title">{row.title}</span>
              <span className="bn-precon-blurb">{row.blurb}</span>
            </div>
            <span className="bn-precon-status">
              <span className="bn-precon-icon" style={{ color: SEVERITY_COLORS[PRECON_SEVERITY[row.status]] }}>
                {PRECON_ICON[row.status]}
              </span>
              <StatusChip label={row.status} severity={PRECON_SEVERITY[row.status]} />
            </span>
          </li>
        ))}
      </ul>
      <CardFooter>Based on Hannila et al. (2020); Hannila (2019).</CardFooter>
    </article>
  );
};

/* =====================================================================
 * CARD 3 — Portfolio Decision Impact (half width, theory-named)
 * ===================================================================== */

const DECISION_TYPES = [
  { key: "discontinuation", label: "Discontinuation",            keywords: ["discontinuation", "discontinue", "kill"] },
  { key: "new_launch",      label: "New Product Launch",         keywords: ["new product launch", "npd", "new launch", "launch"] },
  { key: "product_change",  label: "Engineering Change",         keywords: ["engineering change", "product change", "configuration change", "product modification"] },
  { key: "investment",      label: "Capability Investment",      keywords: ["capability investment", "portfolio investment", "investment"] },
  { key: "eol",             label: "Ramp-down / Retirement",     keywords: ["ramp-down", "ramp down", "eol", "end of life", "end-of-life", "retirement"] },
  { key: "rationalisation", label: "Product Family Rationalisation", keywords: ["rationalisation", "rationalization", "family rationalisation"] },
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

const EXPLICIT_LEVELS = [
  { re: /high( risk)?/i, level: "High" },
  { re: /critical/i, level: "High" },
  { re: /medium( risk)?/i, level: "Medium" },
  { re: /moderate/i, level: "Medium" },
  { re: /low( risk)?/i, level: "Low" },
];

function deriveDecisionImpact(decision, corpus, bottleneckPillar, bottleneckScore) {
  for (const kw of decision.keywords) {
    const idx = corpus.indexOf(kw);
    if (idx === -1) continue;
    const window = corpus.slice(Math.max(0, idx - 60), idx + 120);
    for (const { re, level } of EXPLICIT_LEVELS) {
      if (re.test(window)) return level;
    }
  }
  const byPillar = FALLBACK_BY_PILLAR[bottleneckPillar] || FALLBACK_BY_PILLAR.process;
  let level = byPillar[decision.key] || "Medium";
  if (bottleneckScore < 2.0 && level === "Medium") level = "High";
  if (bottleneckScore > 3.0 && level === "High") level = "Medium";
  if (bottleneckScore > 3.0 && level === "Medium") level = "Low";
  return level;
}

function computeDecisionRows(data) {
  const corpus = buildSignalCorpus(data);
  const pillarKey = data?.bottleneck || "process";
  const pillarScore = Number(data?.scores?.[pillarKey] ?? 2.5);
  return DECISION_TYPES.map((d) => ({
    ...d,
    level: deriveDecisionImpact(d, corpus, pillarKey, pillarScore),
  }));
}

const PortfolioDecisionImpactCard = ({ data, rows }) => {
  const worst = rows.find((r) => r.level === "High") || rows[0];
  return (
    <article className="bn-card" data-testid="dashboard-card-decision-impact">
      <CardHead
        icon={Compass}
        eyebrow="Portfolio Decision Impact"
        chip={
          worst ? (
            <StatusChip
              label={`${worst.label} most exposed`}
              severity={severityFromImpact(worst.level)}
            />
          ) : null
        }
        sub="Decision types most constrained by the current bottleneck."
      />
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
      <CardFooter>Based on Hannila (2019); Tolonen et al. (2015); Cooper et al. (2001).</CardFooter>
    </article>
  );
};

/* =====================================================================
 * CARD 4 — Portfolio Renewal Radar (full width, SVG radar)
 * Derived from the same decision-impact logic but rendered as a holistic
 * exposure pattern instead of a list.
 * ===================================================================== */

const LEVEL_TO_RADIUS = { Low: 0.25, Medium: 0.55, High: 0.92 };

// Short axis labels for the radar (full names live in the legend on the right).
const RADAR_SHORT_LABELS = {
  discontinuation: "Discontinue",
  new_launch: "Launch",
  product_change: "Change",
  investment: "Investment",
  eol: "Retire",
  rationalisation: "Rationalise",
};

function PortfolioRenewalRadar({ rows, accent = "#0891B2" }) {
  const N = rows.length;
  const size = 360;
  const cx = size / 2;
  const cy = size / 2;
  const rMax = size / 2 - 60; // leave room for axis labels outside the chart
  const angleFor = (i) => (Math.PI * 2 * i) / N - Math.PI / 2;

  const polygon = rows
    .map((r, i) => {
      const a = angleFor(i);
      const d = rMax * LEVEL_TO_RADIUS[r.level];
      return `${cx + d * Math.cos(a)},${cy + d * Math.sin(a)}`;
    })
    .join(" ");

  // Reference rings at 0.25 / 0.55 / 0.92 with labels Low / Med / High
  const RINGS = [
    { r: 0.25, label: "Low" },
    { r: 0.55, label: "Medium" },
    { r: 0.92, label: "High" },
  ];

  return (
    <svg
      viewBox={`0 0 ${size} ${size}`}
      className="bn-radar-svg"
      role="img"
      aria-label="Portfolio renewal exposure radar"
    >
      <defs>
        <radialGradient id="radarFill" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={accent} stopOpacity="0.55" />
          <stop offset="100%" stopColor={accent} stopOpacity="0.10" />
        </radialGradient>
      </defs>

      {/* Concentric rings */}
      {RINGS.map((ring) => (
        <circle
          key={ring.label}
          cx={cx}
          cy={cy}
          r={rMax * ring.r}
          className="bn-radar-ring"
        />
      ))}

      {/* Axis spokes */}
      {rows.map((_, i) => {
        const a = angleFor(i);
        return (
          <line
            key={`spoke-${i}`}
            x1={cx}
            y1={cy}
            x2={cx + rMax * Math.cos(a)}
            y2={cy + rMax * Math.sin(a)}
            className="bn-radar-spoke"
          />
        );
      })}

      {/* Ring labels — tiny, only along the top spoke */}
      {RINGS.map((ring) => (
        <text
          key={`rl-${ring.label}`}
          x={cx + 3}
          y={cy - rMax * ring.r + 3}
          className="bn-radar-ringlabel"
        >
          {ring.label}
        </text>
      ))}

      {/* Exposure polygon */}
      <polygon points={polygon} className="bn-radar-shape" fill="url(#radarFill)" stroke={accent} />

      {/* Vertex dots */}
      {rows.map((r, i) => {
        const a = angleFor(i);
        const d = rMax * LEVEL_TO_RADIUS[r.level];
        return (
          <circle
            key={`v-${i}`}
            cx={cx + d * Math.cos(a)}
            cy={cy + d * Math.sin(a)}
            r="4"
            className="bn-radar-vertex"
            style={{ fill: SEVERITY_COLORS[severityFromImpact(r.level)] }}
          />
        );
      })}

      {/* Axis labels — placed just outside rMax (uses short labels) */}
      {rows.map((r, i) => {
        const a = angleFor(i);
        const lx = cx + (rMax + 18) * Math.cos(a);
        const ly = cy + (rMax + 18) * Math.sin(a);
        let anchor = "middle";
        if (Math.cos(a) > 0.35) anchor = "start";
        else if (Math.cos(a) < -0.35) anchor = "end";
        return (
          <text
            key={`l-${i}`}
            x={lx}
            y={ly}
            className="bn-radar-axislabel"
            textAnchor={anchor}
            dominantBaseline="middle"
          >
            {RADAR_SHORT_LABELS[r.key] || r.label}
          </text>
        );
      })}
    </svg>
  );
}

const PortfolioRenewalRadarCard = ({ rows }) => {
  const exposureScore = rows.reduce((acc, r) => acc + LEVEL_TO_RADIUS[r.level], 0) / rows.length;
  const exposureLabel =
    exposureScore >= 0.7 ? "High overall exposure"
      : exposureScore >= 0.45 ? "Moderate overall exposure"
      : "Contained exposure";
  const exposureSev =
    exposureScore >= 0.7 ? "critical" : exposureScore >= 0.45 ? "warning" : "good";
  const worst = rows.find((r) => r.level === "High");

  return (
    <article className="bn-card" data-testid="dashboard-card-renewal-radar">
      <CardHead
        icon={Radar}
        eyebrow="Portfolio Renewal Radar"
        chip={<StatusChip label={exposureLabel} severity={exposureSev} />}
        sub="Holistic exposure pattern across the product renewal lifecycle."
      />
      <div className="bn-radar-stage">
        <PortfolioRenewalRadar rows={rows} accent="#0891B2" />
      </div>
      <div className="bn-radar-footer">
        {worst && (
          <div className="bn-radar-callout">
            <span className="bn-radar-callout-label">Most exposed</span>
            <StatusChip label={worst.label} severity="critical" />
          </div>
        )}
        <div className="bn-radar-legend-scale">
          <span><i className="bn-dot bn-dot--good" /> Low</span>
          <span><i className="bn-dot bn-dot--warning" /> Medium</span>
          <span><i className="bn-dot bn-dot--critical" /> High</span>
        </div>
      </div>
      <CardFooter>
        Synthesis view · derived from the same decision logic used above (Hannila 2019; Tolonen et al. 2015).
      </CardFooter>
    </article>
  );
};

/* =====================================================================
 * Section wrapper — uniform 2×2 grid (all cards same width)
 * Row 1 — Bottleneck · Portfolio Renewal Radar
 * Row 2 — Preconditions · Portfolio Decision Impact
 * ===================================================================== */

export const AssessmentDashboardSection = ({ data }) => {
  const decisionRows = computeDecisionRows(data);
  return (
    <section className="bn-dashboard" data-testid="report-assessment-dashboard">
      <div className="bn-grid-2x2">
        <BottleneckCard data={data} />
        <PortfolioRenewalRadarCard rows={decisionRows} />
        <PreconditionsCard data={data} />
        <PortfolioDecisionImpactCard data={data} rows={decisionRows} />
      </div>
    </section>
  );
};

export default AssessmentDashboardSection;
