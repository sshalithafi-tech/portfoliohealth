import { Check } from "lucide-react";

/**
 * 7-phase stepper aligned with Hannila's 6-turn protocol:
 *   Welcome (intro + context)
 *   People · Process · Data · Technology  (one turn each)
 *   Governance (decision-types + benchmark combined)
 *   Report   (status === completed)
 */
export const PHASES = [
  { key: "welcome",    label: "Welcome",    short: "Welcome" },
  { key: "people",     label: "People",     short: "People" },
  { key: "process",    label: "Process",    short: "Process" },
  { key: "data",       label: "Data",       short: "Data" },
  { key: "technology", label: "Technology", short: "Tech" },
  { key: "governance", label: "Governance", short: "Gov" },
  { key: "report",     label: "Report",     short: "Report" },
];

const getPhaseIndex = (phase) => {
  // Map any legacy phase keys we may still get from the backend
  const aliases = { decision: "governance", benchmark: "governance" };
  const key = aliases[phase] || phase;
  const idx = PHASES.findIndex((p) => p.key === key);
  return idx === -1 ? 0 : idx;
};

export const PhaseIndicator = ({ currentPhase }) => {
  const currentIdx = getPhaseIndex(currentPhase);
  const completedCount = currentPhase === "report" ? PHASES.length - 1 : currentIdx;
  const progressPct = (completedCount / (PHASES.length - 1)) * 100;

  return (
    <div
      data-testid="phase-indicator"
      className="print-hide bg-white border-b border-[#E5E7EB] px-4 sm:px-8 py-4 shrink-0 relative z-10"
    >
      <div className="max-w-4xl mx-auto">
        {/* Progress meta */}
        <div className="flex items-center justify-between mb-3">
          <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#A88A2E] font-['Outfit']">
            {currentPhase === "report" ? "Assessment Complete" : "Assessment Progress"}
          </span>
          <span className="text-[11px] text-[#6B7280] font-['Outfit'] font-medium">
            <span className="text-[#0C1B2A] font-semibold">{Math.min(currentIdx + 1, PHASES.length)}</span>
            <span className="text-[#9CA3AF]"> / {PHASES.length}</span>
            <span className="text-[#9CA3AF] mx-2">·</span>
            <span className="text-[#0C1B2A] font-semibold">{PHASES[currentIdx]?.label}</span>
          </span>
        </div>

        {/* Segmented stepper */}
        <div className="relative">
          {/* Track */}
          <div className="absolute top-3.5 left-0 right-0 h-[2px] bg-[#E5E7EB] rounded-full" />
          {/* Filled track */}
          <div
            className="absolute top-3.5 left-0 h-[2px] rounded-full bg-gradient-to-r from-[#A88A2E] via-[#C9A84C] to-[#E8D49A] transition-all duration-500 ease-out"
            style={{ width: `${progressPct}%` }}
          />

          {/* Step markers */}
          <ol className="relative grid grid-cols-7 gap-1">
            {PHASES.map((phase, idx) => {
              const isCompleted = idx < currentIdx || currentPhase === "report";
              const isCurrent = idx === currentIdx && currentPhase !== "report";
              const isReport = currentPhase === "report" && phase.key === "report";

              return (
                <li
                  key={phase.key}
                  data-testid={`phase-step-${phase.key}`}
                  className="flex flex-col items-center gap-2"
                >
                  {/* Marker */}
                  <div
                    className={`
                      relative w-7 h-7 rounded-full flex items-center justify-center
                      font-['Outfit'] text-[11px] font-bold transition-all duration-300
                      ${isCompleted || isReport
                        ? 'bg-[#C9A84C] text-[#0C1B2A] shadow-[0_2px_8px_rgba(201,168,76,0.40)]'
                        : isCurrent
                          ? 'bg-white border-2 border-[#C9A84C] text-[#A88A2E] shadow-[0_0_0_4px_rgba(201,168,76,0.15)]'
                          : 'bg-white border-2 border-[#E5E7EB] text-[#9CA3AF]'
                      }
                    `}
                  >
                    {isCompleted || isReport ? (
                      <Check size={13} strokeWidth={3} />
                    ) : (
                      <span>{idx + 1}</span>
                    )}
                    {isCurrent && (
                      <span className="absolute inset-0 rounded-full border-2 border-[#C9A84C] animate-ping opacity-40" />
                    )}
                  </div>

                  {/* Label */}
                  <span
                    className={`
                      text-[10px] sm:text-[11px] font-['Outfit'] tracking-tight transition-colors text-center
                      ${isCompleted || isCurrent || isReport
                        ? 'text-[#0C1B2A] font-semibold'
                        : 'text-[#9CA3AF] font-medium'
                      }
                    `}
                  >
                    <span className="hidden sm:inline">{phase.label}</span>
                    <span className="sm:hidden">{phase.short}</span>
                  </span>
                </li>
              );
            })}
          </ol>
        </div>
      </div>
    </div>
  );
};

export default PhaseIndicator;
