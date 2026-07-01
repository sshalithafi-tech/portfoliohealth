import { useEffect, useRef, useState } from "react";
import { ChevronDown } from "lucide-react";

/**
 * Accessible dropdown for grouping secondary nav links ("Resources").
 * - aria-haspopup / aria-expanded on the trigger, role="menu"/"menuitem" on
 *   the panel + items.
 * - Keyboard: Enter/Space toggles or activates, Escape closes and returns
 *   focus to the trigger, ArrowDown/ArrowUp move between items, Home/End
 *   jump to first/last.
 * - Closes on outside click and on item selection.
 */
export const NavDropdown = ({ label, items, triggerTestId, className = "" }) => {
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);
  const triggerRef = useRef(null);
  const itemRefs = useRef([]);

  useEffect(() => {
    if (!open) return;
    const onDocClick = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [open]);

  useEffect(() => {
    if (open && itemRefs.current[0]) {
      itemRefs.current[0].focus();
    }
  }, [open]);

  const closeAndFocusTrigger = () => {
    setOpen(false);
    triggerRef.current && triggerRef.current.focus();
  };

  const onTriggerKeyDown = (e) => {
    if (e.key === "Enter" || e.key === " " || e.key === "ArrowDown") {
      e.preventDefault();
      setOpen(true);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  const onItemKeyDown = (e, idx) => {
    if (e.key === "Escape") {
      e.preventDefault();
      closeAndFocusTrigger();
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      const next = itemRefs.current[(idx + 1) % items.length];
      next && next.focus();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      const prev = itemRefs.current[(idx - 1 + items.length) % items.length];
      prev && prev.focus();
    } else if (e.key === "Home") {
      e.preventDefault();
      itemRefs.current[0] && itemRefs.current[0].focus();
    } else if (e.key === "End") {
      e.preventDefault();
      itemRefs.current[items.length - 1] && itemRefs.current[items.length - 1].focus();
    } else if (e.key === "Tab") {
      setOpen(false);
    }
  };

  return (
    <div className={`ph-nav-dropdown ${className}`} ref={containerRef}>
      <button
        type="button"
        ref={triggerRef}
        className="ph-nav-link ph-nav-dropdown-trigger"
        aria-haspopup="menu"
        aria-expanded={open}
        data-testid={triggerTestId}
        onClick={() => setOpen((v) => !v)}
        onKeyDown={onTriggerKeyDown}
      >
        {label}
        <ChevronDown size={14} className={`ph-nav-dropdown-chevron${open ? " open" : ""}`} />
      </button>
      {open && (
        <div className="ph-nav-dropdown-panel" role="menu" aria-label={label}>
          {items.map((item, idx) => (
            <button
              key={item.label}
              type="button"
              role="menuitem"
              ref={(el) => (itemRefs.current[idx] = el)}
              className="ph-nav-dropdown-item"
              onClick={() => {
                item.onClick();
                setOpen(false);
              }}
              onKeyDown={(e) => onItemKeyDown(e, idx)}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default NavDropdown;
