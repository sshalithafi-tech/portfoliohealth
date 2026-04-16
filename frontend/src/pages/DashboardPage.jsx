import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../App";
import Layout from "../components/Layout";
import { useDashboardData } from "../hooks/useData";
import { getScoreColorClass } from "../utils/scoring";
import { LoadingSpinner, StatusBadge, EmptyState } from "../components/ScoreComponents";
import { 
  ClipboardCheck, 
  Building2, 
  TrendingUp, 
  Play,
  Users,
  Database,
  Monitor,
  Zap
} from "lucide-react";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from "recharts";

const DIMENSION_CONFIG = [
  { icon: Users, label: "People", key: "people" },
  { icon: ClipboardCheck, label: "Process", key: "process" },
  { icon: Database, label: "Data", key: "data" },
  { icon: Monitor, label: "Technology", key: "technology" },
];

// Extracted stat card component
const StatCard = ({ icon: Icon, label, value, color = "#2f81f7" }) => (
  <div className="p-6 bg-[#111827] border border-[#374151] rounded-xl card-hover">
    <div className="flex items-center gap-4">
      <div 
        className="w-12 h-12 rounded-lg flex items-center justify-center"
        style={{ backgroundColor: `${color}20` }}
      >
        <Icon size={24} style={{ color }} />
      </div>
      <div>
        <p className="text-gray-400 text-sm">{label}</p>
        <p className="text-2xl font-semibold text-white font-['JetBrains_Mono']">
          {value}
        </p>
      </div>
    </div>
  </div>
);

// Extracted quick action card
const QuickActionCard = ({ to, icon: Icon, title, description, color = "#2f81f7", highlight = false, badge = null }) => (
  <Link 
    to={to}
    data-testid={`${title.toLowerCase().replace(/\s+/g, '-')}-btn`}
    className={`p-6 border rounded-xl card-hover group ${
      highlight 
        ? `bg-gradient-to-br from-[${color}]/10 to-[#111827] border-[${color}]/30`
        : 'bg-[#111827] border-[#374151]'
    }`}
  >
    <Icon size={32} style={{ color }} className="mb-4" />
    <h3 
      className="text-lg font-semibold text-white mb-2 group-hover:transition-colors"
      style={{ '--hover-color': color }}
    >
      {title}
    </h3>
    <p className="text-gray-400 text-sm">{description}</p>
    {badge && (
      <p className="text-xs mt-2" style={{ color }}>{badge}</p>
    )}
  </Link>
);

const DashboardPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { stats, recentAssessments, loading } = useDashboardData();

  const radarData = stats?.average_scores ? DIMENSION_CONFIG.map(({ label, key }) => ({
    dimension: label,
    score: stats.average_scores[key] || 0,
    fullMark: 5
  })) : [];

  const handleRowClick = (assessment) => {
    const path = assessment.status === "completed" 
      ? `/assessments/${assessment.id}/report` 
      : `/assessments/${assessment.id}`;
    navigate(path);
  };

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
          <StatCard 
            icon={ClipboardCheck} 
            label="Total Assessments" 
            value={stats?.total_assessments || 0} 
            color="#2f81f7" 
          />
          <StatCard 
            icon={TrendingUp} 
            label="Completed" 
            value={stats?.completed_assessments || 0} 
            color="#238636" 
          />
          <StatCard 
            icon={Zap} 
            label="Quick Screenings" 
            value={stats?.total_quick_assessments || 0} 
            color="#D29922" 
          />
          <StatCard 
            icon={Building2} 
            label="Companies" 
            value={stats?.total_companies || 0} 
            color="#A371F7" 
          />
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
                  {DIMENSION_CONFIG.map(({ icon: Icon, label, key }) => (
                    <div key={key} className="flex items-center gap-2">
                      <Icon size={16} className="text-gray-400" />
                      <span className="text-sm text-gray-400">{label}:</span>
                      <span className={`font-semibold font-['JetBrains_Mono'] ${getScoreColorClass(stats?.average_scores?.[key])}`}>
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
                        onClick={() => handleRowClick(assessment)}
                        data-testid={`assessment-row-${assessment.id}`}
                      >
                        <td className="py-4 pr-4 text-white">{assessment.company_name}</td>
                        <td className="py-4 pr-4 text-gray-400">{assessment.respondent_name}</td>
                        <td className="py-4 pr-4">
                          {assessment.scores?.overall ? (
                            <span className={`font-['JetBrains_Mono'] font-semibold ${getScoreColorClass(assessment.scores.overall)}`}>
                              {assessment.scores.overall.toFixed(1)}
                            </span>
                          ) : (
                            <span className="text-gray-500">–</span>
                          )}
                        </td>
                        <td className="py-4 pr-4"><StatusBadge status={assessment.status} /></td>
                        <td className="py-4 text-gray-400">
                          {new Date(assessment.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState
                icon={ClipboardCheck}
                title="No assessments yet"
                action={
                  <Link 
                    to="/assessments" 
                    className="text-[#2f81f7] hover:text-[#58a6ff] transition-colors"
                  >
                    Start your first assessment
                  </Link>
                }
              />
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Link 
            to="/quick-assessment"
            data-testid="quick-assessment-btn"
            className="p-6 bg-gradient-to-br from-[#2f81f7]/10 to-[#111827] border border-[#2f81f7]/30 rounded-xl card-hover group"
          >
            <Zap size={32} className="text-[#2f81f7] mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-[#2f81f7] transition-colors">
              Quick Check (10 min)
            </h3>
            <p className="text-gray-400 text-sm">
              Rapid screening with 15 questions and instant results
            </p>
            {(stats?.total_quick_assessments > 0) && (
              <p className="text-xs text-[#2f81f7] mt-2">
                {stats.total_quick_assessments} screening{stats.total_quick_assessments > 1 ? 's' : ''} saved
              </p>
            )}
          </Link>

          <Link 
            to="/companies"
            data-testid="manage-companies-btn"
            className="p-6 bg-[#111827] border border-[#374151] rounded-xl card-hover group"
          >
            <Building2 size={32} className="text-[#A371F7] mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-[#A371F7] transition-colors">
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
        </div>
      </div>
    </Layout>
  );
};

export default DashboardPage;
