import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import Layout from "../components/Layout";
import { useAssessments } from "../hooks/useData";
import { getScoreColorClass } from "../utils/scoring";
import { LoadingSpinner, StatusBadge, EmptyState } from "../components/ScoreComponents";
import { 
  Plus, 
  ClipboardCheck,
  Calendar,
  ChevronRight,
  Search,
  Building2,
  User,
  Filter,
  Download
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

const AssessmentRow = ({ assessment, onClick }) => {
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
      // silently fail
    }
  };

  return (
    <tr 
      data-testid={`assessment-row-${assessment.id}`}
      className="border-b border-white/[0.04] hover:bg-white/[0.02] cursor-pointer transition-colors"
      onClick={onClick}
    >
      <td className="px-4 sm:px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-[#2f81f7]/15 flex items-center justify-center shrink-0">
            <Building2 size={18} className="text-[#2f81f7]" />
          </div>
          <div className="min-w-0">
            <p className="text-white font-medium truncate">{assessment.company_name}</p>
            <p className="text-xs text-white/30">{assessment.company_industry}</p>
          </div>
        </div>
      </td>
      <td className="px-4 sm:px-6 py-4">
        <p className="text-white/60 text-sm truncate">{assessment.respondent_name}</p>
      </td>
      <td className="px-4 sm:px-6 py-4">
        <StatusBadge status={assessment.status} />
      </td>
      <td className="px-4 sm:px-6 py-4">
        {assessment.scores?.overall ? (
          <span className={`text-lg font-bold font-['JetBrains_Mono'] ${getScoreColorClass(assessment.scores.overall)}`}>
            {assessment.scores.overall.toFixed(1)}
          </span>
        ) : (
          <span className="text-white/30">–</span>
        )}
      </td>
      <td className="px-4 sm:px-6 py-4">
        <span className="text-sm text-white/40 whitespace-nowrap">
          {new Date(assessment.created_at).toLocaleDateString()}
        </span>
      </td>
      <td className="px-4 sm:px-6 py-4">
        {assessment.status === "completed" ? (
          <button
            onClick={downloadPDF}
            data-testid={`download-report-${assessment.id}`}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-[#00E5FF] bg-[#00E5FF]/10 hover:bg-[#00E5FF]/20 rounded-lg border border-[#00E5FF]/20 transition-colors whitespace-nowrap"
          >
            <Download size={12} /> PDF
          </button>
        ) : (
          <ChevronRight size={16} className="text-white/20" />
        )}
      </td>
    </tr>
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
    respondent_role: ""
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (companyFilter) {
      setFormData(prev => ({ ...prev, company_id: companyFilter }));
    }
  }, [companyFilter]);

  const handleFormChange = useCallback((field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  const handleSubmit = useCallback(async (e) => {
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
  }, [formData, navigate]);

  const handleRowClick = useCallback((assessment) => {
    const path = assessment.status === "completed" 
      ? `/assessments/${assessment.id}/report` 
      : `/assessments/${assessment.id}`;
    navigate(path);
  }, [navigate]);

  const filteredAssessments = assessments.filter(a => {
    const matchesSearch = 
      a.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.respondent_name?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || a.status === statusFilter;
    const matchesCompany = !companyFilter || a.company_id === companyFilter;
    return matchesSearch && matchesStatus && matchesCompany;
  });

  const selectedCompany = companies.find(c => c.id === companyFilter);

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
        <div className="flex flex-col gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-semibold text-white font-['Outfit'] tracking-tight">
              Assessments
              {selectedCompany && (
                <span className="text-[#00E5FF]"> · {selectedCompany.name}</span>
              )}
            </h1>
            <p className="text-white/50 mt-1 text-sm sm:text-base">
              {selectedCompany 
                ? `Viewing assessments for ${selectedCompany.name}` 
                : "Manage and review PPDT capability assessments"}
            </p>
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
                    {companies.map(company => (
                      <option key={company.id} value={company.id}>{company.name}</option>
                    ))}
                  </select>
                  {companies.length === 0 && (
                    <Link to="/companies" className="text-sm text-[#00E5FF] hover:text-[#00E5FF]/80">
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
        <div className="flex flex-col md:flex-row gap-4">
          <div className="relative flex-1 max-w-md">
            <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
            <input
              type="text"
              data-testid="assessment-search-input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 glass-input rounded-xl outline-none"
              placeholder="Search by company or respondent..."
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter size={18} className="text-white/40" />
            <select
              data-testid="status-filter-select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-3 glass-input rounded-xl outline-none"
            >
              <option value="all">All Status</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
            </select>
          </div>
          {companyFilter && (
            <Link
              to="/assessments"
              className="px-4 py-3 text-[#00E5FF] hover:text-[#00E5FF]/80 transition-colors"
            >
              Clear company filter
            </Link>
          )}
        </div>

        {/* Assessments List */}
        {filteredAssessments.length > 0 ? (
          <div className="glass-surface-highlight rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wider text-white/40 border-b border-white/[0.08]">
                    <th className="px-4 sm:px-6 py-4">Company</th>
                    <th className="px-4 sm:px-6 py-4">Respondent</th>
                    <th className="px-4 sm:px-6 py-4">Status</th>
                    <th className="px-4 sm:px-6 py-4">Score</th>
                    <th className="px-4 sm:px-6 py-4">Date</th>
                    <th className="px-4 sm:px-6 py-4">Report</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAssessments.map((assessment) => (
                    <AssessmentRow
                      key={assessment.id}
                      assessment={assessment}
                      onClick={() => handleRowClick(assessment)}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="glass-surface-highlight rounded-xl">
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
