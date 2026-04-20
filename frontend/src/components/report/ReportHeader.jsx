import { Link } from "react-router-dom";
import { ArrowLeft, MessageSquare, Download, Building2, User, Calendar, Layers, Target } from "lucide-react";

const Chip = ({ icon: Icon, label, value, testId }) => {
  if (!value) return null;
  return (
    <div data-testid={testId} className="flex items-center gap-2">
      <Icon size={16} className="text-[#C9A84C]" />
      <span className="text-white/50">{label}:</span>
      <span className="text-white font-medium capitalize">{value}</span>
    </div>
  );
};

export const ReportHeader = ({ assessmentId, assessment, onDownload, downloading, businessModel, strategicPriority, businessModelNote }) => (
  <>
    <div className="flex flex-col gap-4">
      <div className="flex items-start gap-3">
        <Link to="/assessments" className="p-2 rounded-xl glass-surface text-white/50 hover:text-white transition-all shrink-0 mt-1">
          <ArrowLeft size={18} />
        </Link>
        <div>
          <h1 className="text-xl sm:text-2xl lg:text-3xl font-semibold text-white font-['Outfit'] tracking-tight">
            PPDT Assessment Report
          </h1>
          <p className="text-white/40 mt-1 text-xs sm:text-sm">PPM Capability Maturity Research · University of Oulu (2026)</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Link to={`/assessments/${assessmentId}`} data-testid="view-chat-btn" className="flex items-center gap-2 px-3 py-2 btn-glass rounded-xl text-sm">
          <MessageSquare size={16} /><span className="hidden sm:inline">View Chat</span>
        </Link>
        <button onClick={onDownload} disabled={downloading} data-testid="export-pdf-btn" className="flex items-center gap-2 px-4 py-2 btn-liquid rounded-xl text-sm disabled:opacity-50">
          <Download size={16} />{downloading ? "..." : "Export PDF"}
        </button>
      </div>
    </div>

    <div data-testid="report-context-chips" className="p-3 sm:p-4 glass-surface-highlight rounded-xl flex flex-col sm:flex-row sm:flex-wrap gap-3 sm:gap-6 text-sm">
      <Chip icon={Building2} label="Company" value={assessment.company_name} testId="chip-company" />
      <Chip icon={User} label="Respondent" value={assessment.respondent_name} testId="chip-respondent" />
      <Chip icon={Calendar} label="Date" value={new Date(assessment.completed_at || assessment.created_at).toLocaleDateString()} testId="chip-date" />
      <Chip icon={Layers} label="Business Model" value={businessModel} testId="chip-business-model" />
      <Chip icon={Target} label="Strategic Priority" value={strategicPriority} testId="chip-strategic-priority" />
    </div>
    {businessModelNote && (
      <p data-testid="business-model-note" className="text-[11px] italic text-white/50 -mt-4 pl-2 sm:pl-4">
        {businessModelNote}
      </p>
    )}
  </>
);

export default ReportHeader;
