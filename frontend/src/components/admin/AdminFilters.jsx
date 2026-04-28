import { Search, Filter, Download } from "lucide-react";

export const AdminFilters = ({
  searchQuery,
  onSearchChange,
  statusFilter,
  onStatusChange,
  showStatusFilter,
  onExport,
  downloading,
  searchPlaceholder,
}) => (
  <div className="flex flex-col sm:flex-row gap-3">
    <div className="relative flex-1 max-w-md">
      <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#8896A5]" />
      <input
        type="text"
        data-testid="admin-search-input"
        value={searchQuery}
        onChange={(e) => onSearchChange(e.target.value)}
        className="w-full pl-10 pr-4 py-2.5 glass-input rounded-xl outline-none text-sm"
        placeholder={searchPlaceholder}
      />
    </div>
    {showStatusFilter && (
      <div className="flex items-center gap-2">
        <Filter size={16} className="text-[#8896A5]" />
        <select
          data-testid="admin-status-filter"
          value={statusFilter}
          onChange={(e) => onStatusChange(e.target.value)}
          className="px-3 py-2.5 glass-input rounded-xl outline-none text-sm"
        >
          <option value="all">All Status</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
        </select>
      </div>
    )}
    <button
      data-testid="export-csv-btn"
      onClick={onExport}
      disabled={downloading}
      className="flex items-center justify-center gap-2 px-4 py-2.5 btn-glass rounded-xl text-sm disabled:opacity-50 shrink-0"
    >
      <Download size={16} />
      {downloading ? "Exporting..." : "Export CSV"}
    </button>
  </div>
);

export default AdminFilters;
