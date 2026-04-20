import { Send } from "lucide-react";
import { Link } from "react-router-dom";

export const ChatInput = ({ inputRef, inputValue, onChange, onSubmit, disabled, isCompleted, assessmentId }) => (
  <div className="glass-surface p-3 sm:p-4 shrink-0 relative z-10">
    <form onSubmit={onSubmit} className="max-w-3xl mx-auto">
      <div className="flex items-center gap-2 sm:gap-3">
        <input
          ref={inputRef}
          type="text"
          data-testid="chat-input"
          value={inputValue}
          onChange={onChange}
          placeholder="Type your response..."
          disabled={disabled || isCompleted}
          className="flex-1 px-3 sm:px-4 py-2.5 sm:py-3 glass-input rounded-xl outline-none disabled:opacity-50 text-sm sm:text-base"
        />
        <button
          type="submit"
          data-testid="send-message-btn"
          disabled={!inputValue.trim() || disabled || isCompleted}
          className="p-2.5 sm:p-3 btn-liquid rounded-xl disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
        >
          <Send size={18} />
        </button>
      </div>
      {isCompleted && (
        <p className="text-center text-white/40 text-sm mt-3">
          This assessment is complete.{" "}
          <Link to={`/assessments/${assessmentId}/report`} className="text-[#C9A84C] hover:text-[#C9A84C]/80">
            View the report
          </Link>
        </p>
      )}
    </form>
  </div>
);

export default ChatInput;
