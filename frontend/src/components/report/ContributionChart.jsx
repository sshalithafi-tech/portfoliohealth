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
    <div data-testid="contribution-chart" className="p-6 glass-surface-highlight rounded-xl">
      <h2 className="text-lg font-semibold text-white mb-6 font-['Outfit']">PPDT Maturity Contribution</h2>
      <div className="h-72 sm:h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} barGap={6} barCategoryGap="45%">
            <GlassDefs />
            <XAxis dataKey="name" tick={{ fill: "rgba(255,255,255,0.6)", fontSize: 13 }} axisLine={{ stroke: "rgba(255,255,255,0.1)" }} tickLine={false} />
            <YAxis domain={[0, 5]} tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} axisLine={{ stroke: "rgba(255,255,255,0.1)" }} tickLine={false} />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
            <Legend wrapperStyle={{ color: "rgba(255,255,255,0.6)", fontSize: 12, paddingTop: 12 }} iconType="circle" />

            {/* Raw Score — thin liquid-glass bar */}
            <Bar
              dataKey="rawScore"
              name="Raw Score"
              fill="url(#glass-raw)"
              stroke="rgba(96,165,250,0.8)"
              strokeWidth={0.6}
              radius={[8, 8, 2, 2]}
              barSize={18}
              isAnimationActive={true}
              animationDuration={700}
            >
              {chartData.map((_, i) => <Cell key={`raw-${i}`} />)}
              <LabelList dataKey="rawScore" position="top" fill="rgba(255,255,255,0.85)" fontSize={11} formatter={v => v.toFixed(1)} />
            </Bar>

            {/* Weighted Contribution — thin liquid-glass bar */}
            <Bar
              dataKey="weightedContribution"
              name="Weighted Contribution"
              fill="url(#glass-weight)"
              stroke="rgba(126,231,135,0.8)"
              strokeWidth={0.6}
              radius={[8, 8, 2, 2]}
              barSize={18}
              isAnimationActive={true}
              animationDuration={900}
            >
              {chartData.map((_, i) => <Cell key={`w-${i}`} />)}
              <LabelList dataKey="weightedContribution" position="top" fill="rgba(255,255,255,0.85)" fontSize={11} formatter={v => v.toFixed(2)} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ContributionChart;
