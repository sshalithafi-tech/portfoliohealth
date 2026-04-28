import { CheckCircle, AlertTriangle, AlertCircle } from "lucide-react";
import { getTrafficLightBgClass } from "../utils/scoring";

/**
 * Traffic light indicator icon
 */
export const TrafficLightIcon = ({ status, size = 20 }) => {
  if (status === "green") return <CheckCircle size={size} className="text-[#34D399]" />;
  if (status === "amber") return <AlertTriangle size={size} className="text-[#C9A84C]" />;
  return <AlertCircle size={size} className="text-[#EF4444]" />;
};

/**
 * Assessment status badge
 */
export const StatusBadge = ({ status }) => {
  if (status === "completed") {
    return (
      <span className="px-3 py-1 text-xs rounded-full bg-[#34D399]/15 text-[#34D399] border border-[#34D399]/20">
        Completed
      </span>
    );
  }
  return (
    <span className="px-3 py-1 text-xs rounded-full bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/20">
      In Progress
    </span>
  );
};

/**
 * Traffic light badge with icon
 */
export const TrafficLightBadge = ({ status }) => {
  return (
    <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full border ${getTrafficLightBgClass(status)}`}>
      <TrafficLightIcon status={status} size={16} />
      <span className="text-sm font-medium text-[#0C1B2A] capitalize">{status} Status</span>
    </div>
  );
};

/**
 * Loading spinner
 */
export const LoadingSpinner = ({ className = "" }) => (
  <div className={`flex items-center justify-center ${className}`}>
    <div className="animate-pulse-glow w-12 h-12 rounded-full bg-[#C9A84C]/15 flex items-center justify-center">
      <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#60A5FA] to-[#C9A84C]" />
    </div>
  </div>
);

/**
 * Score display with color
 */
export const ScoreDisplay = ({ score, size = "lg", showMax = true }) => {
  const getColorClass = (s) => {
    if (s >= 4) return "text-[#C9A84C]";
    if (s >= 3) return "text-[#34D399]";
    if (s >= 2) return "text-[#C9A84C]";
    return "text-[#EF4444]";
  };

  const sizeClasses = {
    sm: "text-xl",
    md: "text-2xl",
    lg: "text-3xl",
    xl: "text-6xl"
  };

  return (
    <div className="flex items-baseline gap-2">
      <span className={`font-bold font-['JetBrains_Mono'] ${sizeClasses[size]} ${getColorClass(score)}`}>
        {typeof score === 'number' ? score.toFixed(1) : score}
      </span>
      {showMax && <span className="text-[#8896A5]">/ 5</span>}
    </div>
  );
};

/**
 * Progress bar
 */
export const ProgressBar = ({ value, max = 100, color = "#C9A84C" }) => {
  const percentage = (value / max) * 100;
  return (
    <div className="w-full h-2 bg-[#F8F9FA] rounded-full overflow-hidden">
      <div 
        className="h-full rounded-full transition-all duration-500"
        style={{ width: `${percentage}%`, backgroundColor: color }}
      />
    </div>
  );
};

/**
 * Numbered list item
 */
export const NumberedListItem = ({ index, children, color = "#C9A84C" }) => (
  <li className="flex items-start gap-3">
    <span 
      className="w-6 h-6 rounded-full flex items-center justify-center text-xs shrink-0 mt-0.5"
      style={{ backgroundColor: `${color}15`, color }}
    >
      {index + 1}
    </span>
    <p className="text-[#4A5568] text-sm">{children}</p>
  </li>
);

/**
 * Arrow list item
 */
export const ArrowListItem = ({ children, color = "#C9A84C" }) => (
  <li className="flex items-start gap-2 text-sm text-[#4A5568]">
    <span style={{ color }}>→</span>
    {children}
  </li>
);

/**
 * Alert list item
 */
export const AlertListItem = ({ children }) => (
  <li className="flex items-start gap-3">
    <span className="w-6 h-6 rounded-full bg-[#EF4444]/15 text-[#EF4444] flex items-center justify-center text-xs shrink-0 mt-0.5">
      !
    </span>
    <p className="text-[#4A5568] text-sm">{children}</p>
  </li>
);

/**
 * Empty state
 */
export const EmptyState = ({ icon: Icon, title, description, action }) => (
  <div className="flex flex-col items-center justify-center py-16 text-[#8896A5]">
    {Icon && <Icon size={64} className="mb-4 opacity-30" />}
    <p className="text-lg">{title}</p>
    {description && <p className="text-sm mt-2 text-[#8896A5]">{description}</p>}
    {action && <div className="mt-6">{action}</div>}
  </div>
);
