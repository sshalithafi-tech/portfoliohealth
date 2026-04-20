import { useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";
import { AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import Layout from "../components/Layout";
import { useAssessment } from "../hooks/useData";
import { LoadingSpinner } from "../components/ScoreComponents";
import { DIMENSIONS } from "../components/report/constants";
import ReportHeader from "../components/report/ReportHeader";
import PortfolioContext from "../components/report/PortfolioContext";
import { OverallScoreCard, DimensionScoreCards } from "../components/report/ScoreCards";
import MaturityLevelsPanel from "../components/report/MaturityLevelsPanel";
import ContributionChart from "../components/report/ContributionChart";
import ScoreBreakdown from "../components/report/ScoreBreakdown";
import ScoreMethodology from "../components/report/ScoreMethodology";
import BottleneckSection from "../components/report/BottleneckSection";
import { GovernanceObservations, ManagementCommitment } from "../components/report/GovernanceSections";
import AssessmentReliability from "../components/report/AssessmentReliability";
import { FindingsAndGaps, DecisionVulnerability, ImprovementRoadmap } from "../components/report/FindingsAndRoadmap";
import { BenchmarkAndNote, ClosingStatement, ReportFooter } from "../components/report/BenchmarkAndClosing";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const SectionLabel = ({ index, title, subtitle }) => (
  <div className="flex items-baseline gap-3">
    <span className="text-[10px] font-['JetBrains_Mono'] text-[#C9A84C]/60 tracking-widest">
      {String(index).padStart(2, "0")}
    </span>
    <div>
      <h2 className="text-base sm:text-lg font-semibold text-white font-['Outfit'] tracking-tight">
        {title}
      </h2>
      {subtitle && <p className="text-[11px] text-white/35 italic mt-0.5">{subtitle}</p>}
    </div>
  </div>
);

const Section = ({ index, title, subtitle, children }) => (
  <section className="space-y-3">
    <SectionLabel index={index} title={title} subtitle={subtitle} />
    <div>{children}</div>
  </section>
);

const ReportPage = () => {
  const { id } = useParams();
  const { assessment, loading } = useAssessment(id);
  const [downloading, setDownloading] = useState(false);

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
    } catch (err) {
      console.error("PDF download failed:", err);
      toast.error("Failed to download PDF");
    } finally {
      setDownloading(false);
    }
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
  const rawTotal = Object.values(weightsRaw).reduce((a, b) => a + (Number(b) || 0), 0) || 1;
  const weightsNorm = report.weights_normalised || Object.fromEntries(
    DIMENSIONS.map(d => [d, (Number(weightsRaw[d]) || 5) / rawTotal])
  );
  const overallLevel = Math.round(scores.overall || 0);
  const contextualScore = typeof report.contextual_score === "number" ? report.contextual_score : null;

  return (
    <Layout>
      <div className="space-y-8 sm:space-y-10">
        <ReportHeader
          assessmentId={id}
          onDownload={downloadPDF}
          downloading={downloading}
        />

        {/* 01 — Portfolio Context */}
        <Section index={1} title="Portfolio Context" subtitle="Who and what this report is about">
          <PortfolioContext assessment={assessment} report={report} />
        </Section>

        {/* 02 — Overall Maturity (Dual Score) */}
        <Section index={2} title="Overall Maturity" subtitle="Equal-weighted vs contextual score">
          <OverallScoreCard
            scores={scores}
            levelNames={levelNames}
            overallLevel={overallLevel}
            contextualScore={contextualScore}
          />
        </Section>

        {/* 03 — Pillar Maturity Levels (L1–L5) */}
        <Section index={3} title="Pillar Maturity Levels" subtitle="Where each pillar sits on the L1–L5 Hannila maturity ladder">
          <MaturityLevelsPanel overallLevel={overallLevel} scores={scores} report={report} />
        </Section>

        {/* 04 — Dimension Scores */}
        <Section index={4} title="Dimension Scores" subtitle="Raw pillar grades (1–5)">
          <DimensionScoreCards scores={scores} levelNames={levelNames} />
        </Section>

        {/* 05 — Weighted Score Calculation */}
        <Section index={5} title="Weighted Score Calculation" subtitle="How the overall score is derived from strategic weighting">
          <div className="space-y-5">
            <ContributionChart scores={scores} weightsNorm={weightsNorm} />
            <ScoreBreakdown scores={scores} weightsRaw={weightsRaw} weightsNorm={weightsNorm} />
            <ScoreMethodology scores={scores} weightsNorm={weightsNorm} />
          </div>
        </Section>

        {/* 06 — Bottleneck Pillar */}
        <Section index={6} title="Bottleneck Pillar" subtitle="The weakest pillar caps real-world capability">
          <BottleneckSection
            bottleneckPillar={report.bottleneck_pillar}
            scores={scores}
            report={report}
          />
        </Section>

        {/* 07 — Governance & Ownership */}
        <Section index={7} title="Governance & Ownership" subtitle="Accountability for portfolio decisions">
          <GovernanceObservations report={report} />
        </Section>

        {/* 08 — Management Commitment */}
        <Section index={8} title="Management Commitment" subtitle="The multiplier on all capability investments">
          <ManagementCommitment report={report} />
        </Section>

        {/* 09 — Assessment Reliability (optional, small) */}
        <Section index={9} title="Assessment Reliability" subtitle="How much to rely on these results">
          <AssessmentReliability report={report} assessment={assessment} />
        </Section>

        {/* 10 — Decision-Type Vulnerability Analysis */}
        <Section index={10} title="Decision-Type Vulnerability" subtitle="Risk by portfolio decision type">
          <DecisionVulnerability report={report} />
        </Section>

        {/* 11 — Key Findings + 12 — Critical Capability Gaps */}
        <Section index={11} title="Key Findings & Critical Gaps" subtitle="What matters most from this assessment">
          <FindingsAndGaps report={report} />
        </Section>

        {/* 13 — Improvement Roadmap */}
        <Section index={12} title="Improvement Roadmap" subtitle="Phased plan — immediate, short-term, strategic">
          <ImprovementRoadmap report={report} />
        </Section>

        {/* 14 — Benchmark Context + 15 — Consultant's Note */}
        <Section index={13} title="Benchmark & Consultant Note" subtitle="Context and a direct final take">
          <BenchmarkAndNote report={report} />
        </Section>

        <ClosingStatement />
        <ReportFooter />
      </div>
    </Layout>
  );
};

export default ReportPage;
