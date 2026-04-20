import { Loader2, FileText } from "lucide-react";
import { Link } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import LogoMark from "../LogoMark";

const CONTACT_EMAIL = "shalitha.samarakoonmudiyanselage@student.oulu.fi";

const AssistantBubble = ({ content, timestamp }) => (
  <div className="chat-message-assistant">
    <div className="flex items-start gap-3">
      <LogoMark className="w-8 h-8 rounded-full shrink-0 mt-1" radius={50} />
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
            {content.replace(/```json[\s\S]*?```/g, '')}
          </ReactMarkdown>
        </div>
        <p className="text-xs text-white/25 mt-2">{new Date(timestamp).toLocaleTimeString()}</p>
      </div>
    </div>
  </div>
);

const UserBubble = ({ content, timestamp }) => (
  <div className="chat-message-user max-w-[80%] px-4 py-3">
    <p className="text-white whitespace-pre-wrap">{content}</p>
    <p className="text-xs text-white/30 mt-2">{new Date(timestamp).toLocaleTimeString()}</p>
  </div>
);

const TypingIndicator = () => (
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
);

const ClosingCard = ({ assessmentId }) => (
  <div className="animate-fade-in p-5 rounded-2xl border border-[#C9A84C]/30 bg-[#C9A84C]/5 backdrop-blur-sm" data-testid="closing-statement-card">
    <p className="text-white/80 text-sm leading-relaxed mb-4">
      Thank you for completing this capability maturity assessment. If you would like further analysis, expert input, or tailored recommendations based on your results, please reach out via email to arrange a follow-up consultation:
    </p>
    <a href={`mailto:${CONTACT_EMAIL}`} className="text-[#C9A84C] hover:text-[#D4B85C] font-medium text-sm transition-colors">
      {CONTACT_EMAIL}
    </a>
    <div className="flex gap-3 mt-4">
      <Link
        to={`/assessments/${assessmentId}/report`}
        className="flex items-center gap-2 px-4 py-2 btn-liquid rounded-xl text-sm"
        data-testid="view-report-from-chat"
      >
        <FileText size={16} />
        View Report
      </Link>
      <Link to="/dashboard" className="flex items-center gap-2 px-4 py-2 btn-glass rounded-xl text-sm">
        Go to Dashboard
      </Link>
    </div>
  </div>
);

export const ChatMessages = ({ messages, sending, isCompleted, assessmentId, messagesEndRef }) => (
  <div className="flex-1 overflow-y-auto px-6 py-6 relative z-10">
    <div className="max-w-3xl mx-auto space-y-6">
      {messages.map((msg, idx) => (
        <div
          key={idx}
          data-testid={`chat-message-${idx}`}
          className={`animate-fade-in ${msg.role === "user" ? "flex justify-end" : ""}`}
          style={{ animationDelay: `${idx * 0.05}s` }}
        >
          {msg.role === "user"
            ? <UserBubble content={msg.content} timestamp={msg.timestamp} />
            : <AssistantBubble content={msg.content} timestamp={msg.timestamp} />}
        </div>
      ))}

      {sending && <TypingIndicator />}

      {isCompleted && <ClosingCard assessmentId={assessmentId} />}

      <div ref={messagesEndRef} />
    </div>
  </div>
);

export default ChatMessages;
