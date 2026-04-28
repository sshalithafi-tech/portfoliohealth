import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { toast } from "sonner";
import Layout from "../components/Layout";
import LogoMark from "../components/LogoMark";
import { LoadingSpinner } from "../components/ScoreComponents";
import AdminStatsGrid from "../components/admin/AdminStatsGrid";
import AdminFilters from "../components/admin/AdminFilters";
import AdminFullAssessmentsTable from "../components/admin/AdminFullAssessmentsTable";
import AdminQuickAssessmentsTable from "../components/admin/AdminQuickAssessmentsTable";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const TabButton = ({ active, onClick, testId, children }) => (
  <button
    data-testid={testId}
    onClick={onClick}
    className={`px-4 py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
      active ? "border-[#0891B2] text-[#0891B2]" : "border-transparent text-[#4A5568] hover:text-[#0C1B2A]"
    }`}
  >
    {children}
  </button>
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

  const fetchData = useCallback(async () => {
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
      if (err.response?.status === 403) toast.error("Admin access required");
      else toast.error("Failed to load admin data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

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
      console.error("CSV export failed:", err);
      toast.error("Failed to export CSV");
    } finally {
      setDownloading(false);
    }
  };

  const filteredAssessments = assessments.filter(a => {
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      a.company_name?.toLowerCase().includes(q) ||
      a.respondent_name?.toLowerCase().includes(q) ||
      a.consultant_name?.toLowerCase().includes(q);
    const matchesStatus = statusFilter === "all" || a.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const filteredQuick = quickAssessments.filter(q => {
    const s = searchQuery.toLowerCase();
    return q.company_name?.toLowerCase().includes(s) ||
      q.respondent_name?.toLowerCase().includes(s) ||
      q.respondent_email?.toLowerCase().includes(s);
  });

  if (loading) return <Layout><LoadingSpinner className="h-64" /></Layout>;

  return (
    <Layout>
      <div className="space-y-6 sm:space-y-8">
        <div className="flex items-center gap-3">
          <LogoMark className="w-11 h-11 rounded-xl shrink-0" radius={18} />
          <div>
            <h1 className="text-2xl sm:text-3xl font-semibold text-[#0C1B2A] font-['Outfit'] tracking-tight">Admin Panel</h1>
            <p className="text-[#4A5568] text-sm">All assessment data across all users</p>
          </div>
        </div>

        <AdminStatsGrid stats={stats} />

        <div className="flex items-center gap-2 border-b border-[#E2E8F0] pb-0">
          <TabButton active={activeTab === "full"} onClick={() => { setActiveTab("full"); setSearchQuery(""); }} testId="tab-full-assessments">
            Full Assessments ({assessments.length})
          </TabButton>
          <TabButton active={activeTab === "quick"} onClick={() => { setActiveTab("quick"); setSearchQuery(""); }} testId="tab-quick-assessments">
            Quick Assessments ({quickAssessments.length})
          </TabButton>
        </div>

        <AdminFilters
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          statusFilter={statusFilter}
          onStatusChange={setStatusFilter}
          showStatusFilter={activeTab === "full"}
          onExport={() => exportCSV(activeTab)}
          downloading={downloading}
          searchPlaceholder={activeTab === "full" ? "Search company, respondent, consultant..." : "Search company, respondent, email..."}
        />

        {activeTab === "full"
          ? <AdminFullAssessmentsTable assessments={filteredAssessments} />
          : <AdminQuickAssessmentsTable quickAssessments={filteredQuick} />}
      </div>
    </Layout>
  );
};

export default AdminPage;
