import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";
import Layout from "../components/Layout";
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

const LEVEL_NAMES = {
  1: "Ad Hoc",
  2: "Developing",
  3: "Defined",
  4: "Managed",
  5: "Optimising"
};

const DIMENSION_ICONS = {
  people: Users,
  process: ClipboardCheck,
  data: Database,
  technology: Monitor
};

const ReportPage = () => {
  const { id } = useParams();
  const [assessment, setAssessment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    const fetchAssessment = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/assessments/${id}`);
        setAssessment(response.data);
      } catch (err) {
        console.error("Failed to fetch assessment:", err);
        toast.error("Failed to load report");
      } finally {
        setLoading(false);
      }
    };
    fetchAssessment();
  }, [id]);

  const downloadPDF = async () => {
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
  };

  const getScoreColor = (score) => {
    if (score >= 4) return "#2f81f7";
    if (score >= 3) return "#238636";
    if (score >= 2) return "#D29922";
    return "#F85149";
  };

  const getScoreColorClass = (score) => {
    if (score >= 4) return "text-[#2f81f7]";
    if (score >= 3) return "text-[#238636]";
    if (score >= 2) return "text-[#D29922]";
    return "text-[#F85149]";
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

  if (!assessment?.report) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center py-16">
          <AlertTriangle size={64} className="text-[#D29922] mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">Report Not Ready</h2>
          <p className="text-gray-400 mb-6">This assessment hasn't been completed yet.</p>
          <Link
            to={`/assessments/${id}`}
            className="px-6 py-3 bg-[#2f81f7] text-white rounded-lg hover:bg-[#58a6ff] transition-colors"
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
  const dimSummaries = report.dimension_summaries || {};
  
  const radarData = [
    { dimension: "People", score: scores.people || 0, fullMark: 5 },
    { dimension: "Process", score: scores.process || 0, fullMark: 5 },
    { dimension: "Data", score: scores.data || 0, fullMark: 5 },
    { dimension: "Technology", score: scores.technology || 0, fullMark: 5 },
  ];

  const barData = [
    { name: "People", score: scores.people || 0 },
    { name: "Process", score: scores.process || 0 },
    { name: "Data", score: scores.data || 0 },
    { name: "Technology", score: scores.technology || 0 },
  ];

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="flex items-center gap-4">
            <Link
              to="/assessments"
              data-testid="back-to-assessments"
              className="p-2 rounded-lg bg-[#111827] border border-[#374151] text-gray-400 hover:text-white hover:border-[#2f81f7] transition-all"
            >
              <ArrowLeft size={20} />
            </Link>
            <div>
              <h1 className="text-2xl lg:text-3xl font-semibold text-white font-['Outfit'] tracking-tight">
                PPDT Assessment Report
              </h1>
              <p className="text-gray-400 mt-1">
                Based on Hannila's Product Wellbeing Framework (2026)
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to={`/assessments/${id}`}
              data-testid="view-chat-btn"
              className="flex items-center gap-2 px-4 py-2 bg-[#111827] border border-[#374151] text-gray-300 rounded-lg hover:border-[#2f81f7] hover:text-white transition-all"
            >
              <MessageSquare size={18} />
              View Chat
            </Link>
            <button
              onClick={downloadPDF}
              data-testid="download-pdf-btn"
              disabled={downloading}
              className="flex items-center gap-2 px-6 py-3 bg-[#2f81f7] text-white font-medium rounded-lg hover:bg-[#58a6ff] transition-all disabled:opacity-50 btn-premium"
            >
              <Download size={18} />
              {downloading ? "Generating..." : "Export PDF"}
            </button>
          </div>
        </div>

        {/* Company Info Bar */}
        <div className="p-4 bg-[#111827] border border-[#374151] rounded-xl flex flex-wrap items-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <Building2 size={16} className="text-[#2f81f7]" />
            <span className="text-gray-400">Company:</span>
            <span className="text-white font-medium">{assessment.company_name}</span>
          </div>
          <div className="flex items-center gap-2">
            <User size={16} className="text-[#2f81f7]" />
            <span className="text-gray-400">Respondent:</span>
            <span className="text-white">{assessment.respondent_name} ({assessment.respondent_role})</span>
          </div>
          <div className="flex items-center gap-2">
            <Calendar size={16} className="text-[#2f81f7]" />
            <span className="text-gray-400">Date:</span>
            <span className="text-white">{new Date(assessment.completed_at || assessment.created_at).toLocaleDateString()}</span>
          </div>
        </div>

        {/* Overall Score */}
        <div className="p-8 bg-gradient-to-r from-[#111827] to-[#0B1120] border border-[#374151] rounded-xl">
          <div className="flex flex-col lg:flex-row items-center gap-8">
            <div className="text-center lg:text-left flex-1">
              <p className="text-xs uppercase tracking-[0.2em] text-[#2f81f7] mb-2">Overall Maturity Level</p>
              <div className="flex items-baseline gap-4">
                <span 
                  data-testid="overall-score"
                  className={`text-6xl lg:text-7xl font-bold font-['JetBrains_Mono'] ${getScoreColorClass(scores.overall)}`}
                >
                  {scores.overall?.toFixed(1) || "–"}
                </span>
                <span className="text-2xl text-gray-400">/ 5.0</span>
              </div>
              <p className="text-2xl font-semibold text-white mt-2 font-['Outfit']">
                {levelNames.overall || LEVEL_NAMES[Math.round(scores.overall)] || "–"}
              </p>
            </div>
            <div className="w-full lg:w-64 h-64">
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
                    strokeWidth={2}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Dimension Scores */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {["people", "process", "data", "technology"].map((dim) => {
            const Icon = DIMENSION_ICONS[dim];
            const score = scores[dim] || 0;
            return (
              <div 
                key={dim}
                data-testid={`dimension-score-${dim}`}
                className="p-6 bg-[#111827] border border-[#374151] rounded-xl card-hover"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${getScoreColor(score)}20` }}>
                    <Icon size={20} style={{ color: getScoreColor(score) }} />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white capitalize">{dim}</h3>
                    <p className="text-xs text-gray-500">{levelNames[dim] || LEVEL_NAMES[Math.round(score)]}</p>
                  </div>
                </div>
                <div className="flex items-baseline gap-2 mb-3">
                  <span className={`text-3xl font-bold font-['JetBrains_Mono'] ${getScoreColorClass(score)}`}>
                    {score}
                  </span>
                  <span className="text-gray-500">/ 5</span>
                </div>
                <div className="w-full h-2 bg-[#1F2937] rounded-full overflow-hidden">
                  <div 
                    className="h-full rounded-full transition-all duration-500"
                    style={{ 
                      width: `${(score / 5) * 100}%`,
                      backgroundColor: getScoreColor(score)
                    }}
                  />
                </div>
                <p className="mt-4 text-sm text-gray-400 line-clamp-3">
                  {dimSummaries[dim] || "No summary available."}
                </p>
              </div>
            );
          })}
        </div>

        {/* Bar Chart */}
        <div className="p-6 bg-[#111827] border border-[#374151] rounded-xl">
          <h2 className="text-lg font-semibold text-white mb-6 font-['Outfit']">Score Comparison</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} layout="vertical">
                <XAxis type="number" domain={[0, 5]} tick={{ fill: "#9CA3AF" }} />
                <YAxis dataKey="name" type="category" tick={{ fill: "#9CA3AF" }} width={80} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: "#1F2937", 
                    border: "1px solid #374151",
                    borderRadius: "8px"
                  }}
                />
                <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                  {barData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getScoreColor(entry.score)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Key Findings & Critical Gaps */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="p-6 bg-[#111827] border border-[#374151] rounded-xl">
            <div className="flex items-center gap-2 mb-4">
              <Target size={20} className="text-[#2f81f7]" />
              <h2 className="text-lg font-semibold text-white font-['Outfit']">Key Findings</h2>
            </div>
            <ul className="space-y-3">
              {(report.key_findings || []).map((finding, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <span className="w-6 h-6 rounded-full bg-[#2f81f7]/20 text-[#2f81f7] flex items-center justify-center text-xs shrink-0 mt-0.5">
                    {idx + 1}
                  </span>
                  <p className="text-gray-300 text-sm">{finding}</p>
                </li>
              ))}
            </ul>
          </div>

          <div className="p-6 bg-[#111827] border border-[#374151] rounded-xl">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle size={20} className="text-[#F85149]" />
              <h2 className="text-lg font-semibold text-white font-['Outfit']">Critical Capability Gaps</h2>
            </div>
            <ul className="space-y-3">
              {(report.critical_gaps || []).map((gap, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <span className="w-6 h-6 rounded-full bg-[#F85149]/20 text-[#F85149] flex items-center justify-center text-xs shrink-0 mt-0.5">
                    !
                  </span>
                  <p className="text-gray-300 text-sm">{gap}</p>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Decision Vulnerability */}
        <div className="p-6 bg-[#111827] border border-[#374151] rounded-xl">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle size={20} className="text-[#D29922]" />
            <h2 className="text-lg font-semibold text-white font-['Outfit']">Decision-Type Vulnerability Analysis</h2>
          </div>
          <p className="text-gray-300">{report.decision_vulnerability || "No analysis available."}</p>
        </div>

        {/* Improvement Roadmap */}
        <div className="p-6 bg-[#111827] border border-[#374151] rounded-xl">
          <div className="flex items-center gap-2 mb-6">
            <TrendingUp size={20} className="text-[#238636]" />
            <h2 className="text-lg font-semibold text-white font-['Outfit']">Improvement Roadmap</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-4 bg-[#0B1120] rounded-lg border border-[#374151]">
              <h3 className="text-sm uppercase tracking-wider text-[#2f81f7] mb-3">Immediate (0-3 months)</h3>
              <ul className="space-y-2">
                {(report.roadmap?.immediate || []).map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-gray-300">
                    <span className="text-[#2f81f7]">→</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="p-4 bg-[#0B1120] rounded-lg border border-[#374151]">
              <h3 className="text-sm uppercase tracking-wider text-[#238636] mb-3">Short-term (3-12 months)</h3>
              <ul className="space-y-2">
                {(report.roadmap?.short_term || []).map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-gray-300">
                    <span className="text-[#238636]">→</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="p-4 bg-[#0B1120] rounded-lg border border-[#374151]">
              <h3 className="text-sm uppercase tracking-wider text-[#A371F7] mb-3">Strategic (12-24 months)</h3>
              <ul className="space-y-2">
                {(report.roadmap?.strategic || []).map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-gray-300">
                    <span className="text-[#A371F7]">→</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Benchmark & Consultant Note */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="p-6 bg-[#111827] border border-[#374151] rounded-xl">
            <h2 className="text-lg font-semibold text-white mb-4 font-['Outfit']">Benchmark Context</h2>
            <p className="text-gray-300">{report.benchmark_context || "No benchmark data available."}</p>
          </div>

          <div className="p-6 bg-gradient-to-br from-[#2f81f7]/10 to-[#111827] border border-[#2f81f7]/30 rounded-xl">
            <h2 className="text-lg font-semibold text-white mb-4 font-['Outfit']">Consultant's Note</h2>
            <p className="text-gray-200 italic">"{report.consultant_note || "No consultant note available."}"</p>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center py-8 border-t border-[#374151]">
          <p className="text-sm text-gray-500">
            Based on Hannila's Product Wellbeing Framework (2026) · University of Oulu Research
          </p>
        </div>
      </div>
    </Layout>
  );
};

export default ReportPage;
