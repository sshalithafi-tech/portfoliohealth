import { useState, useEffect } from "react";
import axios from "axios";
import Layout from "../components/Layout";
import { getScoreColorClass } from "../utils/scoring";
import { LoadingSpinner, StatusBadge, EmptyState } from "../components/ScoreComponents";
import { 
  Shield,
  Download,
  ClipboardCheck,
  Zap,
  Building2,
  Users,
  TrendingUp,
  Search,
  Filter
} from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AdminStatCard = ({ icon: Icon, label, value, color = "#C9A84C" }) => (
  <div className="p-4 sm:p-5 glass-card rounded-xl">
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0" style={{ backgroundColor: `${color}15` }}>
        <Icon size={20} style={{ color }} />
      </div>
      <div>
        <p className="text-white/50 text-xs">{label}</p>
        <p className="text-xl font-semibold text-white font-['JetBrains_Mono']">{value}</p>
      </div>
    </div>
  </div>
);

const AdminPage = () => {
  const [stats, setStats] = useState(null);
  const [assessments, setAssessments] = useState([]);
  const [quickAssessments, setQuickAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("full");
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, assessRes, quickRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/admin/stats`),
        axios.get(`${BACKEND_URL}/api/admin/assessments`),
        axios.get(`${BACKEND_URL}/api/admin/quick-assessments`),
      ]);
      setStats(statsRes.data);
      setAssessments(assessRes.data);
      setQuickAssessments(quickRes.data);
    } catch (err) {
      if (err.response?.status === 403) {
        toast.error("Admin access required");
      } else {
        toast.error("Failed to load admin data");
      }
    } finally {
      setLoading(false);
    }
  };

  const exportCSV = async (type) => {
    setDownloading(true);
    try {
      const endpoint = type === "full" ? "/api/admin/export/assessments" : "/api/admin/export/quick-assessments";
      const response = await axios.get(`${BACKEND_URL}${endpoint}`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", type === "full" ? "assessments_export.csv" : "quick_assessments_export.csv");
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success("CSV exported successfully");
    } catch (err) {
      toast.error("Failed to export CSV");
    } finally {
      setDownloading(false);
    }
  };

  const filteredAssessments = assessments.filter(a => {
    const matchesSearch = 
      a.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.respondent_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.consultant_name?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || a.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const filteredQuick = quickAssessments.filter(q =>
    q.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    q.respondent_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    q.respondent_email?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <Layout>
        <LoadingSpinner className="h-64" />
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6 sm:space-y-8">
        {/* Header */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#C9A84C]/15 flex items-center justify-center">
              <Shield size={22} className="text-[#C9A84C]" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-semibold text-white font-['Outfit'] tracking-tight">
                Admin Panel
              </h1>
              <p className="text-white/50 text-sm">All assessment data across all users</p>
            </div>
          </div>
        </div>

        {/* Global Stats */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4 stagger-children">
            <AdminStatCard icon={ClipboardCheck} label="Full Assessments" value={stats.total_assessments} color="#60A5FA" />
            <AdminStatCard icon={TrendingUp} label="Completed" value={stats.completed_assessments} color="#34D399" />
            <AdminStatCard icon={Zap} label="Quick Assessments" value={stats.total_quick_assessments} color="#C9A84C" />
            <AdminStatCard icon={Building2} label="Companies" value={stats.total_companies} color="#A78BFA" />
            <AdminStatCard icon={Users} label="Users" value={stats.total_users} color="#C9A84C" />
            <AdminStatCard icon={ClipboardCheck} label="In Progress" value={stats.in_progress_assessments} color="#EF4444" />
          </div>
        )}

        {/* Tabs */}
        <div className="flex items-center gap-2 border-b border-white/[0.06] pb-0">
          <button
            data-testid="tab-full-assessments"
            onClick={() => { setActiveTab("full"); setSearchQuery(""); }}
            className={`px-4 py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === "full"
                ? "border-[#C9A84C] text-[#C9A84C]"
                : "border-transparent text-white/50 hover:text-white"
            }`}
          >
            Full Assessments ({assessments.length})
          </button>
          <button
            data-testid="tab-quick-assessments"
            onClick={() => { setActiveTab("quick"); setSearchQuery(""); }}
            className={`px-4 py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === "quick"
                ? "border-[#C9A84C] text-[#C9A84C]"
                : "border-transparent text-white/50 hover:text-white"
            }`}
          >
            Quick Assessments ({quickAssessments.length})
          </button>
        </div>

        {/* Filters + Export */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1 max-w-md">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" />
            <input
              type="text"
              data-testid="admin-search-input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 glass-input rounded-xl outline-none text-sm"
              placeholder={activeTab === "full" ? "Search company, respondent, consultant..." : "Search company, respondent, email..."}
            />
          </div>
          {activeTab === "full" && (
            <div className="flex items-center gap-2">
              <Filter size={16} className="text-white/40" />
              <select
                data-testid="admin-status-filter"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2.5 glass-input rounded-xl outline-none text-sm"
              >
                <option value="all">All Status</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
              </select>
            </div>
          )}
          <button
            data-testid="export-csv-btn"
            onClick={() => exportCSV(activeTab)}
            disabled={downloading}
            className="flex items-center justify-center gap-2 px-4 py-2.5 btn-glass rounded-xl text-sm disabled:opacity-50 shrink-0"
          >
            <Download size={16} />
            {downloading ? "Exporting..." : "Export CSV"}
          </button>
        </div>

        {/* Full Assessments Table */}
        {activeTab === "full" && (
          filteredAssessments.length > 0 ? (
            <div className="glass-surface-highlight rounded-xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-wider text-white/40 border-b border-white/[0.08]">
                      <th className="px-4 sm:px-6 py-3">Company</th>
                      <th className="px-4 sm:px-6 py-3">Respondent</th>
                      <th className="px-4 sm:px-6 py-3">Consultant</th>
                      <th className="px-4 sm:px-6 py-3">Status</th>
                      <th className="px-4 sm:px-6 py-3">P</th>
                      <th className="px-4 sm:px-6 py-3">Pr</th>
                      <th className="px-4 sm:px-6 py-3">D</th>
                      <th className="px-4 sm:px-6 py-3">T</th>
                      <th className="px-4 sm:px-6 py-3">Overall</th>
                      <th className="px-4 sm:px-6 py-3">Date</th>
                      <th className="px-4 sm:px-6 py-3">Report</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm">
                    {filteredAssessments.map((a) => (
                      <tr key={a.id} className="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors" data-testid={`admin-assessment-row-${a.id}`}>
                        <td className="px-4 sm:px-6 py-3">
                          <p className="text-white font-medium">{a.company_name}</p>
                          <p className="text-xs text-white/30">{a.company_industry}</p>
                        </td>
                        <td className="px-4 sm:px-6 py-3">
                          <p className="text-white/60">{a.respondent_name}</p>
                          <p className="text-xs text-white/30">{a.respondent_role}</p>
                        </td>
                        <td className="px-4 sm:px-6 py-3">
                          <p className="text-white/60">{a.consultant_name}</p>
                          <p className="text-xs text-white/30">{a.consultant_email}</p>
                        </td>
                        <td className="px-4 sm:px-6 py-3"><StatusBadge status={a.status} /></td>
                        <td className="px-4 sm:px-6 py-3">
                          <span className={`font-['JetBrains_Mono'] font-semibold text-xs ${getScoreColorClass(a.scores?.people)}`}>
                            {a.scores?.people?.toFixed(1) || "–"}
                          </span>
                        </td>
                        <td className="px-4 sm:px-6 py-3">
                          <span className={`font-['JetBrains_Mono'] font-semibold text-xs ${getScoreColorClass(a.scores?.process)}`}>
                            {a.scores?.process?.toFixed(1) || "–"}
                          </span>
                        </td>
                        <td className="px-4 sm:px-6 py-3">
                          <span className={`font-['JetBrains_Mono'] font-semibold text-xs ${getScoreColorClass(a.scores?.data)}`}>
                            {a.scores?.data?.toFixed(1) || "–"}
                          </span>
                        </td>
                        <td className="px-4 sm:px-6 py-3">
                          <span className={`font-['JetBrains_Mono'] font-semibold text-xs ${getScoreColorClass(a.scores?.technology)}`}>
                            {a.scores?.technology?.toFixed(1) || "–"}
                          </span>
                        </td>
                        <td className="px-4 sm:px-6 py-3">
                          {a.scores?.overall ? (
                            <span className={`font-['JetBrains_Mono'] font-bold ${getScoreColorClass(a.scores.overall)}`}>
                              {a.scores.overall.toFixed(1)}
                            </span>
                          ) : <span className="text-white/30">–</span>}
                        </td>
                        <td className="px-4 sm:px-6 py-3 text-white/40 text-xs whitespace-nowrap">
                          {new Date(a.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-4 sm:px-6 py-3">
                          {a.status === "completed" ? (
                            <button
                              onClick={async () => {
                                try {
                                  const res = await axios.get(`${BACKEND_URL}/api/assessments/${a.id}/pdf`, { responseType: "blob" });
                                  const url = window.URL.createObjectURL(new Blob([res.data]));
                                  const link = document.createElement("a");
                                  link.href = url;
                                  link.setAttribute("download", `${a.company_name?.replace(/\s+/g, "_")}_Report.pdf`);
                                  document.body.appendChild(link);
                                  link.click();
                                  link.remove();
                                } catch { /* */ }
                              }}
                              data-testid={`admin-download-${a.id}`}
                              className="flex items-center gap-1 px-2.5 py-1 text-[10px] font-medium text-[#C9A84C] bg-[#C9A84C]/10 hover:bg-[#C9A84C]/20 rounded-md border border-[#C9A84C]/20 transition-colors whitespace-nowrap"
                            >
                              <Download size={10} /> PDF
                            </button>
                          ) : <span className="text-white/20 text-xs">–</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="glass-surface-highlight rounded-xl">
              <EmptyState icon={ClipboardCheck} title="No assessments found" />
            </div>
          )
        )}

        {/* Quick Assessments Table */}
        {activeTab === "quick" && (
          filteredQuick.length > 0 ? (
            <div className="glass-surface-highlight rounded-xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-wider text-white/40 border-b border-white/[0.08]">
                      <th className="px-4 sm:px-6 py-3">Company</th>
                      <th className="px-4 sm:px-6 py-3">Industry</th>
                      <th className="px-4 sm:px-6 py-3">Respondent</th>
                      <th className="px-4 sm:px-6 py-3">P</th>
                      <th className="px-4 sm:px-6 py-3">Pr</th>
                      <th className="px-4 sm:px-6 py-3">D</th>
                      <th className="px-4 sm:px-6 py-3">T</th>
                      <th className="px-4 sm:px-6 py-3">Overall</th>
                      <th className="px-4 sm:px-6 py-3">Date</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm">
                    {filteredQuick.map((q) => (
                      <tr key={q.id} className="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors" data-testid={`admin-quick-row-${q.id}`}>
                        <td className="px-4 sm:px-6 py-3 text-white font-medium">{q.company_name}</td>
                        <td className="px-4 sm:px-6 py-3 text-white/50">{q.industry}</td>
                        <td className="px-4 sm:px-6 py-3">
                          <p className="text-white/60">{q.respondent_name || "Anonymous"}</p>
                          <p className="text-xs text-white/30">{q.respondent_email || ""}</p>
                        </td>
                        <td className="px-4 sm:px-6 py-3">
                          <span className={`font-['JetBrains_Mono'] font-semibold text-xs ${getScoreColorClass(q.scores?.people)}`}>
                            {q.scores?.people?.toFixed(1) || "–"}
                          </span>
                        </td>
                        <td className="px-4 sm:px-6 py-3">
                          <span className={`font-['JetBrains_Mono'] font-semibold text-xs ${getScoreColorClass(q.scores?.process)}`}>
                            {q.scores?.process?.toFixed(1) || "–"}
                          </span>
                        </td>
                        <td className="px-4 sm:px-6 py-3">
                          <span className={`font-['JetBrains_Mono'] font-semibold text-xs ${getScoreColorClass(q.scores?.data)}`}>
                            {q.scores?.data?.toFixed(1) || "–"}
                          </span>
                        </td>
                        <td className="px-4 sm:px-6 py-3">
                          <span className={`font-['JetBrains_Mono'] font-semibold text-xs ${getScoreColorClass(q.scores?.technology)}`}>
                            {q.scores?.technology?.toFixed(1) || "–"}
                          </span>
                        </td>
                        <td className="px-4 sm:px-6 py-3">
                          {q.scores?.overall ? (
                            <span className={`font-['JetBrains_Mono'] font-bold ${getScoreColorClass(q.scores.overall)}`}>
                              {q.scores.overall.toFixed(1)}
                            </span>
                          ) : <span className="text-white/30">–</span>}
                        </td>
                        <td className="px-4 sm:px-6 py-3 text-white/40 text-xs whitespace-nowrap">
                          {new Date(q.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="glass-surface-highlight rounded-xl">
              <EmptyState icon={Zap} title="No quick assessments found" />
            </div>
          )
        )}
      </div>
    </Layout>
  );
};

export default AdminPage;
