import { Link } from "react-router-dom";
import { ArrowLeft, MessageSquare, Download, Building2, User, Calendar } from "lucide-react";

export const ReportHeader = ({ assessmentId, assessment, onDownload, downloading }) => (
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
        <Link to={`/assessments/${assessmentId}`} className="flex items-center gap-2 px-3 py-2 btn-glass rounded-xl text-sm">
          <MessageSquare size={16} /><span className="hidden sm:inline">View Chat</span>
        </Link>
        <button onClick={onDownload} disabled={downloading} className="flex items-center gap-2 px-4 py-2 btn-liquid rounded-xl text-sm disabled:opacity-50">
          <Download size={16} />{downloading ? "..." : "Export PDF"}
        </button>
      </div>
    </div>

    <div className="p-3 sm:p-4 glass-surface-highlight rounded-xl flex flex-col sm:flex-row sm:flex-wrap gap-3 sm:gap-6 text-sm">
      <div className="flex items-center gap-2"><Building2 size={16} className="text-[#C9A84C]" /><span className="text-white/50">Company:</span><span className="text-white font-medium">{assessment.company_name}</span></div>
      <div className="flex items-center gap-2"><User size={16} className="text-[#C9A84C]" /><span className="text-white/50">Respondent:</span><span className="text-white">{assessment.respondent_name}</span></div>
      <div className="flex items-center gap-2"><Calendar size={16} className="text-[#C9A84C]" /><span className="text-white/50">Date:</span><span className="text-white">{new Date(assessment.completed_at || assessment.created_at).toLocaleDateString()}</span></div>
    </div>
  </>
);

export default ReportHeader;
