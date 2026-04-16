import { useState, useEffect } from "react";
import { useParams, useLocation, Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../App";
import { 
  Download,
  ArrowRight,
  Users,
  ClipboardCheck,
  Database,
  Monitor,
  Save,
  CheckCircle,
  AlertTriangle,
  AlertCircle
} from "lucide-react";
import { toast } from "sonner";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer
} from "recharts";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const DIMENSION_ICONS = {
  people: Users,
  process: ClipboardCheck,
  data: Database,
  technology: Monitor
};

const QuickResultsPage = () => {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [result, setResult] = useState(location.state?.result || null);
  const [loading, setLoading] = useState(!location.state?.result);
  const [downloading, setDownloading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!result && id) {
      const fetchResult = async () => {
        try {
          const response = await axios.get(`${BACKEND_URL}/api/quick-assessment/${id}`);
          setResult(response.data);
          setSaved(response.data.saved);
        } catch (err) {
          console.error("Failed to fetch results:", err);
          toast.error("Failed to load assessment results");
          navigate("/quick-assessment");
        } finally {
          setLoading(false);
        }
      };
      fetchResult();
    }
  }, [id, result, navigate]);

  const downloadPDF = async () => {
    setDownloading(true);
    try {
      const response = await axios.get(`${BACKEND_URL}/api/quick-assessment/${id}/pdf`, {
        responseType: "blob"
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `PPDT_Quick_Health_Check_${result?.company_name?.replace(/\s+/g, "_")}.pdf`);
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

  const saveToAccount = async () => {
    if (!user) {
      toast.info("Please sign in to save this assessment");
      navigate("/login", { state: { returnTo: `/quick-assessment/${id}/results` } });
      return;
    }
    
    setSaving(true);
    try {
      await axios.post(`${BACKEND_URL}/api/quick-assessment/${id}/save`);
      setSaved(true);
      toast.success("Assessment saved to your account");
    } catch (err) {
      console.error("Failed to save:", err);
      toast.error("Failed to save assessment");
    } finally {
      setSaving(false);
    }
  };

  const getTrafficLightIcon = (status) => {
    if (status === "green") return <CheckCircle size={20} className="text-[#238636]" />;
    if (status === "amber") return <AlertTriangle size={20} className="text-[#D29922]" />;
    return <AlertCircle size={20} className="text-[#F85149]" />;
  };

  const getTrafficLightBg = (status) => {
    if (status === "green") return "bg-[#238636]/20 border-[#238636]/30";
    if (status === "amber") return "bg-[#D29922]/20 border-[#D29922]/30";
    return "bg-[#F85149]/20 border-[#F85149]/30";
  };

  const getScoreColor = (score) => {
    if (score >= 4) return "#2f81f7";
    if (score >= 3) return "#238636";
    if (score >= 2) return "#D29922";
    return "#F85149";
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0B1120] flex items-center justify-center">
        <div className="animate-pulse-glow w-12 h-12 rounded-full bg-[#2f81f7]/20 flex items-center justify-center">
          <div className="w-6 h-6 rounded-full bg-[#2f81f7]" />
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="min-h-screen bg-[#0B1120] flex flex-col items-center justify-center">
        <p className="text-gray-400 mb-4">Assessment not found</p>
        <Link to="/quick-assessment" className="text-[#2f81f7] hover:text-[#58a6ff]">
          Start a new assessment
        </Link>
      </div>
    );
  }

  const scores = result.scores || {};
  const trafficLights = result.traffic_lights || {};
  const levelNames = result.level_names || {};

  const radarData = [
    { dimension: "People", score: scores.people || 0, fullMark: 5 },
    { dimension: "Process", score: scores.process || 0, fullMark: 5 },
    { dimension: "Data", score: scores.data || 0, fullMark: 5 },
    { dimension: "Technology", score: scores.technology || 0, fullMark: 5 },
  ];

  return (
    <div className="min-h-screen bg-[#0B1120]">
      {/* Header */}
      <header className="h-16 border-b border-[#374151] bg-[#111827] flex items-center px-6">
        <Link
          to="/"
          className="flex items-center gap-3"
        >
          <div className="w-8 h-8 rounded-lg bg-[#2f81f7] flex items-center justify-center">
            <span className="text-white font-bold text-sm">P</span>
          </div>
          <span className="text-white font-semibold font-['Outfit']">PPDT Advisor</span>
        </Link>
        
        <div className="flex-1" />
        
        <div className="flex items-center gap-3">
          {!saved && (
            <button
              onClick={saveToAccount}
              disabled={saving}
              data-testid="save-assessment-btn"
              className="flex items-center gap-2 px-4 py-2 bg-[#111827] border border-[#374151] text-gray-300 rounded-lg hover:border-[#2f81f7] hover:text-white transition-all disabled:opacity-50"
            >
              <Save size={16} />
              {saving ? "Saving..." : "Save to Account"}
            </button>
          )}
          {saved && (
            <span className="flex items-center gap-2 px-4 py-2 text-[#238636]">
              <CheckCircle size={16} />
              Saved
            </span>
          )}
          <button
            onClick={downloadPDF}
            disabled={downloading}
            data-testid="download-quick-pdf-btn"
            className="flex items-center gap-2 px-5 py-2 bg-[#2f81f7] text-white rounded-lg hover:bg-[#58a6ff] transition-colors disabled:opacity-50"
          >
            <Download size={16} />
            {downloading ? "Generating..." : "Export PDF"}
          </button>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 py-12">
        {/* Title */}
        <div className="text-center mb-12 animate-fade-in">
          <h1 className="text-3xl font-semibold text-white font-['Outfit'] tracking-tight mb-2">
            PPDT Quick Health Check Results
          </h1>
          <p className="text-gray-400">{result.company_name} · {result.industry}</p>
        </div>

        {/* Overall Score */}
        <div className="p-8 bg-gradient-to-r from-[#111827] to-[#0B1120] border border-[#374151] rounded-2xl mb-8 animate-fade-in" style={{ animationDelay: "0.1s" }}>
          <div className="flex flex-col lg:flex-row items-center gap-8">
            <div className="text-center lg:text-left flex-1">
              <p className="text-xs uppercase tracking-[0.2em] text-gray-400 mb-2">Overall Maturity</p>
              <div className="flex items-baseline gap-3 justify-center lg:justify-start">
                <span 
                  data-testid="quick-overall-score"
                  className="text-6xl font-bold font-['JetBrains_Mono']"
                  style={{ color: getScoreColor(scores.overall) }}
                >
                  {scores.overall?.toFixed(1) || "–"}
                </span>
                <span className="text-2xl text-gray-500">/ 5.0</span>
              </div>
              <p className="text-xl font-semibold text-white mt-2 font-['Outfit']">
                {levelNames.overall || "–"}
              </p>
              <div className={`inline-flex items-center gap-2 mt-4 px-4 py-2 rounded-full border ${getTrafficLightBg(trafficLights.overall)}`}>
                {getTrafficLightIcon(trafficLights.overall)}
                <span className="text-sm font-medium text-white capitalize">{trafficLights.overall} Status</span>
              </div>
            </div>
            <div className="w-full lg:w-72 h-72">
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

        {/* Dimension Scores with Traffic Lights */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          {["people", "process", "data", "technology"].map((dim, idx) => {
            const Icon = DIMENSION_ICONS[dim];
            const score = scores[dim] || 0;
            const traffic = trafficLights[dim] || "red";
            const level = levelNames[dim] || "Unknown";
            
            return (
              <div 
                key={dim}
                data-testid={`quick-dimension-${dim}`}
                className={`p-5 bg-[#111827] border rounded-xl animate-fade-in flex items-center gap-4 ${getTrafficLightBg(traffic)}`}
                style={{ animationDelay: `${0.2 + idx * 0.1}s` }}
              >
                <div className="w-12 h-12 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${getScoreColor(score)}20` }}>
                  <Icon size={24} style={{ color: getScoreColor(score) }} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-semibold text-white capitalize">{dim}</h3>
                    {getTrafficLightIcon(traffic)}
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-bold font-['JetBrains_Mono']" style={{ color: getScoreColor(score) }}>
                      {score}
                    </span>
                    <span className="text-gray-500">/ 5</span>
                    <span className="text-sm text-gray-400 ml-2">· {level}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* CTA Box */}
        <div className="p-8 bg-gradient-to-br from-[#2f81f7]/10 to-[#111827] border border-[#2f81f7]/30 rounded-2xl animate-fade-in" style={{ animationDelay: "0.6s" }}>
          <h2 className="text-xl font-semibold text-white mb-4 font-['Outfit']">
            Ready for a Deeper Assessment?
          </h2>
          <p className="text-gray-300 mb-6">
            {result.cta_message}
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
            <Link
              to={user ? "/assessments" : "/register"}
              data-testid="start-full-assessment-cta"
              className="flex items-center justify-center gap-2 px-6 py-3 bg-[#2f81f7] text-white font-medium rounded-lg hover:bg-[#58a6ff] transition-colors"
            >
              {user ? "Start Full Assessment" : "Create Account to Start"}
              <ArrowRight size={18} />
            </Link>
            <Link
              to="/"
              className="flex items-center justify-center gap-2 px-6 py-3 bg-[#111827] border border-[#374151] text-gray-300 rounded-lg hover:border-[#2f81f7] hover:text-white transition-colors"
            >
              Back to Home
            </Link>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center py-8 mt-8 border-t border-[#374151]">
          <p className="text-sm text-gray-500">
            Based on Hannila's Product Wellbeing Framework (2026) · University of Oulu Research
          </p>
        </div>
      </div>
    </div>
  );
};

export default QuickResultsPage;
