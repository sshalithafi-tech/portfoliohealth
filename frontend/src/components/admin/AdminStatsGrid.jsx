import { ClipboardCheck, TrendingUp, Zap, Building2, Users } from "lucide-react";

const AdminStatCard = ({ icon: Icon, label, value, color = "#0891B2" }) => (
  <div className="p-4 sm:p-5 glass-card rounded-xl">
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0" style={{ backgroundColor: `${color}15` }}>
        <Icon size={20} style={{ color }} />
      </div>
      <div>
        <p className="text-[#4A5568] text-xs">{label}</p>
        <p className="text-xl font-semibold text-[#0C1B2A] font-['JetBrains_Mono']">{value}</p>
      </div>
    </div>
  </div>
);

export const AdminStatsGrid = ({ stats }) => {
  if (!stats) return null;
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4 stagger-children">
      <AdminStatCard icon={ClipboardCheck} label="Full Assessments" value={stats.total_assessments} color="#60A5FA" />
      <AdminStatCard icon={TrendingUp} label="Completed" value={stats.completed_assessments} color="#34D399" />
      <AdminStatCard icon={Zap} label="Quick Assessments" value={stats.total_quick_assessments} color="#0891B2" />
      <AdminStatCard icon={Building2} label="Companies" value={stats.total_companies} color="#A78BFA" />
      <AdminStatCard icon={Users} label="Users" value={stats.total_users} color="#0891B2" />
      <AdminStatCard icon={ClipboardCheck} label="In Progress" value={stats.in_progress_assessments} color="#EF4444" />
    </div>
  );
};

export default AdminStatsGrid;
