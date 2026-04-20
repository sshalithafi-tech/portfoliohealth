import { AlertOctagon, Users, ClipboardCheck, Database, Monitor } from "lucide-react";

const PILLAR_ICONS = { people: Users, process: ClipboardCheck, data: Database, technology: Monitor };
const PILLAR_COLORS = { people: "#60A5FA", process: "#34D399", data: "#C9A84C", technology: "#A78BFA" };

export const BottleneckSection = ({ bottleneckPillar, scores, report }) => {
  if (!bottleneckPillar) return null;
  const key = String(bottleneckPillar).toLowerCase();
  const Icon = PILLAR_ICONS[key] || AlertOctagon;
  const color = PILLAR_COLORS[key] || "#EF4444";
  const score = scores?.[key];
  const interp = report?.pillar_interpretations?.[key];

  return (
    <div data-testid="bottleneck-section" className="p-6 glass-surface-highlight rounded-xl border-l-4" style={{ borderLeftColor: color }}>
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0" style={{ backgroundColor: `${color}18` }}>
          <AlertOctagon size={22} style={{ color }} />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-white font-['Outfit']">Bottleneck Pillar</h2>
          <p className="text-xs text-white/40 italic">The weakest pillar caps real-world capability regardless of other scores.</p>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-5 mt-4">
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl" style={{ backgroundColor: `${color}10`, borderColor: `${color}30`, borderWidth: 1 }}>
          <Icon size={20} style={{ color }} />
          <div>
            <p className="text-[11px] uppercase tracking-wider" style={{ color }}>Bottleneck</p>
            <p className="text-lg font-semibold text-white capitalize font-['Outfit']">{bottleneckPillar}</p>
          </div>
          {typeof score === "number" && (
            <span className="ml-2 font-['JetBrains_Mono'] font-bold text-xl" style={{ color }}>
              {score}/5
            </span>
          )}
        </div>
      </div>

      {interp && (
        <p className="text-white/70 text-sm leading-relaxed mt-4 p-3 rounded-lg bg-white/[0.03] border border-white/[0.06]">
          {interp}
        </p>
      )}
    </div>
  );
};

export default BottleneckSection;
