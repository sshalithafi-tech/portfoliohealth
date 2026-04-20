import { ArrowLeft, Building2, User, FileText } from "lucide-react";
import { Link } from "react-router-dom";

export const ChatHeader = ({ assessment, assessmentId }) => (
  <header className="h-14 sm:h-16 glass-surface flex items-center px-3 sm:px-6 shrink-0 relative z-10">
    <Link
      to="/assessments"
      data-testid="back-to-assessments"
      className="flex items-center gap-1 sm:gap-2 text-white/50 hover:text-white transition-colors mr-3 sm:mr-6"
    >
      <ArrowLeft size={18} />
      <span className="hidden sm:inline">Back</span>
    </Link>

    <div className="flex items-center gap-2 sm:gap-4 flex-1 min-w-0">
      <div className="flex items-center gap-1.5 sm:gap-2 min-w-0">
        <Building2 size={16} className="text-[#C9A84C] shrink-0" />
        <span className="text-white font-medium text-sm sm:text-base truncate">{assessment?.company_name}</span>
      </div>
      <div className="hidden md:flex items-center gap-2 text-white/50">
        <User size={14} />
        <span className="text-sm">{assessment?.respondent_name} · {assessment?.respondent_role}</span>
      </div>
    </div>

    {assessment?.status === "completed" && (
      <Link
        to={`/assessments/${assessmentId}/report`}
        data-testid="view-report-btn"
        className="flex items-center gap-1 sm:gap-2 px-3 sm:px-4 py-2 bg-[#34D399] text-white rounded-xl hover:bg-[#34D399]/80 transition-colors text-xs sm:text-sm shrink-0"
      >
        <FileText size={14} />
        <span className="hidden sm:inline">View Report</span>
        <span className="sm:hidden">Report</span>
      </Link>
    )}
  </header>
);

export default ChatHeader;
