import { Link } from "react-router-dom";
import { ArrowLeft, MessageSquare, Download, ExternalLink } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const ReportHeader = ({ assessmentId, onDownload, downloading }) => {
  const token = localStorage.getItem("token");
  const openHtmlReport = async () => {
    try {
      const res = await fetch(
        `${BACKEND_URL}/api/assessments/${assessmentId}/report.html`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) throw new Error("HTML report unavailable");
      const html = await res.text();
      const blob = new Blob([html], { type: "text/html" });
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank", "noopener");
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (e) {
      console.error(e);
      alert("Could not open HTML report.");
    }
  };

  return (
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
      <div className="flex items-center gap-2 sm:self-start flex-wrap">
        <Link
          to={`/assessments/${assessmentId}`}
          data-testid="view-chat-btn"
          className="flex items-center gap-2 px-3 py-2 btn-glass rounded-xl text-sm"
        >
          <MessageSquare size={16} />
          <span className="hidden sm:inline">View Chat</span>
        </Link>
        <button
          onClick={openHtmlReport}
          data-testid="view-html-report-btn"
          className="flex items-center gap-2 px-3 py-2 btn-glass rounded-xl text-sm"
          title="Open interactive HTML report in a new tab"
        >
          <ExternalLink size={16} />
          <span className="hidden sm:inline">View HTML</span>
        </button>
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
};

export default ReportHeader;
