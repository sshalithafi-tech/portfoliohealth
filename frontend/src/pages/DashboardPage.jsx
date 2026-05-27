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
  Zap,
  ChevronRight,
  Calendar,
  AlertTriangle,
} from "lucide-react";

const DIMENSION_CONFIG = [
  { icon: Users, label: "People", key: "people" },
  { icon: ClipboardCheck, label: "Process", key: "process" },
  { icon: Database, label: "Data", key: "data" },
  { icon: Monitor, label: "Technology", key: "technology" },
];

/* ── helpers ── */
const PILLAR_META = {
  people:     { letter: "P", precondition: "P1–P2", label: "People" },
  process:    { letter: "P", precondition: "P3",    label: "Process" },
  data:       { letter: "D", precondition: "P4",    label: "Data" },
  technology: { letter: "T", precondition: "P5",    label: "Technology" },
};

const RISK_COLOR = {
  HIGH:   { dot: "#EF4444", bg: "rgba(239,68,68,0.08)",   text: "#B91C1C" },
  MEDIUM: { dot: "#F59E0B", bg: "rgba(245,158,11,0.08)",  text: "#B45309" },
  LOW:    { dot: "#22C55E", bg: "rgba(34,197,94,0.08)",   text: "#15803D" },
};

const RiskPill = ({ level }) => {
  const c = RISK_COLOR[level] || RISK_COLOR.MEDIUM;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 5,
      background: c.bg, color: c.text,
      border: `1px solid ${c.dot}40`,
      borderRadius: 50, padding: "2px 10px",
      fontSize: 11, fontWeight: 700, letterSpacing: "0.04em",
      fontFamily: "'Outfit', sans-serif",
    }}>
      <span style={{ width: 7, height: 7, borderRadius: "50%", background: c.dot, flexShrink: 0 }} />
      {level}
    </span>
  );
};

/* ── Card 1 — Bottleneck Alert ── */
const BottleneckAlertCard = ({ bottleneck, score, company }) => {
  if (!bottleneck) return null;
  const meta = PILLAR_META[bottleneck] || { letter: bottleneck[0].toUpperCase(), precondition: "P4", label: bottleneck };

  return (
    <div style={{
      background: "#fff",
      border: "1px solid #E5E7EB",
      borderLeft: "4px solid #EF4444",
      borderRadius: 16,
      boxShadow: "0 4px 16px rgba(239,68,68,0.07), 0 1px 3px rgba(15,23,42,0.06)",
      overflow: "hidden",
    }} data-testid="bottleneck-alert-card">

      {/* Header */}
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "14px 20px",
        borderBottom: "1px solid #FEE2E2",
        background: "linear-gradient(135deg, rgba(239,68,68,0.04) 0%, rgba(255,255,255,0) 100%)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <AlertTriangle size={15} style={{ color: "#EF4444", flexShrink: 0 }} />
          <span style={{
            fontSize: 11, fontWeight: 700, letterSpacing: "0.14em",
            textTransform: "uppercase", color: "#B91C1C",
            fontFamily: "'Outfit', sans-serif",
          }}>Bottleneck Identified</span>
        </div>
        <span style={{
          display: "inline-flex", alignItems: "center", gap: 6,
          background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.25)",
          borderRadius: 50, padding: "3px 12px",
          fontSize: 11, fontWeight: 700, color: "#B91C1C",
          fontFamily: "'Outfit', sans-serif",
        }}>
          <span style={{ width: 7, height: 7, borderRadius: "50%", background: "#EF4444" }} />
          {meta.label.toUpperCase()}
        </span>
      </div>

      {/* Body */}
      <div style={{ padding: "16px 20px", display: "flex", flexDirection: "column", gap: 14 }}>

        {/* Root cause */}
        <div>
          <div style={{
            fontSize: 10, fontWeight: 700, letterSpacing: "0.12em",
            textTransform: "uppercase", color: "#6B7280",
            marginBottom: 5, fontFamily: "'Outfit', sans-serif",
          }}>Root Cause</div>
          <p style={{ fontSize: 13, color: "#1E293B", lineHeight: 1.6, margin: 0 }}>
            The <strong style={{ color: "#0C1B2A" }}>{meta.label}</strong> pillar is structurally
            isolated from portfolio decision systems — leading indicators cannot flow
            into renewal, retirement, or investment decisions.
          </p>
          <div style={{
            display: "inline-flex", alignItems: "center", gap: 6,
            marginTop: 7,
            background: "rgba(8,145,178,0.06)", border: "1px solid rgba(8,145,178,0.18)",
            borderRadius: 8, padding: "4px 10px",
          }}>
            <span style={{ fontSize: 11, color: "#0E7490", fontWeight: 600 }}>
              → Precondition {meta.precondition} unmet
            </span>
            <span style={{
              fontSize: 10, color: "#0891B2", fontWeight: 500,
              fontStyle: "italic",
            }}>(Hannila et al. 2020)</span>
          </div>
        </div>

        {/* Proven consequence */}
        <div style={{
          background: "rgba(239,68,68,0.04)",
          border: "1px solid rgba(239,68,68,0.12)",
          borderRadius: 10, padding: "11px 14px",
        }}>
          <div style={{
            fontSize: 10, fontWeight: 700, letterSpacing: "0.12em",
            textTransform: "uppercase", color: "#6B7280",
            marginBottom: 5, fontFamily: "'Outfit', sans-serif",
          }}>Proven Consequence</div>
          <p style={{ fontSize: 12.5, color: "#374151", lineHeight: 1.65, margin: 0 }}>
            Signals existed <strong>12+ months before financial impact</strong> — but
            could not reach the decision layer. Cost: a 6-month delayed decision.
            The gap widens with every new project accepted.
          </p>
        </div>

        {/* Risk row */}
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          paddingTop: 4,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div>
              <div style={{
                fontSize: 10, fontWeight: 700, letterSpacing: "0.10em",
                textTransform: "uppercase", color: "#6B7280",
                marginBottom: 3, fontFamily: "'Outfit', sans-serif",
              }}>Risk</div>
              <RiskPill level="HIGH" />
            </div>
            <div style={{ width: 1, height: 28, background: "#E5E7EB" }} />
            <div>
              <div style={{
                fontSize: 10, fontWeight: 700, letterSpacing: "0.10em",
                textTransform: "uppercase", color: "#6B7280",
                marginBottom: 3, fontFamily: "'Outfit', sans-serif",
              }}>Until Resolved</div>
              <p style={{ fontSize: 12, color: "#374151", margin: 0, lineHeight: 1.4 }}>
                Gap widens with every new project accepted
              </p>
            </div>
          </div>
          {score && (
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 10, color: "#9CA3AF", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase" }}>Score</div>
              <div style={{ fontSize: 22, fontWeight: 700, color: "#EF4444", fontFamily: "'JetBrains Mono', monospace", lineHeight: 1.1 }}>
                {typeof score === "number" ? score.toFixed(1) : score}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Citation footer */}
      <div style={{
        padding: "9px 20px",
        borderTop: "1px solid #F3F4F6",
        background: "#FAFAFA",
        fontSize: 10.5, color: "#9CA3AF",
        fontStyle: "italic", lineHeight: 1.5,
      }}>
        Hannila et al. 2022, Journal of Decision Systems 31(3), 258–279 ·
        Hannila et al. 2020, JEIM 33(1), 214–237
      </div>
    </div>
  );
};

/* ── Existing sub-components (unchanged) ── */
const StatCard = ({ icon: Icon, label, value, color = "#0891B2" }) => (
  <div className="p-4 sm:p-5 glass-card rounded-xl">
    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4">
      <div className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0" style={{ backgroundColor: `${color}12` }}>
        <Icon size={20} style={{ color }} />
      </div>
      <div>
        <p className="text-[#8896A5] text-xs">{label}</p>
        <p className="text-xl sm:text-2xl font-semibold text-[#0C1B2A] font-['JetBrains_Mono']">{value}</p>
      </div>
    </div>
  </div>
);

const DimensionBar = ({ icon: Icon, label, score, color }) => (
  <div className="flex items-center gap-3 py-2.5">
    <Icon size={16} className="text-[#8896A5] shrink-0" />
    <span className="text-sm text-[#4A5568] w-20">{label}</span>
    <div className="flex-1 h-2 bg-[#F8F9FA] rounded-full overflow-hidden">
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

  // Derive bottleneck from most recent completed assessment
  const latestCompleted = recentAssessments.find((a) => a.status === "completed");
  const bottleneckKey = latestCompleted?.bottleneck || latestCompleted?.report?.bottleneck || null;
  const bottleneckScore = bottleneckKey && latestCompleted?.scores
    ? latestCompleted.scores[bottleneckKey]
    : null;

  if (loading) return <Layout><LoadingSpinner className="h-64" /></Layout>;

  return (
    <Layout>
      <div className="space-y-6 sm:space-y-8" data-testid="patient-dashboard">
        {/* Header */}
        <div className="flex flex-col gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-semibold text-[#0C1B2A] font-['Outfit'] tracking-tight">
              Welcome back, {user?.name?.split(" ")[0]}
            </h1>
            <p className="text-[#8896A5] mt-1 text-sm">Overview of your PPDT assessments</p>
          </div>
          <Link to="/assessments" data-testid="start-assessment-btn" className="inline-flex items-center justify-center gap-2 px-6 py-3 btn-liquid rounded-xl w-full sm:w-auto sm:self-start">
            <Play size={18} /> New Assessment
          </Link>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 stagger-children">
          <StatCard icon={ClipboardCheck} label="Total Assessments" value={stats?.total_assessments || 0} color="#0891B2" />
          <StatCard icon={TrendingUp} label="Completed" value={stats?.completed_assessments || 0} color="#27AE60" />
          <StatCard icon={Zap} label="Quick Screenings" value={stats?.total_quick_assessments || 0} color="#67E8F9" />
          <StatCard icon={Building2} label="Companies" value={stats?.total_companies || 0} color="#0891B2" />
        </div>

        {/* Bottleneck Alert Card — only when a bottleneck is detected */}
        {bottleneckKey && (
          <BottleneckAlertCard
            bottleneck={bottleneckKey}
            score={bottleneckScore}
            company={latestCompleted?.company_name}
          />
        )}

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Average PPDT Scores */}
          <div className="lg:col-span-1 p-5 glass-surface-highlight rounded-xl">
            <h2 className="text-base font-semibold text-[#0C1B2A] mb-4 font-['Outfit']">Average PPDT Scores</h2>
            {stats?.completed_assessments > 0 ? (
              <div className="space-y-1">
                {DIMENSION_CONFIG.map(({ icon, label, key }) => (
                  <DimensionBar key={key} icon={icon} label={label} score={stats?.average_scores?.[key] || 0} color={getScoreColor(stats?.average_scores?.[key] || 0)} />
                ))}
                <div className="pt-3 mt-3 border-t border-[#E2E8F0] flex items-center justify-between">
                  <span className="text-sm text-[#4A5568]">Overall Average</span>
                  <span className={`font-['JetBrains_Mono'] font-bold text-lg ${getScoreColorClass(
                    ((stats?.average_scores?.people || 0) + (stats?.average_scores?.process || 0) + (stats?.average_scores?.data || 0) + (stats?.average_scores?.technology || 0)) / 4
                  )}`}>
                    {(((stats?.average_scores?.people || 0) + (stats?.average_scores?.process || 0) + (stats?.average_scores?.data || 0) + (stats?.average_scores?.technology || 0)) / 4).toFixed(1)}
                  </span>
                </div>
              </div>
            ) : (
              <div className="py-12 text-center text-[#8896A5] text-sm">Complete assessments to see scores</div>
            )}
          </div>

          {/* Recent Assessments */}
          <div className="lg:col-span-2 p-5 glass-surface-highlight rounded-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-[#0C1B2A] font-['Outfit']">Recent Assessments</h2>
              <Link to="/assessments" className="text-[#0891B2] hover:text-[#0891B2]/80 text-sm transition-colors">View all</Link>
            </div>
            {recentAssessments.length > 0 ? (
              <div className="space-y-2.5">
                {recentAssessments.map((a) => (
                  <div
                    key={a.id}
                    onClick={() => handleRowClick(a)}
                    data-testid={`assessment-row-${a.id}`}
                    className="group flex items-center gap-4 p-3.5 rounded-xl bg-[#F8F9FA] hover:bg-[#F8F9FA] border border-[#E2E8F0] hover:border-[#0891B2]/20 cursor-pointer transition-all duration-200"
                  >
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#0891B2]/20 to-[#60A5FA]/5 border border-[#60A5FA]/15 flex items-center justify-center shrink-0">
                      <Building2 size={16} className="text-[#60A5FA]" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-[#0C1B2A] font-medium text-sm truncate leading-tight">{a.company_name}</p>
                      <p className="text-xs text-[#8896A5] mt-0.5 truncate">{a.respondent_name}</p>
                    </div>
                    <div className="hidden sm:flex items-center gap-1.5 text-xs text-[#8896A5] shrink-0">
                      <Calendar size={12} />
                      <span>{new Date(a.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</span>
                    </div>
                    <div className="shrink-0">
                      <StatusBadge status={a.status} />
                    </div>
                    <div className="w-12 text-right shrink-0">
                      {a.scores?.overall ? (
                        <span className={`font-['JetBrains_Mono'] font-bold text-base ${getScoreColorClass(a.scores.overall)}`}>
                          {a.scores.overall.toFixed(1)}
                        </span>
                      ) : (
                        <span className="text-[#8896A5] text-sm">–</span>
                      )}
                    </div>
                    <ChevronRight size={16} className="text-[#8896A5] group-hover:text-[#0891B2] group-hover:translate-x-0.5 transition-all shrink-0" />
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState icon={ClipboardCheck} title="No assessments yet" action={<Link to="/assessments" className="text-[#0891B2]">Start your first assessment</Link>} />
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link to="/quick-assessment" data-testid="quick-assessment-btn" className="p-5 glass-card rounded-xl group hover:border-[#0891B2]/15">
            <Zap size={28} className="text-[#0891B2] mb-3" />
            <h3 className="text-base font-semibold text-[#0C1B2A] mb-1 group-hover:text-[#0891B2] transition-colors font-['Outfit']">Quick Check</h3>
            <p className="text-[#8896A5] text-sm">10-minute rapid screening</p>
          </Link>
          <Link to="/companies" data-testid="manage-companies-btn" className="p-5 glass-card rounded-xl group hover:border-[#A78BFA]/15">
            <Building2 size={28} className="text-[#A78BFA] mb-3" />
            <h3 className="text-base font-semibold text-[#0C1B2A] mb-1 group-hover:text-[#A78BFA] transition-colors font-['Outfit']">Companies</h3>
            <p className="text-[#8896A5] text-sm">Manage client companies</p>
          </Link>
          <Link to="/assessments" data-testid="view-assessments-btn" className="p-5 glass-card rounded-xl group hover:border-[#34D399]/15">
            <ClipboardCheck size={28} className="text-[#34D399] mb-3" />
            <h3 className="text-base font-semibold text-[#0C1B2A] mb-1 group-hover:text-[#34D399] transition-colors font-['Outfit']">Assessments</h3>
            <p className="text-[#8896A5] text-sm">Review past assessments</p>
          </Link>
        </div>
      </div>
    </Layout>
  );
};

export default DashboardPage;
