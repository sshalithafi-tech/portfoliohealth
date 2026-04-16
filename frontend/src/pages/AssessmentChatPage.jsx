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
      
      // If no messages, start the assessment
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

    // Add user message immediately
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

      // Add assistant response
      setMessages(prev => [...prev, response.data.message]);

      // Check if report is ready
      if (response.data.report_ready) {
        toast.success("Assessment complete! Report generated.");
        setTimeout(() => {
          navigate(`/assessments/${id}/report`);
        }, 2000);
      }

      // Estimate phase based on message count
      const messageCount = messages.length + 2; // +2 for new user and assistant messages
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
      // Remove the optimistic user message on error
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
      <div className="min-h-screen bg-[#0B1120] flex items-center justify-center">
        <div className="animate-pulse-glow w-12 h-12 rounded-full bg-[#2f81f7]/20 flex items-center justify-center">
          <div className="w-6 h-6 rounded-full bg-[#2f81f7]" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B1120] flex flex-col">
      {/* Header */}
      <header className="h-16 border-b border-[#374151] bg-[#111827] flex items-center px-6 shrink-0">
        <Link
          to="/assessments"
          data-testid="back-to-assessments"
          className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors mr-6"
        >
          <ArrowLeft size={20} />
          <span className="hidden sm:inline">Back</span>
        </Link>
        
        <div className="flex items-center gap-4 flex-1">
          <div className="flex items-center gap-2">
            <Building2 size={18} className="text-[#2f81f7]" />
            <span className="text-white font-medium">{assessment?.company_name}</span>
          </div>
          <div className="hidden md:flex items-center gap-2 text-gray-400">
            <User size={14} />
            <span className="text-sm">{assessment?.respondent_name} · {assessment?.respondent_role}</span>
          </div>
        </div>

        {assessment?.status === "completed" && (
          <Link
            to={`/assessments/${id}/report`}
            data-testid="view-report-btn"
            className="flex items-center gap-2 px-4 py-2 bg-[#238636] text-white rounded-lg hover:bg-[#238636]/80 transition-colors"
          >
            <FileText size={16} />
            View Report
          </Link>
        )}
      </header>

      {/* Phase Indicator */}
      <div className="h-14 border-b border-[#374151] bg-[#111827]/50 flex items-center px-6 overflow-x-auto shrink-0">
        <div className="flex items-center gap-2">
          {PHASES.map((phase, idx) => {
            const currentIdx = getPhaseIndex(currentPhase);
            const isCompleted = idx < currentIdx;
            const isCurrent = idx === currentIdx;
            
            return (
              <div key={phase.key} className="flex items-center">
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm transition-all ${
                  isCompleted ? 'bg-[#238636]/20 text-[#238636]' :
                  isCurrent ? 'bg-[#2f81f7]/20 text-[#2f81f7] ring-1 ring-[#2f81f7]' :
                  'bg-[#374151]/30 text-gray-500'
                }`}>
                  {isCompleted ? (
                    <CheckCircle2 size={14} />
                  ) : isCurrent ? (
                    <div className="w-3.5 h-3.5 rounded-full bg-[#2f81f7] animate-pulse" />
                  ) : (
                    <Circle size={14} />
                  )}
                  <span className="hidden sm:inline whitespace-nowrap">{phase.label}</span>
                </div>
                {idx < PHASES.length - 1 && (
                  <div className={`w-8 h-0.5 mx-1 ${
                    idx < currentIdx ? 'bg-[#238636]' : 'bg-[#374151]'
                  }`} />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
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
                  <p className="text-xs text-gray-500 mt-2">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              ) : (
                <div className="chat-message-assistant">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-[#2f81f7]/20 flex items-center justify-center shrink-0 mt-1">
                      <img 
                        src="https://images.unsplash.com/photo-1770170389700-eb0f9b910ed8?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjY2NzN8MHwxfHNlYXJjaHwxfHxhYnN0cmFjdCUyMGFpJTIwdGVjaG5vbG9neSUyMG5vZGV8ZW58MHx8fHwxNzc2MzQyOTQ3fDA&ixlib=rb-4.1.0&q=85"
                        alt="AI"
                        className="w-8 h-8 rounded-full object-cover"
                      />
                    </div>
                    <div className="flex-1">
                      <p className="text-xs text-[#2f81f7] font-medium mb-2">PortfolioHealth Advisor</p>
                      <div className="text-gray-200 prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown
                          components={{
                            p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
                            strong: ({ children }) => <strong className="text-white">{children}</strong>,
                            ul: ({ children }) => <ul className="list-disc list-inside mb-3">{children}</ul>,
                            ol: ({ children }) => <ol className="list-decimal list-inside mb-3">{children}</ol>,
                            code: ({ children }) => <code className="bg-[#1F2937] px-1 py-0.5 rounded text-[#2f81f7]">{children}</code>,
                            pre: ({ children }) => <pre className="bg-[#1F2937] p-3 rounded-lg overflow-x-auto text-sm">{children}</pre>
                          }}
                        >
                          {msg.content.replace(/```json[\s\S]*?```/g, '')}
                        </ReactMarkdown>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
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
                <div className="w-8 h-8 rounded-full bg-[#2f81f7]/20 flex items-center justify-center shrink-0">
                  <Loader2 size={16} className="text-[#2f81f7] animate-spin" />
                </div>
                <div className="flex items-center gap-2 text-gray-400">
                  <span>Thinking</span>
                  <span className="flex gap-1">
                    <span className="w-1.5 h-1.5 bg-[#2f81f7] rounded-full animate-bounce" style={{ animationDelay: "0s" }} />
                    <span className="w-1.5 h-1.5 bg-[#2f81f7] rounded-full animate-bounce" style={{ animationDelay: "0.1s" }} />
                    <span className="w-1.5 h-1.5 bg-[#2f81f7] rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
                  </span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-[#374151] bg-[#111827] p-4 shrink-0">
        <form onSubmit={sendMessage} className="max-w-3xl mx-auto">
          <div className="flex items-center gap-3">
            <input
              ref={inputRef}
              type="text"
              data-testid="chat-input"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Type your response..."
              disabled={sending || assessment?.status === "completed"}
              className="flex-1 px-4 py-3 bg-[#0B1120] border border-[#374151] rounded-lg text-white focus:ring-2 focus:ring-[#2f81f7] focus:border-transparent transition-all outline-none disabled:opacity-50"
            />
            <button
              type="submit"
              data-testid="send-message-btn"
              disabled={!inputValue.trim() || sending || assessment?.status === "completed"}
              className="p-3 bg-[#2f81f7] text-white rounded-lg hover:bg-[#58a6ff] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send size={20} />
            </button>
          </div>
          {assessment?.status === "completed" && (
            <p className="text-center text-gray-500 text-sm mt-3">
              This assessment is complete.{" "}
              <Link to={`/assessments/${id}/report`} className="text-[#2f81f7] hover:text-[#58a6ff]">
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
