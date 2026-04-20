import { Zap } from "lucide-react";
import { getScoreColorClass } from "../../utils/scoring";
import { EmptyState } from "../ScoreComponents";

const ScoreCell = ({ value }) => (
  <span className={`font-['JetBrains_Mono'] font-semibold text-xs ${getScoreColorClass(value)}`}>
    {value?.toFixed ? value.toFixed(1) : "–"}
  </span>
);

const QuickRow = ({ q }) => (
  <tr className="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors" data-testid={`admin-quick-row-${q.id}`}>
    <td className="px-4 sm:px-6 py-3 text-white font-medium">{q.company_name}</td>
    <td className="px-4 sm:px-6 py-3 text-white/50">{q.industry}</td>
    <td className="px-4 sm:px-6 py-3">
      <p className="text-white/60">{q.respondent_name || "Anonymous"}</p>
      <p className="text-xs text-white/30">{q.respondent_email || ""}</p>
    </td>
    <td className="px-4 sm:px-6 py-3"><ScoreCell value={q.scores?.people} /></td>
    <td className="px-4 sm:px-6 py-3"><ScoreCell value={q.scores?.process} /></td>
    <td className="px-4 sm:px-6 py-3"><ScoreCell value={q.scores?.data} /></td>
    <td className="px-4 sm:px-6 py-3"><ScoreCell value={q.scores?.technology} /></td>
    <td className="px-4 sm:px-6 py-3">
      {q.scores?.overall
        ? <span className={`font-['JetBrains_Mono'] font-bold ${getScoreColorClass(q.scores.overall)}`}>{q.scores.overall.toFixed(1)}</span>
        : <span className="text-white/30">–</span>}
    </td>
    <td className="px-4 sm:px-6 py-3 text-white/40 text-xs whitespace-nowrap">
      {new Date(q.created_at).toLocaleDateString()}
    </td>
  </tr>
);

export const AdminQuickAssessmentsTable = ({ quickAssessments }) => {
  if (quickAssessments.length === 0) {
    return (
      <div className="glass-surface-highlight rounded-xl">
        <EmptyState icon={Zap} title="No quick assessments found" />
      </div>
    );
  }

  return (
    <div className="glass-surface-highlight rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wider text-white/40 border-b border-white/[0.08]">
              <th className="px-4 sm:px-6 py-3">Company</th>
              <th className="px-4 sm:px-6 py-3">Industry</th>
              <th className="px-4 sm:px-6 py-3">Respondent</th>
              <th className="px-4 sm:px-6 py-3">P</th>
              <th className="px-4 sm:px-6 py-3">Pr</th>
              <th className="px-4 sm:px-6 py-3">D</th>
              <th className="px-4 sm:px-6 py-3">T</th>
              <th className="px-4 sm:px-6 py-3">Overall</th>
              <th className="px-4 sm:px-6 py-3">Date</th>
            </tr>
          </thead>
          <tbody className="text-sm">
            {quickAssessments.map((q) => <QuickRow key={q.id} q={q} />)}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AdminQuickAssessmentsTable;
