import { Send } from "lucide-react";
import { Link } from "react-router-dom";

export const ChatInput = ({ inputRef, inputValue, onChange, onSubmit, disabled, isCompleted, assessmentId }) => (
  <div className="glass-surface p-2 sm:p-4 shrink-0 relative z-10 pb-[env(safe-area-inset-bottom)]">
    <form onSubmit={onSubmit} className="max-w-3xl mx-auto">
      <div className="flex items-center gap-2">
        <input
          ref={inputRef}
          type="text"
          data-testid="chat-input"
          value={inputValue}
          onChange={onChange}
          placeholder="Type your response..."
          disabled={disabled || isCompleted}
          autoComplete="off"
          className="flex-1 min-w-0 px-3 py-2 sm:px-4 sm:py-3 glass-input rounded-xl outline-none disabled:opacity-50 text-sm sm:text-base"
        />
        <button
          type="submit"
          data-testid="send-message-btn"
          disabled={!inputValue.trim() || disabled || isCompleted}
          aria-label="Send message"
          className="shrink-0 flex items-center justify-center w-10 h-10 sm:w-12 sm:h-12 btn-liquid rounded-xl disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send size={18} />
        </button>
      </div>
      {isCompleted && (
        <p className="text-center text-[#8896A5] text-xs sm:text-sm mt-3">
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
