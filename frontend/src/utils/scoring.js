/**
 * Utility functions for PPDT scoring and display
 */

export const LEVEL_NAMES = {
  1: "Ad Hoc",
  2: "Developing",
  3: "Defined",
  4: "Managed",
  5: "Optimising"
};

export const DIMENSION_LABELS = {
  people: "People",
  process: "Process",
  data: "Data",
  technology: "Technology"
};

/**
 * Get Tailwind color class based on score
 */
export const getScoreColorClass = (score) => {
  if (score >= 4) return "text-[#2f81f7]";
  if (score >= 3) return "text-[#238636]";
  if (score >= 2) return "text-[#D29922]";
  return "text-[#F85149]";
};

/**
 * Get hex color based on score
 */
export const getScoreColor = (score) => {
  if (score >= 4) return "#2f81f7";
  if (score >= 3) return "#238636";
  if (score >= 2) return "#D29922";
  return "#F85149";
};

/**
 * Get traffic light status based on score
 */
export const getTrafficLight = (score) => {
  if (score >= 4) return "green";
  if (score >= 3) return "amber";
  return "red";
};

/**
 * Get traffic light background class
 */
export const getTrafficLightBgClass = (status) => {
  if (status === "green") return "bg-[#238636]/20 border-[#238636]/30";
  if (status === "amber") return "bg-[#D29922]/20 border-[#D29922]/30";
  return "bg-[#F85149]/20 border-[#F85149]/30";
};

/**
 * Get level name from score
 */
export const getLevelName = (score) => {
  const level = Math.max(1, Math.min(5, Math.round(score)));
  return LEVEL_NAMES[level] || "Unknown";
};

/**
 * Get dimension badge color class
 */
export const getDimensionBadgeClass = (dimension) => {
  const colors = {
    people: "bg-[#2f81f7]/20 text-[#2f81f7]",
    process: "bg-[#238636]/20 text-[#238636]",
    data: "bg-[#D29922]/20 text-[#D29922]",
    technology: "bg-[#A371F7]/20 text-[#A371F7]",
    qualifier: "bg-gray-500/20 text-gray-400"
  };
  return colors[dimension] || colors.qualifier;
};

/**
 * Format date for display
 */
export const formatDate = (dateString) => {
  if (!dateString) return "N/A";
  return new Date(dateString).toLocaleDateString();
};

/**
 * Format time for display
 */
export const formatTime = (dateString) => {
  if (!dateString) return "";
  return new Date(dateString).toLocaleTimeString();
};

/**
 * Generate unique key for list items
 * Falls back to index if no id available
 */
export const getItemKey = (item, index, prefix = "item") => {
  if (item?.id) return item.id;
  if (item?._id) return item._id;
  return `${prefix}-${index}`;
};

/**
 * Prepare radar chart data from scores
 */
export const prepareRadarData = (scores) => {
  if (!scores) return [];
  return [
    { dimension: "People", score: scores.people || 0, fullMark: 5 },
    { dimension: "Process", score: scores.process || 0, fullMark: 5 },
    { dimension: "Data", score: scores.data || 0, fullMark: 5 },
    { dimension: "Technology", score: scores.technology || 0, fullMark: 5 },
  ];
};

/**
 * Prepare bar chart data from scores
 */
export const prepareBarData = (scores) => {
  if (!scores) return [];
  return [
    { name: "People", score: scores.people || 0 },
    { name: "Process", score: scores.process || 0 },
    { name: "Data", score: scores.data || 0 },
    { name: "Technology", score: scores.technology || 0 },
  ];
};
