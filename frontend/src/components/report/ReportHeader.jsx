import { Link } from "react-router-dom";
import { ArrowLeft, MessageSquare, Download } from "lucide-react";

export const ReportHeader = ({ assessmentId, onDownload, downloading }) => (
  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
    <div className="flex items-start gap-3">
      <Link
        to="/assessments"
        className="p-2 rounded-xl glass-surface text-white/50 hover:text-white transition-all shrink-0 mt-1"
        data-testid="report-back-btn"
      >
        <ArrowLeft size={18} />
      </Link>
      <div>
        <h1 className="text-xl sm:text-2xl lg:text-3xl font-semibold text-white font-['Outfit'] tracking-tight">
          PPDT Assessment Report
        </h1>
        <p className="text-white/40 mt-1 text-xs sm:text-sm">
          PPM Capability Maturity Research · University of Oulu (2026)
        </p>
      </div>
    </div>
    <div className="flex items-center gap-2 sm:self-start">
      <Link
        to={`/assessments/${assessmentId}`}
        data-testid="view-chat-btn"
        className="flex items-center gap-2 px-3 py-2 btn-glass rounded-xl text-sm"
      >
        <MessageSquare size={16} />
        <span className="hidden sm:inline">View Chat</span>
      </Link>
      <button
        onClick={onDownload}
        disabled={downloading}
        data-testid="export-pdf-btn"
        className="flex items-center gap-2 px-4 py-2 btn-liquid rounded-xl text-sm disabled:opacity-50"
      >
        <Download size={16} />
        {downloading ? "..." : "Export PDF"}
      </button>
    </div>
  </div>
);

export default ReportHeader;
