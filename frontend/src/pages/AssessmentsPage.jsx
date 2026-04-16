import { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import Layout from "../components/Layout";
import { 
  Plus, 
  ClipboardCheck,
  Calendar,
  ChevronRight,
  Search,
  Building2,
  User,
  Filter
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

const AssessmentsPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const companyFilter = searchParams.get("company");
  
  const [assessments, setAssessments] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [showNewDialog, setShowNewDialog] = useState(false);
  const [formData, setFormData] = useState({
    company_id: companyFilter || "",
    respondent_name: "",
    respondent_role: ""
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    try {
      const [assessmentsRes, companiesRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/assessments`),
        axios.get(`${BACKEND_URL}/api/companies`)
      ]);
      setAssessments(assessmentsRes.data);
      setCompanies(companiesRes.data);
    } catch (err) {
      console.error("Failed to fetch data:", err);
      toast.error("Failed to load assessments");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (companyFilter) {
      setFormData(prev => ({ ...prev, company_id: companyFilter }));
    }
  }, [companyFilter]);

  const handleSubmit = async (e) => {
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
  };

  const filteredAssessments = assessments.filter(a => {
    const matchesSearch = 
      a.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.respondent_name?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || a.status === statusFilter;
    const matchesCompany = !companyFilter || a.company_id === companyFilter;
    return matchesSearch && matchesStatus && matchesCompany;
  });

  const getScoreColor = (score) => {
    if (score >= 4) return "text-[#2f81f7]";
    if (score >= 3) return "text-[#238636]";
    if (score >= 2) return "text-[#D29922]";
    return "text-[#F85149]";
  };

  const getStatusBadge = (status) => {
    if (status === "completed") {
      return <span className="px-3 py-1 text-xs rounded-full bg-[#238636]/20 text-[#238636] border border-[#238636]/30">Completed</span>;
    }
    return <span className="px-3 py-1 text-xs rounded-full bg-[#D29922]/20 text-[#D29922] border border-[#D29922]/30">In Progress</span>;
  };

  const selectedCompany = companies.find(c => c.id === companyFilter);

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold text-white font-['Outfit'] tracking-tight">
              Assessments
              {selectedCompany && (
                <span className="text-[#2f81f7]"> · {selectedCompany.name}</span>
              )}
            </h1>
            <p className="text-gray-400 mt-1">
              {selectedCompany 
                ? `Viewing assessments for ${selectedCompany.name}` 
                : "Manage and review PPDT capability assessments"}
            </p>
          </div>
          <Dialog open={showNewDialog} onOpenChange={setShowNewDialog}>
            <DialogTrigger asChild>
              <button
                data-testid="new-assessment-btn"
                className="inline-flex items-center gap-2 px-6 py-3 bg-[#2f81f7] text-white font-medium rounded-lg hover:bg-[#58a6ff] transition-all btn-premium"
              >
                <Plus size={18} />
                New Assessment
              </button>
            </DialogTrigger>
            <DialogContent className="bg-[#111827] border-[#374151] text-white max-w-md">
              <DialogHeader>
                <DialogTitle className="text-xl font-semibold font-['Outfit']">
                  Start New Assessment
                </DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <label className="text-sm text-gray-400">Company *</label>
                  <select
                    data-testid="assessment-company-select"
                    value={formData.company_id}
                    onChange={(e) => setFormData({ ...formData, company_id: e.target.value })}
                    className="w-full px-4 py-3 bg-[#0B1120] border border-[#374151] rounded-lg text-white focus:ring-2 focus:ring-[#2f81f7] focus:border-transparent transition-all outline-none"
                    required
                  >
                    <option value="">Select company</option>
                    {companies.map(company => (
                      <option key={company.id} value={company.id}>{company.name}</option>
                    ))}
                  </select>
                  {companies.length === 0 && (
                    <Link to="/companies" className="text-sm text-[#2f81f7] hover:text-[#58a6ff]">
                      + Add a company first
                    </Link>
                  )}
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-gray-400">Respondent Name *</label>
                  <input
                    type="text"
                    data-testid="respondent-name-input"
                    value={formData.respondent_name}
                    onChange={(e) => setFormData({ ...formData, respondent_name: e.target.value })}
                    className="w-full px-4 py-3 bg-[#0B1120] border border-[#374151] rounded-lg text-white focus:ring-2 focus:ring-[#2f81f7] focus:border-transparent transition-all outline-none"
                    placeholder="John Smith"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-gray-400">Respondent Role *</label>
                  <input
                    type="text"
                    data-testid="respondent-role-input"
                    value={formData.respondent_role}
                    onChange={(e) => setFormData({ ...formData, respondent_role: e.target.value })}
                    className="w-full px-4 py-3 bg-[#0B1120] border border-[#374151] rounded-lg text-white focus:ring-2 focus:ring-[#2f81f7] focus:border-transparent transition-all outline-none"
                    placeholder="VP of Product Management"
                    required
                  />
                </div>
                <button
                  type="submit"
                  data-testid="start-assessment-submit-btn"
                  disabled={submitting || companies.length === 0}
                  className="w-full py-3 px-6 bg-[#2f81f7] text-white font-medium rounded-lg hover:bg-[#58a6ff] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
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
            <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              data-testid="assessment-search-input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-[#111827] border border-[#374151] rounded-lg text-white focus:ring-2 focus:ring-[#2f81f7] focus:border-transparent transition-all outline-none"
              placeholder="Search by company or respondent..."
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter size={18} className="text-gray-400" />
            <select
              data-testid="status-filter-select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-3 bg-[#111827] border border-[#374151] rounded-lg text-white focus:ring-2 focus:ring-[#2f81f7] focus:border-transparent transition-all outline-none"
            >
              <option value="all">All Status</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
            </select>
          </div>
          {companyFilter && (
            <Link
              to="/assessments"
              className="px-4 py-3 text-[#2f81f7] hover:text-[#58a6ff] transition-colors"
            >
              Clear company filter
            </Link>
          )}
        </div>

        {/* Assessments List */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-pulse-glow w-12 h-12 rounded-full bg-[#2f81f7]/20 flex items-center justify-center">
              <div className="w-6 h-6 rounded-full bg-[#2f81f7]" />
            </div>
          </div>
        ) : filteredAssessments.length > 0 ? (
          <div className="bg-[#111827] border border-[#374151] rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wider text-gray-400 border-b border-[#374151] bg-[#0B1120]">
                    <th className="px-6 py-4">Company</th>
                    <th className="px-6 py-4">Respondent</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4">Score</th>
                    <th className="px-6 py-4">Date</th>
                    <th className="px-6 py-4"></th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAssessments.map((assessment, idx) => (
                    <tr 
                      key={assessment.id}
                      data-testid={`assessment-row-${assessment.id}`}
                      className={`border-b border-[#374151]/50 hover:bg-[#1F2937] cursor-pointer transition-colors ${idx % 2 === 0 ? 'bg-[#111827]' : 'bg-[#0B1120]/50'}`}
                      onClick={() => navigate(assessment.status === "completed" ? `/assessments/${assessment.id}/report` : `/assessments/${assessment.id}`)}
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-lg bg-[#2f81f7]/20 flex items-center justify-center">
                            <Building2 size={18} className="text-[#2f81f7]" />
                          </div>
                          <div>
                            <p className="text-white font-medium">{assessment.company_name}</p>
                            <p className="text-xs text-gray-500">{assessment.company_industry}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <User size={14} className="text-gray-400" />
                          <div>
                            <p className="text-gray-300">{assessment.respondent_name}</p>
                            <p className="text-xs text-gray-500">{assessment.respondent_role}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {getStatusBadge(assessment.status)}
                      </td>
                      <td className="px-6 py-4">
                        {assessment.scores?.overall ? (
                          <span className={`text-2xl font-bold font-['JetBrains_Mono'] ${getScoreColor(assessment.scores.overall)}`}>
                            {assessment.scores.overall.toFixed(1)}
                          </span>
                        ) : (
                          <span className="text-gray-500">–</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2 text-gray-400">
                          <Calendar size={14} />
                          <span className="text-sm">
                            {new Date(assessment.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <ChevronRight size={18} className="text-gray-400" />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-16 text-gray-500 bg-[#111827] border border-[#374151] rounded-xl">
            <ClipboardCheck size={64} className="mb-4 opacity-50" />
            <p className="text-lg">No assessments found</p>
            <p className="text-sm mt-2">Start your first assessment to evaluate PPM capability</p>
            <button
              onClick={() => setShowNewDialog(true)}
              className="mt-6 px-6 py-2 bg-[#2f81f7] text-white rounded-lg hover:bg-[#58a6ff] transition-colors"
            >
              Create Assessment
            </button>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default AssessmentsPage;
