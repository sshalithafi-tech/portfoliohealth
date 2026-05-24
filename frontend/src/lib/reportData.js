/**
 * JS port of backend html_report._build_report_data — turns an assessment +
 * its stored `report` JSON into the shape consumed by the premium report UI:
 *   { company, industry, business_model, size, role, date,
 *     scores, levels, bottleneck, bottleneck_capped,
 *     evidence, confidence, roadmap, kpi }
 */

export const LEVEL_NAMES = ["", "AD HOC", "DEVELOPING", "DEFINED", "MANAGED", "PREDICTIVE"];
export const LEVEL_TITLES = ["", "Ad Hoc", "Developing", "Defined", "Managed", "Predictive"];
export const LEVEL_COLORS = { 1: "#C0392B", 2: "#D4850A", 3: "#B8860B", 4: "#27AE60", 5: "#1A5276" };
export const LEVEL_TEXT_COLORS = { 1: "#C0392B", 2: "#D4850A", 3: "#5C4308", 4: "#27AE60", 5: "#1A5276" };

/* Dynamic maturity-band colors — driven by NUMERIC score band, not discrete level index.
   1.0–1.4 red · 1.5–2.4 amber · 2.5–3.4 green · 3.5–4.4 sky · 4.5–5.0 emerald */
export const BAND_COLORS = { 1: "#DC2626", 2: "#F59E0B", 3: "#10B981", 4: "#0EA5E9", 5: "#059669" };
export const BAND_TEXT_COLORS = { 1: "#DC2626", 2: "#B45309", 3: "#047857", 4: "#0369A1", 5: "#047857" };

export function scoreToBand(s) {
  const n = parseFloat(s);
  if (!Number.isFinite(n)) return 1;
  if (n < 1.5) return 1;
  if (n < 2.5) return 2;
  if (n < 3.5) return 3;
  if (n < 4.5) return 4;
  return 5;
}

const LEVEL_NAME_TO_INDEX = {
  "ad hoc": 1,
  developing: 2,
  aware: 2,
  defined: 3,
  managed: 4,
  predictive: 5,
  optimising: 5,
  optimizing: 5,
};

export function scoreToLevel(s) {
  if (s < 2) return 1;
  if (s < 3) return 2;
  if (s < 4) return 3;
  if (s < 4.5) return 4;
  return 5;
}

export function levelNameFromScore(s) {
  return LEVEL_NAMES[scoreToLevel(s)];
}

function levelIndexFromName(name) {
  if (typeof name !== "string") return 0;
  return LEVEL_NAME_TO_INDEX[name.trim().toLowerCase()] || 0;
}

function toFloat(v, def = 0) {
  const n = parseFloat(v);
  return Number.isFinite(n) ? n : def;
}

function cleanLevel(name) {
  if (typeof name !== "string") return "";
  return name.replace(/^LEVEL\s+[\d\-–]+\s*:?\s*/i, "").trim().toUpperCase();
}

function splitActions(text) {
  if (!text) return [];
  if (Array.isArray(text)) return text.map(s => String(s).trim()).filter(Boolean);
  const parts = String(text)
    .split(/(?:\r?\n+|(?<=[.!?])\s+(?=[A-Z]))/)
    .map(p => p.trim().replace(/^[-—•·\s]+/, ""))
    .filter(p => p.length > 8);
  return parts.slice(0, 4);
}

function evidenceBullets(report, pillar, fallback) {
  const bullets = [];
  const summaries = report?.dimension_summaries || {};
  const interp = report?.pillar_interpretations || {};
  const findings = report?.key_findings || [];
  const gaps = report?.critical_gaps || [];

  if (typeof summaries[pillar] === "string" && summaries[pillar].trim()) bullets.push(summaries[pillar].trim());
  if (typeof interp[pillar] === "string" && interp[pillar].trim()) bullets.push(interp[pillar].trim());

  const pl = pillar.toLowerCase();
  for (const src of [findings, gaps]) {
    if (Array.isArray(src)) {
      for (const item of src) {
        const s = String(item).trim();
        if (s && s.toLowerCase().includes(pl) && !bullets.includes(s)) bullets.push(s);
        if (bullets.length >= 4) break;
      }
    }
    if (bullets.length >= 4) break;
  }
  if (!bullets.length) bullets.push(fallback);
  return bullets.slice(0, 4);
}

function confidenceForPillar(report) {
  const conf = (report?.assessment_reliability?.confidence || "").trim().toLowerCase();
  return ({
    high:   { strong: 80, inferred: 15, assumed: 5 },
    medium: { strong: 60, inferred: 30, assumed: 10 },
    low:    { strong: 40, inferred: 40, assumed: 20 },
  })[conf] || { strong: 60, inferred: 30, assumed: 10 };
}

function bottleneckPillar(report, scores) {
  const name = report?.bottleneck_pillar;
  if (typeof name === "string" && name.trim()) return name.trim().toLowerCase();
  // Fallback: derive lowest pillar
  const pillars = ["people", "process", "data", "technology"];
  let lowest = pillars[0];
  for (const p of pillars) if ((scores[p] || 0) < (scores[lowest] || 0)) lowest = p;
  return lowest;
}

function isBottleneckCapped(scores, bottleneck) {
  if (!bottleneck) return false;
  return (scores.overall - (scores[bottleneck] || 0)) >= 1.0;
}

function projectedPhase1(scores, bottleneck) {
  if (!bottleneck) return Math.min(5, (scores.overall || 0) + 0.5);
  const fixed = { ...scores };
  fixed[bottleneck] = Math.max(3.0, fixed[bottleneck] || 0);
  const sum = ["people", "process", "data", "technology"].reduce((acc, p) => acc + (fixed[p] || 0), 0);
  return Math.round((sum / 4) * 100) / 100;
}

function phaseActions(roadmap, key, defaults) {
  const phase = roadmap?.[key] || {};
  const parts = splitActions(phase.actions);
  return parts.length ? parts : defaults;
}

const FALLBACK_EVIDENCE = {
  people: "Roles, accountability, and decision-making capability across the portfolio function.",
  process: "Formal review cycles, change control, and decision traceability across the product lifecycle.",
  data: "Product master data, profitability data quality, and the ability to assemble decision-grade information.",
  technology: "Tools and integrations actually used inside the portfolio decision room.",
};

const BUSINESS_MODEL_MAP = {
  ETO: "ETO", CTO: "CTO", CETO: "CETO",
  STANDARD: "STD", "STANDARD/BULK": "STD", BULK: "STD", STD: "STD",
  MTO: "ETO",
};

export function buildReportData(assessment) {
  const report = assessment?.report || {};
  const rawScores = report.scores || assessment?.scores || {};

  const scores = {
    people: toFloat(rawScores.people),
    process: toFloat(rawScores.process),
    data: toFloat(rawScores.data),
    technology: toFloat(rawScores.technology),
    overall: toFloat(rawScores.overall),
  };

  const levelNamesRaw = report.level_names || {};
  const levels = {};
  for (const k of ["people", "process", "data", "technology", "overall"]) {
    const nm = cleanLevel(levelNamesRaw[k]);
    levels[k] = nm || levelNameFromScore(scores[k]);
  }

  const bottleneck = bottleneckPillar(report, scores);
  const bottleneck_capped = isBottleneckCapped(scores, bottleneck);

  const completed = assessment?.completed_at || assessment?.created_at;
  let date = "";
  if (completed) {
    try {
      const d = new Date(completed);
      date = d.toLocaleDateString(undefined, { year: "numeric", month: "long" });
    } catch (e) {
      date = String(completed).slice(0, 10);
    }
  }

  const bmRaw = (assessment?.business_model || report?.business_model || "").trim().toUpperCase();
  const business_model = BUSINESS_MODEL_MAP[bmRaw] || bmRaw || null;

  const pillarLetters = { people: "P", process: "P", data: "D", technology: "T" };
  const pillars = ["people", "process", "data", "technology"].map((key) => {
    const sc = scores[key];
    const idx = levelIndexFromName(levels[key]) || scoreToLevel(sc);
    return {
      key,
      letter: pillarLetters[key],
      name: key.charAt(0).toUpperCase() + key.slice(1),
      score: sc,
      level: idx,
      level_name: LEVEL_NAMES[idx],
    };
  });

  const evidence = {};
  for (const p of Object.keys(FALLBACK_EVIDENCE)) {
    evidence[p] = evidenceBullets(report, p, FALLBACK_EVIDENCE[p]);
  }

  const confidenceShared = confidenceForPillar(report);
  const confidence = Object.fromEntries(
    Object.keys(FALLBACK_EVIDENCE).map((p) => [p, { ...confidenceShared }])
  );

  const roadmapObj = report.roadmap || {};
  const score_phase1 = projectedPhase1(scores, bottleneck);
  const score_phase3 = Math.min(5, Math.max(score_phase1 + 0.8, 4.0));

  const roadmap = {
    score_now: Math.round(scores.overall * 100) / 100,
    score_phase1: Math.round(score_phase1 * 100) / 100,
    score_phase3: Math.round(score_phase3 * 100) / 100,
    phase1_actions: phaseActions(roadmapObj, "immediate", [
      "Resolve the highest-leverage bottleneck constraint with a named accountable owner.",
    ]),
    phase2_actions: phaseActions(roadmapObj, "short_term", [
      "Establish recurring portfolio review cadence with documented retirement and reallocation criteria.",
    ]),
    phase3_actions: phaseActions(roadmapObj, "strategic", [
      "Reach Managed/Predictive maturity: integrated dashboards, predictive analytics and consolidated governance.",
    ]),
    immediate: roadmapObj.immediate || {},
    short_term: roadmapObj.short_term || {},
    strategic: roadmapObj.strategic || {},
  };

  return {
    company: assessment?.company_name || "Organisation",
    industry: assessment?.company_industry || assessment?.industry || "—",
    business_model,
    size: assessment?.company_size || "—",
    role: assessment?.respondent_role || assessment?.respondent_name || "—",
    respondent_name: assessment?.respondent_name || "",
    date,
    scores,
    levels,
    bottleneck,
    bottleneck_capped,
    evidence,
    confidence,
    roadmap,
    kpi: {
      overall: {
        score: scores.overall,
        level_name: levels.overall,
        level_index: levelIndexFromName(levels.overall) || scoreToLevel(scores.overall),
      },
      pillars,
    },
    // Pass through narrative bits that the premium report uses verbatim
    executive_summary: report.executive_summary || report.consultant_note || "",
    bottleneck_narrative: report.bottleneck_narrative || report.decision_vulnerability || "",
    decision_vulnerability_narrative: report.decision_vulnerability || "",
    benchmark_context: report.benchmark_context || "",
    consultant_note: report.consultant_note || "",
    closing_statement: report.closing_statement || "",
    key_findings: report.key_findings || [],
    critical_gaps: report.critical_gaps || [],
  };
}
