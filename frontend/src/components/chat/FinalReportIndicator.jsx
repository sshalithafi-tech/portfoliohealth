import { useEffect, useState } from "react";
import { Sparkles, Clock } from "lucide-react";
import LogoMark from "../LogoMark";

const STAGES = [
  "Synthesising the conversation…",
  "Scoring People, Process, Data, Technology…",
  "Identifying the bottleneck pillar…",
  "Rating decision-type vulnerability…",
  "Drafting the improvement roadmap…",
  "Finalising the consultant's note…",
];

export const FinalReportIndicator = () => {
  const [stage, setStage] = useState(0);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const stageTimer = setInterval(() => {
      setStage((s) => (s + 1) % STAGES.length);
    }, 3500);
    const tickTimer = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => {
      clearInterval(stageTimer);
      clearInterval(tickTimer);
    };
  }, []);

  const slow = elapsed > 60;

  return (
    <div
      data-testid="final-report-indicator"
      className="animate-fade-in rounded-2xl border border-[#67E8F9] bg-gradient-to-br from-[#ECFEFF] to-white p-4 sm:p-5"
    >
      <div className="flex items-start gap-3">
        <LogoMark className="w-9 h-9 rounded-lg shrink-0" radius={14} />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles size={13} className="text-[#0891B2]" />
            <p className="text-[10px] sm:text-[11px] uppercase tracking-[0.2em] text-[#0891B2] font-semibold">
              Generating final report
            </p>
          </div>

          <p
            key={stage}
            className="text-sm text-[#4A5568] font-['Outfit'] animate-fade-in mb-3"
          >
            {STAGES[stage]}
          </p>

          {/* Indeterminate progress bar — a shimmering gradient that loops */}
          <div
            role="progressbar"
            aria-label="Generating final report"
            className="relative h-1.5 w-full rounded-full bg-[#F8F9FA] overflow-hidden"
          >
            <div className="absolute inset-y-0 w-1/3 rounded-full bg-gradient-to-r from-transparent via-[#0891B2] to-transparent animate-progress-sweep" />
          </div>

          <div className="mt-2.5 flex items-center justify-between text-[10px] text-[#8896A5]">
            <span className="flex items-center gap-1.5">
              <Clock size={10} />
              <span>
                {elapsed}s · typically ~30–60s for the full report
              </span>
            </span>
            {slow && (
              <span data-testid="final-report-slow-hint" className="text-[#0891B2]/70 italic">
                taking longer than usual — hang tight
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FinalReportIndicator;
