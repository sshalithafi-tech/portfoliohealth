/**
 * Utility functions for PPDT scoring and display — Corporate Navy theme
 */

export const LEVEL_NAMES = {
  1: "Ad Hoc",
  2: "Developing",
  3: "Defined",
  4: "Managed",
  5: "Predictive"
};

export const DIMENSION_LABELS = {
  people: "People",
  process: "Process",
  data: "Data",
  technology: "Technology"
};

export const getScoreColorClass = (score) => {
  if (score >= 4) return "text-[#60A5FA]";
  if (score >= 3) return "text-[#34D399]";
  if (score >= 2) return "text-[#0891B2]";
  return "text-[#EF4444]";
};

export const getScoreColor = (score) => {
  if (score >= 4) return "#60A5FA";
  if (score >= 3) return "#34D399";
  if (score >= 2) return "#0891B2";
  return "#EF4444";
};

export const getTrafficLight = (score) => {
  if (score >= 4) return "green";
  if (score >= 3) return "amber";
  return "red";
};

export const getTrafficLightBgClass = (status) => {
  if (status === "green") return "bg-[#34D399]/10 border-[#34D399]/20";
  if (status === "amber") return "bg-[#0891B2]/10 border-[#0891B2]/20";
  return "bg-[#EF4444]/10 border-[#EF4444]/20";
};

export const getLevelName = (score) => {
  const level = Math.max(1, Math.min(5, Math.round(score)));
  return LEVEL_NAMES[level] || "Unknown";
};

export const getDimensionBadgeClass = (dimension) => {
  const colors = {
    people: "bg-[#60A5FA]/12 text-[#60A5FA] border border-[#60A5FA]/20",
    process: "bg-[#34D399]/12 text-[#34D399] border border-[#34D399]/20",
    data: "bg-[#0891B2]/12 text-[#0891B2] border border-[#0891B2]/20",
    technology: "bg-[#A78BFA]/12 text-[#A78BFA] border border-[#A78BFA]/20",
    qualifier: "bg-white/[0.06] text-white/40 border border-white/10"
  };
  return colors[dimension] || colors.qualifier;
};

export const formatDate = (dateString) => {
  if (!dateString) return "N/A";
  return new Date(dateString).toLocaleDateString();
};

export const formatTime = (dateString) => {
  if (!dateString) return "";
  return new Date(dateString).toLocaleTimeString();
};

export const getItemKey = (item, index, prefix = "item") => {
  if (item?.id) return item.id;
  if (item?._id) return item._id;
  return `${prefix}-${index}`;
};

export const prepareRadarData = (scores) => {
  if (!scores) return [];
  return [
    { dimension: "People", score: scores.people || 0, fullMark: 5 },
    { dimension: "Process", score: scores.process || 0, fullMark: 5 },
    { dimension: "Data", score: scores.data || 0, fullMark: 5 },
    { dimension: "Technology", score: scores.technology || 0, fullMark: 5 },
  ];
};

export const prepareBarData = (scores) => {
  if (!scores) return [];
  return [
    { name: "People", score: scores.people || 0 },
    { name: "Process", score: scores.process || 0 },
    { name: "Data", score: scores.data || 0 },
    { name: "Technology", score: scores.technology || 0 },
  ];
};
