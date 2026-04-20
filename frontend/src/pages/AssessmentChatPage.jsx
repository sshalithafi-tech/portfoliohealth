import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import axios from "axios";
import { 
  Send, 
  ArrowLeft, 
  Building2,
  User,
  FileText,
  CheckCircle2,
  Circle,
  Loader2
} from "lucide-react";
import { toast } from "sonner";
import ReactMarkdown from "react-markdown";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const PHASES = [
  { key: "welcome", label: "Welcome" },
  { key: "people", label: "People" },
  { key: "process", label: "Process" },
  { key: "data", label: "Data" },
  { key: "technology", label: "Technology" },
  { key: "decision", label: "Decision Types" },
  { key: "benchmark", label: "Benchmark" },
  { key: "report", label: "Report" }
];

const AssessmentChatPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  
  const [assessment, setAssessment] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [currentPhase, setCurrentPhase] = useState("welcome");

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchAssessment = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/assessments/${id}`);
      setAssessment(response.data);
      setMessages(response.data.chat_history || []);
      setCurrentPhase(response.data.current_phase || "welcome");
      if (!response.data.chat_history || response.data.chat_history.length === 0) {
        startAssessment();
      }
    } catch (err) {
      console.error("Failed to fetch assessment:", err);
      toast.error("Failed to load assessment");
      navigate("/assessments");
    } finally {
      setLoading(false);
    }
  };

  const startAssessment = async () => {
    try {
      const response = await axios.post(`${BACKEND_URL}/api/assessments/${id}/start`);
      setMessages([response.data.message]);
    } catch (err) {
      console.error("Failed to start assessment:", err);
      toast.error("Failed to start assessment");
    }
  };

  useEffect(() => {
    fetchAssessment();
  }, [id]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || sending) return;

    const userMessage = inputValue.trim();
    setInputValue("");
    setSending(true);

    const tempUserMsg = {
      role: "user",
      content: userMessage,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempUserMsg]);

    try {
      const response = await axios.post(`${BACKEND_URL}/api/assessments/${id}/chat`, {
        message: userMessage
      });

      setMessages(prev => [...prev, response.data.message]);

      if (response.data.report_ready) {
        toast.success("Assessment complete! Redirecting to dashboard...");
        setAssessment(prev => ({ ...prev, status: "completed" }));
        setTimeout(() => {
          navigate("/dashboard");
        }, 3000);
      }

      const messageCount = messages.length + 2;
      if (messageCount <= 4) setCurrentPhase("welcome");
      else if (messageCount <= 14) setCurrentPhase("people");
      else if (messageCount <= 24) setCurrentPhase("process");
      else if (messageCount <= 38) setCurrentPhase("data");
      else if (messageCount <= 48) setCurrentPhase("technology");
      else if (messageCount <= 54) setCurrentPhase("decision");
      else if (messageCount <= 58) setCurrentPhase("benchmark");
      else setCurrentPhase("report");

    } catch (err) {
      console.error("Failed to send message:", err);
      toast.error("Failed to send message. Please try again.");
      setMessages(prev => prev.slice(0, -1));
      setInputValue(userMessage);
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  };

  const getPhaseIndex = (phase) => {
    return PHASES.findIndex(p => p.key === phase);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse-glow w-12 h-12 rounded-full bg-[#C9A84C]/15 flex items-center justify-center">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#60A5FA] to-[#C9A84C]" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Glass Header */}
      <header className="h-14 sm:h-16 glass-surface flex items-center px-3 sm:px-6 shrink-0 relative z-10">
        <Link
          to="/assessments"
          data-testid="back-to-assessments"
          className="flex items-center gap-1 sm:gap-2 text-white/50 hover:text-white transition-colors mr-3 sm:mr-6"
        >
          <ArrowLeft size={18} />
          <span className="hidden sm:inline">Back</span>
        </Link>
        
        <div className="flex items-center gap-2 sm:gap-4 flex-1 min-w-0">
          <div className="flex items-center gap-1.5 sm:gap-2 min-w-0">
            <Building2 size={16} className="text-[#C9A84C] shrink-0" />
            <span className="text-white font-medium text-sm sm:text-base truncate">{assessment?.company_name}</span>
          </div>
          <div className="hidden md:flex items-center gap-2 text-white/50">
            <User size={14} />
            <span className="text-sm">{assessment?.respondent_name} · {assessment?.respondent_role}</span>
          </div>
        </div>

        {assessment?.status === "completed" && (
          <Link
            to={`/assessments/${id}/report`}
            data-testid="view-report-btn"
            className="flex items-center gap-1 sm:gap-2 px-3 sm:px-4 py-2 bg-[#34D399] text-white rounded-xl hover:bg-[#34D399]/80 transition-colors text-xs sm:text-sm shrink-0"
          >
            <FileText size={14} />
            <span className="hidden sm:inline">View Report</span>
            <span className="sm:hidden">Report</span>
          </Link>
        )}
      </header>

      {/* Phase Indicator */}
      <div className="h-12 sm:h-14 glass-surface flex items-center px-3 sm:px-6 overflow-x-auto shrink-0 relative z-10 scrollbar-hide">
        <div className="flex items-center gap-1 sm:gap-2">
          {PHASES.map((phase, idx) => {
            const currentIdx = getPhaseIndex(currentPhase);
            const isCompleted = idx < currentIdx;
            const isCurrent = idx === currentIdx;
            
            return (
              <div key={phase.key} className="flex items-center">
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm transition-all ${
                  isCompleted ? 'bg-[#34D399]/15 text-[#34D399] border border-[#34D399]/20' :
                  isCurrent ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' :
                  'bg-white/[0.03] text-white/30 border border-white/[0.05]'
                }`}>
                  {isCompleted ? (
                    <CheckCircle2 size={14} />
                  ) : isCurrent ? (
                    <div className="w-3.5 h-3.5 rounded-full bg-[#C9A84C] animate-pulse" />
                  ) : (
                    <Circle size={14} />
                  )}
                  <span className="hidden sm:inline whitespace-nowrap">{phase.label}</span>
                </div>
                {idx < PHASES.length - 1 && (
                  <div className={`w-8 h-0.5 mx-1 ${
                    idx < currentIdx ? 'bg-[#34D399]/50' : 'bg-white/[0.06]'
                  }`} />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 relative z-10">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              data-testid={`chat-message-${idx}`}
              className={`animate-fade-in ${
                msg.role === "user" ? "flex justify-end" : ""
              }`}
              style={{ animationDelay: `${idx * 0.05}s` }}
            >
              {msg.role === "user" ? (
                <div className="chat-message-user max-w-[80%] px-4 py-3">
                  <p className="text-white whitespace-pre-wrap">{msg.content}</p>
                  <p className="text-xs text-white/30 mt-2">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              ) : (
                <div className="chat-message-assistant">
                  <div className="flex items-start gap-3">
                    <img src="https://static.prod-images.emergentagent.com/jobs/ad26f002-f220-4b9d-b343-979dba7f2367/images/d646700fab8f8fe4907058c3e80e52bb7fde0a398525ad319ca353e76a6edf0f.png" alt="PH" className="w-8 h-8 rounded-full object-contain shrink-0 mt-1" />
                    <div className="flex-1">
                      <p className="text-xs text-[#C9A84C] font-medium mb-2">PortfolioHealth Advisor</p>
                      <div className="text-white/80 prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown
                          components={{
                            p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
                            strong: ({ children }) => <strong className="text-white">{children}</strong>,
                            ul: ({ children }) => <ul className="list-disc list-inside mb-3">{children}</ul>,
                            ol: ({ children }) => <ol className="list-decimal list-inside mb-3">{children}</ol>,
                            code: ({ children }) => <code className="bg-white/[0.08] px-1 py-0.5 rounded text-[#C9A84C]">{children}</code>,
                            pre: ({ children }) => <pre className="bg-white/[0.05] p-3 rounded-lg overflow-x-auto text-sm">{children}</pre>
                          }}
                        >
                          {msg.content.replace(/```json[\s\S]*?```/g, '')}
                        </ReactMarkdown>
                      </div>
                      <p className="text-xs text-white/25 mt-2">
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
          
          {sending && (
            <div className="chat-message-assistant animate-fade-in">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-[#C9A84C]/15 flex items-center justify-center shrink-0">
                  <Loader2 size={16} className="text-[#C9A84C] animate-spin" />
                </div>
                <div className="flex items-center gap-2 text-white/50">
                  <span>Thinking</span>
                  <span className="flex gap-1">
                    <span className="w-1.5 h-1.5 bg-[#C9A84C] rounded-full animate-bounce" style={{ animationDelay: "0s" }} />
                    <span className="w-1.5 h-1.5 bg-[#C9A84C] rounded-full animate-bounce" style={{ animationDelay: "0.1s" }} />
                    <span className="w-1.5 h-1.5 bg-[#C9A84C] rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
                  </span>
                </div>
              </div>
            </div>
          )}
          
          {/* Closing Statement Card */}
          {assessment?.status === "completed" && (
            <div className="animate-fade-in p-5 rounded-2xl border border-[#C9A84C]/30 bg-[#C9A84C]/5 backdrop-blur-sm" data-testid="closing-statement-card">
              <p className="text-white/80 text-sm leading-relaxed mb-4">
                Thank you for completing this capability maturity assessment. If you would like further analysis, expert input, or tailored recommendations based on your results, please reach out via email to arrange a follow-up consultation:
              </p>
              <a href="mailto:shalitha.samarakoonmudiyanselage@student.oulu.fi" className="text-[#C9A84C] hover:text-[#D4B85C] font-medium text-sm transition-colors">
                shalitha.samarakoonmudiyanselage@student.oulu.fi
              </a>
              <div className="flex gap-3 mt-4">
                <Link
                  to={`/assessments/${id}/report`}
                  className="flex items-center gap-2 px-4 py-2 btn-liquid rounded-xl text-sm"
                  data-testid="view-report-from-chat"
                >
                  <FileText size={16} />
                  View Report
                </Link>
                <Link
                  to="/dashboard"
                  className="flex items-center gap-2 px-4 py-2 btn-glass rounded-xl text-sm"
                >
                  Go to Dashboard
                </Link>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="glass-surface p-3 sm:p-4 shrink-0 relative z-10">
        <form onSubmit={sendMessage} className="max-w-3xl mx-auto">
          <div className="flex items-center gap-2 sm:gap-3">
            <input
              ref={inputRef}
              type="text"
              data-testid="chat-input"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Type your response..."
              disabled={sending || assessment?.status === "completed"}
              className="flex-1 px-3 sm:px-4 py-2.5 sm:py-3 glass-input rounded-xl outline-none disabled:opacity-50 text-sm sm:text-base"
            />
            <button
              type="submit"
              data-testid="send-message-btn"
              disabled={!inputValue.trim() || sending || assessment?.status === "completed"}
              className="p-2.5 sm:p-3 btn-liquid rounded-xl disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
            >
              <Send size={18} />
            </button>
          </div>
          {assessment?.status === "completed" && (
            <p className="text-center text-white/40 text-sm mt-3">
              This assessment is complete.{" "}
              <Link to={`/assessments/${id}/report`} className="text-[#C9A84C] hover:text-[#C9A84C]/80">
                View the report
              </Link>
            </p>
          )}
        </form>
      </div>
    </div>
  );
};

export default AssessmentChatPage;
