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

const StatCard = ({ icon: Icon, label, value, color = "#C9A84C" }) => (
  <div className="p-4 sm:p-6 glass-card rounded-xl">
    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4">
      <div 
        className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg flex items-center justify-center shrink-0"
        style={{ backgroundColor: `${color}15` }}
      >
        <Icon size={20} style={{ color }} className="sm:hidden" />
        <Icon size={24} style={{ color }} className="hidden sm:block" />
      </div>
      <div>
        <p className="text-white/50 text-xs sm:text-sm">{label}</p>
        <p className="text-xl sm:text-2xl font-semibold text-white font-['JetBrains_Mono']">
          {value}
        </p>
      </div>
    </div>
  </div>
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
      <div className="space-y-6 sm:space-y-8" data-testid="patient-dashboard">
        {/* Header */}
        <div className="flex flex-col gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-semibold text-white font-['Outfit'] tracking-tight">
              Welcome back, {user?.name?.split(" ")[0]}
            </h1>
            <p className="text-white/50 mt-1 text-sm sm:text-base">Here's an overview of your PPDT assessments</p>
          </div>
          <Link
            to="/assessments"
            data-testid="start-assessment-btn"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 btn-liquid rounded-xl w-full sm:w-auto sm:self-start"
          >
            <Play size={18} />
            New Assessment
          </Link>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6 stagger-children">
          <StatCard icon={ClipboardCheck} label="Total Assessments" value={stats?.total_assessments || 0} color="#60A5FA" />
          <StatCard icon={TrendingUp} label="Completed" value={stats?.completed_assessments || 0} color="#34D399" />
          <StatCard icon={Zap} label="Quick Screenings" value={stats?.total_quick_assessments || 0} color="#C9A84C" />
          <StatCard icon={Building2} label="Companies" value={stats?.total_companies || 0} color="#A78BFA" />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Average PPDT Scores */}
          <div className="lg:col-span-1 p-6 glass-surface-highlight rounded-xl">
            <h2 className="text-lg font-semibold text-white mb-4 font-['Outfit']">
              Average PPDT Scores
            </h2>
            {stats?.completed_assessments > 0 ? (
              <>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="rgba(255,255,255,0.08)" />
                      <PolarAngleAxis dataKey="dimension" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 12 }} />
                      <PolarRadiusAxis domain={[0, 5]} tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 10 }} />
                      <Radar
                        name="Score"
                        dataKey="score"
                        stroke="#C9A84C"
                        fill="#C9A84C"
                        fillOpacity={0.15}
                        strokeWidth={2}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-4">
                  {DIMENSION_CONFIG.map(({ icon: Icon, label, key }) => (
                    <div key={key} className="flex items-center gap-2">
                      <Icon size={16} className="text-white/40" />
                      <span className="text-sm text-white/50">{label}:</span>
                      <span className={`font-semibold font-['JetBrains_Mono'] ${getScoreColorClass(stats?.average_scores?.[key])}`}>
                        {stats?.average_scores?.[key]?.toFixed(1) || "–"}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="h-64 flex items-center justify-center text-white/30">
                <p>Complete assessments to see average scores</p>
              </div>
            )}
          </div>

          {/* Recent Assessments */}
          <div className="lg:col-span-2 p-6 glass-surface-highlight rounded-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white font-['Outfit']">
                Recent Assessments
              </h2>
              <Link to="/assessments" className="text-[#C9A84C] hover:text-[#C9A84C]/80 text-sm transition-colors">
                View all
              </Link>
            </div>
            {recentAssessments.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-wider text-white/40 border-b border-white/[0.08]">
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
                        className="border-b border-white/[0.04] hover:bg-white/[0.02] cursor-pointer transition-colors"
                        onClick={() => handleRowClick(assessment)}
                        data-testid={`assessment-row-${assessment.id}`}
                      >
                        <td className="py-4 pr-4 text-white">{assessment.company_name}</td>
                        <td className="py-4 pr-4 text-white/50">{assessment.respondent_name}</td>
                        <td className="py-4 pr-4">
                          {assessment.scores?.overall ? (
                            <span className={`font-['JetBrains_Mono'] font-semibold ${getScoreColorClass(assessment.scores.overall)}`}>
                              {assessment.scores.overall.toFixed(1)}
                            </span>
                          ) : (
                            <span className="text-white/30">–</span>
                          )}
                        </td>
                        <td className="py-4 pr-4"><StatusBadge status={assessment.status} /></td>
                        <td className="py-4 text-white/40">
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
                    className="text-[#C9A84C] hover:text-[#C9A84C]/80 transition-colors"
                  >
                    Start your first assessment
                  </Link>
                }
              />
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6">
          <Link 
            to="/quick-assessment"
            data-testid="quick-assessment-btn"
            className="p-6 glass-card rounded-xl group hover:border-[#C9A84C]/20"
          >
            <Zap size={32} className="text-[#C9A84C] mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-[#C9A84C] transition-colors font-['Outfit']">
              Quick Check (10 min)
            </h3>
            <p className="text-white/50 text-sm">
              Rapid screening with 15 questions and instant results
            </p>
            {(stats?.total_quick_assessments > 0) && (
              <p className="text-xs text-[#C9A84C] mt-2">
                {stats.total_quick_assessments} screening{stats.total_quick_assessments > 1 ? 's' : ''} saved
              </p>
            )}
          </Link>

          <Link 
            to="/companies"
            data-testid="manage-companies-btn"
            className="p-6 glass-card rounded-xl group hover:border-[#A78BFA]/20"
          >
            <Building2 size={32} className="text-[#A78BFA] mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-[#A78BFA] transition-colors font-['Outfit']">
              Manage Companies
            </h3>
            <p className="text-white/50 text-sm">
              Add and manage client companies for longitudinal tracking
            </p>
          </Link>

          <Link 
            to="/assessments"
            data-testid="view-assessments-btn"
            className="p-6 glass-card rounded-xl group hover:border-[#34D399]/20"
          >
            <ClipboardCheck size={32} className="text-[#34D399] mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-[#34D399] transition-colors font-['Outfit']">
              View Assessments
            </h3>
            <p className="text-white/50 text-sm">
              Review past assessments and track maturity progress
            </p>
          </Link>
        </div>
      </div>
    </Layout>
  );
};

export default DashboardPage;
