import { Loader2, LayoutDashboard, FileText } from "lucide-react";
import { Link } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import LogoMark from "../LogoMark";
import FinalReportIndicator from "./FinalReportIndicator";

const CONTACT_EMAIL = "shalitha.samarakoonmudiyanselage@student.oulu.fi";

// Strips both fenced JSON blocks AND any loose json-like tail that starts with
// the closing-JSON marker (defensive — some AI replies break the fence)
const stripReportBlocks = (content) => {
  let out = content.replace(/```json[\s\S]*?```/g, '');
  // Remove any trailing ```json (unterminated) block
  out = out.replace(/```json[\s\S]*$/g, '');
  // Remove raw JSON object that contains ready_for_report (no fence)
  out = out.replace(/\{[\s\S]*?"ready_for_report"[\s\S]*?\n\}\s*$/g, '');
  return out.trim();
};

// The LLM often emits numbered questions as:
//   1.
//
//   **System Landscape & Integration:** ...question...
//   2.
//
//   **PLM as Decision Backbone:** ...
// That causes ReactMarkdown to render orphan "1." "2." lines detached from
// their question text. Normalise to proper single-line list items:
//   1. **System Landscape & Integration:** ...
const normalizeNumberedItems = (content) => {
  // Collapse "<num>.\n\n**..." or "<num>.\n**..." into "<num>. **..."
  return content
    .replace(/^(\s*)(\d+)\.\s*\n+\s*(\*\*)/gm, '$1$2. $3')
    // Also handle "<num>)" variants the model sometimes uses
    .replace(/^(\s*)(\d+)\)\s*\n+\s*(\*\*)/gm, '$1$2. $3');
};

const cleanContent = (content) => normalizeNumberedItems(stripReportBlocks(content));

// Detects the assistant's final "emit report" message
const isReportEmission = (msg) =>
  msg.role === "assistant" && /ready_for_report|```json|# PPDT Capability Maturity Assessment Report/i.test(msg.content || "");

const AssistantBubble = ({ content, timestamp }) => (
  <div className="chat-message-assistant">
    <div className="flex items-start gap-3">
      <LogoMark className="w-8 h-8 rounded-full shrink-0 mt-1" radius={50} />
      <div className="flex-1 min-w-0">
        <p className="text-xs text-[#C9A84C] font-medium mb-2">PortfolioHealth Advisor</p>
        <div className="text-white/80 prose prose-invert prose-sm max-w-none">
          <ReactMarkdown
            components={{
              p: ({ children }) => <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>,
              strong: ({ children }) => <strong className="text-white font-semibold">{children}</strong>,
              ul: ({ children }) => <ul className="list-disc pl-5 mb-3 space-y-2 marker:text-[#C9A84C]/70">{children}</ul>,
              ol: ({ children }) => (
                <ol className="list-decimal pl-6 mb-3 space-y-3 marker:text-[#C9A84C] marker:font-semibold">
                  {children}
                </ol>
              ),
              li: ({ children }) => <li className="pl-1 leading-relaxed">{children}</li>,
              code: ({ children }) => <code className="bg-white/[0.08] px-1 py-0.5 rounded text-[#C9A84C]">{children}</code>,
              pre: ({ children }) => <pre className="bg-white/[0.05] p-3 rounded-lg overflow-x-auto text-sm">{children}</pre>
            }}
          >
            {cleanContent(content)}
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
  <div
    data-testid="closing-statement-card"
    className="animate-fade-in p-4 sm:p-6 rounded-2xl border border-[#C9A84C]/30 bg-gradient-to-br from-[#C9A84C]/10 to-transparent backdrop-blur-xl"
  >
    <div className="flex items-center gap-3 mb-4">
      <LogoMark className="w-9 h-9 rounded-lg shrink-0" radius={14} />
      <div className="min-w-0">
        <p className="text-[10px] sm:text-[11px] uppercase tracking-[0.2em] text-[#C9A84C]">Assessment Complete</p>
        <p className="text-sm text-white/60">Your report is ready on the dashboard.</p>
      </div>
    </div>

    <h3 className="text-base sm:text-lg font-semibold text-white font-['Outfit'] mb-3 leading-snug">
      Thank you for completing this PPDT Capability Maturity Assessment.
    </h3>

    <div className="space-y-3 text-sm text-white/70 leading-relaxed">
      <p>
        This assessment is part of a Master's thesis at the University of Oulu: <em>"To develop and validate a PPM Decision-Making Capability Assessment Framework grounded in Hannila's Product Wellbeing PPDT model — identifying which organizational capability gaps most critically impair product portfolio decisions."</em> It is based on the doctoral research of Hannu Hannila and related peer-reviewed studies from the Industrial Engineering and Management department, under the supervision of Professor Janne Härkönen.
      </p>
      <p className="break-words">
        If you would like further analysis or tailored recommendations based on your results, please contact:{" "}
        <a href={`mailto:${CONTACT_EMAIL}`} className="text-[#C9A84C] hover:text-[#D4B85C] font-medium break-all">
          {CONTACT_EMAIL}
        </a>
      </p>
      <p className="text-xs text-white/45 italic">
        This report is confidential. Distribution without authorisation is not permitted.
      </p>
      <p className="text-[10px] sm:text-[11px] uppercase tracking-wider text-white/35 pt-1">
        PortfolioHealth Advisor · PPM Capability Maturity Assessment · University of Oulu
      </p>
    </div>

    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 mt-5">
      <Link
        to="/dashboard"
        data-testid="go-to-dashboard-btn"
        className="flex items-center justify-center gap-2 px-4 py-2.5 btn-liquid rounded-xl text-sm font-medium"
      >
        <LayoutDashboard size={16} />
        <span>Go to Dashboard</span>
      </Link>
      <Link
        to={`/assessments/${assessmentId}/report`}
        data-testid="view-report-inline-btn"
        className="flex items-center justify-center gap-2 px-4 py-2.5 btn-glass rounded-xl text-sm"
      >
        <FileText size={16} />
        <span>View Report Now</span>
      </Link>
    </div>
  </div>
);

export const ChatMessages = ({ messages, sending, isCompleted, assessmentId, messagesEndRef, isFinalTurn }) => {
  // When the assessment is completed OR the last message is clearly a report
  // emission (contains report header / JSON block), hide that noisy final
  // message and show the Closing Card instead.
  const lastIdx = messages.length - 1;
  const last = messages[lastIdx];
  const lastIsEmission = last && isReportEmission(last);
  const showClosing = isCompleted || lastIsEmission;
  const hideLast = showClosing && lastIsEmission;
  const visible = hideLast ? messages.slice(0, lastIdx) : messages;

  return (
    <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-4 sm:py-6 relative z-10">
      <div className="max-w-3xl mx-auto space-y-5 sm:space-y-6">
        {visible.map((msg, idx) => (
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

        {sending && (isFinalTurn ? <FinalReportIndicator /> : <TypingIndicator />)}

        {showClosing && <ClosingCard assessmentId={assessmentId} />}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default ChatMessages;
