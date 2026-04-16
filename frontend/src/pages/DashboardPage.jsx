import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../App";
import Layout from "../components/Layout";
import { 
  ClipboardCheck, 
  Building2, 
  TrendingUp, 
  Play,
  BarChart3,
  Users,
  Database,
  Monitor
} from "lucide-react";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from "recharts";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const DashboardPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [recentAssessments, setRecentAssessments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, assessmentsRes] = await Promise.all([
          axios.get(`${BACKEND_URL}/api/dashboard/stats`),
          axios.get(`${BACKEND_URL}/api/assessments`)
        ]);
        setStats(statsRes.data);
        setRecentAssessments(assessmentsRes.data.slice(0, 5));
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const radarData = stats?.average_scores ? [
    { dimension: "People", score: stats.average_scores.people, fullMark: 5 },
    { dimension: "Process", score: stats.average_scores.process, fullMark: 5 },
    { dimension: "Data", score: stats.average_scores.data, fullMark: 5 },
    { dimension: "Technology", score: stats.average_scores.technology, fullMark: 5 },
  ] : [];

  const getScoreColor = (score) => {
    if (score >= 4) return "text-[#2f81f7]";
    if (score >= 3) return "text-[#238636]";
    if (score >= 2) return "text-[#D29922]";
    return "text-[#F85149]";
  };

  const getStatusBadge = (status) => {
    if (status === "completed") {
      return <span className="px-2 py-1 text-xs rounded bg-[#238636]/20 text-[#238636]">Completed</span>;
    }
    return <span className="px-2 py-1 text-xs rounded bg-[#D29922]/20 text-[#D29922]">In Progress</span>;
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-pulse-glow w-12 h-12 rounded-full bg-[#2f81f7]/20 flex items-center justify-center">
            <div className="w-6 h-6 rounded-full bg-[#2f81f7]" />
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold text-white font-['Outfit'] tracking-tight">
              Welcome back, {user?.name?.split(" ")[0]}
            </h1>
            <p className="text-gray-400 mt-1">Here's an overview of your PPDT assessments</p>
          </div>
          <Link
            to="/assessments"
            data-testid="start-assessment-btn"
            className="inline-flex items-center gap-2 px-6 py-3 bg-[#2f81f7] text-white font-medium rounded-lg hover:bg-[#58a6ff] transition-all btn-premium"
          >
            <Play size={18} />
            New Assessment
          </Link>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 stagger-children">
          <div className="p-6 bg-[#111827] border border-[#374151] rounded-xl card-hover">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-[#2f81f7]/20 flex items-center justify-center">
                <ClipboardCheck size={24} className="text-[#2f81f7]" />
              </div>
              <div>
                <p className="text-gray-400 text-sm">Total Assessments</p>
                <p className="text-2xl font-semibold text-white font-['JetBrains_Mono']">
                  {stats?.total_assessments || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="p-6 bg-[#111827] border border-[#374151] rounded-xl card-hover">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-[#238636]/20 flex items-center justify-center">
                <TrendingUp size={24} className="text-[#238636]" />
              </div>
              <div>
                <p className="text-gray-400 text-sm">Completed</p>
                <p className="text-2xl font-semibold text-white font-['JetBrains_Mono']">
                  {stats?.completed_assessments || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="p-6 bg-[#111827] border border-[#374151] rounded-xl card-hover">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-[#D29922]/20 flex items-center justify-center">
                <BarChart3 size={24} className="text-[#D29922]" />
              </div>
              <div>
                <p className="text-gray-400 text-sm">In Progress</p>
                <p className="text-2xl font-semibold text-white font-['JetBrains_Mono']">
                  {stats?.in_progress_assessments || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="p-6 bg-[#111827] border border-[#374151] rounded-xl card-hover">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-[#A371F7]/20 flex items-center justify-center">
                <Building2 size={24} className="text-[#A371F7]" />
              </div>
              <div>
                <p className="text-gray-400 text-sm">Companies</p>
                <p className="text-2xl font-semibold text-white font-['JetBrains_Mono']">
                  {stats?.total_companies || 0}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Average PPDT Scores */}
          <div className="lg:col-span-1 p-6 bg-[#111827] border border-[#374151] rounded-xl">
            <h2 className="text-lg font-semibold text-white mb-4 font-['Outfit']">
              Average PPDT Scores
            </h2>
            {stats?.completed_assessments > 0 ? (
              <>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="#374151" />
                      <PolarAngleAxis dataKey="dimension" tick={{ fill: "#9CA3AF", fontSize: 12 }} />
                      <PolarRadiusAxis domain={[0, 5]} tick={{ fill: "#6B7280", fontSize: 10 }} />
                      <Radar
                        name="Score"
                        dataKey="score"
                        stroke="#2f81f7"
                        fill="#2f81f7"
                        fillOpacity={0.3}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-4">
                  {[
                    { icon: Users, label: "People", key: "people" },
                    { icon: ClipboardCheck, label: "Process", key: "process" },
                    { icon: Database, label: "Data", key: "data" },
                    { icon: Monitor, label: "Technology", key: "technology" },
                  ].map(({ icon: Icon, label, key }) => (
                    <div key={key} className="flex items-center gap-2">
                      <Icon size={16} className="text-gray-400" />
                      <span className="text-sm text-gray-400">{label}:</span>
                      <span className={`font-semibold font-['JetBrains_Mono'] ${getScoreColor(stats?.average_scores?.[key])}`}>
                        {stats?.average_scores?.[key]?.toFixed(1) || "–"}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500">
                <p>Complete assessments to see average scores</p>
              </div>
            )}
          </div>

          {/* Recent Assessments */}
          <div className="lg:col-span-2 p-6 bg-[#111827] border border-[#374151] rounded-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white font-['Outfit']">
                Recent Assessments
              </h2>
              <Link to="/assessments" className="text-[#2f81f7] hover:text-[#58a6ff] text-sm transition-colors">
                View all
              </Link>
            </div>
            {recentAssessments.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-wider text-gray-400 border-b border-[#374151]">
                      <th className="pb-3 pr-4">Company</th>
                      <th className="pb-3 pr-4">Respondent</th>
                      <th className="pb-3 pr-4">Score</th>
                      <th className="pb-3 pr-4">Status</th>
                      <th className="pb-3">Date</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm">
                    {recentAssessments.map((assessment) => (
                      <tr 
                        key={assessment.id} 
                        className="border-b border-[#374151]/50 hover:bg-[#1F2937] cursor-pointer transition-colors"
                        onClick={() => navigate(assessment.status === "completed" ? `/assessments/${assessment.id}/report` : `/assessments/${assessment.id}`)}
                        data-testid={`assessment-row-${assessment.id}`}
                      >
                        <td className="py-4 pr-4 text-white">{assessment.company_name}</td>
                        <td className="py-4 pr-4 text-gray-400">{assessment.respondent_name}</td>
                        <td className="py-4 pr-4">
                          {assessment.scores?.overall ? (
                            <span className={`font-['JetBrains_Mono'] font-semibold ${getScoreColor(assessment.scores.overall)}`}>
                              {assessment.scores.overall.toFixed(1)}
                            </span>
                          ) : (
                            <span className="text-gray-500">–</span>
                          )}
                        </td>
                        <td className="py-4 pr-4">{getStatusBadge(assessment.status)}</td>
                        <td className="py-4 text-gray-400">
                          {new Date(assessment.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="h-48 flex flex-col items-center justify-center text-gray-500">
                <ClipboardCheck size={48} className="mb-4 opacity-50" />
                <p>No assessments yet</p>
                <Link 
                  to="/assessments" 
                  className="mt-4 text-[#2f81f7] hover:text-[#58a6ff] transition-colors"
                >
                  Start your first assessment
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Link 
            to="/companies"
            data-testid="manage-companies-btn"
            className="p-6 bg-[#111827] border border-[#374151] rounded-xl card-hover group"
          >
            <Building2 size={32} className="text-[#2f81f7] mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-[#2f81f7] transition-colors">
              Manage Companies
            </h3>
            <p className="text-gray-400 text-sm">
              Add and manage client companies for longitudinal tracking
            </p>
          </Link>

          <Link 
            to="/assessments"
            data-testid="view-assessments-btn"
            className="p-6 bg-[#111827] border border-[#374151] rounded-xl card-hover group"
          >
            <ClipboardCheck size={32} className="text-[#238636] mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-[#238636] transition-colors">
              View Assessments
            </h3>
            <p className="text-gray-400 text-sm">
              Review past assessments and track maturity progress
            </p>
          </Link>

          <div className="p-6 bg-[#111827] border border-[#374151] rounded-xl">
            <BarChart3 size={32} className="text-[#A371F7] mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">PPDT Model</h3>
            <p className="text-gray-400 text-sm">
              Assess People, Process, Data, and Technology dimensions for PPM readiness
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default DashboardPage;
