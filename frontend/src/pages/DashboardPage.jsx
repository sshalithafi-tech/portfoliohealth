import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../App";
import Layout from "../components/Layout";
import { useDashboardData } from "../hooks/useData";
import { getScoreColorClass, getScoreColor } from "../utils/scoring";
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

const DIMENSION_CONFIG = [
  { icon: Users, label: "People", key: "people" },
  { icon: ClipboardCheck, label: "Process", key: "process" },
  { icon: Database, label: "Data", key: "data" },
  { icon: Monitor, label: "Technology", key: "technology" },
];

const StatCard = ({ icon: Icon, label, value, color = "#C9A84C" }) => (
  <div className="p-4 sm:p-5 glass-card rounded-xl">
    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4">
      <div className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0" style={{ backgroundColor: `${color}12` }}>
        <Icon size={20} style={{ color }} />
      </div>
      <div>
        <p className="text-white/45 text-xs">{label}</p>
        <p className="text-xl sm:text-2xl font-semibold text-white font-['JetBrains_Mono']">{value}</p>
      </div>
    </div>
  </div>
);

const DimensionBar = ({ icon: Icon, label, score, color }) => (
  <div className="flex items-center gap-3 py-2.5">
    <Icon size={16} className="text-white/40 shrink-0" />
    <span className="text-sm text-white/60 w-20">{label}</span>
    <div className="flex-1 h-2 bg-white/[0.06] rounded-full overflow-hidden">
      <div className="h-full rounded-full transition-all duration-700" style={{ width: `${(score / 5) * 100}%`, backgroundColor: color }} />
    </div>
    <span className={`font-['JetBrains_Mono'] font-semibold text-sm w-8 text-right ${getScoreColorClass(score)}`}>
      {score?.toFixed(1) || "–"}
    </span>
  </div>
);

const DashboardPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { stats, recentAssessments, loading } = useDashboardData();

  const handleRowClick = (assessment) => {
    navigate(assessment.status === "completed" ? `/assessments/${assessment.id}/report` : `/assessments/${assessment.id}`);
  };

  if (loading) return <Layout><LoadingSpinner className="h-64" /></Layout>;

  return (
    <Layout>
      <div className="space-y-6 sm:space-y-8" data-testid="patient-dashboard">
        {/* Header */}
        <div className="flex flex-col gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-semibold text-white font-['Outfit'] tracking-tight">
              Welcome back, {user?.name?.split(" ")[0]}
            </h1>
            <p className="text-white/45 mt-1 text-sm">Overview of your PPDT assessments</p>
          </div>
          <Link to="/assessments" data-testid="start-assessment-btn" className="inline-flex items-center justify-center gap-2 px-6 py-3 btn-liquid rounded-xl w-full sm:w-auto sm:self-start">
            <Play size={18} /> New Assessment
          </Link>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 stagger-children">
          <StatCard icon={ClipboardCheck} label="Total Assessments" value={stats?.total_assessments || 0} color="#60A5FA" />
          <StatCard icon={TrendingUp} label="Completed" value={stats?.completed_assessments || 0} color="#34D399" />
          <StatCard icon={Zap} label="Quick Screenings" value={stats?.total_quick_assessments || 0} color="#C9A84C" />
          <StatCard icon={Building2} label="Companies" value={stats?.total_companies || 0} color="#A78BFA" />
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Average PPDT Scores */}
          <div className="lg:col-span-1 p-5 glass-surface-highlight rounded-xl">
            <h2 className="text-base font-semibold text-white mb-4 font-['Outfit']">Average PPDT Scores</h2>
            {stats?.completed_assessments > 0 ? (
              <div className="space-y-1">
                {DIMENSION_CONFIG.map(({ icon, label, key }) => (
                  <DimensionBar key={key} icon={icon} label={label} score={stats?.average_scores?.[key] || 0} color={getScoreColor(stats?.average_scores?.[key] || 0)} />
                ))}
                <div className="pt-3 mt-3 border-t border-white/[0.06] flex items-center justify-between">
                  <span className="text-sm text-white/60">Overall Average</span>
                  <span className={`font-['JetBrains_Mono'] font-bold text-lg ${getScoreColorClass(
                    ((stats?.average_scores?.people || 0) + (stats?.average_scores?.process || 0) + (stats?.average_scores?.data || 0) + (stats?.average_scores?.technology || 0)) / 4
                  )}`}>
                    {(((stats?.average_scores?.people || 0) + (stats?.average_scores?.process || 0) + (stats?.average_scores?.data || 0) + (stats?.average_scores?.technology || 0)) / 4).toFixed(1)}
                  </span>
                </div>
              </div>
            ) : (
              <div className="py-12 text-center text-white/25 text-sm">Complete assessments to see scores</div>
            )}
          </div>

          {/* Recent Assessments */}
          <div className="lg:col-span-2 p-5 glass-surface-highlight rounded-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-white font-['Outfit']">Recent Assessments</h2>
              <Link to="/assessments" className="text-[#C9A84C] hover:text-[#C9A84C]/80 text-sm transition-colors">View all</Link>
            </div>
            {recentAssessments.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-wider text-white/35 border-b border-white/[0.06]">
                      <th className="pb-3 pr-4">Company</th>
                      <th className="pb-3 pr-4">Respondent</th>
                      <th className="pb-3 pr-4">Score</th>
                      <th className="pb-3 pr-4">Status</th>
                      <th className="pb-3">Date</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm">
                    {recentAssessments.map((a) => (
                      <tr key={a.id} className="border-b border-white/[0.04] hover:bg-white/[0.02] cursor-pointer transition-colors" onClick={() => handleRowClick(a)} data-testid={`assessment-row-${a.id}`}>
                        <td className="py-3.5 pr-4 text-white">{a.company_name}</td>
                        <td className="py-3.5 pr-4 text-white/50">{a.respondent_name}</td>
                        <td className="py-3.5 pr-4">
                          {a.scores?.overall ? (
                            <span className={`font-['JetBrains_Mono'] font-semibold ${getScoreColorClass(a.scores.overall)}`}>{a.scores.overall.toFixed(1)}</span>
                          ) : <span className="text-white/25">–</span>}
                        </td>
                        <td className="py-3.5 pr-4"><StatusBadge status={a.status} /></td>
                        <td className="py-3.5 text-white/35">{new Date(a.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState icon={ClipboardCheck} title="No assessments yet" action={<Link to="/assessments" className="text-[#C9A84C]">Start your first assessment</Link>} />
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link to="/quick-assessment" data-testid="quick-assessment-btn" className="p-5 glass-card rounded-xl group hover:border-[#C9A84C]/15">
            <Zap size={28} className="text-[#C9A84C] mb-3" />
            <h3 className="text-base font-semibold text-white mb-1 group-hover:text-[#C9A84C] transition-colors font-['Outfit']">Quick Check</h3>
            <p className="text-white/40 text-sm">10-minute rapid screening</p>
          </Link>
          <Link to="/companies" data-testid="manage-companies-btn" className="p-5 glass-card rounded-xl group hover:border-[#A78BFA]/15">
            <Building2 size={28} className="text-[#A78BFA] mb-3" />
            <h3 className="text-base font-semibold text-white mb-1 group-hover:text-[#A78BFA] transition-colors font-['Outfit']">Companies</h3>
            <p className="text-white/40 text-sm">Manage client companies</p>
          </Link>
          <Link to="/assessments" data-testid="view-assessments-btn" className="p-5 glass-card rounded-xl group hover:border-[#34D399]/15">
            <ClipboardCheck size={28} className="text-[#34D399] mb-3" />
            <h3 className="text-base font-semibold text-white mb-1 group-hover:text-[#34D399] transition-colors font-['Outfit']">Assessments</h3>
            <p className="text-white/40 text-sm">Review past assessments</p>
          </Link>
        </div>
      </div>
    </Layout>
  );
};

export default DashboardPage;
