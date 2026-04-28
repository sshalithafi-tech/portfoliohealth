import { useEffect, useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import {
  BarChart3, AlertTriangle, TrendingUp, TrendingDown,
  Users, Workflow, Database, Cpu, ArrowRight, Building2,
} from "lucide-react";
import Layout from "../components/Layout";
import { LoadingSpinner } from "../components/ScoreComponents";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const PILLARS = [
  { key: "people",     label: "People",     icon: Users,    color: "#0891B2" },
  { key: "process",    label: "Process",    icon: Workflow, color: "#0E7490" },
  { key: "data",       label: "Data",       icon: Database, color: "#0284C7" },
  { key: "technology", label: "Technology", icon: Cpu,      color: "#0369A1" },
];

const fmt = (v, suffix = "") => (v === null || v === undefined ? "—" : `${Number(v).toFixed(1)}${suffix}`);

const StatTile = ({ label, value, sub, icon: Icon, accent = "#0891B2" }) => (
  <div className="glass-card p-5">
    <div className="flex items-start justify-between gap-3 mb-3">
      <span className="eyebrow">{label}</span>
      {Icon && (
        <div className="w-9 h-9 rounded-xl bg-[#ECFEFF] border border-[#67E8F9] flex items-center justify-center">
          <Icon size={16} style={{ color: accent }} />
        </div>
      )}
    </div>
    <div className="text-3xl font-bold text-[#0C1B2A] font-display tracking-tight" data-testid={`stat-${label.toLowerCase().replace(/\s+/g,'-')}`}>
      {value}
    </div>
    {sub && <p className="text-xs text-[#6B7280] mt-1">{sub}</p>}
  </div>
);

const PillarRow = ({ pillar, cohortAvg, distribution }) => {
  const Icon = pillar.icon;
  const pct = cohortAvg ? (cohortAvg / 5) * 100 : 0;
  const dotsLeft = (s) => `${(s / 5) * 100}%`;

  return (
    <div className="glass-card p-5" data-testid={`benchmark-pillar-${pillar.key}`}>
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-xl bg-[#ECFEFF] border border-[#67E8F9] flex items-center justify-center">
          <Icon size={18} style={{ color: pillar.color }} />
        </div>
        <div className="flex-1">
          <p className="text-[10px] uppercase tracking-[0.18em] font-bold text-[#0E7490]">{pillar.label}</p>
          <p className="text-xl font-semibold text-[#0C1B2A] font-display">
            {fmt(cohortAvg)}<span className="text-sm font-normal text-[#9CA3AF]"> / 5.0 cohort avg</span>
          </p>
        </div>
        <span className="text-xs text-[#6B7280]">
          {distribution.length} assessment{distribution.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Track + cohort avg + dots */}
      <div className="relative h-10">
        <div className="absolute top-1/2 left-0 right-0 -translate-y-1/2 h-[6px] rounded-full bg-[#EEF1F5]" />
        {cohortAvg !== null && cohortAvg !== undefined && (
          <div
            className="absolute top-1/2 left-0 -translate-y-1/2 h-[6px] rounded-full"
            style={{
              width: `${pct}%`,
              background: `linear-gradient(90deg, #0E7490, ${pillar.color}, #67E8F9)`,
            }}
          />
        )}

        {/* Per-assessment dots */}
        {distribution.map((s, i) => (
          <div
            key={i}
            className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-white border-2 transition-transform hover:scale-125"
            style={{
              left: dotsLeft(s),
              borderColor: pillar.color,
              transform: `translate(-50%, -50%)`,
            }}
            title={`Score ${s.toFixed(1)}`}
          />
        ))}
      </div>

      <div className="flex justify-between text-[10px] text-[#9CA3AF] mt-1 px-1">
        <span>1</span><span>2</span><span>3</span><span>4</span><span>5</span>
      </div>
    </div>
  );
};

const ComparisonRow = ({ row, cohort }) => {
  const overall = row.scores?.overall;
  const delta = (overall !== null && overall !== undefined && cohort?.overall !== null) ? overall - cohort.overall : null;
  const deltaPositive = delta !== null && delta >= 0;

  return (
    <Link
      to={`/assessments/${row.id}/report`}
      data-testid={`benchmark-row-${row.id}`}
      className="block glass-card p-5 hover:shadow-lg group"
    >
      <div className="flex flex-wrap items-center gap-4">
        <div className="w-11 h-11 rounded-xl bg-[#ECFEFF] border border-[#67E8F9] flex items-center justify-center shrink-0">
          <Building2 size={18} className="text-[#0E7490]" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-[#0C1B2A] font-['Outfit'] truncate">{row.company_name}</p>
          <p className="text-xs text-[#6B7280] truncate">
            {[row.company_industry, row.business_model, row.company_size].filter(Boolean).join(" · ")}
          </p>
        </div>

        {/* Per-pillar mini bars */}
        <div className="grid grid-cols-4 gap-2 w-full sm:w-72 order-3 sm:order-2">
          {PILLARS.map((p) => {
            const v = row.scores?.[p.key];
            const cv = cohort?.[p.key];
            const isBottleneck = row.bottleneck_pillar === p.key;
            return (
              <div key={p.key} className="text-center">
                <div className="text-[9px] uppercase tracking-wider text-[#9CA3AF] font-semibold mb-1">
                  {p.label.slice(0, 4)}
                </div>
                <div className="h-1.5 rounded-full bg-[#EEF1F5] relative overflow-hidden">
                  {v !== null && v !== undefined && (
                    <div
                      className="absolute inset-y-0 left-0 rounded-full"
                      style={{
                        width: `${(v / 5) * 100}%`,
                        background: isBottleneck ? "#B23C2A" : p.color,
                      }}
                    />
                  )}
                  {cv !== null && cv !== undefined && (
                    <div
                      className="absolute top-0 bottom-0 w-px bg-[#0C1B2A]/40"
                      style={{ left: `${(cv / 5) * 100}%` }}
                      title={`Cohort ${cv.toFixed(1)}`}
                    />
                  )}
                </div>
                <div className={`text-xs mt-1 font-semibold ${isBottleneck ? "text-[#B23C2A]" : "text-[#0C1B2A]"}`}>
                  {fmt(v)}
                </div>
              </div>
            );
          })}
        </div>

        {/* Overall + delta */}
        <div className="flex items-center gap-4 order-2 sm:order-3">
          <div className="text-right">
            <div className="text-2xl font-bold text-[#0C1B2A] font-display leading-none">{fmt(overall)}</div>
            <div className="text-[10px] uppercase tracking-wider text-[#9CA3AF] mt-1">Overall</div>
          </div>
          {delta !== null && (
            <div
              className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold border ${
                deltaPositive
                  ? "bg-[rgba(31,139,76,0.08)] text-[#1F8B4C] border-[rgba(31,139,76,0.25)]"
                  : "bg-[rgba(178,60,42,0.08)] text-[#B23C2A] border-[rgba(178,60,42,0.25)]"
              }`}
            >
              {deltaPositive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
              {deltaPositive ? "+" : ""}
              {delta.toFixed(1)}
            </div>
          )}
          <ArrowRight size={16} className="text-[#9CA3AF] group-hover:text-[#0891B2] transition-colors" />
        </div>
      </div>
    </Link>
  );
};

const BenchmarksPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${BACKEND_URL}/api/benchmarks`)
      .then((r) => setData(r.data))
      .catch((e) => console.error("Failed to load benchmarks:", e))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Layout><LoadingSpinner className="h-64" /></Layout>;

  const empty = !data || data.cohort_size === 0;

  if (empty) {
    return (
      <Layout>
        <div className="max-w-2xl mx-auto py-16 text-center">
          <div className="w-16 h-16 rounded-2xl bg-[#ECFEFF] border border-[#67E8F9] flex items-center justify-center mx-auto mb-5">
            <BarChart3 size={28} className="text-[#0891B2]" />
          </div>
          <h1 className="text-2xl font-bold text-[#0C1B2A] font-display mb-2">No benchmark data yet</h1>
          <p className="text-[#4B5563] mb-6">
            Complete at least one full assessment to unlock cross-company benchmarking. Your cohort will grow as you assess more companies — every new completion sharpens the comparison.
          </p>
          <Link to="/assessments" data-testid="benchmarks-empty-cta" className="inline-flex items-center gap-2 px-5 py-3 btn-liquid rounded-xl text-sm">
            View Assessments <ArrowRight size={16} />
          </Link>
        </div>
      </Layout>
    );
  }

  const { cohort_size, cohort_avg, distribution, common_bottleneck, strongest_pillar, weakest_pillar, assessments } = data;
  const pillarLabel = (k) => k ? PILLARS.find(p => p.key === k)?.label || k : "—";

  return (
    <Layout>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-8">
        <div>
          <span className="eyebrow">Cross-Company Benchmarks</span>
          <h1 className="text-3xl sm:text-4xl font-bold text-[#0C1B2A] font-display tracking-tight mt-2" data-testid="benchmarks-title">
            How your portfolio measures up
          </h1>
          <p className="text-[#4B5563] mt-2 max-w-2xl">
            Maturity comparison across {cohort_size} completed assessment{cohort_size !== 1 ? "s" : ""} in your workspace.
            Each dot is one company — the bar shows your cohort average.
          </p>
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8 stagger-children">
        <StatTile
          label="Cohort Size"
          value={cohort_size}
          sub={`completed assessment${cohort_size !== 1 ? "s" : ""}`}
          icon={Building2}
        />
        <StatTile
          label="Avg Overall"
          value={fmt(cohort_avg.overall)}
          sub="of 5.0 maturity"
          icon={BarChart3}
        />
        <StatTile
          label="Strongest Pillar"
          value={pillarLabel(strongest_pillar)}
          sub={`avg ${fmt(cohort_avg[strongest_pillar])}`}
          icon={TrendingUp}
          accent="#1F8B4C"
        />
        <StatTile
          label="Most Common Bottleneck"
          value={pillarLabel(common_bottleneck)}
          sub={common_bottleneck ? `weakest avg ${fmt(cohort_avg[weakest_pillar])}` : "no recurring pattern"}
          icon={AlertTriangle}
          accent="#B23C2A"
        />
      </div>

      {/* Per-pillar distribution */}
      <div className="mb-10">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-[#0C1B2A] font-display">Pillar Distribution</h2>
          <span className="text-xs text-[#6B7280]">Each dot = one company</span>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 stagger-children">
          {PILLARS.map((p) => (
            <PillarRow
              key={p.key}
              pillar={p}
              cohortAvg={cohort_avg[p.key]}
              distribution={distribution[p.key] || []}
            />
          ))}
        </div>
      </div>

      {/* Per-assessment comparison */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-[#0C1B2A] font-display">Your Companies vs Cohort</h2>
          <span className="text-xs text-[#6B7280]">Click a row to open the report</span>
        </div>
        <div className="space-y-3 stagger-children">
          {assessments.map((row) => (
            <ComparisonRow key={row.id} row={row} cohort={cohort_avg} />
          ))}
        </div>
      </div>
    </Layout>
  );
};

export default BenchmarksPage;
