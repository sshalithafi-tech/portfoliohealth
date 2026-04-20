import { useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";
import Layout from "../components/Layout";
import { useAssessment } from "../hooks/useData";
import { getScoreColor, getScoreColorClass, LEVEL_NAMES } from "../utils/scoring";
import { LoadingSpinner } from "../components/ScoreComponents";
import {
  ArrowLeft, Download, Building2, User, Calendar,
  Users, ClipboardCheck, Database, Monitor,
  AlertTriangle, Target, TrendingUp, MessageSquare,
  Shield, ArrowUpRight, ChevronDown, ChevronUp, Info
} from "lucide-react";
import { toast } from "sonner";
import {
  BarChart, Bar, XAxis, YAxis, Cell, Tooltip, Legend,
  ResponsiveContainer, LabelList
} from "recharts";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const CONTACT_EMAIL = "shalitha.samarakoonmudiyanselage@student.oulu.fi";
const DIMENSIONS = ["people", "process", "data", "technology"];
const DIM_ICONS = { people: Users, process: ClipboardCheck, data: Database, technology: Monitor };

const MATURITY_LEVELS = [
  { level: 1, name: "Ad Hoc", desc: "No structured approach. Decisions are reactive, informal, and based on individual intuition. Data is fragmented; processes are undefined.", color: "#EF4444" },
  { level: 2, name: "Developing", desc: "Some processes are defined but inconsistently applied. Basic data collection exists but lacks integration. People have varying levels of PPM understanding.", color: "#C9A84C" },
  { level: 3, name: "Defined", desc: "Structured processes and roles are established. Data is accessible but not fully integrated. A common language around portfolio management is forming.", color: "#C9A84C" },
  { level: 4, name: "Managed", desc: "Data-driven decisions are supported by integrated systems. Metrics and KPIs are actively tracked and used in governance. Decisions are traceable.", color: "#34D399" },
  { level: 5, name: "Optimizing", desc: "Continuous improvement culture embedded. All four PPDT dimensions fully aligned. PPM decisions are fully fact-based, real-time, and strategically integrated.", color: "#C9A84C" },
];

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-heavy rounded-lg px-3 py-2 text-xs border border-white/10">
      <p className="text-white font-medium mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>{p.name}: {p.value.toFixed(2)}</p>
      ))}
    </div>
  );
};

const ReportPage = () => {
  const { id } = useParams();
  const { assessment, loading } = useAssessment(id);
  const [downloading, setDownloading] = useState(false);
  const [showMethodology, setShowMethodology] = useState(false);

  const downloadPDF = useCallback(async () => {
    setDownloading(true);
    try {
      const response = await axios.get(`${BACKEND_URL}/api/assessments/${id}/pdf`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `PPDT_Assessment_${assessment?.company_name?.replace(/\s+/g, "_")}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("PDF downloaded");
    } catch { toast.error("Failed to download PDF"); }
    finally { setDownloading(false); }
  }, [id, assessment?.company_name]);

  if (loading) return <Layout><LoadingSpinner className="h-64" /></Layout>;

  if (!assessment?.report) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center py-16">
          <AlertTriangle size={64} className="text-[#C9A84C] mb-4 opacity-50" />
          <h2 className="text-xl font-semibold text-white mb-2 font-['Outfit']">Report Not Ready</h2>
          <p className="text-white/50 mb-6">This assessment hasn't been completed yet.</p>
          <Link to={`/assessments/${id}`} className="px-6 py-3 btn-liquid rounded-xl">Continue Assessment</Link>
        </div>
      </Layout>
    );
  }

  const report = assessment.report;
  const scores = report.scores || {};
  const levelNames = report.level_names || {};
  const weightsRaw = report.weights_raw || { people: 5, process: 5, data: 5, technology: 5 };
  const rawTotal = Object.values(weightsRaw).reduce((a, b) => a + b, 0) || 1;
  const weightsNorm = report.weights_normalised || Object.fromEntries(
    DIMENSIONS.map(d => [d, (weightsRaw[d] || 5) / rawTotal])
  );
  const overallLevel = Math.round(scores.overall || 0);

  // Chart data
  const chartData = DIMENSIONS.map(d => ({
    name: d.charAt(0).toUpperCase() + d.slice(1),
    rawScore: scores[d] || 0,
    weightedContribution: parseFloat(((scores[d] || 0) * (weightsNorm[d] || 0.25)).toFixed(2)),
  }));

  return (
    <Layout>
      <div className="space-y-6 sm:space-y-8">
        {/* Header */}
        <div className="flex flex-col gap-4">
          <div className="flex items-start gap-3">
            <Link to="/assessments" className="p-2 rounded-xl glass-surface text-white/50 hover:text-white transition-all shrink-0 mt-1">
              <ArrowLeft size={18} />
            </Link>
            <div>
              <h1 className="text-xl sm:text-2xl lg:text-3xl font-semibold text-white font-['Outfit'] tracking-tight">
                PPDT Assessment Report
              </h1>
              <p className="text-white/40 mt-1 text-xs sm:text-sm">PPM Capability Maturity Research · University of Oulu (2026)</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Link to={`/assessments/${id}`} className="flex items-center gap-2 px-3 py-2 btn-glass rounded-xl text-sm">
              <MessageSquare size={16} /><span className="hidden sm:inline">View Chat</span>
            </Link>
            <button onClick={downloadPDF} disabled={downloading} className="flex items-center gap-2 px-4 py-2 btn-liquid rounded-xl text-sm disabled:opacity-50">
              <Download size={16} />{downloading ? "..." : "Export PDF"}
            </button>
          </div>
        </div>

        {/* Company Info */}
        <div className="p-3 sm:p-4 glass-surface-highlight rounded-xl flex flex-col sm:flex-row sm:flex-wrap gap-3 sm:gap-6 text-sm">
          <div className="flex items-center gap-2"><Building2 size={16} className="text-[#C9A84C]" /><span className="text-white/50">Company:</span><span className="text-white font-medium">{assessment.company_name}</span></div>
          <div className="flex items-center gap-2"><User size={16} className="text-[#C9A84C]" /><span className="text-white/50">Respondent:</span><span className="text-white">{assessment.respondent_name}</span></div>
          <div className="flex items-center gap-2"><Calendar size={16} className="text-[#C9A84C]" /><span className="text-white/50">Date:</span><span className="text-white">{new Date(assessment.completed_at || assessment.created_at).toLocaleDateString()}</span></div>
        </div>

        {/* Overall Score */}
        <div className="p-6 sm:p-8 glass-surface-highlight rounded-2xl">
          <p className="text-xs uppercase tracking-[0.2em] text-[#C9A84C] mb-2">Overall Maturity Level</p>
          <div className="flex items-baseline gap-3">
            <span className={`text-5xl sm:text-6xl font-bold font-['JetBrains_Mono'] ${getScoreColorClass(scores.overall)}`}>
              {scores.overall?.toFixed(2) || "–"}
            </span>
            <span className="text-xl text-white/30">/ 5.00</span>
          </div>
          <p className="text-xl font-semibold text-white mt-2 font-['Outfit']">
            {levelNames.overall || LEVEL_NAMES[overallLevel] || "–"}
          </p>
        </div>

        {/* Dimension Score Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          {DIMENSIONS.map(dim => {
            const Icon = DIM_ICONS[dim];
            const score = scores[dim] || 0;
            const color = getScoreColor(score);
            return (
              <div key={dim} className="p-4 sm:p-5 glass-card rounded-xl">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" style={{ backgroundColor: `${color}15` }}>
                    <Icon size={16} style={{ color }} />
                  </div>
                  <div className="min-w-0">
                    <h3 className="text-sm font-semibold text-white capitalize font-['Outfit'] truncate">{dim}</h3>
                    <p className="text-[10px] text-white/40 truncate">{levelNames[dim] || ""}</p>
                  </div>
                </div>
                <div className="flex items-baseline gap-1 mb-2">
                  <span className={`text-2xl font-bold font-['JetBrains_Mono'] ${getScoreColorClass(score)}`}>{score}</span>
                  <span className="text-white/30 text-xs">/ 5</span>
                </div>
                <div className="w-full h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-500" style={{ width: `${(score / 5) * 100}%`, backgroundColor: color }} />
                </div>
              </div>
            );
          })}
        </div>

        {/* 2. PPDT Maturity Contribution Chart */}
        <div className="p-6 glass-surface-highlight rounded-xl">
          <h2 className="text-lg font-semibold text-white mb-6 font-['Outfit']">PPDT Maturity Contribution</h2>
          <div className="h-72 sm:h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} barGap={4} barCategoryGap="20%">
                <XAxis dataKey="name" tick={{ fill: "rgba(255,255,255,0.6)", fontSize: 13 }} axisLine={{ stroke: "rgba(255,255,255,0.1)" }} />
                <YAxis domain={[0, 5]} tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} axisLine={{ stroke: "rgba(255,255,255,0.1)" }} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                <Legend wrapperStyle={{ color: "rgba(255,255,255,0.6)", fontSize: 12, paddingTop: 8 }} />
                <Bar dataKey="rawScore" name="Raw Score" fill="#60A5FA" radius={[4, 4, 0, 0]}>
                  <LabelList dataKey="rawScore" position="top" fill="rgba(255,255,255,0.7)" fontSize={11} formatter={v => v.toFixed(1)} />
                </Bar>
                <Bar dataKey="weightedContribution" name="Weighted Contribution" fill="#7ee787" radius={[4, 4, 0, 0]}>
                  <LabelList dataKey="weightedContribution" position="top" fill="rgba(255,255,255,0.7)" fontSize={11} formatter={v => v.toFixed(2)} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 3. Score Breakdown Panel */}
        <div className="p-6 glass-surface-highlight rounded-xl">
          <h2 className="text-lg font-semibold text-white mb-6 font-['Outfit']">Score Breakdown</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: Raw Scores */}
            <div>
              <h3 className="text-sm text-white/50 uppercase tracking-wider mb-3">Raw Scores</h3>
              <div className="space-y-2">
                {DIMENSIONS.map(d => (
                  <div key={d} className="flex items-center justify-between py-1.5 border-b border-white/[0.06]">
                    <span className="text-white capitalize text-sm">{d}</span>
                    <span className={`font-['JetBrains_Mono'] font-semibold ${getScoreColorClass(scores[d])}`}>{scores[d] || 0} / 5</span>
                  </div>
                ))}
              </div>
            </div>
            {/* Right: Strategic Weighting */}
            <div>
              <h3 className="text-sm text-white/50 uppercase tracking-wider mb-3">Strategic Weighting & Contribution</h3>
              <div className="space-y-2">
                {DIMENSIONS.map(d => {
                  const raw = weightsRaw[d] || 5;
                  const pct = ((weightsNorm[d] || 0.25) * 100).toFixed(0);
                  const contrib = ((scores[d] || 0) * (weightsNorm[d] || 0.25)).toFixed(2);
                  return (
                    <div key={d} className="flex items-center justify-between py-1.5 border-b border-white/[0.06] text-sm">
                      <span className="text-white/60 capitalize">{d} Weight: <span className="text-white">{raw}</span> ({pct}%)</span>
                      <span className="text-white/50 font-['JetBrains_Mono'] text-xs">
                        {scores[d] || 0} x {(weightsNorm[d] || 0.25).toFixed(2)} = <span className="text-[#7ee787] font-semibold">{contrib}</span>
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
          {/* Overall */}
          <div className="mt-6 pt-4 border-t border-white/[0.08] flex items-center justify-between">
            <span className="text-white font-semibold font-['Outfit']">Overall Maturity Score</span>
            <span className={`text-3xl font-bold font-['JetBrains_Mono'] ${getScoreColorClass(scores.overall)}`}>
              {scores.overall?.toFixed(2) || "–"} <span className="text-sm text-white/30">/ 5.00</span>
            </span>
          </div>
        </div>

        {/* 4. Score Methodology Explainer */}
        <div className="glass-surface-highlight rounded-xl overflow-hidden">
          <button
            onClick={() => setShowMethodology(!showMethodology)}
            className="w-full flex items-center justify-between p-5 text-left hover:bg-white/[0.02] transition-colors"
          >
            <div className="flex items-center gap-2">
              <Info size={18} className="text-[#C9A84C]" />
              <span className="text-white font-medium font-['Outfit']">How is this score calculated?</span>
            </div>
            {showMethodology ? <ChevronUp size={18} className="text-white/50" /> : <ChevronDown size={18} className="text-white/50" />}
          </button>
          {showMethodology && (
            <div className="px-5 pb-6 space-y-5 animate-fade-in border-t border-white/[0.06]">
              <p className="text-white/60 text-sm leading-relaxed mt-4">
                A traditional maturity model calculates a simple average across its dimensions. But a simple average can be misleading.
              </p>
              <p className="text-white/60 text-sm leading-relaxed">
                If a company has world-class engineers (Score: 5) and great software (Score: 5), but their data is completely siloed and inaccurate (Score: 1), a standard average gives them a '3.0 — Satisfactory.' But with a Data score of 1, product-level portfolio analysis is literally impossible. The overall score should reflect that critical bottleneck.
              </p>
              <p className="text-white/60 text-sm leading-relaxed">
                That is why we use a <span className="text-[#C9A84C] font-semibold">Weighted Sum Equation</span> based on the strategic priorities <em>your organisation</em> assigned to each PPDT dimension:
              </p>
              {/* Formula */}
              <div className="p-5 bg-white/[0.03] rounded-xl border border-white/[0.08] text-center">
                <div className="text-2xl sm:text-3xl text-[#C9A84C] font-['JetBrains_Mono'] tracking-wide mb-4">
                  M = w<sub className="text-xs">pe</sub> · S<sub className="text-xs">pe</sub> + w<sub className="text-xs">pr</sub> · S<sub className="text-xs">pr</sub> + w<sub className="text-xs">d</sub> · S<sub className="text-xs">d</sub> + w<sub className="text-xs">t</sub> · S<sub className="text-xs">t</sub>
                </div>
                <div className="text-white/50 text-xs space-y-1 text-left max-w-md mx-auto">
                  <p><span className="text-white font-medium italic">M</span> = Overall Maturity Score (1.0 to 5.0)</p>
                  <p><span className="text-white font-medium italic">w</span> = Strategic Weight assigned to the specific pillar</p>
                  <p><span className="text-white font-medium italic">S</span> = Assessed Grade (1 to 5) for the pillar</p>
                  <p className="pt-1 text-[#C9A84C]">All weights sum to 1: w<sub>pe</sub> + w<sub>pr</sub> + w<sub>d</sub> + w<sub>t</sub> = 1</p>
                </div>
              </div>
              {/* Actual calculation */}
              <div className="p-4 bg-white/[0.03] rounded-xl border border-white/[0.08]">
                <h4 className="text-sm font-semibold text-white mb-3 font-['Outfit']">Your Calculation</h4>
                <div className="space-y-1.5 font-['JetBrains_Mono'] text-xs">
                  {DIMENSIONS.map(d => {
                    const s = scores[d] || 0;
                    const w = weightsNorm[d] || 0.25;
                    return (
                      <div key={d} className="flex items-center gap-2 text-white/60">
                        <span className="text-white capitalize w-20">{d}</span>
                        <span>{s} x {w.toFixed(2)} = <span className="text-[#7ee787] font-semibold">{(s * w).toFixed(2)}</span></span>
                      </div>
                    );
                  })}
                  <div className="border-t border-white/10 pt-2 mt-2 flex items-center gap-2">
                    <span className="text-white font-semibold w-20">Total</span>
                    <span className={`text-lg font-bold ${getScoreColorClass(scores.overall)}`}>
                      {scores.overall?.toFixed(2) || "–"} / 5.00
                    </span>
                  </div>
                </div>
              </div>
              <div className="p-4 bg-[#C9A84C]/5 border border-[#C9A84C]/15 rounded-xl">
                <p className="text-white/70 text-sm italic">
                  "The weighting reflects what <em>your organisation</em> declared as most strategically important. A low score in a high-weight pillar has a disproportionate impact on your overall maturity — and signals where to focus first."
                </p>
              </div>
            </div>
          )}
        </div>

        {/* 5. Five Maturity Levels */}
        <div className="p-6 glass-surface-highlight rounded-xl">
          <h2 className="text-lg font-semibold text-white mb-6 font-['Outfit']">The Five PPDT Maturity Levels</h2>
          <div className="flex flex-col sm:flex-row gap-2 sm:gap-1">
            {MATURITY_LEVELS.map(ml => {
              const isActive = overallLevel === ml.level;
              return (
                <div
                  key={ml.level}
                  className={`flex-1 p-3 sm:p-4 rounded-xl border transition-all ${
                    isActive
                      ? 'border-[' + ml.color + '] bg-white/[0.06] shadow-lg'
                      : 'border-white/[0.06] bg-white/[0.02]'
                  }`}
                  style={isActive ? { borderColor: ml.color, boxShadow: `0 0 20px ${ml.color}33` } : {}}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ backgroundColor: `${ml.color}20`, color: ml.color }}>
                      L{ml.level}
                    </span>
                    <span className={`text-xs sm:text-sm font-semibold ${isActive ? 'text-white' : 'text-white/60'}`}>{ml.name}</span>
                  </div>
                  <p className={`text-[11px] leading-relaxed ${isActive ? 'text-white/70' : 'text-white/40'}`}>{ml.desc}</p>
                </div>
              );
            })}
          </div>
          {/* Per-pillar interpretation */}
          <div className="mt-6 space-y-2">
            {DIMENSIONS.map(d => {
              const score = scores[d] || 0;
              const lvl = Math.round(score);
              const interp = report.pillar_interpretations?.[d] ||
                `Your ${d.charAt(0).toUpperCase() + d.slice(1)} score of ${score} places you at Level ${lvl} — ${MATURITY_LEVELS[Math.max(0, lvl - 1)]?.name || "Ad Hoc"}.`;
              return (
                <div key={d} className="flex items-start gap-3 py-2 border-b border-white/[0.04] last:border-0">
                  <span className="text-xs font-bold px-2 py-0.5 rounded shrink-0 mt-0.5" style={{ backgroundColor: `${getScoreColor(score)}20`, color: getScoreColor(score) }}>
                    {d.charAt(0).toUpperCase() + d.slice(1)}
                  </span>
                  <p className="text-white/60 text-sm">{interp}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Governance Observations (L4-5) */}
        {report.governance_observations && Object.values(report.governance_observations).some(v => v && !v.includes("N/A") && !v.toLowerCase().includes("below")) && (
          <div className="p-6 glass-surface-highlight rounded-xl border-l-4 border-[#C9A84C]">
            <div className="flex items-center gap-2 mb-4">
              <span className="px-2 py-0.5 bg-[#C9A84C]/15 text-[#C9A84C] text-xs font-semibold rounded border border-[#C9A84C]/20">GOVERNANCE</span>
              <h2 className="text-lg font-semibold text-white font-['Outfit']">Governance Indicators (Levels 4–5)</h2>
            </div>
            <div className="space-y-3">
              {DIMENSIONS.map(dim => {
                const obs = report.governance_observations?.[dim];
                if (!obs || obs.includes("N/A") || obs.toLowerCase().includes("below")) return null;
                return (
                  <div key={`gov-${dim}`} className="p-3 bg-[#C9A84C]/5 rounded-lg border border-[#C9A84C]/10">
                    <span className="text-xs font-semibold text-[#C9A84C] uppercase">{dim}</span>
                    <p className="text-white/60 text-sm mt-1">{obs}</p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 6. Governance & Ownership Card */}
        <div className="p-6 glass-surface-highlight rounded-xl">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-[#A78BFA]/15 flex items-center justify-center"><Shield size={22} className="text-[#A78BFA]" /></div>
            <h2 className="text-lg font-semibold text-white font-['Outfit']">Governance & Ownership</h2>
          </div>
          <p className="text-white/60 text-sm mb-4 leading-relaxed">
            Governance is the connective tissue between all four PPDT dimensions. High capability in People, Process, Data, or Technology without clear ownership and accountability still produces unreliable, inconsistent portfolio decisions.
          </p>
          <ul className="space-y-2 mb-4">
            {["Who owns the product portfolio decision-making process?",
              "Are stage-gate reviews conducted with defined decision criteria and assigned owners?",
              "Is there a Product Manager or Portfolio Manager with cross-functional authority?",
              "Are portfolio priorities reviewed on a defined cadence (e.g. quarterly PPM reviews)?"
            ].map((q, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-white/50">
                <span className="text-[#A78BFA] mt-0.5">-</span>{q}
              </li>
            ))}
          </ul>
          {report.governance_assessment && (
            <p className="text-white/70 text-sm italic leading-relaxed p-3 bg-white/[0.03] rounded-lg border border-white/[0.06]">
              {report.governance_assessment}
            </p>
          )}
          <div className="mt-4 p-3 bg-[#EF4444]/5 border border-[#EF4444]/15 rounded-lg">
            <p className="text-[#EF4444] text-xs font-medium">
              "Without governance structures, even well-trained people and advanced technology produce fragmented decisions. Accountability must be assigned — not assumed."
            </p>
          </div>
        </div>

        {/* 7. Management Commitment Card */}
        <div className="p-6 glass-surface-highlight rounded-xl">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-[#34D399]/15 flex items-center justify-center"><ArrowUpRight size={22} className="text-[#34D399]" /></div>
            <div>
              <h2 className="text-lg font-semibold text-white font-['Outfit']">Management Commitment</h2>
              <p className="text-xs text-white/40 italic">The multiplier effect on all capability investments</p>
            </div>
          </div>
          <p className="text-white/60 text-sm mb-4 leading-relaxed">
            Management commitment acts as a multiplier on all capability investments. Without leadership buy-in, investments in People training and Process redesign produce limited, short-lived change. With it, even modest interventions can rapidly elevate maturity across all four PPDT dimensions.
          </p>
          <ul className="space-y-2 mb-4">
            {["Leadership sets the strategic priority for PPM — if portfolio management is not visibly championed at the executive level, it will be deprioritised at the operational level.",
              "Management commitment enables resource allocation: time, budget, and cross-functional cooperation needed for PPM improvement.",
              "In organisations where leadership actively participates in stage-gate reviews and portfolio prioritisation, maturity levels increase faster and more sustainably."
            ].map((p, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-white/50"><span className="text-[#34D399] mt-0.5">-</span>{p}</li>
            ))}
          </ul>
          {report.management_commitment_assessment && (
            <p className="text-white/70 text-sm italic leading-relaxed p-3 bg-white/[0.03] rounded-lg border border-white/[0.06]">
              {report.management_commitment_assessment}
            </p>
          )}
          <div className="mt-4 p-3 bg-[#34D399]/5 border border-[#34D399]/15 rounded-lg">
            <p className="text-[#34D399] text-xs font-medium">
              "If management commitment is low, prioritise leadership alignment before investing in tools or training — otherwise capability improvements will not stick."
            </p>
          </div>
        </div>

        {/* Key Findings & Critical Gaps */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="p-6 glass-surface-highlight rounded-xl">
            <div className="flex items-center gap-2 mb-4">
              <Target size={20} className="text-[#C9A84C]" />
              <h2 className="text-lg font-semibold text-white font-['Outfit']">Key Findings</h2>
            </div>
            <ul className="space-y-3">
              {(report.key_findings || []).map((f, i) => (
                <li key={i} className="flex items-start gap-3"><span className="w-5 h-5 rounded-full bg-[#C9A84C]/15 text-[#C9A84C] flex items-center justify-center text-[10px] shrink-0 mt-0.5">{i + 1}</span><p className="text-white/60 text-sm">{f}</p></li>
              ))}
            </ul>
          </div>
          <div className="p-6 glass-surface-highlight rounded-xl">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle size={20} className="text-[#EF4444]" />
              <h2 className="text-lg font-semibold text-white font-['Outfit']">Critical Capability Gaps</h2>
            </div>
            <ul className="space-y-3">
              {(report.critical_gaps || []).map((g, i) => (
                <li key={i} className="flex items-start gap-3"><span className="w-5 h-5 rounded-full bg-[#EF4444]/15 text-[#EF4444] flex items-center justify-center text-[10px] shrink-0 mt-0.5">!</span><p className="text-white/60 text-sm">{g}</p></li>
              ))}
            </ul>
          </div>
        </div>

        {/* Decision Vulnerability */}
        <div className="p-6 glass-surface-highlight rounded-xl">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle size={20} className="text-[#C9A84C]" />
            <h2 className="text-lg font-semibold text-white font-['Outfit']">Decision-Type Vulnerability Analysis</h2>
          </div>
          <p className="text-white/60 text-sm leading-relaxed">{report.decision_vulnerability || "No analysis available."}</p>
        </div>

        {/* 8. Enhanced Improvement Roadmap */}
        <div className="p-6 glass-surface-highlight rounded-xl">
          <div className="flex items-center gap-2 mb-6">
            <TrendingUp size={20} className="text-[#34D399]" />
            <h2 className="text-lg font-semibold text-white font-['Outfit']">Improvement Roadmap</h2>
          </div>
          <div className="space-y-4">
            {[
              { key: "immediate", title: "Phase 1 — Immediate (0–3 months)", subtitle: "Stabilise the Foundation", color: "#C9A84C" },
              { key: "short_term", title: "Phase 2 — Short-Term (3–12 months)", subtitle: "Build Capability", color: "#34D399" },
              { key: "strategic", title: "Phase 3 — Strategic (12+ months)", subtitle: "Optimise and Scale", color: "#A78BFA" },
            ].map(phase => {
              const data = report.roadmap?.[phase.key];
              const actions = typeof data === 'object' && !Array.isArray(data) ? data.actions : (Array.isArray(data) ? data : []);
              const isRich = typeof data === 'object' && !Array.isArray(data);
              return (
                <div key={phase.key} className="p-4 glass-surface rounded-xl border-l-4" style={{ borderLeftColor: phase.color }}>
                  <h3 className="text-sm font-semibold text-white font-['Outfit'] mb-1" style={{ color: phase.color }}>{phase.title}</h3>
                  <p className="text-xs text-white/40 mb-3 italic">{phase.subtitle}</p>
                  <ul className="space-y-1.5 mb-3">
                    {(actions || []).map((a, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-white/60"><span style={{ color: phase.color }}>-</span>{a}</li>
                    ))}
                  </ul>
                  {isRich && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                      {data.pillar_focus && <div className="text-white/40"><span className="text-white/60 font-medium">Pillar Focus:</span> {data.pillar_focus}</div>}
                      {data.governance_milestone && <div className="text-white/40"><span className="text-white/60 font-medium">Governance:</span> {data.governance_milestone}</div>}
                      {data.management_commitment && <div className="text-white/40"><span className="text-white/60 font-medium">Management:</span> {data.management_commitment}</div>}
                      {data.expected_gain && <div className="text-white/40"><span className="text-white/60 font-medium">Expected Gain:</span> {data.expected_gain}</div>}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Benchmark & Consultant Note */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="p-6 glass-surface-highlight rounded-xl">
            <h2 className="text-lg font-semibold text-white mb-4 font-['Outfit']">Benchmark Context</h2>
            <p className="text-white/60 text-sm leading-relaxed">{report.benchmark_context || "No benchmark data available."}</p>
          </div>
          <div className="p-6 glass-card rounded-xl hover:border-[#C9A84C]/20">
            <h2 className="text-lg font-semibold text-white mb-4 font-['Outfit']">Consultant's Note</h2>
            <p className="text-white/70 italic text-sm leading-relaxed">"{report.consultant_note || "No consultant note available."}"</p>
          </div>
        </div>

        {/* Closing Statement */}
        <div className="p-6 glass-card rounded-xl border border-[#C9A84C]/20 hover:border-[#C9A84C]/30">
          <p className="text-white/70 text-sm leading-relaxed mb-3">
            Thank you for completing this capability maturity assessment. If you would like further analysis, expert input, or tailored recommendations based on your results, please reach out via email to arrange a follow-up consultation:
          </p>
          <a href={`mailto:${CONTACT_EMAIL}`} className="text-[#C9A84C] hover:text-[#D4B85C] font-medium text-sm transition-colors">{CONTACT_EMAIL}</a>
        </div>

        {/* Footer */}
        <div className="text-center py-8 border-t border-white/[0.06]">
          <p className="text-sm text-white/30">Based on: PPM Capability Maturity Research · University of Oulu (2026)</p>
        </div>
      </div>
    </Layout>
  );
};

export default ReportPage;
