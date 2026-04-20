import { ShieldCheck, CheckCircle2, AlertCircle, AlertTriangle } from "lucide-react";

const CONFIDENCE_TONES = {
  high: {
    color: "#34D399",
    label: "HIGH",
    icon: CheckCircle2,
    blurb: "Results are well-supported by the evidence shared during the assessment.",
  },
  medium: {
    color: "#C9A84C",
    label: "MEDIUM",
    icon: AlertCircle,
    blurb: "Directionally sound — some signals are self-reported or based on a single respondent.",
  },
  low: {
    color: "#EF4444",
    label: "LOW",
    icon: AlertTriangle,
    blurb: "Treat as indicative only — key evidence is missing or comes from a narrow perspective.",
  },
};

const normaliseConfidence = (value) => {
  const k = String(value || "").toLowerCase();
  if (k === "high") return "high";
  if (k === "low") return "low";
  return "medium";
};

// Heuristic fallback when the LLM hasn't populated assessment_reliability.
const deriveFactors = (report, assessment) => {
  const factors = [];
  const scores = report?.scores || {};
  const dataScore = Number(scores.data) || 0;

  // Data availability — derived from the Data pillar score.
  if (dataScore && dataScore < 2) {
    factors.push({
      label: "Data Availability",
      detail: "Limited product-level profitability and portfolio data available.",
      tone: "low",
    });
  } else if (dataScore && dataScore < 3) {
    factors.push({
      label: "Data Availability",
      detail: "Partial product-level data — some evidence is self-reported.",
      tone: "medium",
    });
  } else if (dataScore) {
    factors.push({
      label: "Data Availability",
      detail: "Product-level data is accessible enough to ground findings.",
      tone: "high",
    });
  }

  // Respondent scope — one assessment currently captures a single respondent.
  if (assessment?.respondent_name) {
    factors.push({
      label: "Respondent Scope",
      detail: `Single respondent (${assessment.respondent_role || "individual view"}) — not cross-functionally triangulated.`,
      tone: "medium",
    });
  }

  // Answer clarity — default sensible note.
  factors.push({
    label: "Answer Clarity",
    detail: "Based on the respondent's self-reported evidence captured in the conversation.",
    tone: "medium",
  });

  return factors;
};

const deriveConfidence = (factors) => {
  if (factors.some((f) => f.tone === "low") && factors.filter((f) => f.tone === "low").length >= 2) return "low";
  if (factors.every((f) => f.tone === "high")) return "high";
  return "medium";
};

const TONE_DOT = {
  high: "bg-[#34D399]",
  medium: "bg-[#C9A84C]",
  low: "bg-[#EF4444]",
};

export const AssessmentReliability = ({ report, assessment }) => {
  const provided = report?.assessment_reliability;
  let confidence;
  let factors;

  if (provided && typeof provided === "object") {
    confidence = normaliseConfidence(provided.confidence);
    factors = Array.isArray(provided.factors) && provided.factors.length > 0
      ? provided.factors.map((f) => ({
          label: f.label || f.name || "Signal",
          detail: f.detail || f.note || f.value || "",
          tone: normaliseConfidence(f.tone || f.rating),
        }))
      : deriveFactors(report, assessment);
  } else if (typeof provided === "string") {
    confidence = normaliseConfidence(provided);
    factors = deriveFactors(report, assessment);
  } else {
    factors = deriveFactors(report, assessment);
    confidence = deriveConfidence(factors);
  }

  const tone = CONFIDENCE_TONES[confidence];
  const ToneIcon = tone.icon;

  return (
    <div
      data-testid="assessment-reliability-card"
      className="p-5 sm:p-6 glass-surface-highlight rounded-2xl"
    >
      <div className="flex items-start justify-between gap-4 flex-wrap mb-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-white/[0.04] border border-white/[0.08] flex items-center justify-center shrink-0">
            <ShieldCheck size={16} className="text-white/60" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white font-['Outfit'] leading-tight">
              Assessment Reliability
            </h2>
            <p className="text-[11px] text-white/40 italic mt-0.5">
              How much to rely on these results for decisions
            </p>
          </div>
        </div>
        <div
          data-testid="reliability-confidence-badge"
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl"
          style={{
            backgroundColor: `${tone.color}14`,
            border: `1px solid ${tone.color}35`,
          }}
        >
          <ToneIcon size={14} style={{ color: tone.color }} />
          <span className="text-[10px] uppercase tracking-[0.15em] text-white/50">Confidence</span>
          <span className="text-xs font-bold font-['Outfit']" style={{ color: tone.color }}>
            {tone.label}
          </span>
        </div>
      </div>

      <p className="text-sm text-white/60 mb-4 leading-relaxed">{tone.blurb}</p>

      <div className="space-y-2">
        {factors.map((f, i) => (
          <div
            key={i}
            data-testid={`reliability-factor-${i}`}
            className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.025] border border-white/[0.05]"
          >
            <span className={`w-1.5 h-1.5 rounded-full mt-2 shrink-0 ${TONE_DOT[f.tone] || TONE_DOT.medium}`} />
            <div className="min-w-0">
              <p className="text-xs font-semibold text-white font-['Outfit']">{f.label}</p>
              <p className="text-xs text-white/55 leading-relaxed mt-0.5">{f.detail}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AssessmentReliability;
