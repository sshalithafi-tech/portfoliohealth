import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import Layout from "../components/Layout";
import { useAssessments } from "../hooks/useData";
import { getLevelName } from "../utils/scoring";
import { LoadingSpinner, StatusBadge, EmptyState } from "../components/ScoreComponents";
import RingGauge from "../components/ui/RingGauge";
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
  AlertTriangle,
  Users,
  Database,
  Monitor,
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

// ── Bottleneck pill ────────────────────────────────────────────────────────
const PILLAR_ICONS   = { people: Users, process: ClipboardCheck, data: Database, technology: Monitor };
const PILLAR_COLORS  = { people: "#60A5FA", process: "#34D399", data: "#C9A84C", technology: "#A78BFA" };
const PILLAR_LABELS  = { people: "People", process: "Process", data: "Data", technology: "Technology" };

const BottleneckPill = ({ pillar, score }) => {
  if (!pillar) return null;
  const key    = String(pillar).toLowerCase();
  const color  = PILLAR_COLORS[key]  ?? "#EF4444";
  const label  = PILLAR_LABELS[key]  ?? pillar;
  const Icon   = PILLAR_ICONS[key]   ?? AlertTriangle;
  return (
    <div
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border"
      style={{ color, borderColor: `${color}35`, backgroundColor: `${color}12` }}
    >
      <AlertTriangle size={10} style={{ color }} />
      <span>Bottleneck — {label}</span>
      {typeof score === "number" && (
        <span className="font-['JetBrains_Mono'] font-bold">{score.toFixed(1)}</span>
      )}
    </div>
  );
};

// ── Assessment card ──────────────────────────────────────────────────────────
const AssessmentCard = ({ assessment, onClick }) => {
  const downloadPDF = async (e) => {
    e.stopPropagation();
    try {
      const response = await axios.get(
        `${BACKEND_URL}/api/assessments/${assessment.id}/pdf`,
        { responseType: "blob" }
      );
      const url  = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute(
        "download",
        `${assessment.company_name?.replace(/\s+/g, "_")}_Report.pdf`
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch {
      toast.error("Unable to download report");
    }
  };

  const overall    = assessment.scores?.overall;
  const isComplete = assessment.status === "completed";
  const levelLabel = overall ? getLevelName(overall) : null;

  // Bottleneck — try report JSON first, fallback to lowest dimension score
  const report         = assessment.report ?? {};
  const bnPillar       = report.bottleneck_pillar ?? assessment.bottleneck_pillar ?? null;
  const bnScore        = bnPillar
    ? (assessment.scores?.[String(bnPillar).toLowerCase()] ?? null)
    : null;

  // One-liner preview (AI summary or first key finding)
  const oneLiner =
    report.one_liner ??
    report.executive_summary?.[0] ??
    report.key_findings?.[0] ??
    null;

  return (
    <div
      data-testid={`assessment-card-${assessment.id}`}
      onClick={onClick}
      className="group relative flex flex-col glass-surface-highlight rounded-2xl p-5 cursor-pointer transition-all duration-300 hover:border-[#0891B2]/30 hover:-translate-y-0.5 hover:shadow-[0_8px_32px_-8px_rgba(8,145,178,0.25)]"
    >
      {/* ─ Top: company + status ─ */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex items-start gap-3 min-w-0 flex-1">
          <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-[#0891B2]/20 to-[#60A5FA]/05 border border-[#60A5FA]/15 flex items-center justify-center shrink-0">
            <Building2 size={18} className="text-[#60A5FA]" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-[#0C1B2A] font-semibold font-['Outfit'] truncate leading-tight">
              {assessment.company_name}
            </p>
            <p className="text-xs text-[#8896A5] mt-0.5 truncate">
              {assessment.company_industry || "—"}
            </p>
          </div>
        </div>
        <StatusBadge status={assessment.status} />
      </div>

      {/* ─ Score row: RingGauge + level + bottleneck pill ─ */}
      <div className="flex items-center gap-4 py-3 px-4 rounded-xl bg-[#F8F9FA] border border-[#E2E8F0] mb-3">
        <RingGauge
          score={overall ?? 0}
          size={72}
          thickness={7}
          showLevel={false}
          animate={!!overall}
        />
        <div className="min-w-0 flex-1 space-y-1.5">
          <div>
            <p className="text-[10px] uppercase tracking-wider text-[#8896A5] font-semibold leading-none mb-0.5">
              Overall Maturity
            </p>
            <p className={`text-sm font-semibold font-['Outfit'] truncate ${
              overall ? "text-[#0C1B2A]" : "text-[#8896A5]"
            }`}>
              {levelLabel || "Not yet scored"}
            </p>
          </div>
          {bnPillar && (
            <BottleneckPill pillar={bnPillar} score={bnScore} />
          )}
        </div>
      </div>

      {/* ─ One-liner preview ─ */}
      {oneLiner && (
        <p className="text-xs text-[#8896A5] leading-relaxed line-clamp-2 mb-3 px-1">
          {oneLiner}
        </p>
      )}

      {/* ─ Meta rows ─ */}
      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2.5 text-[#4A5568]">
          <UserRound size={13} className="text-[#8896A5] shrink-0" />
          <span className="truncate">
            {assessment.respondent_name}
            {assessment.respondent_role && (
              <span className="text-[#8896A5]"> · {assessment.respondent_role}</span>
            )}
          </span>
        </div>
        <div className="flex items-center gap-2.5 text-[#4A5568]">
          <Calendar size={13} className="text-[#8896A5] shrink-0" />
          <span>
            {new Date(assessment.created_at).toLocaleDateString(undefined, {
              year: "numeric",
              month: "short",
              day: "numeric",
            })}
          </span>
        </div>
      </div>

      {/* ─ Footer ─ */}
      <div className="mt-5 pt-4 border-t border-[#E2E8F0] flex items-center justify-between">
        {isComplete ? (
          <button
            onClick={downloadPDF}
            data-testid={`download-report-${assessment.id}`}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-[#0891B2] bg-[#0891B2]/10 hover:bg-[#0891B2]/20 rounded-lg border border-[#0891B2]/20 transition-colors"
          >
            <Download size={12} /> Download PDF
          </button>
        ) : (
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-[#4A5568] bg-[#F8F9FA] rounded-lg border border-[#E2E8F0]">
            <FileText size={12} /> Continue
          </span>
        )}
        <span className="inline-flex items-center gap-1 text-xs text-[#8896A5] group-hover:text-[#0891B2] transition-colors">
          {isComplete ? "View report" : "Resume"}
          <ChevronRight size={14} className="transition-transform group-hover:translate-x-0.5" />
        </span>
      </div>
    </div>
  );
};

// ── Page ────────────────────────────────────────────────────────────────────
const AssessmentsPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const companyFilter = searchParams.get("company");

  const { assessments, companies, loading } = useAssessments();
  const [searchQuery, setSearchQuery]   = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [showNewDialog, setShowNewDialog] = useState(false);
  const [formData, setFormData] = useState({
    company_id: companyFilter || "",
    respondent_name: "",
    respondent_role: "",
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (companyFilter) setFormData((prev) => ({ ...prev, company_id: companyFilter }));
  }, [companyFilter]);

  const handleFormChange = useCallback((field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  }, []);

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      if (!formData.company_id) { toast.error("Please select a company"); return; }
      setSubmitting(true);
      try {
        const response = await axios.post(`${BACKEND_URL}/api/assessments`, formData);
        setShowNewDialog(false);
        navigate(`/assessments/${response.data.id}`);
      } catch {
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
    const matchesStatus  = statusFilter === "all" || a.status === statusFilter;
    const matchesCompany = !companyFilter || a.company_id === companyFilter;
    return matchesSearch && matchesStatus && matchesCompany;
  });

  const selectedCompany  = companies.find((c) => c.id === companyFilter);
  const completedCount   = filteredAssessments.filter((a) => a.status === "completed").length;
  const inProgressCount  = filteredAssessments.length - completedCount;

  if (loading) return <Layout><LoadingSpinner className="h-64" /></Layout>;

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-semibold text-[#0C1B2A] font-['Outfit'] tracking-tight">
              Assessments
              {selectedCompany && <span className="text-[#0891B2]"> · {selectedCompany.name}</span>}
            </h1>
            <p className="text-[#4A5568] mt-1 text-sm sm:text-base">
              {selectedCompany
                ? `Viewing assessments for ${selectedCompany.name}`
                : "Manage and review PPDT capability assessments"}
            </p>
            {filteredAssessments.length > 0 && (
              <div className="flex items-center gap-4 mt-3 text-xs text-[#8896A5]">
                <span className="inline-flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#34D399]" /> {completedCount} completed
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#0891B2]" /> {inProgressCount} in progress
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
                <Plus size={18} /> New Assessment
              </button>
            </DialogTrigger>
            <DialogContent className="glass-heavy border-[#E2E8F0] text-[#0C1B2A] max-w-md rounded-2xl">
              <DialogHeader>
                <DialogTitle className="text-xl font-semibold font-['Outfit']">Start New Assessment</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <label className="text-sm text-[#4A5568]">Company *</label>
                  <select
                    data-testid="assessment-company-select"
                    value={formData.company_id}
                    onChange={(e) => handleFormChange("company_id", e.target.value)}
                    className="w-full px-4 py-3 glass-input rounded-xl outline-none"
                    required
                  >
                    <option value="">Select company</option>
                    {companies.map((company) => (
                      <option key={company.id} value={company.id}>{company.name}</option>
                    ))}
                  </select>
                  {companies.length === 0 && (
                    <Link to="/companies" className="text-sm text-[#0891B2] hover:text-[#0891B2]/80">
                      + Add a company first
                    </Link>
                  )}
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-[#4A5568]">Respondent Name *</label>
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
                  <label className="text-sm text-[#4A5568]">Respondent Role *</label>
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
            <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-[#8896A5]" />
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
            <Filter size={16} className="text-[#8896A5]" />
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
            <Link to="/assessments" className="px-4 py-2.5 text-[#0891B2] hover:text-[#0891B2]/80 transition-colors text-sm">
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
                <button onClick={() => setShowNewDialog(true)} className="px-6 py-2 btn-liquid rounded-xl">
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
