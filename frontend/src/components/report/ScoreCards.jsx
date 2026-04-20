import { Users, ClipboardCheck, Database, Monitor } from "lucide-react";
import { getScoreColor, getScoreColorClass, LEVEL_NAMES } from "../../utils/scoring";
import { DIMENSIONS } from "./constants";

const DIM_ICONS = { people: Users, process: ClipboardCheck, data: Database, technology: Monitor };

const deriveLevelName = (s) => {
  if (s === null || s === undefined || isNaN(s)) return "–";
  const n = Number(s);
  if (n < 1.5) return "Ad Hoc";
  if (n < 2.5) return "Developing";
  if (n < 3.5) return "Defined";
  if (n < 4.5) return "Managed";
  return "Predictive";
};

const cleanLevel = (candidate, score) => {
  const fallback = deriveLevelName(score);
  if (!candidate) return fallback;
  const trimmed = String(candidate).trim();
  if (!trimmed || trimmed.toUpperCase() === "N/A" || trimmed === "–") return fallback;
  return trimmed;
};

export const OverallScoreCard = ({ scores, levelNames, overallLevel, contextualScore }) => {
  const equal = scores.overall;
  const equalLevelName = cleanLevel(levelNames.overall || LEVEL_NAMES[overallLevel], equal);
  const contextualLevelName = cleanLevel(null, contextualScore);
  const hasContextual = typeof contextualScore === "number";

  return (
    <div data-testid="overall-score-card" className="p-6 sm:p-8 glass-surface-highlight rounded-2xl">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
        {/* Equal-Weighted — primary */}
        <div data-testid="equal-weighted-score">
          <div className="flex items-center gap-2 mb-2">
            <p className="text-xs uppercase tracking-[0.2em] text-[#C9A84C]">Equal-Weighted Score</p>
            <span className="text-[10px] px-2 py-0.5 rounded bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/20 uppercase tracking-wider">Primary</span>
          </div>
          <div className="flex items-baseline gap-3">
            <span className={`text-5xl sm:text-6xl font-bold font-['JetBrains_Mono'] ${getScoreColorClass(equal)}`}>
              {equal?.toFixed(2) || "–"}
            </span>
            <span className="text-xl text-white/30">/ 5.00</span>
          </div>
          <p className="text-base sm:text-lg font-semibold text-white mt-1 font-['Outfit']">{equalLevelName}</p>
          <p className="text-[11px] text-white/40 mt-1 italic">Academically validated baseline (25% each pillar)</p>
        </div>

        {/* Contextual — secondary */}
        <div data-testid="contextual-score" className="md:border-l md:border-white/[0.08] md:pl-6 lg:pl-8">
          <div className="flex items-center gap-2 mb-2">
            <p className="text-xs uppercase tracking-[0.2em] text-white/50">Contextual Score</p>
            <span className="text-[10px] px-2 py-0.5 rounded bg-white/[0.05] text-white/60 border border-white/[0.08] uppercase tracking-wider">Secondary</span>
          </div>
          {hasContextual ? (
            <>
              <div className="flex items-baseline gap-3">
                <span className={`text-5xl sm:text-6xl font-bold font-['JetBrains_Mono'] ${getScoreColorClass(contextualScore)}`}>
                  {contextualScore.toFixed(2)}
                </span>
                <span className="text-xl text-white/30">/ 5.00</span>
              </div>
              <p className="text-base sm:text-lg font-semibold text-white mt-1 font-['Outfit']">{contextualLevelName}</p>
              <p className="text-[11px] text-white/40 mt-1 italic">Adjusted for business model + stated priority</p>
            </>
          ) : (
            <p className="text-white/40 text-sm italic pt-2">Not yet calculated for this assessment.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export const DimensionScoreCards = ({ scores, levelNames }) => (
  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
    {DIMENSIONS.map(dim => {
      const Icon = DIM_ICONS[dim];
      const score = scores[dim] || 0;
      const color = getScoreColor(score);
      return (
        <div key={dim} data-testid={`dimension-card-${dim}`} className="p-4 sm:p-5 glass-card rounded-xl">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" style={{ backgroundColor: `${color}15` }}>
              <Icon size={16} style={{ color }} />
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-semibold text-white capitalize font-['Outfit'] truncate">{dim}</h3>
              <p className="text-[10px] text-white/40 truncate">{levelNames[dim] || ""}</p>
            </div>
          </div>
          <div className="flex items-baseline gap-1 mb-2">
            <span className={`text-2xl font-bold font-['JetBrains_Mono'] ${getScoreColorClass(score)}`}>{score}</span>
            <span className="text-white/30 text-xs">/ 5</span>
          </div>
          <div className="w-full h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
            <div className="h-full rounded-full transition-all duration-500" style={{ width: `${(score / 5) * 100}%`, backgroundColor: color }} />
          </div>
        </div>
      );
    })}
  </div>
);
