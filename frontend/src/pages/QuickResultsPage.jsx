import { useState, useCallback } from "react";
import { useParams, useLocation, Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../App";
import { useQuickAssessmentResult } from "../hooks/useData";
import { 
  getScoreColor, 
  getScoreColorClass,
  getTrafficLightBgClass
} from "../utils/scoring";
import { 
  LoadingSpinner, 
  TrafficLightIcon 
} from "../components/ScoreComponents";
import { 
  Download,
  ArrowRight,
  Users,
  ClipboardCheck,
  Database,
  Monitor,
  Save,
  CheckCircle
} from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const DIMENSION_ICONS = {
  people: Users, process: ClipboardCheck, data: Database, technology: Monitor
};

const DIMENSIONS = ["people", "process", "data", "technology"];

const DimensionCard = ({ dimension, score, traffic, level }) => {
  const Icon = DIMENSION_ICONS[dimension];
  const color = getScoreColor(score);
  
  return (
    <div 
      data-testid={`quick-dimension-${dimension}`}
      className={`p-5 glass-card rounded-xl animate-fade-in flex items-center gap-4 ${getTrafficLightBgClass(traffic)}`}
    >
      <div 
        className="w-12 h-12 rounded-lg flex items-center justify-center" 
        style={{ backgroundColor: `${color}15` }}
      >
        <Icon size={24} style={{ color }} />
      </div>
      <div className="flex-1">
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-semibold text-white capitalize font-['Outfit']">{dimension}</h3>
          <TrafficLightIcon status={traffic} size={20} />
        </div>
        <div className="flex items-baseline gap-2">
          <span 
            className="text-2xl font-bold font-['JetBrains_Mono']" 
            style={{ color }}
          >
            {score}
          </span>
          <span className="text-white/30">/ 5</span>
          <span className="text-sm text-white/40 ml-2">· {level}</span>
        </div>
      </div>
    </div>
  );
};

const QuickResultsPage = () => {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const { result, loading, saved, setSaved } = useQuickAssessmentResult(id, location.state?.result);
  const [downloading, setDownloading] = useState(false);
  const [saving, setSaving] = useState(false);

  const downloadPDF = useCallback(async () => {
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
  }, [id, result?.company_name]);

  const saveToAccount = useCallback(async () => {
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
  }, [id, user, navigate, setSaved]);

  if (loading) {
    return (
      <div className="min-h-screen">
        <LoadingSpinner className="min-h-screen" />
      </div>
    );
  }

  if (!result) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center">
        <p className="text-white/50 mb-4">Assessment not found</p>
        <Link to="/quick-assessment" className="text-[#C9A84C] hover:text-[#C9A84C]/80">
          Start a new assessment
        </Link>
      </div>
    );
  }

  const scores = result.scores || {};
  const trafficLights = result.traffic_lights || {};
  const levelNames = result.level_names || {};

  return (
    <div className="min-h-screen">
      {/* Glass Header */}
      <header className="h-14 sm:h-16 glass-surface flex items-center px-4 sm:px-6 relative z-10">
        <Link to="/" className="flex items-center gap-2 sm:gap-3">
          <img src="https://static.prod-images.emergentagent.com/jobs/ad26f002-f220-4b9d-b343-979dba7f2367/images/52f8bbaa7bef05bb75194db309bc570b7ebaa50def42d7c4be946a17056a8065.png" alt="PH" className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg object-contain" />
          <span className="text-white font-semibold font-['Outfit'] text-sm sm:text-base">PortfolioHealth</span>
        </Link>
        
        <div className="flex-1" />
        
        <div className="flex items-center gap-2 sm:gap-3">
          {!saved ? (
            <button
              onClick={saveToAccount}
              disabled={saving}
              data-testid="save-assessment-btn"
              className="flex items-center gap-1 sm:gap-2 px-3 sm:px-4 py-2 btn-glass rounded-xl disabled:opacity-50 text-xs sm:text-sm"
            >
              <Save size={14} />
              <span className="hidden sm:inline">{saving ? "Saving..." : "Save to Account"}</span>
              <span className="sm:hidden">{saving ? "..." : "Save"}</span>
            </button>
          ) : (
            <span className="flex items-center gap-1 sm:gap-2 px-3 sm:px-4 py-2 text-[#34D399] text-xs sm:text-sm">
              <CheckCircle size={14} />
              Saved
            </span>
          )}
          <button
            onClick={downloadPDF}
            disabled={downloading}
            data-testid="download-quick-pdf-btn"
            className="flex items-center gap-1 sm:gap-2 px-3 sm:px-5 py-2 btn-liquid rounded-xl disabled:opacity-50 text-xs sm:text-sm"
          >
            <Download size={14} />
            <span className="hidden sm:inline">{downloading ? "Generating..." : "Export PDF"}</span>
            <span className="sm:hidden">{downloading ? "..." : "PDF"}</span>
          </button>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 py-12 relative z-10">
        {/* Title */}
        <div className="text-center mb-12 animate-fade-in">
          <h1 className="text-3xl font-semibold text-white font-['Outfit'] tracking-tight mb-2">
            PPDT Quick Health Check Results
          </h1>
          <p className="text-white/50">{result.company_name} · {result.industry}</p>
        </div>

        {/* Overall Score */}
        <div className="p-6 sm:p-8 glass-surface-highlight rounded-2xl mb-8 animate-fade-in">
          <div className="text-center mb-6">
            <p className="text-xs uppercase tracking-[0.2em] text-white/40 mb-2">Overall Maturity</p>
            <span data-testid="quick-overall-score" className="text-5xl sm:text-6xl font-bold font-['JetBrains_Mono']" style={{ color: getScoreColor(scores.overall) }}>
              {scores.overall?.toFixed(1) || "–"}
            </span>
            <span className="text-xl text-white/30 ml-2">/ 5.0</span>
            <p className="text-lg font-semibold text-white mt-2 font-['Outfit']">{levelNames.overall || "–"}</p>
            <div className={`inline-flex items-center gap-2 mt-3 px-4 py-1.5 rounded-full border ${getTrafficLightBgClass(trafficLights.overall)}`}>
              <TrafficLightIcon status={trafficLights.overall} size={14} />
              <span className="text-sm text-white capitalize">{trafficLights.overall} Status</span>
            </div>
          </div>
          {/* Dimension bars */}
          <div className="space-y-3 max-w-lg mx-auto">
            {DIMENSIONS.map(dim => {
              const s = scores[dim] || 0;
              const color = getScoreColor(s);
              return (
                <div key={`bar-${dim}`} className="flex items-center gap-3">
                  <span className="text-sm text-white/50 w-24 capitalize">{dim}</span>
                  <div className="flex-1 h-2.5 bg-white/[0.06] rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-700" style={{ width: `${(s / 5) * 100}%`, backgroundColor: color }} />
                  </div>
                  <span className={`font-['JetBrains_Mono'] font-semibold text-sm w-8 text-right ${getScoreColorClass(s)}`}>{s.toFixed(1)}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Dimension Scores */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          {DIMENSIONS.map((dim) => (
            <DimensionCard
              key={dim}
              dimension={dim}
              score={scores[dim] || 0}
              traffic={trafficLights[dim] || "red"}
              level={levelNames[dim] || "Unknown"}
            />
          ))}
        </div>

        {/* CTA Box */}
        <div className="p-6 sm:p-8 glass-card rounded-2xl animate-fade-in hover:border-[#C9A84C]/20">
          <h2 className="text-lg sm:text-xl font-semibold text-white mb-3 sm:mb-4 font-['Outfit']">
            Ready for a Deeper Assessment?
          </h2>
          <p className="text-white/60 mb-6">
            {result.cta_message}
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
            <Link
              to={user ? "/assessments" : "/register"}
              data-testid="start-full-assessment-cta"
              className="flex items-center justify-center gap-2 px-6 py-3 btn-liquid rounded-xl"
            >
              {user ? "Start Full Assessment" : "Create Account to Start"}
              <ArrowRight size={18} />
            </Link>
            <Link
              to="/"
              className="flex items-center justify-center gap-2 px-6 py-3 btn-glass rounded-xl"
            >
              Back to Home
            </Link>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center py-8 mt-8 border-t border-white/[0.06]">
          <p className="text-sm text-white/30">
            Based on: PPM Capability Maturity Research · University of Oulu (2026)
          </p>
        </div>
      </div>
    </div>
  );
};

export default QuickResultsPage;
