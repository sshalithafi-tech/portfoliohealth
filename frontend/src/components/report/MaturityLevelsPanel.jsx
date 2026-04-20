import { getScoreColor } from "../../utils/scoring";
import { DIMENSIONS, MATURITY_LEVELS } from "./constants";

export const MaturityLevelsPanel = ({ overallLevel, scores, report }) => (
  <div className="p-6 glass-surface-highlight rounded-xl">
    <h2 className="text-lg font-semibold text-white mb-6 font-['Outfit']">The Five PPDT Maturity Levels</h2>
    <div className="flex flex-col sm:flex-row gap-2 sm:gap-1">
      {MATURITY_LEVELS.map(ml => {
        const isActive = overallLevel === ml.level;
        return (
          <div
            key={ml.level}
            className={`flex-1 p-3 sm:p-4 rounded-xl border transition-all ${
              isActive ? 'bg-white/[0.06] shadow-lg' : 'border-white/[0.06] bg-white/[0.02]'
            }`}
            style={isActive ? { borderColor: ml.color, boxShadow: `0 0 20px ${ml.color}33` } : {}}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ backgroundColor: `${ml.color}20`, color: ml.color }}>
                L{ml.level}
              </span>
              <span className={`text-xs sm:text-sm font-semibold ${isActive ? 'text-white' : 'text-white/60'}`}>{ml.name}</span>
            </div>
            <p className={`text-[11px] leading-relaxed ${isActive ? 'text-white/70' : 'text-white/40'}`}>{ml.desc}</p>
          </div>
        );
      })}
    </div>
    <div className="mt-6 space-y-2">
      {DIMENSIONS.map(d => {
        const score = scores[d] || 0;
        const lvl = Math.round(score);
        const interp = report.pillar_interpretations?.[d] ||
          `Your ${d.charAt(0).toUpperCase() + d.slice(1)} score of ${score} places you at Level ${lvl} — ${MATURITY_LEVELS[Math.max(0, lvl - 1)]?.name || "Ad Hoc"}.`;
        return (
          <div key={d} className="flex items-start gap-3 py-2 border-b border-white/[0.04] last:border-0">
            <span className="text-xs font-bold px-2 py-0.5 rounded shrink-0 mt-0.5" style={{ backgroundColor: `${getScoreColor(score)}20`, color: getScoreColor(score) }}>
              {d.charAt(0).toUpperCase() + d.slice(1)}
            </span>
            <p className="text-white/60 text-sm">{interp}</p>
          </div>
        );
      })}
    </div>
  </div>
);

export default MaturityLevelsPanel;
