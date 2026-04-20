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
import { OverallScoreCard, DimensionScoreCards } from "../components/report/ScoreCards";
import ContributionChart from "../components/report/ContributionChart";
import ScoreBreakdown from "../components/report/ScoreBreakdown";
import ScoreMethodology from "../components/report/ScoreMethodology";
import MaturityLevelsPanel from "../components/report/MaturityLevelsPanel";
import BottleneckSection from "../components/report/BottleneckSection";
import { GovernanceObservations, ManagementCommitment } from "../components/report/GovernanceSections";
import { FindingsAndGaps, DecisionVulnerability, ImprovementRoadmap } from "../components/report/FindingsAndRoadmap";
import { BenchmarkAndNote, ClosingStatement, ReportFooter } from "../components/report/BenchmarkAndClosing";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

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
  const businessModel = report.business_model || assessment.business_model;
  const strategicPriority = report.strategic_priority || assessment.strategic_priority;

  return (
    <Layout>
      <div className="space-y-6 sm:space-y-8">
        <ReportHeader
          assessmentId={id}
          assessment={assessment}
          onDownload={downloadPDF}
          downloading={downloading}
          businessModel={businessModel}
          strategicPriority={strategicPriority}
          businessModelNote={report.business_model_note}
        />
        <OverallScoreCard
          scores={scores}
          levelNames={levelNames}
          overallLevel={overallLevel}
          contextualScore={contextualScore}
        />
        <DimensionScoreCards scores={scores} levelNames={levelNames} />
        <BottleneckSection
          bottleneckPillar={report.bottleneck_pillar}
          scores={scores}
          report={report}
        />
        <ContributionChart scores={scores} weightsNorm={weightsNorm} />
        <ScoreBreakdown scores={scores} weightsRaw={weightsRaw} weightsNorm={weightsNorm} />
        <ScoreMethodology scores={scores} weightsNorm={weightsNorm} />
        <MaturityLevelsPanel overallLevel={overallLevel} scores={scores} report={report} />
        <GovernanceObservations report={report} />
        <ManagementCommitment report={report} />
        <FindingsAndGaps report={report} />
        <DecisionVulnerability report={report} />
        <ImprovementRoadmap report={report} />
        <BenchmarkAndNote report={report} />
        <ClosingStatement />
        <ReportFooter />
      </div>
    </Layout>
  );
};

export default ReportPage;
