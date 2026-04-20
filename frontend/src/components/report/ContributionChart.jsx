import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend, Cell,
  ResponsiveContainer, LabelList
} from "recharts";
import { DIMENSIONS } from "./constants";

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-heavy rounded-lg px-3 py-2 text-xs border border-white/10 backdrop-blur-xl">
      <p className="text-white font-medium mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>{p.name}: {p.value.toFixed(2)}</p>
      ))}
    </div>
  );
};

// Liquid-glass gradient + highlight defs, reusable inside the SVG
const GlassDefs = () => (
  <defs>
    {/* Raw-score bar — cyan/blue glass */}
    <linearGradient id="glass-raw" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stopColor="rgba(96,165,250,0.85)" />
      <stop offset="55%" stopColor="rgba(96,165,250,0.55)" />
      <stop offset="100%" stopColor="rgba(96,165,250,0.25)" />
    </linearGradient>
    <linearGradient id="glass-raw-sheen" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stopColor="rgba(255,255,255,0.45)" />
      <stop offset="35%" stopColor="rgba(255,255,255,0.12)" />
      <stop offset="100%" stopColor="rgba(255,255,255,0.00)" />
    </linearGradient>
    {/* Weighted contribution bar — mint/emerald glass */}
    <linearGradient id="glass-weight" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stopColor="rgba(126,231,135,0.85)" />
      <stop offset="55%" stopColor="rgba(126,231,135,0.55)" />
      <stop offset="100%" stopColor="rgba(126,231,135,0.25)" />
    </linearGradient>
  </defs>
);

export const ContributionChart = ({ scores, weightsNorm }) => {
  const chartData = DIMENSIONS.map(d => ({
    name: d.charAt(0).toUpperCase() + d.slice(1),
    rawScore: scores[d] || 0,
    weightedContribution: parseFloat(((scores[d] || 0) * (weightsNorm[d] || 0.25)).toFixed(2)),
  }));

  return (
    <div data-testid="contribution-chart" className="p-5 sm:p-6 glass-surface-highlight rounded-xl max-w-3xl mx-auto w-full">
      <div className="flex items-baseline justify-between mb-4 gap-3 flex-wrap">
        <h2 className="text-base sm:text-lg font-semibold text-white font-['Outfit']">PPDT Maturity Contribution</h2>
        <p className="text-[11px] text-white/40 italic">Raw score vs weight × score</p>
      </div>
      <div className="h-56 sm:h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} barGap={4} barCategoryGap="35%" margin={{ top: 16, right: 8, bottom: 4, left: -16 }}>
            <GlassDefs />
            <XAxis dataKey="name" tick={{ fill: "rgba(255,255,255,0.6)", fontSize: 12 }} axisLine={{ stroke: "rgba(255,255,255,0.08)" }} tickLine={false} />
            <YAxis domain={[0, 5]} tick={{ fill: "rgba(255,255,255,0.35)", fontSize: 10 }} axisLine={{ stroke: "rgba(255,255,255,0.08)" }} tickLine={false} width={32} />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
            <Legend wrapperStyle={{ color: "rgba(255,255,255,0.55)", fontSize: 11, paddingTop: 10 }} iconType="circle" iconSize={8} />

            <Bar
              dataKey="rawScore"
              name="Raw Score"
              fill="url(#glass-raw)"
              stroke="rgba(96,165,250,0.7)"
              strokeWidth={0.5}
              radius={[6, 6, 1, 1]}
              barSize={14}
              isAnimationActive={true}
              animationDuration={700}
            >
              {chartData.map((_, i) => <Cell key={`raw-${i}`} />)}
              <LabelList dataKey="rawScore" position="top" fill="rgba(255,255,255,0.75)" fontSize={10} formatter={v => v.toFixed(1)} />
            </Bar>

            <Bar
              dataKey="weightedContribution"
              name="Weighted Contribution"
              fill="url(#glass-weight)"
              stroke="rgba(126,231,135,0.7)"
              strokeWidth={0.5}
              radius={[6, 6, 1, 1]}
              barSize={14}
              isAnimationActive={true}
              animationDuration={900}
            >
              {chartData.map((_, i) => <Cell key={`w-${i}`} />)}
              <LabelList dataKey="weightedContribution" position="top" fill="rgba(255,255,255,0.75)" fontSize={10} formatter={v => v.toFixed(2)} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ContributionChart;
