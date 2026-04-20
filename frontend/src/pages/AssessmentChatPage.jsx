import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import ChatHeader from "../components/chat/ChatHeader";
import PhaseIndicator from "../components/chat/PhaseIndicator";
import ChatMessages from "../components/chat/ChatMessages";
import ChatInput from "../components/chat/ChatInput";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const phaseFromMessageCount = (count) => {
  if (count <= 4) return "welcome";
  if (count <= 14) return "people";
  if (count <= 24) return "process";
  if (count <= 38) return "data";
  if (count <= 48) return "technology";
  if (count <= 54) return "decision";
  if (count <= 58) return "benchmark";
  return "report";
};

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

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const startAssessment = useCallback(async () => {
    try {
      const response = await axios.post(`${BACKEND_URL}/api/assessments/${id}/start`);
      setMessages([response.data.message]);
    } catch (err) {
      console.error("Failed to start assessment:", err);
      toast.error("Failed to start assessment");
    }
  }, [id]);

  const fetchAssessment = useCallback(async () => {
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
  }, [id, navigate, startAssessment]);

  useEffect(() => {
    fetchAssessment();
  }, [fetchAssessment]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || sending) return;

    const userMessage = inputValue.trim();
    setInputValue("");
    setSending(true);

    const tempUserMsg = { role: "user", content: userMessage, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, tempUserMsg]);

    try {
      const response = await axios.post(`${BACKEND_URL}/api/assessments/${id}/chat`, {
        message: userMessage
      });

      setMessages(prev => [...prev, response.data.message]);

      if (response.data.report_ready) {
        toast.success("Assessment complete! Redirecting to dashboard...");
        setAssessment(prev => ({ ...prev, status: "completed" }));
        setTimeout(() => navigate("/dashboard"), 3000);
      }

      setCurrentPhase(phaseFromMessageCount(messages.length + 2));
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse-glow w-12 h-12 rounded-full bg-[#C9A84C]/15 flex items-center justify-center">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#60A5FA] to-[#C9A84C]" />
        </div>
      </div>
    );
  }

  const isCompleted = assessment?.status === "completed";

  return (
    <div className="min-h-screen flex flex-col">
      <ChatHeader assessment={assessment} assessmentId={id} />
      <PhaseIndicator currentPhase={currentPhase} />
      <ChatMessages
        messages={messages}
        sending={sending}
        isCompleted={isCompleted}
        assessmentId={id}
        messagesEndRef={messagesEndRef}
      />
      <ChatInput
        inputRef={inputRef}
        inputValue={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onSubmit={sendMessage}
        disabled={sending}
        isCompleted={isCompleted}
        assessmentId={id}
      />
    </div>
  );
};

export default AssessmentChatPage;
