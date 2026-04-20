import axios from "axios";
import { Download, ClipboardCheck } from "lucide-react";
import { getScoreColorClass } from "../../utils/scoring";
import { StatusBadge, EmptyState } from "../ScoreComponents";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ScoreCell = ({ value }) => (
  <span className={`font-['JetBrains_Mono'] font-semibold text-xs ${getScoreColorClass(value)}`}>
    {value?.toFixed ? value.toFixed(1) : "–"}
  </span>
);

const downloadPdf = async (assessment) => {
  try {
    const res = await axios.get(`${BACKEND_URL}/api/assessments/${assessment.id}/pdf`, { responseType: "blob" });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `${assessment.company_name?.replace(/\s+/g, "_")}_Report.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    console.error("Failed to download PDF:", err);
  }
};

const TableRow = ({ a }) => (
  <tr className="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors" data-testid={`admin-assessment-row-${a.id}`}>
    <td className="px-4 sm:px-6 py-3">
      <p className="text-white font-medium">{a.company_name}</p>
      <p className="text-xs text-white/30">{a.company_industry}</p>
    </td>
    <td className="px-4 sm:px-6 py-3">
      <p className="text-white/60">{a.respondent_name}</p>
      <p className="text-xs text-white/30">{a.respondent_role}</p>
    </td>
    <td className="px-4 sm:px-6 py-3">
      <p className="text-white/60">{a.consultant_name}</p>
      <p className="text-xs text-white/30">{a.consultant_email}</p>
    </td>
    <td className="px-4 sm:px-6 py-3"><StatusBadge status={a.status} /></td>
    <td className="px-4 sm:px-6 py-3"><ScoreCell value={a.scores?.people} /></td>
    <td className="px-4 sm:px-6 py-3"><ScoreCell value={a.scores?.process} /></td>
    <td className="px-4 sm:px-6 py-3"><ScoreCell value={a.scores?.data} /></td>
    <td className="px-4 sm:px-6 py-3"><ScoreCell value={a.scores?.technology} /></td>
    <td className="px-4 sm:px-6 py-3">
      {a.scores?.overall
        ? <span className={`font-['JetBrains_Mono'] font-bold ${getScoreColorClass(a.scores.overall)}`}>{a.scores.overall.toFixed(1)}</span>
        : <span className="text-white/30">–</span>}
    </td>
    <td className="px-4 sm:px-6 py-3 text-white/40 text-xs whitespace-nowrap">
      {new Date(a.created_at).toLocaleDateString()}
    </td>
    <td className="px-4 sm:px-6 py-3">
      {a.status === "completed" ? (
        <button
          onClick={() => downloadPdf(a)}
          data-testid={`admin-download-${a.id}`}
          className="flex items-center gap-1 px-2.5 py-1 text-[10px] font-medium text-[#C9A84C] bg-[#C9A84C]/10 hover:bg-[#C9A84C]/20 rounded-md border border-[#C9A84C]/20 transition-colors whitespace-nowrap"
        >
          <Download size={10} /> PDF
        </button>
      ) : <span className="text-white/20 text-xs">–</span>}
    </td>
  </tr>
);

export const AdminFullAssessmentsTable = ({ assessments }) => {
  if (assessments.length === 0) {
    return (
      <div className="glass-surface-highlight rounded-xl">
        <EmptyState icon={ClipboardCheck} title="No assessments found" />
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
              <th className="px-4 sm:px-6 py-3">Respondent</th>
              <th className="px-4 sm:px-6 py-3">Consultant</th>
              <th className="px-4 sm:px-6 py-3">Status</th>
              <th className="px-4 sm:px-6 py-3">P</th>
              <th className="px-4 sm:px-6 py-3">Pr</th>
              <th className="px-4 sm:px-6 py-3">D</th>
              <th className="px-4 sm:px-6 py-3">T</th>
              <th className="px-4 sm:px-6 py-3">Overall</th>
              <th className="px-4 sm:px-6 py-3">Date</th>
              <th className="px-4 sm:px-6 py-3">Report</th>
            </tr>
          </thead>
          <tbody className="text-sm">
            {assessments.map((a) => <TableRow key={a.id} a={a} />)}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AdminFullAssessmentsTable;
