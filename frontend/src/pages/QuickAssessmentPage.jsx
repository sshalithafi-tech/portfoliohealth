import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useQuickAssessmentQuestions } from "../hooks/useData";
import { getDimensionBadgeClass } from "../utils/scoring";
import { LoadingSpinner } from "../components/ScoreComponents";
import { 
  ArrowLeft, 
  ArrowRight, 
  Building2,
  ChevronRight,
  Loader2
} from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const INDUSTRIES = [
  "Manufacturing", "Technology", "Healthcare", "Retail",
  "Financial Services", "Automotive", "Energy",
  "Telecommunications", "Consumer Goods", "Industrial Equipment", "Other"
];

const QuestionOption = ({ option, questionId, optionIndex, isSelected, onSelect }) => (
  <button
    data-testid={`option-${questionId}-${optionIndex}`}
    onClick={() => onSelect(option.value)}
    className={`w-full p-4 rounded-xl border text-left transition-all flex items-center justify-between group ${
      isSelected
        ? "bg-[#00E5FF]/10 border-[#00E5FF]/30 text-white"
        : "bg-white/[0.03] border-white/[0.08] text-white/70 hover:border-[#00E5FF]/20 hover:bg-white/[0.05]"
    }`}
  >
    <span className="font-medium">{option.label}</span>
    <ChevronRight size={18} className={`transition-all ${
      isSelected ? "text-[#00E5FF]" : "text-white/30 group-hover:text-white/50"
    }`} />
  </button>
);

const ProgressDots = ({ questions, currentQuestion, answers, onDotClick }) => (
  <div className="flex items-center justify-center gap-1.5 mt-8">
    {questions.map((q, idx) => (
      <button
        key={`dot-${q.id}`}
        onClick={() => onDotClick(idx)}
        className={`h-2 rounded-full transition-all ${
          idx === currentQuestion
            ? "bg-[#00E5FF] w-6"
            : answers[String(q.id)]
            ? "bg-[#238636] w-2"
            : "bg-white/[0.15] w-2"
        }`}
      />
    ))}
  </div>
);

const QuickAssessmentPage = () => {
  const navigate = useNavigate();
  const { questions, loading } = useQuickAssessmentQuestions();
  const [step, setStep] = useState("intro");
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState({});
  const [companyInfo, setCompanyInfo] = useState({
    company_name: "", industry: "", respondent_name: "", respondent_email: ""
  });

  const handleCompanyInfoChange = useCallback((field, value) => {
    setCompanyInfo(prev => ({ ...prev, [field]: value }));
  }, []);

  const handleStartAssessment = useCallback((e) => {
    e.preventDefault();
    if (!companyInfo.company_name || !companyInfo.industry) {
      toast.error("Please fill in company name and industry");
      return;
    }
    setStep("questions");
  }, [companyInfo]);

  const handleAnswer = useCallback((questionId, value) => {
    setAnswers(prev => ({ ...prev, [questionId]: value }));
    if (currentQuestion < questions.length - 1) {
      setTimeout(() => {
        setCurrentQuestion(prev => prev + 1);
      }, 300);
    }
  }, [currentQuestion, questions.length]);

  const handleSubmit = useCallback(async () => {
    if (Object.keys(answers).length < questions.length) {
      toast.error("Please answer all questions");
      return;
    }
    setStep("submitting");
    try {
      const response = await axios.post(`${BACKEND_URL}/api/quick-assessment/submit`, {
        company_name: companyInfo.company_name,
        industry: companyInfo.industry,
        respondent_name: companyInfo.respondent_name || null,
        respondent_email: companyInfo.respondent_email || null,
        answers: answers
      });
      navigate(`/quick-assessment/${response.data.id}/results`, { 
        state: { result: response.data } 
      });
    } catch (err) {
      console.error("Failed to submit assessment:", err);
      toast.error("Failed to submit assessment");
      setStep("questions");
    }
  }, [answers, questions.length, companyInfo, navigate]);

  const handleBack = useCallback(() => {
    if (step === "intro") {
      navigate("/");
    } else {
      setStep("intro");
    }
  }, [step, navigate]);

  const progress = questions.length > 0 ? ((currentQuestion + 1) / questions.length) * 100 : 0;
  const currentQ = questions[currentQuestion];

  const getDimensionLabel = (dimension) => {
    if (dimension === "qualifier") return "Portfolio Size";
    return dimension.charAt(0).toUpperCase() + dimension.slice(1);
  };

  if (loading) {
    return (
      <div className="min-h-screen">
        <LoadingSpinner className="min-h-screen" />
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Glass Header */}
      <header className="h-16 glass-surface flex items-center px-6 relative z-10">
        <button
          onClick={handleBack}
          data-testid="back-btn"
          className="flex items-center gap-2 text-white/50 hover:text-white transition-colors mr-6"
        >
          <ArrowLeft size={20} />
          <span className="hidden sm:inline">Back</span>
        </button>
        
        <div className="flex items-center gap-3 flex-1">
          <img src="https://static.prod-images.emergentagent.com/jobs/ad26f002-f220-4b9d-b343-979dba7f2367/images/6407f98124d827501f865028cbbf81566506fd19a8f17f5fd5b271241d491414.png" alt="PH" className="w-8 h-8 rounded-lg object-contain" />
          <span className="text-white font-semibold font-['Outfit']">PortfolioHealth</span>
        </div>

        {step === "questions" && (
          <span className="text-white/50 text-sm">
            {currentQuestion + 1} of {questions.length}
          </span>
        )}
      </header>

      {/* Progress Bar */}
      {step === "questions" && (
        <div className="h-1 bg-white/[0.06] relative z-10">
          <div 
            className="h-full bg-gradient-to-r from-[#2f81f7] to-[#00E5FF] transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      <div className="max-w-2xl mx-auto px-6 py-12 relative z-10">
        {/* Intro Step */}
        {step === "intro" && (
          <div className="animate-fade-in">
            <h1 className="text-3xl font-semibold text-white font-['Outfit'] tracking-tight mb-4">
              Quick PPDT Health Check
            </h1>
            <p className="text-white/50 mb-8">
              Answer 15 questions to get an instant assessment of your organisation's 
              PPM capability maturity across People, Process, Data, and Technology dimensions.
            </p>

            <form onSubmit={handleStartAssessment} className="space-y-6">
              <div className="p-6 glass-surface-highlight rounded-xl space-y-4">
                <div className="flex items-center gap-3 mb-4">
                  <Building2 size={20} className="text-[#00E5FF]" />
                  <h2 className="text-lg font-semibold text-white font-['Outfit']">Company Information</h2>
                </div>

                <div className="space-y-2">
                  <label className="text-sm text-white/50">Company Name *</label>
                  <input
                    type="text"
                    data-testid="quick-company-name"
                    value={companyInfo.company_name}
                    onChange={(e) => handleCompanyInfoChange("company_name", e.target.value)}
                    className="w-full px-4 py-3 glass-input rounded-xl outline-none"
                    placeholder="Your Company Name"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm text-white/50">Industry *</label>
                  <select
                    data-testid="quick-industry"
                    value={companyInfo.industry}
                    onChange={(e) => handleCompanyInfoChange("industry", e.target.value)}
                    className="w-full px-4 py-3 glass-input rounded-xl outline-none"
                    required
                  >
                    <option value="">Select industry</option>
                    {INDUSTRIES.map(ind => (
                      <option key={ind} value={ind}>{ind}</option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm text-white/50">Your Name (optional)</label>
                    <input
                      type="text"
                      data-testid="quick-respondent-name"
                      value={companyInfo.respondent_name}
                      onChange={(e) => handleCompanyInfoChange("respondent_name", e.target.value)}
                      className="w-full px-4 py-3 glass-input rounded-xl outline-none"
                      placeholder="John Smith"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm text-white/50">Email (optional)</label>
                    <input
                      type="email"
                      data-testid="quick-respondent-email"
                      value={companyInfo.respondent_email}
                      onChange={(e) => handleCompanyInfoChange("respondent_email", e.target.value)}
                      className="w-full px-4 py-3 glass-input rounded-xl outline-none"
                      placeholder="you@company.com"
                    />
                  </div>
                </div>
              </div>

              <button
                type="submit"
                data-testid="start-quick-assessment-btn"
                className="w-full py-4 px-6 btn-liquid rounded-xl flex items-center justify-center gap-2"
              >
                Start Assessment
                <ArrowRight size={20} />
              </button>
            </form>
          </div>
        )}

        {/* Questions Step */}
        {step === "questions" && currentQ && (
          <div className="animate-fade-in" key={`question-${currentQuestion}`}>
            <div className="mb-8">
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${getDimensionBadgeClass(currentQ.dimension)}`}>
                {getDimensionLabel(currentQ.dimension)}
              </span>
            </div>

            <h2 className="text-2xl font-semibold text-white mb-8 font-['Outfit']">
              {currentQ.question}
            </h2>

            <div className="space-y-3">
              {currentQ.options.map((option, idx) => (
                <QuestionOption
                  key={`option-${currentQ.id}-${idx}`}
                  option={option}
                  questionId={currentQ.id}
                  optionIndex={idx}
                  isSelected={answers[String(currentQ.id)] === option.value}
                  onSelect={(value) => handleAnswer(String(currentQ.id), value)}
                />
              ))}
            </div>

            {/* Navigation */}
            <div className="flex items-center justify-between mt-8 pt-8 border-t border-white/[0.06]">
              <button
                onClick={() => setCurrentQuestion(prev => Math.max(0, prev - 1))}
                disabled={currentQuestion === 0}
                className="flex items-center gap-2 text-white/50 hover:text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <ArrowLeft size={18} />
                Previous
              </button>

              {currentQuestion < questions.length - 1 ? (
                <button
                  onClick={() => setCurrentQuestion(prev => prev + 1)}
                  disabled={!answers[String(currentQ.id)]}
                  className="flex items-center gap-2 px-6 py-2 btn-liquid rounded-xl disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  Next
                  <ArrowRight size={18} />
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={Object.keys(answers).length < questions.length}
                  data-testid="submit-quick-assessment-btn"
                  className="flex items-center gap-2 px-6 py-2 bg-[#238636] text-white rounded-xl hover:bg-[#238636]/80 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  Get Results
                  <ArrowRight size={18} />
                </button>
              )}
            </div>

            <ProgressDots
              questions={questions}
              currentQuestion={currentQuestion}
              answers={answers}
              onDotClick={setCurrentQuestion}
            />
          </div>
        )}

        {/* Submitting Step */}
        {step === "submitting" && (
          <div className="flex flex-col items-center justify-center py-20 animate-fade-in">
            <Loader2 size={48} className="text-[#00E5FF] animate-spin mb-6" />
            <h2 className="text-xl font-semibold text-white mb-2 font-['Outfit']">Calculating Your Scores</h2>
            <p className="text-white/50">This will only take a moment...</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default QuickAssessmentPage;
