import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend,
  ResponsiveContainer, LabelList
} from "recharts";
import { DIMENSIONS } from "./constants";

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-heavy rounded-lg px-3 py-2 text-xs border border-white/10">
      <p className="text-white font-medium mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>{p.name}: {p.value.toFixed(2)}</p>
      ))}
    </div>
  );
};

export const ContributionChart = ({ scores, weightsNorm }) => {
  const chartData = DIMENSIONS.map(d => ({
    name: d.charAt(0).toUpperCase() + d.slice(1),
    rawScore: scores[d] || 0,
    weightedContribution: parseFloat(((scores[d] || 0) * (weightsNorm[d] || 0.25)).toFixed(2)),
  }));

  return (
    <div className="p-6 glass-surface-highlight rounded-xl">
      <h2 className="text-lg font-semibold text-white mb-6 font-['Outfit']">PPDT Maturity Contribution</h2>
      <div className="h-72 sm:h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} barGap={4} barCategoryGap="20%">
            <XAxis dataKey="name" tick={{ fill: "rgba(255,255,255,0.6)", fontSize: 13 }} axisLine={{ stroke: "rgba(255,255,255,0.1)" }} />
            <YAxis domain={[0, 5]} tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} axisLine={{ stroke: "rgba(255,255,255,0.1)" }} />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
            <Legend wrapperStyle={{ color: "rgba(255,255,255,0.6)", fontSize: 12, paddingTop: 8 }} />
            <Bar dataKey="rawScore" name="Raw Score" fill="#60A5FA" radius={[4, 4, 0, 0]}>
              <LabelList dataKey="rawScore" position="top" fill="rgba(255,255,255,0.7)" fontSize={11} formatter={v => v.toFixed(1)} />
            </Bar>
            <Bar dataKey="weightedContribution" name="Weighted Contribution" fill="#7ee787" radius={[4, 4, 0, 0]}>
              <LabelList dataKey="weightedContribution" position="top" fill="rgba(255,255,255,0.7)" fontSize={11} formatter={v => v.toFixed(2)} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ContributionChart;
