import { ArrowLeft, Building2, User, FileText, Download } from "lucide-react";
import { Link } from "react-router-dom";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const ChatHeader = ({ assessment, assessmentId }) => {
  const token = localStorage.getItem("token");

  const downloadPdf = async () => {
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/assessments/${assessmentId}/pdf`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) throw new Error();
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `PortfolioHealth_${(assessment?.company_name || "Report").replace(/\s+/g, "_")}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (e) {
      alert("PDF not ready yet.");
    }
  };

  return (
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
        <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
          <button
            onClick={downloadPdf}
            data-testid="chat-download-pdf-btn"
            title="Download PDF"
            className="flex items-center gap-1 sm:gap-2 px-2.5 sm:px-3 py-2 btn-glass rounded-xl text-xs sm:text-sm"
          >
            <Download size={14} />
            <span className="hidden md:inline">PDF</span>
          </button>
          <Link
            to={`/assessments/${assessmentId}/report`}
            data-testid="view-report-btn"
            className="flex items-center gap-1 sm:gap-2 px-3 sm:px-4 py-2 bg-[#34D399] text-white rounded-xl hover:bg-[#34D399]/80 transition-colors text-xs sm:text-sm"
          >
            <FileText size={14} />
            <span className="hidden sm:inline">View Report</span>
            <span className="sm:hidden">Report</span>
          </Link>
        </div>
      )}
    </header>
  );
};

export default ChatHeader;
