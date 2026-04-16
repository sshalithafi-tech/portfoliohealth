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
  "Manufacturing",
  "Technology",
  "Healthcare",
  "Retail",
  "Financial Services",
  "Automotive",
  "Energy",
  "Telecommunications",
  "Consumer Goods",
  "Industrial Equipment",
  "Other"
];

// Question option button component
const QuestionOption = ({ option, questionId, optionIndex, isSelected, onSelect }) => (
  <button
    data-testid={`option-${questionId}-${optionIndex}`}
    onClick={() => onSelect(option.value)}
    className={`w-full p-4 rounded-xl border text-left transition-all flex items-center justify-between group ${
      isSelected
        ? "bg-[#2f81f7]/20 border-[#2f81f7] text-white"
        : "bg-[#111827] border-[#374151] text-gray-300 hover:border-[#2f81f7]/50 hover:bg-[#1F2937]"
    }`}
  >
    <span className="font-medium">{option.label}</span>
    <ChevronRight size={18} className={`transition-all ${
      isSelected ? "text-[#2f81f7]" : "text-gray-500 group-hover:text-gray-300"
    }`} />
  </button>
);

// Progress dots component
const ProgressDots = ({ questions, currentQuestion, answers, onDotClick }) => (
  <div className="flex items-center justify-center gap-1.5 mt-8">
    {questions.map((q, idx) => (
      <button
        key={`dot-${q.id}`}
        onClick={() => onDotClick(idx)}
        className={`h-2 rounded-full transition-all ${
          idx === currentQuestion
            ? "bg-[#2f81f7] w-6"
            : answers[String(q.id)]
            ? "bg-[#238636] w-2"
            : "bg-[#374151] w-2"
        }`}
      />
    ))}
  </div>
);

const QuickAssessmentPage = () => {
  const navigate = useNavigate();
  const { questions, loading } = useQuickAssessmentQuestions();
  const [step, setStep] = useState("intro"); // intro, questions, submitting
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState({});
  const [companyInfo, setCompanyInfo] = useState({
    company_name: "",
    industry: "",
    respondent_name: "",
    respondent_email: ""
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
    
    // Auto-advance to next question
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

  // Get dimension badge label
  const getDimensionLabel = (dimension) => {
    if (dimension === "qualifier") return "Portfolio Size";
    return dimension.charAt(0).toUpperCase() + dimension.slice(1);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0B1120]">
        <LoadingSpinner className="min-h-screen" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B1120]">
      {/* Header */}
      <header className="h-16 border-b border-[#374151] bg-[#111827] flex items-center px-6">
        <button
          onClick={handleBack}
          data-testid="back-btn"
          className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors mr-6"
        >
          <ArrowLeft size={20} />
          <span className="hidden sm:inline">Back</span>
        </button>
        
        <div className="flex items-center gap-3 flex-1">
          <div className="w-8 h-8 rounded-lg bg-[#2f81f7] flex items-center justify-center">
            <span className="text-white font-bold text-sm">P</span>
          </div>
          <span className="text-white font-semibold font-['Outfit']">Quick Health Check</span>
        </div>

        {step === "questions" && (
          <span className="text-gray-400 text-sm">
            {currentQuestion + 1} of {questions.length}
          </span>
        )}
      </header>

      {/* Progress Bar */}
      {step === "questions" && (
        <div className="h-1 bg-[#1F2937]">
          <div 
            className="h-full bg-[#2f81f7] transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      <div className="max-w-2xl mx-auto px-6 py-12">
        {/* Intro Step */}
        {step === "intro" && (
          <div className="animate-fade-in">
            <h1 className="text-3xl font-semibold text-white font-['Outfit'] tracking-tight mb-4">
              Quick PPDT Health Check
            </h1>
            <p className="text-gray-400 mb-8">
              Answer 15 questions to get an instant assessment of your organisation's 
              PPM capability maturity across People, Process, Data, and Technology dimensions.
            </p>

            <form onSubmit={handleStartAssessment} className="space-y-6">
              <div className="p-6 bg-[#111827] border border-[#374151] rounded-xl space-y-4">
                <div className="flex items-center gap-3 mb-4">
                  <Building2 size={20} className="text-[#2f81f7]" />
                  <h2 className="text-lg font-semibold text-white">Company Information</h2>
                </div>

                <div className="space-y-2">
                  <label className="text-sm text-gray-400">Company Name *</label>
                  <input
                    type="text"
                    data-testid="quick-company-name"
                    value={companyInfo.company_name}
                    onChange={(e) => handleCompanyInfoChange("company_name", e.target.value)}
                    className="w-full px-4 py-3 bg-[#0B1120] border border-[#374151] rounded-lg text-white focus:ring-2 focus:ring-[#2f81f7] focus:border-transparent transition-all outline-none"
                    placeholder="Your Company Name"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm text-gray-400">Industry *</label>
                  <select
                    data-testid="quick-industry"
                    value={companyInfo.industry}
                    onChange={(e) => handleCompanyInfoChange("industry", e.target.value)}
                    className="w-full px-4 py-3 bg-[#0B1120] border border-[#374151] rounded-lg text-white focus:ring-2 focus:ring-[#2f81f7] focus:border-transparent transition-all outline-none"
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
                    <label className="text-sm text-gray-400">Your Name (optional)</label>
                    <input
                      type="text"
                      data-testid="quick-respondent-name"
                      value={companyInfo.respondent_name}
                      onChange={(e) => handleCompanyInfoChange("respondent_name", e.target.value)}
                      className="w-full px-4 py-3 bg-[#0B1120] border border-[#374151] rounded-lg text-white focus:ring-2 focus:ring-[#2f81f7] focus:border-transparent transition-all outline-none"
                      placeholder="John Smith"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm text-gray-400">Email (optional)</label>
                    <input
                      type="email"
                      data-testid="quick-respondent-email"
                      value={companyInfo.respondent_email}
                      onChange={(e) => handleCompanyInfoChange("respondent_email", e.target.value)}
                      className="w-full px-4 py-3 bg-[#0B1120] border border-[#374151] rounded-lg text-white focus:ring-2 focus:ring-[#2f81f7] focus:border-transparent transition-all outline-none"
                      placeholder="you@company.com"
                    />
                  </div>
                </div>
              </div>

              <button
                type="submit"
                data-testid="start-quick-assessment-btn"
                className="w-full py-4 px-6 bg-[#2f81f7] text-white font-medium rounded-lg hover:bg-[#58a6ff] transition-all btn-premium flex items-center justify-center gap-2"
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
            <div className="flex items-center justify-between mt-8 pt-8 border-t border-[#374151]">
              <button
                onClick={() => setCurrentQuestion(prev => Math.max(0, prev - 1))}
                disabled={currentQuestion === 0}
                className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <ArrowLeft size={18} />
                Previous
              </button>

              {currentQuestion < questions.length - 1 ? (
                <button
                  onClick={() => setCurrentQuestion(prev => prev + 1)}
                  disabled={!answers[String(currentQ.id)]}
                  className="flex items-center gap-2 px-6 py-2 bg-[#2f81f7] text-white rounded-lg hover:bg-[#58a6ff] transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  Next
                  <ArrowRight size={18} />
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={Object.keys(answers).length < questions.length}
                  data-testid="submit-quick-assessment-btn"
                  className="flex items-center gap-2 px-6 py-2 bg-[#238636] text-white rounded-lg hover:bg-[#238636]/80 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  Get Results
                  <ArrowRight size={18} />
                </button>
              )}
            </div>

            {/* Question dots */}
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
            <Loader2 size={48} className="text-[#2f81f7] animate-spin mb-6" />
            <h2 className="text-xl font-semibold text-white mb-2">Calculating Your Scores</h2>
            <p className="text-gray-400">This will only take a moment...</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default QuickAssessmentPage;
