import { Users, ClipboardCheck, Database, Monitor } from "lucide-react";
import { getScoreColor, getScoreColorClass, LEVEL_NAMES } from "../../utils/scoring";
import { DIMENSIONS } from "./constants";

const DIM_ICONS = { people: Users, process: ClipboardCheck, data: Database, technology: Monitor };

export const OverallScoreCard = ({ scores, levelNames, overallLevel }) => (
  <div className="p-6 sm:p-8 glass-surface-highlight rounded-2xl">
    <p className="text-xs uppercase tracking-[0.2em] text-[#C9A84C] mb-2">Overall Maturity Level</p>
    <div className="flex items-baseline gap-3">
      <span className={`text-5xl sm:text-6xl font-bold font-['JetBrains_Mono'] ${getScoreColorClass(scores.overall)}`}>
        {scores.overall?.toFixed(2) || "–"}
      </span>
      <span className="text-xl text-white/30">/ 5.00</span>
    </div>
    <p className="text-xl font-semibold text-white mt-2 font-['Outfit']">
      {levelNames.overall || LEVEL_NAMES[overallLevel] || "–"}
    </p>
  </div>
);

export const DimensionScoreCards = ({ scores, levelNames }) => (
  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
    {DIMENSIONS.map(dim => {
      const Icon = DIM_ICONS[dim];
      const score = scores[dim] || 0;
      const color = getScoreColor(score);
      return (
        <div key={dim} className="p-4 sm:p-5 glass-card rounded-xl">
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
