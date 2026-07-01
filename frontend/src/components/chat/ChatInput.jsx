import { useEffect } from "react";
import { Send } from "lucide-react";
import { Link } from "react-router-dom";

// Cap the auto-grow height so a long multi-line message doesn't push the
// send button / page around indefinitely — after this it scrolls internally.
const MAX_TEXTAREA_HEIGHT_PX = 160;

export const ChatInput = ({ inputRef, inputValue, onChange, onSubmit, disabled, isCompleted, assessmentId }) => {
  // Auto-grow the textarea as the user types/deletes lines, then cap + scroll.
  // Runs on every inputValue change (typing, deleting, or clearing after send)
  // so the box always reflects the current content height.
  useEffect(() => {
    const el = inputRef?.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, MAX_TEXTAREA_HEIGHT_PX)}px`;
  }, [inputValue, inputRef]);

  // Enter (no Shift) submits; Shift+Enter inserts a newline via native
  // textarea behavior (we simply don't preventDefault in that case).
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit(e);
    }
  };

  return (
    <div className="glass-surface p-2 sm:p-4 shrink-0 relative z-10 pb-[env(safe-area-inset-bottom)]">
      <form onSubmit={onSubmit} className="max-w-3xl mx-auto">
        <div className="flex items-end gap-2">
          <textarea
            ref={inputRef}
            rows={1}
            data-testid="chat-input"
            value={inputValue}
            onChange={onChange}
            onKeyDown={handleKeyDown}
            placeholder="Type your response... (Shift+Enter for new line)"
            disabled={disabled || isCompleted}
            autoComplete="off"
            maxLength={8000}
            className="flex-1 min-w-0 px-3 py-2 sm:px-4 sm:py-3 glass-input rounded-xl outline-none disabled:opacity-50 text-sm sm:text-base resize-none leading-relaxed max-h-40 overflow-y-auto"
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
            <Link to={`/assessments/${assessmentId}/report`} className="text-[#0891B2] hover:text-[#0891B2]/80">
              View the report
            </Link>
          </p>
        )}
      </form>
    </div>
  );
};

export default ChatInput;
