import { getScoreColorClass } from "../../utils/scoring";
import { DIMENSIONS } from "./constants";

export const ScoreBreakdown = ({ scores, weightsRaw, weightsNorm }) => (
  <div className="p-6 glass-surface-highlight rounded-xl">
    <h2 className="text-lg font-semibold text-white mb-6 font-['Outfit']">Score Breakdown</h2>
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div>
        <h3 className="text-sm text-white/50 uppercase tracking-wider mb-3">Raw Scores</h3>
        <div className="space-y-2">
          {DIMENSIONS.map(d => (
            <div key={d} className="flex items-center justify-between py-1.5 border-b border-white/[0.06]">
              <span className="text-white capitalize text-sm">{d}</span>
              <span className={`font-['JetBrains_Mono'] font-semibold ${getScoreColorClass(scores[d])}`}>{scores[d] || 0} / 5</span>
            </div>
          ))}
        </div>
      </div>
      <div>
        <h3 className="text-sm text-white/50 uppercase tracking-wider mb-3">Strategic Weighting & Contribution</h3>
        <div className="space-y-2">
          {DIMENSIONS.map(d => {
            const pct = ((weightsNorm[d] || 0.25) * 100).toFixed(1);
            const contrib = ((scores[d] || 0) * (weightsNorm[d] || 0.25)).toFixed(2);
            return (
              <div key={d} className="flex items-center justify-between py-1.5 border-b border-white/[0.06] text-sm">
                <span className="text-white/60 capitalize">{d} Weight: <span className="text-white">{pct}%</span></span>
                <span className="text-white/50 font-['JetBrains_Mono'] text-xs">
                  {scores[d] || 0} × {(weightsNorm[d] || 0.25).toFixed(3)} = <span className="text-[#7ee787] font-semibold">{contrib}</span>
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
    <div className="mt-6 pt-4 border-t border-white/[0.08] flex items-center justify-between">
      <span className="text-white font-semibold font-['Outfit']">Overall Maturity Score</span>
      <span className={`text-3xl font-bold font-['JetBrains_Mono'] ${getScoreColorClass(scores.overall)}`}>
        {scores.overall?.toFixed(2) || "–"} <span className="text-sm text-white/30">/ 5.00</span>
      </span>
    </div>
  </div>
);

export default ScoreBreakdown;
