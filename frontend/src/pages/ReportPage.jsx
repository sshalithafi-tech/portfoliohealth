import { useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";
import Layout from "../components/Layout";
import { useAssessment } from "../hooks/useData";
import { 
  getScoreColor, 
  getScoreColorClass, 
  prepareRadarData, 
  prepareBarData,
  LEVEL_NAMES
} from "../utils/scoring";
import { 
  LoadingSpinner, 
  NumberedListItem, 
  AlertListItem, 
  ArrowListItem 
} from "../components/ScoreComponents";
import { 
  ArrowLeft,
  Download,
  Building2,
  User,
  Calendar,
  Users,
  ClipboardCheck,
  Database,
  Monitor,
  AlertTriangle,
  Target,
  TrendingUp,
  MessageSquare
} from "lucide-react";
import { toast } from "sonner";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Cell,
  Tooltip
} from "recharts";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const DIMENSION_ICONS = {
  people: Users, process: ClipboardCheck, data: Database, technology: Monitor
};

const DIMENSIONS = ["people", "process", "data", "technology"];

const DimensionScoreCard = ({ dimension, score, levelName }) => {
  const Icon = DIMENSION_ICONS[dimension];
  const color = getScoreColor(score);
  
  return (
    <div 
      data-testid={`dimension-score-${dimension}`}
      className="p-4 sm:p-6 glass-card rounded-xl"
    >
      <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-4">
        <div 
          className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg flex items-center justify-center shrink-0" 
          style={{ backgroundColor: `${color}15` }}
        >
          <Icon size={16} style={{ color }} className="sm:hidden" />
          <Icon size={20} style={{ color }} className="hidden sm:block" />
        </div>
        <div className="min-w-0">
          <h3 className="text-sm sm:text-lg font-semibold text-white capitalize font-['Outfit'] truncate">{dimension}</h3>
          <p className="text-[10px] sm:text-xs text-white/40 truncate">{levelName}</p>
        </div>
      </div>
      <div className="flex items-baseline gap-1 sm:gap-2 mb-2 sm:mb-3">
        <span className={`text-xl sm:text-3xl font-bold font-['JetBrains_Mono'] ${getScoreColorClass(score)}`}>
          {score}
        </span>
        <span className="text-white/30 text-xs sm:text-base">/ 5</span>
      </div>
      <div className="w-full h-1.5 sm:h-2 bg-white/[0.06] rounded-full overflow-hidden">
        <div 
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${(score / 5) * 100}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
};

const RoadmapSection = ({ title, items, color }) => (
  <div className="p-4 glass-surface rounded-xl">
    <h3 className="text-sm uppercase tracking-wider mb-3 font-['Outfit']" style={{ color }}>{title}</h3>
    <ul className="space-y-2">
      {(items || []).map((item, idx) => (
        <ArrowListItem key={`roadmap-${title}-${idx}`} color={color}>
          {item}
        </ArrowListItem>
      ))}
    </ul>
  </div>
);

const ReportPage = () => {
  const { id } = useParams();
  const { assessment, loading } = useAssessment(id);
  const [downloading, setDownloading] = useState(false);

  const downloadPDF = useCallback(async () => {
    setDownloading(true);
    try {
      const response = await axios.get(`${BACKEND_URL}/api/assessments/${id}/pdf`, {
        responseType: "blob"
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `PPDT_Assessment_${assessment?.company_name?.replace(/\s+/g, "_")}_${id.slice(0, 8)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success("PDF downloaded successfully");
    } catch (err) {
      console.error("Failed to download PDF:", err);
      toast.error("Failed to download PDF");
    } finally {
      setDownloading(false);
    }
  }, [id, assessment?.company_name]);

  if (loading) {
    return (
      <Layout>
        <LoadingSpinner className="h-64" />
      </Layout>
    );
  }

  if (!assessment?.report) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center py-16">
          <AlertTriangle size={64} className="text-[#D29922] mb-4 opacity-50" />
          <h2 className="text-xl font-semibold text-white mb-2 font-['Outfit']">Report Not Ready</h2>
          <p className="text-white/50 mb-6">This assessment hasn't been completed yet.</p>
          <Link
            to={`/assessments/${id}`}
            className="px-6 py-3 btn-liquid rounded-xl"
          >
            Continue Assessment
          </Link>
        </div>
      </Layout>
    );
  }

  const report = assessment.report;
  const scores = report.scores || {};
  const levelNames = report.level_names || {};
  const radarData = prepareRadarData(scores);
  const barData = prepareBarData(scores);

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col gap-4">
          <div className="flex items-start gap-3 sm:gap-4">
            <Link
              to="/assessments"
              data-testid="back-to-assessments"
              className="p-2 rounded-xl glass-surface text-white/50 hover:text-white hover:border-[#00E5FF]/20 transition-all shrink-0 mt-1"
            >
              <ArrowLeft size={18} />
            </Link>
            <div>
              <h1 className="text-xl sm:text-2xl lg:text-3xl font-semibold text-white font-['Outfit'] tracking-tight">
                PPDT Assessment Report
              </h1>
              <p className="text-white/40 mt-1 text-xs sm:text-sm">
                Based on: PPM Capability Maturity Research · University of Oulu (2026)
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <Link
              to={`/assessments/${id}`}
              data-testid="view-chat-btn"
              className="flex items-center gap-2 px-3 sm:px-4 py-2 btn-glass rounded-xl text-sm"
            >
              <MessageSquare size={16} />
              <span className="hidden sm:inline">View Chat</span>
              <span className="sm:hidden">Chat</span>
            </Link>
            <button
              onClick={downloadPDF}
              data-testid="download-pdf-btn"
              disabled={downloading}
              className="flex items-center gap-2 px-4 sm:px-6 py-2 sm:py-3 btn-liquid rounded-xl disabled:opacity-50 text-sm"
            >
              <Download size={16} />
              {downloading ? "..." : "Export PDF"}
            </button>
          </div>
        </div>

        {/* Company Info Bar */}
        <div className="p-3 sm:p-4 glass-surface-highlight rounded-xl flex flex-col sm:flex-row sm:flex-wrap items-start sm:items-center gap-3 sm:gap-6 text-sm">
          <div className="flex items-center gap-2">
            <Building2 size={16} className="text-[#00E5FF]" />
            <span className="text-white/50">Company:</span>
            <span className="text-white font-medium">{assessment.company_name}</span>
          </div>
          <div className="flex items-center gap-2">
            <User size={16} className="text-[#00E5FF]" />
            <span className="text-white/50">Respondent:</span>
            <span className="text-white">{assessment.respondent_name} ({assessment.respondent_role})</span>
          </div>
          <div className="flex items-center gap-2">
            <Calendar size={16} className="text-[#00E5FF]" />
            <span className="text-white/50">Date:</span>
            <span className="text-white">{new Date(assessment.completed_at || assessment.created_at).toLocaleDateString()}</span>
          </div>
        </div>

        {/* Overall Score */}
        <div className="p-6 sm:p-8 glass-surface-highlight rounded-2xl">
          <div className="flex flex-col items-center gap-6 sm:gap-8 lg:flex-row">
            <div className="text-center lg:text-left flex-1">
              <p className="text-xs uppercase tracking-[0.2em] text-[#00E5FF] mb-2">Overall Maturity Level</p>
              <div className="flex items-baseline gap-3 sm:gap-4 justify-center lg:justify-start">
                <span 
                  data-testid="overall-score"
                  className={`text-5xl sm:text-6xl lg:text-7xl font-bold font-['JetBrains_Mono'] ${getScoreColorClass(scores.overall)}`}
                >
                  {scores.overall?.toFixed(1) || "–"}
                </span>
                <span className="text-2xl text-white/30">/ 5.0</span>
              </div>
              <p className="text-2xl font-semibold text-white mt-2 font-['Outfit']">
                {levelNames.overall || LEVEL_NAMES[Math.round(scores.overall)] || "–"}
              </p>
            </div>
            <div className="w-full lg:w-64 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke="rgba(255,255,255,0.08)" />
                  <PolarAngleAxis dataKey="dimension" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 12 }} />
                  <PolarRadiusAxis domain={[0, 5]} tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 10 }} />
                  <Radar
                    name="Score"
                    dataKey="score"
                    stroke="#00E5FF"
                    fill="#00E5FF"
                    fillOpacity={0.15}
                    strokeWidth={2}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Dimension Scores */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6">
          {DIMENSIONS.map((dim) => (
            <DimensionScoreCard
              key={dim}
              dimension={dim}
              score={scores[dim] || 0}
              levelName={levelNames[dim] || LEVEL_NAMES[Math.round(scores[dim] || 0)]}
            />
          ))}
        </div>

        {/* Bar Chart */}
        <div className="p-6 glass-surface-highlight rounded-xl">
          <h2 className="text-lg font-semibold text-white mb-6 font-['Outfit']">Score Comparison</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} layout="vertical">
                <XAxis type="number" domain={[0, 5]} tick={{ fill: "rgba(255,255,255,0.5)" }} />
                <YAxis dataKey="name" type="category" tick={{ fill: "rgba(255,255,255,0.5)" }} width={80} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: "rgba(5,5,10,0.9)", 
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: "12px",
                    backdropFilter: "blur(12px)"
                  }}
                />
                <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                  {barData.map((entry) => (
                    <Cell key={`bar-${entry.name}`} fill={getScoreColor(entry.score)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Key Findings & Critical Gaps */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="p-6 glass-surface-highlight rounded-xl">
            <div className="flex items-center gap-2 mb-4">
              <Target size={20} className="text-[#00E5FF]" />
              <h2 className="text-lg font-semibold text-white font-['Outfit']">Key Findings</h2>
            </div>
            <ul className="space-y-3">
              {(report.key_findings || []).map((finding, idx) => (
                <NumberedListItem key={`finding-${idx}`} index={idx} color="#00E5FF">
                  {finding}
                </NumberedListItem>
              ))}
            </ul>
          </div>

          <div className="p-6 glass-surface-highlight rounded-xl">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle size={20} className="text-[#F85149]" />
              <h2 className="text-lg font-semibold text-white font-['Outfit']">Critical Capability Gaps</h2>
            </div>
            <ul className="space-y-3">
              {(report.critical_gaps || []).map((gap, idx) => (
                <AlertListItem key={`gap-${idx}`}>
                  {gap}
                </AlertListItem>
              ))}
            </ul>
          </div>
        </div>

        {/* Decision Vulnerability */}
        <div className="p-6 glass-surface-highlight rounded-xl">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle size={20} className="text-[#D29922]" />
            <h2 className="text-lg font-semibold text-white font-['Outfit']">Decision-Type Vulnerability Analysis</h2>
          </div>
          <p className="text-white/60">{report.decision_vulnerability || "No analysis available."}</p>
        </div>

        {/* Improvement Roadmap */}
        <div className="p-6 glass-surface-highlight rounded-xl">
          <div className="flex items-center gap-2 mb-6">
            <TrendingUp size={20} className="text-[#238636]" />
            <h2 className="text-lg font-semibold text-white font-['Outfit']">Improvement Roadmap</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <RoadmapSection title="Immediate (0-3 months)" items={report.roadmap?.immediate} color="#00E5FF" />
            <RoadmapSection title="Short-term (3-12 months)" items={report.roadmap?.short_term} color="#238636" />
            <RoadmapSection title="Strategic (12-24 months)" items={report.roadmap?.strategic} color="#A371F7" />
          </div>
        </div>

        {/* Benchmark & Consultant Note */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="p-6 glass-surface-highlight rounded-xl">
            <h2 className="text-lg font-semibold text-white mb-4 font-['Outfit']">Benchmark Context</h2>
            <p className="text-white/60">{report.benchmark_context || "No benchmark data available."}</p>
          </div>

          <div className="p-6 glass-card rounded-xl hover:border-[#00E5FF]/20">
            <h2 className="text-lg font-semibold text-white mb-4 font-['Outfit']">Consultant's Note</h2>
            <p className="text-white/70 italic">"{report.consultant_note || "No consultant note available."}"</p>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center py-8 border-t border-white/[0.06]">
          <p className="text-sm text-white/30">
            Based on: PPM Capability Maturity Research · University of Oulu (2026)
          </p>
        </div>
      </div>
    </Layout>
  );
};

export default ReportPage;
