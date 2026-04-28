import { CheckCircle2, Circle } from "lucide-react";

export const PHASES = [
  { key: "welcome", label: "Welcome" },
  { key: "people", label: "People" },
  { key: "process", label: "Process" },
  { key: "data", label: "Data" },
  { key: "technology", label: "Technology" },
  { key: "decision", label: "Decision Types" },
  { key: "benchmark", label: "Benchmark" },
  { key: "report", label: "Report" }
];

const getPhaseIndex = (phase) => PHASES.findIndex(p => p.key === phase);

export const PhaseIndicator = ({ currentPhase }) => {
  const currentIdx = getPhaseIndex(currentPhase);
  return (
    <div className="h-12 sm:h-14 glass-surface flex items-center px-3 sm:px-6 overflow-x-auto shrink-0 relative z-10 scrollbar-hide">
      <div className="flex items-center gap-1 sm:gap-2">
        {PHASES.map((phase, idx) => {
          const isCompleted = idx < currentIdx;
          const isCurrent = idx === currentIdx;
          return (
            <div key={phase.key} className="flex items-center">
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm transition-all ${
                isCompleted ? 'bg-[#34D399]/15 text-[#34D399] border border-[#34D399]/20' :
                isCurrent ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' :
                'bg-[#F8F9FA] text-[#8896A5] border border-[#E2E8F0]'
              }`}>
                {isCompleted ? <CheckCircle2 size={14} /> :
                 isCurrent ? <div className="w-3.5 h-3.5 rounded-full bg-[#C9A84C] animate-pulse" /> :
                 <Circle size={14} />}
                <span className="hidden sm:inline whitespace-nowrap">{phase.label}</span>
              </div>
              {idx < PHASES.length - 1 && (
                <div className={`w-8 h-0.5 mx-1 ${idx < currentIdx ? 'bg-[#34D399]/60' : 'bg-[#E2E8F0]'}`} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default PhaseIndicator;
