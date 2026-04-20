import { useState } from "react";
import { Info, ChevronDown, ChevronUp } from "lucide-react";
import { getScoreColorClass } from "../../utils/scoring";
import { DIMENSIONS } from "./constants";

export const ScoreMethodology = ({ scores, weightsNorm }) => {
  const [open, setOpen] = useState(false);
  return (
    <div className="glass-surface-highlight rounded-xl overflow-hidden">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-between p-5 text-left hover:bg-white/[0.02] transition-colors">
        <div className="flex items-center gap-2">
          <Info size={18} className="text-[#C9A84C]" />
          <span className="text-white font-medium font-['Outfit']">How is this score calculated?</span>
        </div>
        {open ? <ChevronUp size={18} className="text-white/50" /> : <ChevronDown size={18} className="text-white/50" />}
      </button>
      {open && (
        <div className="px-5 pb-6 space-y-5 animate-fade-in border-t border-white/[0.06]">
          <p className="text-white/60 text-sm leading-relaxed mt-4">
            A traditional maturity model calculates a simple average across its dimensions. But a simple average can be misleading.
          </p>
          <p className="text-white/60 text-sm leading-relaxed">
            If a company has world-class engineers (Score: 5) and great software (Score: 5), but their data is completely siloed and inaccurate (Score: 1), a standard average gives them a '3.0 — Satisfactory.' But with a Data score of 1, product-level portfolio analysis is literally impossible. The overall score should reflect that critical bottleneck.
          </p>
          <p className="text-white/60 text-sm leading-relaxed">
            That is why we use a <span className="text-[#C9A84C] font-semibold">Weighted Sum Equation</span> based on the strategic priorities <em>your organisation</em> assigned to each PPDT dimension:
          </p>
          <div className="p-5 bg-white/[0.03] rounded-xl border border-white/[0.08] text-center">
            <div className="text-2xl sm:text-3xl text-[#C9A84C] font-['JetBrains_Mono'] tracking-wide mb-4">
              M = w<sub className="text-xs">pe</sub> · S<sub className="text-xs">pe</sub> + w<sub className="text-xs">pr</sub> · S<sub className="text-xs">pr</sub> + w<sub className="text-xs">d</sub> · S<sub className="text-xs">d</sub> + w<sub className="text-xs">t</sub> · S<sub className="text-xs">t</sub>
            </div>
            <div className="text-white/50 text-xs space-y-1 text-left max-w-md mx-auto">
              <p><span className="text-white font-medium italic">M</span> = Overall Maturity Score (1.0 to 5.0)</p>
              <p><span className="text-white font-medium italic">w</span> = Strategic Weight assigned to the specific pillar</p>
              <p><span className="text-white font-medium italic">S</span> = Assessed Grade (1 to 5) for the pillar</p>
              <p className="pt-1 text-[#C9A84C]">All weights sum to 1: w<sub>pe</sub> + w<sub>pr</sub> + w<sub>d</sub> + w<sub>t</sub> = 1</p>
            </div>
          </div>
          <div className="p-4 bg-white/[0.03] rounded-xl border border-white/[0.08]">
            <h4 className="text-sm font-semibold text-white mb-3 font-['Outfit']">Your Calculation</h4>
            <div className="space-y-1.5 font-['JetBrains_Mono'] text-xs">
              {DIMENSIONS.map(d => {
                const s = scores[d] || 0;
                const w = weightsNorm[d] || 0.25;
                return (
                  <div key={d} className="flex items-center gap-2 text-white/60">
                    <span className="text-white capitalize w-20">{d}</span>
                    <span>{s} x {w.toFixed(2)} = <span className="text-[#7ee787] font-semibold">{(s * w).toFixed(2)}</span></span>
                  </div>
                );
              })}
              <div className="border-t border-white/10 pt-2 mt-2 flex items-center gap-2">
                <span className="text-white font-semibold w-20">Total</span>
                <span className={`text-lg font-bold ${getScoreColorClass(scores.overall)}`}>
                  {scores.overall?.toFixed(2) || "–"} / 5.00
                </span>
              </div>
            </div>
          </div>
          <div className="p-4 bg-[#C9A84C]/5 border border-[#C9A84C]/15 rounded-xl">
            <p className="text-white/70 text-sm italic">
              "The weighting reflects what <em>your organisation</em> declared as most strategically important. A low score in a high-weight pillar has a disproportionate impact on your overall maturity — and signals where to focus first."
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScoreMethodology;
