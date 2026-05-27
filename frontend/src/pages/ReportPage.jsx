import { useState, useCallback } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import axios from "axios";
import {
  AlertTriangle, RefreshCw, Clock, ArrowLeft, ArrowRight, ChevronDown,
  MessageSquare, Download, Info, GraduationCap, Printer,
} from "lucide-react";
import { toast } from "sonner";
import Layout from "../components/Layout";
import { useAssessment } from "../hooks/useData";
import { LoadingSpinner } from "../components/ScoreComponents";
import {
  buildReportData,
  scoreToLevel,
  scoreToBand,
  LEVEL_TITLES,
  BAND_COLORS,
  BAND_TEXT_COLORS,
} from "../lib/reportData";
import "../components/report/premium.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/* Level pill + class helpers — driven by numeric band (not discrete level index)
   so the colour scale stays continuous across pillar scores. */
const bandClass = (score) => `l${scoreToBand(score)}`;

/* ============ R1 Cover ============ */
const R1Cover = ({ data }) => {
  const { company, industry, business_model, role, date, kpi, bottleneck_capped } = data;
  const overallLvl = kpi.overall.level_index;
  const overallScore = kpi.overall.score;

  const metaParts = [industry, business_model, role, date].filter(Boolean);

  return (
    <section className="r1-cover" data-testid="report-r1-cover">
      <div className="r1-inner">
        <div className="r1-top">
          <div className="r1-left">
            <span className="r1-tag">PPDT Maturity Assessment</span>
            <h1 className="r1-company">{company}</h1>
            <div className="r1-meta">
              {metaParts.map((m, i) => (
                <span key={i} className="r1-meta-item">
                  <span>{m}</span>
                  {i < metaParts.length - 1 && <span className="sep">·</span>}
                </span>
              ))}
            </div>
            <div className="r1-complete">
              <span className="ico"><Clock size={13} /></span>
              Full Assessment · 45–60 minutes
            </div>
          </div>
          <div className="r1-right">
            <span className="r1-score-label">Overall Maturity</span>
            <div className="r1-score-block">
              <span className="r1-score" data-testid="report-overall-score">{overallScore.toFixed(1)}</span>
              <span className="r1-score-suffix">/ 5.0</span>
            </div>
            <span className="r1-level-name" data-testid="report-overall-level">
              {LEVEL_TITLES[overallLvl] || "—"}
            </span>
            {bottleneck_capped && (
              <div className="r1-bcap" data-testid="report-bottleneck-capped">
                <AlertTriangle size={11} />
                Bottleneck-capped
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 4-pillar score strip */}
      <div className="r1-strip">
        {kpi.pillars.map((p) => {
          const isBn = data.bottleneck === p.key;
          return (
            <div key={p.key} className={`r1-tile${isBn ? " bottleneck" : ""}`}>
              <div className="r1-tile-top">
                <div className="r1-tile-badge">{p.letter}</div>
                <span className="r1-tile-label">{p.name}</span>
                {isBn && <span className="r1-tile-bn-mark">⚠</span>}
              </div>
              <div className="r1-tile-score">{p.score.toFixed(1)}</div>
              <div className="r1-tile-level">{LEVEL_TITLES[p.level] || "—"}</div>
            </div>
          );
        })}
      </div>
    </section>
  );
};

/* ============ R2 Executive Summary ============ */
const R2ExecutiveSummary = ({ data }) => {
  const { kpi, bottleneck, bottleneck_capped, executive_summary, scores } = data;
  const bnPillar = data.kpi.pillars.find((p) => p.key === bottleneck);
  const strongest = [...kpi.pillars].sort((a, b) => b.score - a.score)[0];

  const intro =
    executive_summary ||
    `${data.company} scores ${scores.overall.toFixed(1)}/5.0 (${LEVEL_TITLES[kpi.overall.level_index]}) on the PPDT maturity baseline.${
      bottleneck_capped && bnPillar
        ? ` The ${bnPillar.name} pillar at ${bnPillar.score.toFixed(1)} is capping the full system — no matter how strong the other pillars score, portfolio decisions cannot become data-driven until this bottleneck is resolved.`
        : ""
    }`;

  return (
    <section className="r2" data-testid="report-r2">
      <div className="glass-card r2-card">
        <span className="section-label">Executive Summary</span>
        <p className="r2-open">{intro}</p>
        {bottleneck_capped && bnPillar && (
          <div className="r2-callout">
            Portfolio decisions are currently being made without a verified {bnPillar.name.toLowerCase()} foundation, exposing the business to retaining low-leverage initiatives and under-investing in genuine high-margin opportunities.
          </div>
        )}
        <div className="r2-bullets">
          {strongest && (
            <div className="r2-bullet">
              <span className="dot" />
              <p>
                <b>Strongest pillar — {strongest.name} ({strongest.score.toFixed(1)}):</b>{" "}
                {data.evidence[strongest.key]?.[0] ||
                  "This pillar provides the foundation to build from once the bottleneck is resolved."}
              </p>
            </div>
          )}
          {bnPillar && (
            <div className="r2-bullet">
              <span className="dot" style={{ background: "var(--danger)" }} />
              <p>
                <b>Critical bottleneck — {bnPillar.name} ({bnPillar.score.toFixed(1)}):</b>{" "}
                {data.evidence[bottleneck]?.[0] ||
                  "This pillar is the binding constraint on overall maturity."}
              </p>
            </div>
          )}
          <div className="r2-bullet">
            <span className="dot" />
            <p>
              <b>Immediate priority:</b>{" "}
              {data.roadmap.phase1_actions?.[0] ||
                "Appoint a single accountable owner with a 90-day mandate to resolve the highest-leverage bottleneck."}
            </p>
          </div>
        </div>
        <div className="section-footer">
          Assessment grounded in Hannila (2019) doctoral dissertation, IEM, University of Oulu.
        </div>
      </div>
    </section>
  );
};

/* ============ R3 Organisation Profile ============ */

/* Business-model → pillar weight table (mirrors the backend canonical map in
   chat_service.py BUSINESS_MODEL_WEIGHTS — kept in sync by hand). Used only
   to display the weight row alongside the explanation of the contextual
   score in the Business Model Context card. */
const BUSINESS_MODEL_WEIGHT_TABLE = {
  ETO:      { people: 0.35, process: 0.30, data: 0.20, technology: 0.15 },
  CETO:     { people: 0.25, process: 0.30, data: 0.25, technology: 0.20 },
  CTO:      { people: 0.20, process: 0.25, data: 0.30, technology: 0.25 },
  Standard: { people: 0.15, process: 0.30, data: 0.35, technology: 0.20 },
  Bulk:     { people: 0.10, process: 0.35, data: 0.20, technology: 0.35 },
};

const PRIORITY_PILLAR_KEYWORDS = [
  { pillar: "People",     kws: ["people", "talent", "culture", "training", "leadership", "hr"] },
  { pillar: "Process",    kws: ["process", "governance", "workflow", "review", "cadence"] },
  { pillar: "Data",       kws: ["data", "master data", "analytics", "reporting", "bi", "insight"] },
  { pillar: "Technology", kws: ["technology", "systems", "erp", "plm", "it ", "digital tool"] },
];
const AMBIGUOUS_PRIORITY_TERMS = new Set([
  "portfolio simplification", "profitability improvement", "complexity reduction",
  "digital transformation", "innovation", "growth",
]);

const detectPriorityPillar = (priority) => {
  const p = (priority || "").trim().toLowerCase();
  if (!p || AMBIGUOUS_PRIORITY_TERMS.has(p)) return null;
  for (const { pillar, kws } of PRIORITY_PILLAR_KEYWORDS) {
    if (kws.some((kw) => p.includes(kw))) return pillar;
  }
  return null;
};

const formatPct = (v) => {
  const n = parseFloat(v);
  if (!Number.isFinite(n)) return "–";
  return `${Math.round(n * 100)}%`;
};

const BusinessModelContextCard = ({ data }) => {
  const { business_model, business_model_raw, contextual_weights, strategic_priority,
          equal_weighted_score, contextual_score } = data;

  // Resolve which canonical row applies. Prefer the raw model name from the
  // LLM (preserves Bulk vs Standard); fall back to the display code.
  const canonicalKey = (() => {
    const candidates = [business_model_raw, business_model]
      .filter(Boolean)
      .map((s) => String(s).trim());
    for (const c of candidates) {
      if (BUSINESS_MODEL_WEIGHT_TABLE[c]) return c;
      const cap = c.charAt(0).toUpperCase() + c.slice(1).toLowerCase();
      if (BUSINESS_MODEL_WEIGHT_TABLE[cap]) return cap;
      const upper = c.toUpperCase();
      if (BUSINESS_MODEL_WEIGHT_TABLE[upper]) return upper;
    }
    return null;
  })();

  const weightsToShow = contextual_weights || (canonicalKey
    ? BUSINESS_MODEL_WEIGHT_TABLE[canonicalKey]
    : null);

  const boostedPillar = detectPriorityPillar(strategic_priority);
  const hasContextual = typeof contextual_score === "number" && Number.isFinite(contextual_score);
  const eqShown = typeof equal_weighted_score === "number" && Number.isFinite(equal_weighted_score)
    ? equal_weighted_score
    : null;

  return (
    <div className="glass-card r3-card" data-testid="business-model-context-card">
      <span className="section-label">Business Model Context</span>
      {business_model && <div className="r3-badge">{business_model}</div>}

      <div className="r3-bmc">
        <p className="r3-bmc-line">
          <b>Equal-Weighted Score (primary):</b> the academically validated baseline —
          the simple average of the four pillar scores (25% each).
          {eqShown !== null && (
            <> Current value: <b>{eqShown.toFixed(2)} / 5.00</b>.</>
          )}
        </p>
        <p className="r3-bmc-line">
          <b>Contextual Score (secondary):</b> a weighted sum that adjusts the four
          pillar scores using the weight row declared for your business model
          {boostedPillar ? <> and a +5% boost toward <b>{boostedPillar}</b> (your stated strategic priority)</> : null}.
          {hasContextual && (
            <> Current value: <b>{contextual_score.toFixed(2)} / 5.00</b>.</>
          )}
        </p>

        {weightsToShow && (
          <div className="r3-bmc-weights" data-testid="business-model-weight-row">
            <span className="r3-bmc-weights-lbl">
              Weight row · {canonicalKey || business_model || "Equal"}
            </span>
            <div className="r3-bmc-weights-grid">
              <div><span>People</span><b>{formatPct(weightsToShow.people)}</b></div>
              <div><span>Process</span><b>{formatPct(weightsToShow.process)}</b></div>
              <div><span>Data</span><b>{formatPct(weightsToShow.data)}</b></div>
              <div><span>Technology</span><b>{formatPct(weightsToShow.technology)}</b></div>
            </div>
          </div>
        )}

        <p className="r3-note">
          Business model changes the <i>contextual score calculation</i> directly — not just
          the narrative interpretation. A strategic-priority boost (+5% to a single pillar)
          is applied only when the priority maps unambiguously to one of the four pillars.
        </p>
      </div>

      <div className="section-footer">
        Business model classification: Hannila (2019) and Hannila et al. (2020) product type frameworks.
      </div>
    </div>
  );
};

const R3OrgProfile = ({ data }) => (
  <section className="r3" data-testid="report-r3">
    <div className="glass-card r3-card">
      <span className="section-label">Organisation</span>
      <div className="r3-row"><span className="lbl">Company</span><span className="val">{data.company}</span></div>
      <div className="r3-row"><span className="lbl">Industry</span><span className="val">{data.industry}</span></div>
      {data.business_model && (
        <div className="r3-row"><span className="lbl">Business Model</span><span className="val">{data.business_model}</span></div>
      )}
      <div className="r3-row"><span className="lbl">Company Size</span><span className="val">{data.size}</span></div>
      {data.respondent_name && (
        <div className="r3-row"><span className="lbl">Respondent</span><span className="val">{data.respondent_name}</span></div>
      )}
      {data.role && (
        <div className="r3-row"><span className="lbl">Role</span><span className="val">{data.role}</span></div>
      )}
      {data.date && (
        <div className="r3-row"><span className="lbl">Assessment Date</span><span className="val">{data.date}</span></div>
      )}
    </div>
    <BusinessModelContextCard data={data} />
  </section>
);

/* ============ R4 Pillar Cards (clickable accordion) ============ */
const PillarCard = ({ pillar, data, idx, isOpen, onToggle }) => {
  const { key, letter, name, score, level } = pillar;
  const lvl = bandClass(score);
  const nextLvl = `l${Math.min(5, scoreToBand(score) + 1)}`;
  const isBn = data.bottleneck === key;
  const bullets = data.evidence[key] || [];
  const nextLevel = Math.min(5, level + 1);
  const summary = bullets[0] || "";

  return (
    <div
      className={`glass-card r4-card ${lvl}${isOpen ? " is-open" : ""}${isBn ? " is-bottleneck" : ""}`}
      data-testid={`report-pillar-${key}`}
    >
      <button
        type="button"
        className="r4-head"
        onClick={onToggle}
        aria-expanded={isOpen}
        data-testid={`report-pillar-toggle-${key}`}
      >
        <div className="r4-head-left">
          <div className="r4-letter">{letter}</div>
          <div className="r4-head-info">
            <div className="r4-title-row">
              <span className="r4-title">{name}</span>
              {isBn && <span className="r4-bn-tag">⚠ Bottleneck</span>}
            </div>
            <div className="r4-sub">Dimension {idx + 1} of 4 · {LEVEL_TITLES[level]}</div>
          </div>
        </div>
        <div className="r4-head-right">
          <div className={`r4-score-badge ${lvl}`}>
            <span className="r4-score-num">{score.toFixed(1)}</span>
            <span className="r4-score-suffix">/ 5.0</span>
          </div>
          <span className={`r4-chevron ${isOpen ? "open" : ""}`} aria-hidden="true">
            <ChevronDown size={18} />
          </span>
        </div>
      </button>

      {/* Always-visible compact bar (gives at-a-glance status even when collapsed) */}
      <div className="r4-bar">
        <div className="r4-track">
          <div
            className={`r4-fill ${lvl}`}
            style={{ width: `${(score / 5) * 100}%` }}
          />
        </div>
        <div className="r4-scale">
          <span>1</span><span>2</span><span>3</span><span>4</span><span>5</span>
        </div>
      </div>

      {/* Compact one-liner shown only when collapsed */}
      {!isOpen && summary && (
        <div className="r4-summary">
          <span className="r4-summary-quote">"</span>
          <p>{summary}</p>
          <span className="r4-expand-hint">Click to read full evidence →</span>
        </div>
      )}

      {/* Expanded body */}
      <div className={`r4-body ${isOpen ? "open" : ""}`}>
        <div className="r4-body-inner">
          <span className="section-label">Evidence from Assessment</span>
          <div className="r4-evidence">
            {bullets.map((b, i) => (
              <div key={i} className="r4-bullet">
                <span className="dash">—</span>
                <p>{b}</p>
              </div>
            ))}
          </div>
          {level < 5 && (
            <div className="r4-gap">
              <div className="r4-gap-head">
                <span className={`level-pill ${lvl}`}>{LEVEL_TITLES[level]}</span>
                <span className="r4-gap-arrow"><ArrowRight size={14} /></span>
                <span className={`level-pill ${nextLvl}`}>{LEVEL_TITLES[nextLevel]}</span>
              </div>
              <p className="r4-gap-desc">
                To reach {LEVEL_TITLES[nextLevel]}, the {name.toLowerCase()} pillar needs the practices described in the roadmap (Phases 1–2) to be operational and consistently applied.
              </p>
            </div>
          )}
          <div className="section-footer">
            PPDT pillar definitions: Hannila (2019) · Hannila, Härkönen &amp; Haapasalo (2022), Journal of Decision Systems, 31(3), 258–279.
          </div>
        </div>
      </div>
    </div>
  );
};

const R4PillarSection = ({ data }) => {
  // Default: bottleneck pillar open, all others closed
  const [openKey, setOpenKey] = useState(data.bottleneck || data.kpi.pillars[0]?.key);
  return (
    <section className="r4" data-testid="report-r4">
      <span className="section-label" style={{ marginBottom: 4 }}>The Four Pillars</span>
      <p className="r4-intro">
        Click a pillar to read the evidence behind its score.
        {data.bottleneck && " The bottleneck pillar is expanded by default."}
      </p>
      {data.kpi.pillars.map((p, i) => (
        <PillarCard
          key={p.key}
          pillar={p}
          data={data}
          idx={i}
          isOpen={openKey === p.key}
          onToggle={() => setOpenKey(openKey === p.key ? null : p.key)}
        />
      ))}
    </section>
  );
};

/* ============ R5 Overall Score Calculation ============ */
const R5Calculation = ({ data }) => {
  const { scores, kpi, bottleneck, bottleneck_capped } = data;
  const bnPillar = kpi.pillars.find((p) => p.key === bottleneck);
  const lvl = scoreToLevel(scores.overall);

  return (
    <section className="r5" data-testid="report-r5">
      <div className="r5-card">
        <div className="r5-left">
          <span className="r5-label">Overall Maturity Score</span>
          <div>
            <span className="r5-score">
              {scores.overall.toFixed(1)}
            </span>
            <span className="r5-score-suffix">/5.0</span>
          </div>
          <span className="r5-level">{LEVEL_TITLES[lvl]}</span>
          {bottleneck_capped && bnPillar && (
            <div className="r5-cap">
              <span className="ico"><AlertTriangle size={14} /></span>
              Capped by {bnPillar.name.toUpperCase()} bottleneck ({bnPillar.score.toFixed(1)} / 5.0)
            </div>
          )}
        </div>
        <div className="r5-right">
          <div className="r5-calc">
            {kpi.pillars.map((p) => (
              <div key={p.key} className="r5-calc-row">
                <span>{p.name.padEnd(11)} × 0.25</span>
                <span>= {(p.score * 0.25).toFixed(2)}</span>
              </div>
            ))}
            <div className="r5-calc-div" />
            <div className="r5-calc-row tot">
              <span>Overall Score</span>
              <span>= {scores.overall.toFixed(2)}</span>
            </div>
          </div>
          <p className="r5-research">
            Equal weights: validated IEM baseline. Business-model weighting is open research (RQ5).
          </p>
        </div>
      </div>
    </section>
  );
};

/* ============ R6 Bottleneck ============ */
const R6Bottleneck = ({ data }) => {
  const { bottleneck, kpi, bottleneck_narrative } = data;
  if (!bottleneck) return null;
  const bn = kpi.pillars.find((p) => p.key === bottleneck);
  if (!bn) return null;

  const narrative =
    bottleneck_narrative ||
    `The ${bn.name} pillar scores ${bn.score.toFixed(1)}/5.0 (${LEVEL_TITLES[bn.level]}) and is the binding constraint on overall maturity. It caps the other pillars because every portfolio decision ultimately depends on the practices and evidence this pillar provides. Until this gap is closed, investments in the other pillars will not lift the overall maturity score.`;

  return (
    <section className="r6" data-testid="report-r6">
      <div className="r6-card">
        <div className="r6-head">
          <span className="ico"><AlertTriangle size={22} /></span>
          <span className="r6-title">⚠ Bottleneck Identified — {bn.name.toUpperCase()}</span>
        </div>
        <p className="r6-body">{narrative}</p>
        <div className="r6-risk">
          <div className="r6-risk-head">
            <span className="ico"><Info size={14} /></span>
            <span className="r6-risk-label">Decision Risk</span>
          </div>
          <p className="r6-risk-body">
            Portfolio renewal, retirement and investment-reallocation decisions are currently made on incomplete or unverified evidence in the {bn.name.toLowerCase()} pillar — and the gap will widen with every new project the organisation accepts until it is closed.
          </p>
        </div>
        <div className="section-footer">
          Bottleneck principle: Hannila et al. (2022) — five preconditions that must all function together for data-driven PPM to be possible.
        </div>
      </div>
    </section>
  );
};

/* ============ R7 Roadmap Board ============ */
const RoadmapPhase = ({ phaseClass, num, tag, title, window: win, actions, outcomeLabel, outcomeValue, deltaText }) => (
  <div className={`rb-phase ${phaseClass}`}>
    <div className="rb-head">
      <span className="rb-tag">{tag}</span>
      <div className="rb-num">{num}</div>
    </div>
    <h3 className="rb-title">{title}</h3>
    <div className="rb-window">{win}</div>
    <div className="rb-actions">
      {actions.map((a, i) => (
        <div key={i} className="rb-action"><span>{a}</span></div>
      ))}
    </div>
    <div className="rb-outcome">
      <span className="rb-outcome-lbl">{outcomeLabel}</span>
      <span className="rb-outcome-val">
        <span className="arrow">→</span>
        {outcomeValue}
        {deltaText && <span className="delta">{deltaText}</span>}
      </span>
    </div>
  </div>
);

const R7Roadmap = ({ data }) => {
  const { roadmap } = data;
  const delta1 = roadmap.score_phase1 - roadmap.score_now;
  const delta3 = roadmap.score_phase3 - roadmap.score_phase1;

  return (
    <section className="r7" data-testid="report-r7">
      <span className="section-label">Improvement Roadmap</span>
      <p className="r7-intro">
        Actions are sequenced bottleneck-first. Phase 2 work will not improve overall maturity until the Phase 1 bottleneck is resolved.
      </p>
      <div className="roadmap-board">
        <RoadmapPhase
          phaseClass="p1"
          num="1"
          tag="Phase 1"
          title="Resolve the Bottleneck"
          window="0–3 months"
          actions={roadmap.phase1_actions}
          outcomeLabel="Projected Score"
          outcomeValue={`${roadmap.score_phase1.toFixed(1)} / 5.0`}
          deltaText={delta1 > 0 ? `+${delta1.toFixed(1)}` : null}
        />
        <RoadmapPhase
          phaseClass="p2"
          num="2"
          tag="Phase 2"
          title="Systemic Improvement"
          window="3–12 months"
          actions={roadmap.phase2_actions}
          outcomeLabel="Build governance"
          outcomeValue={`Defined → Managed`}
        />
        <RoadmapPhase
          phaseClass="p3"
          num="3"
          tag="Phase 3"
          title="Sustained Capability"
          window="12+ months"
          actions={roadmap.phase3_actions}
          outcomeLabel="Target Maturity"
          outcomeValue={`${roadmap.score_phase3.toFixed(1)} / 5.0`}
          deltaText={delta3 > 0 ? `+${delta3.toFixed(1)}` : null}
        />
      </div>
      <div className="glass-card r7-gov" style={{ marginTop: 18, padding: "16px 20px" }}>
        <span className="ico"><Info size={16} /></span>
        <p>
          Each phase action must have a named governance owner. Investing in Phase 3 tooling before the Phase 1 bottleneck is resolved will not improve overall portfolio maturity. Sequence matters.
        </p>
      </div>
      <div className="section-footer" style={{ paddingLeft: 0 }}>
        Roadmap logic: Hannila et al. (2020), Journal of Enterprise Information Management, 33(1), 214–237. Bottleneck-first sequencing principle.
      </div>
    </section>
  );
};

/* ============ R8 Portfolio Decision Impact ============ */
const R8DecisionImpact = ({ data }) => {
  const narrative =
    data.decision_vulnerability_narrative ||
    `Portfolio decisions today rely on the practices captured in the pillar scores above. Until the bottleneck is resolved, retirement, renewal and reallocation choices will be made on incomplete evidence — meaning low-leverage initiatives may be retained while high-margin opportunities are under-funded.`;

  return (
    <section className="r8" data-testid="report-r8">
      <div className="glass-card r8-card">
        <span className="section-label">Portfolio Decision Impact</span>
        <div className="r8-sub">
          <span className="r8-sub-label">Current Decision Quality</span>
          <p className="r8-sub-body">{narrative}</p>
        </div>
        <div className="r8-sub">
          <span className="r8-sub-label">At Next Maturity Level</span>
          <p className="r8-sub-body">
            Once Phase 1 is complete, leadership will be able to review portfolio performance on verified data with shorter cycle times. Retirement decisions become evidence-based rather than political. Manual reconciliation effort is freed for analytical work.
          </p>
        </div>
        <div className="r8-sub">
          <span className="r8-sub-label">At Full Maturity (Level 4–5)</span>
          <p className="r8-sub-body">
            Full maturity routinely supports continuous portfolio optimisation: live profitability dashboards, predictive flags for under-performing initiatives, and integrated decision-support at the moment of approval. The Portfolio Council reviews exception cases continuously rather than the entire portfolio annually.
          </p>
        </div>
        <div className="section-footer">Decision quality framing: Hannila (2019) and Hannila et al. (2022).</div>
      </div>
    </section>
  );
};

/* ============ R9 Dashboard charts (Bar + Confidence + Benchmark) ============ */
const BarChart = ({ data }) => {
  const { kpi, scores, bottleneck } = data;
  const avg = scores.overall;

  return (
    <div className="chart-container" data-testid="report-bar-chart">
      <div className="chart-head">
        <div>
          <div className="chart-title">Pillar Scores</div>
          <div className="chart-sub">Scored against IEM maturity criteria</div>
        </div>
      </div>
      {kpi.pillars.map((p) => {
        const isBn = p.key === bottleneck;
        const band = scoreToBand(p.score);
        const color = BAND_COLORS[band];
        const textColor = BAND_TEXT_COLORS[band];
        return (
          <div key={p.key} className={`bar-row${isBn ? " bottleneck" : ""}`}>
            <div className="bar-top">
              <div className="bar-left">
                <div className="bar-letter">{p.letter}</div>
                <div>
                  <span className="bar-name">
                    {p.name}
                    {isBn && <span style={{ color: "var(--danger)", fontWeight: 700, marginLeft: 4 }}>⚠</span>}
                  </span>
                  <span className={`level-pill ${bandClass(p.score)}`} style={{ marginLeft: 8 }}>
                    {LEVEL_TITLES[p.level]}
                  </span>
                </div>
              </div>
              <div>
                <span className="bar-value" style={{ color: textColor }}>{p.score.toFixed(1)}</span>
                <span className="bar-value-suffix">/5</span>
              </div>
            </div>
            <div className="bar-track">
              <div
                className="bar-fill"
                style={{
                  width: `${(p.score / 5) * 100}%`,
                  background: `linear-gradient(90deg, ${color}, ${color}BF)`,
                }}
              />
              <div className="bar-avg" style={{ left: `${(avg / 5) * 100}%` }}>
                <span className="bar-avg-lbl">AVG</span>
              </div>
            </div>
            <div className="bar-scale">
              <span>1</span><span>2</span><span>3</span><span>4</span><span>5</span>
            </div>
          </div>
        );
      })}
      <div className="chart-foot">Criteria: Hannila et al. (2022, 2020) · Silvola (2018)</div>
    </div>
  );
};

/* Note: Score Confidence and Benchmark Context charts were removed from the
   dashboard view per design polish. They still exist in the PDF export
   pipeline (`/app/backend/pdf_builder.py`). */

const R9Dashboard = ({ data }) => (
  <section className="r9" data-testid="report-r9">
    <span className="section-label">Assessment Dashboard</span>
    <BarChart data={data} />
  </section>
);

/* ============ R10 Research Basis ============ */
const R10Research = () => (
  <section className="r10" data-testid="report-r10">
    <div className="r10-wrap">
      <span className="section-label">Academic Foundation</span>
      <p className="r10-sub">
        Every dimension, maturity level, and improvement principle in this report has a published academic source. This section documents those sources.
      </p>
      <div className="r10-grid">
        <div className="r10-cite">
          <span className="r10-cite-tag">Doctoral Dissertation</span>
          <h4 className="r10-cite-title">Towards data-driven decision-making in product portfolio management</h4>
          <p className="r10-cite-auth">Hannila, H. (2019). University of Oulu, Finland.</p>
          <p className="r10-cite-rel"><b>Relevance:</b> Provides the PPDT framework, five preconditions, and identifies the core research gap this tool addresses.</p>
        </div>
        <div className="r10-cite">
          <span className="r10-cite-tag">Peer-Reviewed Article</span>
          <h4 className="r10-cite-title">Digitalisation of a company decision-making system</h4>
          <p className="r10-cite-auth">Hannila, H., Härkönen, J. &amp; Haapasalo, H. (2022). Journal of Decision Systems, 31(3), 258–279.</p>
          <p className="r10-cite-rel"><b>Relevance:</b> Five preconditions that form the backbone of pillar assessment and bottleneck logic.</p>
        </div>
        <div className="r10-cite">
          <span className="r10-cite-tag">Peer-Reviewed Article</span>
          <h4 className="r10-cite-title">Product-level profitability: Preconditions for data-driven PPM</h4>
          <p className="r10-cite-auth">Hannila, H., Koskinen, J., Härkönen, J. &amp; Haapasalo, H. (2020). JEIM, 33(1), 214–237.</p>
          <p className="r10-cite-rel"><b>Relevance:</b> Empirical 8-company study confirming maturity variation and identifying the assessment gap.</p>
        </div>
        <div className="r10-cite">
          <span className="r10-cite-tag">Doctoral Dissertation + Article</span>
          <h4 className="r10-cite-title">One product data for integrated business processes</h4>
          <p className="r10-cite-auth">Silvola, R. (2018). University of Oulu, Finland. Also: Hannila et al. (2022). Data-driven begins with DATA. JCIS, 62(1), 29–38.</p>
          <p className="r10-cite-rel"><b>Relevance:</b> Defines Level 5 benchmark and the data-first principle underpinning the Data pillar.</p>
        </div>
      </div>
      <div className="r10-thesis">
        <div className="r10-thesis-head">
          <span className="ico"><GraduationCap size={18} /></span>
          <span className="r10-thesis-title">Master's Thesis Contribution</span>
          <span className="r10-thesis-pill">IEM · University of Oulu · 2026</span>
        </div>
        <p className="r10-thesis-body">
          This assessment instrument was developed as original Master's thesis research in Industrial Engineering and Management at the University of Oulu (IPIC programme, 2026). The instrument operationalises the research gap identified across Hannila (2019), Hannila et al. (2020, 2022) and Silvola (2018) — bridging the gap between published academic framework and practitioner-facing assessment tool.
        </p>
      </div>
      <div className="section-footer">
        Academic sources are publicly available through the University of Oulu repository and respective journal publishers.
      </div>
    </div>
  </section>
);

/* ============ Footer ============ */
const ReportFooter = ({ data }) => (
  <footer className="report-footer">
    <div className="l">PortfolioHealth Advisor · PPDT Maturity Assessment</div>
    <div className="c">
      <span className="a">IEM research-grounded · University of Oulu</span>
      <span className="b">Hannila (2019) · Hannila et al. (2020, 2022) · Silvola (2018)</span>
    </div>
    <div className="r">
      <span className="a">Full Assessment Report{data.date ? ` · ${data.date}` : ""}</span>
      <span className="b">Prepared for: {data.company}</span>
    </div>
  </footer>
);

/* ============ Top toolbar (sits above the report doc, in the light app shell) ============ */
const ReportToolbar = ({ id, onDownload, onPrint, downloading, companyName }) => (
  <div className="print-hide flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
    <div className="flex items-center gap-3">
      <Link
        to="/assessments"
        data-testid="report-back-btn"
        className="p-2.5 rounded-xl bg-white border border-[#E8E2D2] text-[#3D4A5C] hover:text-[#0C1B2A] hover:border-[#E8D49A] transition-all shadow-sm"
      >
        <ArrowLeft size={18} />
      </Link>
      <div>
        <span className="eyebrow">Consultant Report</span>
        <h1 className="text-xl sm:text-2xl font-semibold text-[#0C1B2A] font-display tracking-tight mt-1">
          PPDT Maturity Assessment
        </h1>
        <p className="text-[#7B8694] text-xs mt-0.5">{companyName}</p>
      </div>
    </div>
    <div className="flex items-center gap-2 flex-wrap">
      <Link
        to={`/assessments/${id}`}
        data-testid="view-chat-btn"
        className="flex items-center gap-2 px-3.5 py-2.5 btn-glass rounded-xl text-sm"
      >
        <MessageSquare size={16} />
        <span className="hidden sm:inline">View Chat</span>
      </Link>
      <button
        onClick={onPrint}
        data-testid="print-report-btn"
        title="Print / Save as PDF (A4, board-room ready)"
        className="flex items-center gap-2 px-3.5 py-2.5 btn-glass rounded-xl text-sm"
      >
        <Printer size={16} />
        <span className="hidden sm:inline">Print</span>
      </button>
      <button
        onClick={onDownload}
        disabled={downloading}
        data-testid="export-pdf-btn"
        className="flex items-center gap-2 px-4 py-2.5 btn-liquid rounded-xl text-sm disabled:opacity-50"
      >
        <Download size={16} />
        {downloading ? "..." : "Export PDF"}
      </button>
    </div>
  </div>
);

/* ============ Main page ============ */
const ReportPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { assessment, loading } = useAssessment(id);
  const [downloading, setDownloading] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  const regenerateReport = useCallback(async () => {
    setRegenerating(true);
    try {
      const { data } = await axios.post(`${BACKEND_URL}/api/assessments/${id}/regenerate-report`);
      if (data?.report_ready) {
        toast.success(
          data.status === "salvaged"
            ? "Report recovered from the last message."
            : "Report regenerated successfully."
        );
        navigate(0);
      } else {
        toast.error("Could not regenerate the report.");
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Regeneration failed. Please try again.");
    } finally {
      setRegenerating(false);
    }
  }, [id, navigate]);

  const downloadPDF = useCallback(async () => {
    setDownloading(true);
    try {
      const response = await axios.get(`${BACKEND_URL}/api/assessments/${id}/pdf`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `PPDT_Assessment_${(assessment?.company_name || "Report").replace(/\s+/g, "_")}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("PDF downloaded");
    } catch (err) {
      console.error(err);
      toast.error("Failed to download PDF");
    } finally {
      setDownloading(false);
    }
  }, [id, assessment?.company_name]);

  const printReport = useCallback(() => {
    // Slight delay so toast can appear before browser print dialog grabs focus
    toast.success("Opening print preview · choose 'Save as PDF' for board-room ready output", { duration: 2200 });
    setTimeout(() => window.print(), 250);
  }, []);

  if (loading) return <Layout><LoadingSpinner className="h-64" /></Layout>;

  if (!assessment?.report) {
    const hasHistory = (assessment?.chat_history?.length || 0) >= 2;
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center py-16 max-w-xl mx-auto text-center">
          <AlertTriangle size={64} className="text-[#C9A84C] mb-4 opacity-70" />
          <h2 className="text-xl font-semibold text-[#0C1B2A] mb-2 font-['Outfit']">Report Not Ready</h2>
          <p className="text-[#4A5568] mb-2">This assessment hasn't been fully scored yet.</p>
          {hasHistory && (
            <p className="text-[#8896A5] text-sm mb-6">
              If the chat already showed "Assessment Complete", the model may have been cut off mid-emission. You can try to regenerate the report from the existing conversation.
            </p>
          )}
          <div className="flex flex-col sm:flex-row gap-3">
            {hasHistory && (
              <button
                onClick={regenerateReport}
                disabled={regenerating}
                data-testid="regenerate-report-btn"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 btn-liquid rounded-xl disabled:opacity-50"
              >
                <RefreshCw size={16} className={regenerating ? "animate-spin" : ""} />
                {regenerating ? "Regenerating…" : "Regenerate Report"}
              </button>
            )}
            <Link
              to={`/assessments/${id}`}
              data-testid="continue-assessment-btn"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 btn-glass rounded-xl"
            >
              Continue Assessment
            </Link>
          </div>
        </div>
      </Layout>
    );
  }

  const data = buildReportData(assessment);

  return (
    <Layout>
      <ReportToolbar
        id={id}
        onDownload={downloadPDF}
        onPrint={printReport}
        downloading={downloading}
        companyName={data.company}
      />
      <div className="ph-report" data-testid="premium-report">
        <R1Cover data={data} />
        <R2ExecutiveSummary data={data} />
        <R3OrgProfile data={data} />
        <R4PillarSection data={data} />
        <R5Calculation data={data} />
        <R6Bottleneck data={data} />
        <R7Roadmap data={data} />
        <R8DecisionImpact data={data} />
        <R9Dashboard data={data} />
        <R10Research />
        <ReportFooter data={data} />
      </div>
    </Layout>
  );
};

export default ReportPage;
