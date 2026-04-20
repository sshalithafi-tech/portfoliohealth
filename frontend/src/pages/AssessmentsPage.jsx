import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import Layout from "../components/Layout";
import { useAssessments } from "../hooks/useData";
import { getScoreColorClass, getScoreColor, getLevelName } from "../utils/scoring";
import { LoadingSpinner, StatusBadge, EmptyState } from "../components/ScoreComponents";
import {
  Plus,
  ClipboardCheck,
  ChevronRight,
  Search,
  Building2,
  Filter,
  Download,
  Calendar,
  UserRound,
  FileText,
} from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ScoreRing = ({ score }) => {
  const pct = score ? Math.max(0, Math.min(100, (score / 5) * 100)) : 0;
  const color = score ? getScoreColor(score) : "#ffffff20";
  const circumference = 2 * Math.PI * 22;
  const offset = circumference - (pct / 100) * circumference;
  return (
    <div className="relative w-14 h-14 shrink-0">
      <svg viewBox="0 0 50 50" className="w-full h-full -rotate-90">
        <circle cx="25" cy="25" r="22" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="3" />
        {score ? (
          <circle
            cx="25"
            cy="25"
            r="22"
            fill="none"
            stroke={color}
            strokeWidth="3"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 700ms ease" }}
          />
        ) : null}
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        {score ? (
          <span className={`text-base font-bold font-['JetBrains_Mono'] ${getScoreColorClass(score)}`}>
            {score.toFixed(1)}
          </span>
        ) : (
          <span className="text-white/25 text-sm font-['JetBrains_Mono']">–</span>
        )}
      </div>
    </div>
  );
};

const AssessmentCard = ({ assessment, onClick }) => {
  const downloadPDF = async (e) => {
    e.stopPropagation();
    try {
      const response = await axios.get(`${BACKEND_URL}/api/assessments/${assessment.id}/pdf`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${assessment.company_name?.replace(/\s+/g, "_")}_Report.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch {
      toast.error("Unable to download report");
    }
  };

  const overall = assessment.scores?.overall;
  const isComplete = assessment.status === "completed";
  const levelName = overall ? getLevelName(overall) : null;

  return (
    <div
      data-testid={`assessment-card-${assessment.id}`}
      onClick={onClick}
      className="group relative flex flex-col glass-surface-highlight rounded-2xl p-5 cursor-pointer transition-all duration-300 hover:border-[#C9A84C]/30 hover:-translate-y-0.5 hover:shadow-[0_8px_32px_-8px_rgba(201,168,76,0.25)]"
    >
      {/* Top: company + status */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex items-start gap-3 min-w-0 flex-1">
          <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-[#60A5FA]/20 to-[#60A5FA]/5 border border-[#60A5FA]/15 flex items-center justify-center shrink-0">
            <Building2 size={18} className="text-[#60A5FA]" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-white font-semibold font-['Outfit'] truncate leading-tight">
              {assessment.company_name}
            </p>
            <p className="text-xs text-white/35 mt-0.5 truncate">
              {assessment.company_industry || "—"}
            </p>
          </div>
        </div>
        <StatusBadge status={assessment.status} />
      </div>

      {/* Middle: score + level */}
      <div className="flex items-center gap-4 py-4 px-4 rounded-xl bg-white/[0.02] border border-white/[0.04] mb-4">
        <ScoreRing score={overall} />
        <div className="min-w-0 flex-1">
          <p className="text-[10px] uppercase tracking-wider text-white/30 font-semibold">
            Overall Maturity
          </p>
          <p className={`text-base font-semibold font-['Outfit'] truncate ${overall ? "text-white" : "text-white/40"}`}>
            {levelName || "Not yet scored"}
          </p>
        </div>
      </div>

      {/* Meta rows */}
      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2.5 text-white/55">
          <UserRound size={13} className="text-white/30 shrink-0" />
          <span className="truncate">
            {assessment.respondent_name}
            {assessment.respondent_role && (
              <span className="text-white/30"> · {assessment.respondent_role}</span>
            )}
          </span>
        </div>
        <div className="flex items-center gap-2.5 text-white/55">
          <Calendar size={13} className="text-white/30 shrink-0" />
          <span>{new Date(assessment.created_at).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })}</span>
        </div>
      </div>

      {/* Footer action */}
      <div className="mt-5 pt-4 border-t border-white/[0.05] flex items-center justify-between">
        {isComplete ? (
          <button
            onClick={downloadPDF}
            data-testid={`download-report-${assessment.id}`}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-[#C9A84C] bg-[#C9A84C]/10 hover:bg-[#C9A84C]/20 rounded-lg border border-[#C9A84C]/20 transition-colors"
          >
            <Download size={12} /> Download PDF
          </button>
        ) : (
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white/50 bg-white/[0.03] rounded-lg border border-white/[0.06]">
            <FileText size={12} /> Continue
          </span>
        )}
        <span className="inline-flex items-center gap-1 text-xs text-white/35 group-hover:text-[#C9A84C] transition-colors">
          {isComplete ? "View report" : "Resume"}
          <ChevronRight size={14} className="transition-transform group-hover:translate-x-0.5" />
        </span>
      </div>
    </div>
  );
};

const AssessmentsPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const companyFilter = searchParams.get("company");

  const { assessments, companies, loading } = useAssessments();
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [showNewDialog, setShowNewDialog] = useState(false);
  const [formData, setFormData] = useState({
    company_id: companyFilter || "",
    respondent_name: "",
    respondent_role: "",
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (companyFilter) {
      setFormData((prev) => ({ ...prev, company_id: companyFilter }));
    }
  }, [companyFilter]);

  const handleFormChange = useCallback((field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  }, []);

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      if (!formData.company_id) {
        toast.error("Please select a company");
        return;
      }
      setSubmitting(true);
      try {
        const response = await axios.post(`${BACKEND_URL}/api/assessments`, formData);
        setShowNewDialog(false);
        navigate(`/assessments/${response.data.id}`);
      } catch (err) {
        toast.error("Failed to create assessment");
      } finally {
        setSubmitting(false);
      }
    },
    [formData, navigate]
  );

  const handleRowClick = useCallback(
    (assessment) => {
      const path =
        assessment.status === "completed"
          ? `/assessments/${assessment.id}/report`
          : `/assessments/${assessment.id}`;
      navigate(path);
    },
    [navigate]
  );

  const filteredAssessments = assessments.filter((a) => {
    const matchesSearch =
      a.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.respondent_name?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || a.status === statusFilter;
    const matchesCompany = !companyFilter || a.company_id === companyFilter;
    return matchesSearch && matchesStatus && matchesCompany;
  });

  const selectedCompany = companies.find((c) => c.id === companyFilter);

  const completedCount = filteredAssessments.filter((a) => a.status === "completed").length;
  const inProgressCount = filteredAssessments.length - completedCount;

  if (loading) {
    return (
      <Layout>
        <LoadingSpinner className="h-64" />
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-semibold text-white font-['Outfit'] tracking-tight">
              Assessments
              {selectedCompany && (
                <span className="text-[#C9A84C]"> · {selectedCompany.name}</span>
              )}
            </h1>
            <p className="text-white/50 mt-1 text-sm sm:text-base">
              {selectedCompany
                ? `Viewing assessments for ${selectedCompany.name}`
                : "Manage and review PPDT capability assessments"}
            </p>
            {filteredAssessments.length > 0 && (
              <div className="flex items-center gap-4 mt-3 text-xs text-white/45">
                <span className="inline-flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#34D399]" /> {completedCount} completed
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#C9A84C]" /> {inProgressCount} in progress
                </span>
              </div>
            )}
          </div>
          <Dialog open={showNewDialog} onOpenChange={setShowNewDialog}>
            <DialogTrigger asChild>
              <button
                data-testid="new-assessment-btn"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 btn-liquid rounded-xl w-full sm:w-auto"
              >
                <Plus size={18} />
                New Assessment
              </button>
            </DialogTrigger>
            <DialogContent className="glass-heavy border-white/10 text-white max-w-md rounded-2xl">
              <DialogHeader>
                <DialogTitle className="text-xl font-semibold font-['Outfit']">
                  Start New Assessment
                </DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <label className="text-sm text-white/50">Company *</label>
                  <select
                    data-testid="assessment-company-select"
                    value={formData.company_id}
                    onChange={(e) => handleFormChange("company_id", e.target.value)}
                    className="w-full px-4 py-3 glass-input rounded-xl outline-none"
                    required
                  >
                    <option value="">Select company</option>
                    {companies.map((company) => (
                      <option key={company.id} value={company.id}>
                        {company.name}
                      </option>
                    ))}
                  </select>
                  {companies.length === 0 && (
                    <Link to="/companies" className="text-sm text-[#C9A84C] hover:text-[#C9A84C]/80">
                      + Add a company first
                    </Link>
                  )}
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-white/50">Respondent Name *</label>
                  <input
                    type="text"
                    data-testid="respondent-name-input"
                    value={formData.respondent_name}
                    onChange={(e) => handleFormChange("respondent_name", e.target.value)}
                    className="w-full px-4 py-3 glass-input rounded-xl outline-none"
                    placeholder="John Smith"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-white/50">Respondent Role *</label>
                  <input
                    type="text"
                    data-testid="respondent-role-input"
                    value={formData.respondent_role}
                    onChange={(e) => handleFormChange("respondent_role", e.target.value)}
                    className="w-full px-4 py-3 glass-input rounded-xl outline-none"
                    placeholder="VP of Product Management"
                    required
                  />
                </div>
                <button
                  type="submit"
                  data-testid="start-assessment-submit-btn"
                  disabled={submitting || companies.length === 0}
                  className="w-full py-3 px-6 btn-liquid rounded-xl disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {submitting ? "Creating..." : "Start Assessment"}
                </button>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Filters */}
        <div className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1 max-w-md">
            <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
            <input
              type="text"
              data-testid="assessment-search-input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-11 pr-4 py-2.5 glass-input rounded-xl outline-none text-sm"
              placeholder="Search by company or respondent..."
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter size={16} className="text-white/40" />
            <select
              data-testid="status-filter-select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2.5 glass-input rounded-xl outline-none text-sm"
            >
              <option value="all">All Status</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
            </select>
          </div>
          {companyFilter && (
            <Link
              to="/assessments"
              className="px-4 py-2.5 text-[#C9A84C] hover:text-[#C9A84C]/80 transition-colors text-sm"
            >
              Clear company filter
            </Link>
          )}
        </div>

        {/* Card Grid */}
        {filteredAssessments.length > 0 ? (
          <div
            data-testid="assessments-grid"
            className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-5 stagger-children"
          >
            {filteredAssessments.map((assessment) => (
              <AssessmentCard
                key={assessment.id}
                assessment={assessment}
                onClick={() => handleRowClick(assessment)}
              />
            ))}
          </div>
        ) : (
          <div className="glass-surface-highlight rounded-2xl">
            <EmptyState
              icon={ClipboardCheck}
              title="No assessments found"
              description="Start your first assessment to evaluate PPM capability"
              action={
                <button
                  onClick={() => setShowNewDialog(true)}
                  className="px-6 py-2 btn-liquid rounded-xl"
                >
                  Create Assessment
                </button>
              }
            />
          </div>
        )}
      </div>
    </Layout>
  );
};

export default AssessmentsPage;
