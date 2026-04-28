import { useState, useCallback } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import Layout from "../components/Layout";
import { useCompanies } from "../hooks/useData";
import { getScoreColorClass } from "../utils/scoring";
import { LoadingSpinner, EmptyState } from "../components/ScoreComponents";
import { 
  Plus, 
  Building2, 
  Calendar,
  ChevronRight,
  Search,
  ClipboardCheck,
  Trash2,
  Download,
  MoreVertical
} from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const INDUSTRIES = [
  "Manufacturing", "Technology", "Healthcare", "Retail",
  "Financial Services", "Automotive", "Energy",
  "Telecommunications", "Consumer Goods", "Industrial Equipment", "Other"
];

const CompanyCard = ({ company, onDelete }) => {
  const [showActions, setShowActions] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await axios.delete(`${BACKEND_URL}/api/companies/${company.id}`);
      toast.success(`${company.name} deleted`);
      onDelete(company.id);
    } catch {
      toast.error("Failed to delete company");
    } finally {
      setDeleting(false);
      setShowConfirm(false);
    }
  };

  const downloadPDF = async (type) => {
    try {
      // For full assessment, find the latest completed assessment
      const res = await axios.get(`${BACKEND_URL}/api/companies/${company.id}/assessments`);
      const assessments = res.data;
      const completed = assessments.find(a => a.status === "completed");
      
      if (type === "full" && completed) {
        const pdfRes = await axios.get(`${BACKEND_URL}/api/assessments/${completed.id}/pdf`, { responseType: "blob" });
        const url = window.URL.createObjectURL(new Blob([pdfRes.data]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", `${company.name.replace(/\s+/g, "_")}_Full_Assessment.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        toast.success("PDF downloaded");
      } else if (type === "full") {
        toast.info("No completed assessment found for this company");
      }
    } catch {
      toast.error("Failed to download");
    }
    setShowActions(false);
  };

  return (
    <div
      data-testid={`company-card-${company.id}`}
      className="p-5 sm:p-6 glass-card rounded-xl group relative"
    >
      {/* Actions Menu */}
      <div className="absolute top-4 right-4 z-10">
        <button
          data-testid={`company-actions-${company.id}`}
          onClick={() => setShowActions(!showActions)}
          className="p-1.5 rounded-lg text-[#8896A5] hover:text-[#0C1B2A] hover:bg-[#F8F9FA] transition-all"
        >
          <MoreVertical size={18} />
        </button>
        {showActions && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setShowActions(false)} />
            <div className="absolute right-0 top-10 w-48 rounded-xl shadow-2xl z-50 py-1 animate-fade-in border border-[#E2E8F0]"
                 style={{ background: 'rgba(13,17,23,0.95)', backdropFilter: 'blur(20px)' }}>
              <button
                data-testid={`download-full-${company.id}`}
                onClick={() => downloadPDF("full")}
                className="w-full flex items-center gap-2 px-3 py-2 text-xs text-[#4A5568] hover:text-[#0C1B2A] hover:bg-[#F8F9FA] transition-colors"
              >
                <Download size={13} /> Download Report
              </button>
              <Link
                to={`/assessments?company=${company.id}`}
                className="w-full flex items-center gap-2 px-3 py-2 text-xs text-[#4A5568] hover:text-[#0C1B2A] hover:bg-[#F8F9FA] transition-colors"
                onClick={() => setShowActions(false)}
              >
                <ClipboardCheck size={13} /> View Assessments
              </Link>
              <hr className="border-[#E2E8F0] my-0.5" />
              <button
                data-testid={`delete-company-${company.id}`}
                onClick={() => { setShowConfirm(true); setShowActions(false); }}
                className="w-full flex items-center gap-2 px-3 py-2 text-xs text-[#EF4444] hover:bg-[#EF4444]/10 transition-colors"
              >
                <Trash2 size={13} /> Delete Company
              </button>
            </div>
          </>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      {showConfirm && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4" onClick={() => setShowConfirm(false)}>
          <div className="glass-heavy rounded-2xl p-6 max-w-sm w-full animate-fade-in" onClick={e => e.stopPropagation()} data-testid="delete-confirm-dialog">
            <h3 className="text-lg font-semibold text-[#0C1B2A] font-['Outfit'] mb-3">Delete Company?</h3>
            <p className="text-[#4A5568] text-sm mb-6">
              Are you sure you want to delete <strong className="text-[#0C1B2A]">{company.name}</strong> and all associated assessments? This cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowConfirm(false)}
                className="flex-1 py-2.5 btn-glass rounded-xl text-sm"
              >
                Cancel
              </button>
              <button
                data-testid="confirm-delete-btn"
                onClick={handleDelete}
                disabled={deleting}
                className="flex-1 py-2.5 bg-[#EF4444] text-[#0C1B2A] rounded-xl text-sm hover:bg-[#EF4444]/80 transition-colors disabled:opacity-50"
              >
                {deleting ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="flex items-start gap-3 pr-8">
        <div className="w-12 h-12 rounded-lg bg-[#60A5FA]/15 flex items-center justify-center shrink-0">
          <Building2 size={24} className="text-[#60A5FA]" />
        </div>
        <div className="min-w-0">
          <h3 className="text-lg font-semibold text-[#0C1B2A] group-hover:text-[#C9A84C] transition-colors font-['Outfit'] truncate">
            {company.name}
          </h3>
          <p className="text-sm text-[#4A5568]">{company.industry}</p>
        </div>
      </div>

      {/* Assessment status badges */}
      <div className="flex flex-wrap gap-2 mt-4">
        {company.completed_count > 0 && (
          <span className="px-2.5 py-1 text-xs rounded-full bg-[#34D399]/15 text-[#34D399] border border-[#34D399]/20">
            {company.completed_count} Completed
          </span>
        )}
        {(company.assessment_count - (company.completed_count || 0)) > 0 && (
          <span className="px-2.5 py-1 text-xs rounded-full bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/20">
            {company.assessment_count - (company.completed_count || 0)} In Progress
          </span>
        )}
        {company.latest_score && (
          <span className={`px-2.5 py-1 text-xs rounded-full font-['JetBrains_Mono'] font-semibold ${getScoreColorClass(company.latest_score)} bg-[#F8F9FA] border border-[#E2E8F0]`}>
            Score: {company.latest_score.toFixed(1)}
          </span>
        )}
      </div>

      {(company.portfolio_size || company.company_size || company.active_products) && (
        <div className="mt-3 space-y-1 text-sm text-[#8896A5]">
          {company.company_size && <p><span className="text-[#8896A5]">Size:</span> {company.company_size}</p>}
          {company.active_products && <p><span className="text-[#8896A5]">Products:</span> {company.active_products}</p>}
          {company.portfolio_size && !company.company_size && <p><span className="text-[#8896A5]">Portfolio:</span> {company.portfolio_size}</p>}
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-[#E2E8F0] flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-[#8896A5]">
          <Calendar size={14} />
          {new Date(company.created_at).toLocaleDateString()}
        </div>
        <Link
          to={`/assessments?company=${company.id}`}
          className="flex items-center gap-1 text-sm text-[#C9A84C] hover:text-[#C9A84C]/80 transition-colors"
        >
          <ClipboardCheck size={14} />
          Assessments
          <ChevronRight size={14} />
        </Link>
      </div>
    </div>
  );
};

const CompaniesPage = () => {
  const { companies, loading, addCompany, setCompanies } = useCompanies();
  const [searchQuery, setSearchQuery] = useState("");
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [formData, setFormData] = useState({
    name: "", industry: "", portfolio_size: "",
    company_size: "", active_products: "",
    primary_challenge: ""
  });
  const [submitting, setSubmitting] = useState(false);

  const handleFormChange = useCallback((field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  const resetForm = useCallback(() => {
    setFormData({
      name: "", industry: "", portfolio_size: "",
      company_size: "", active_products: "",
      primary_challenge: ""
    });
  }, []);

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/companies`, formData);
      addCompany(response.data);
      setShowAddDialog(false);
      resetForm();
      toast.success("Company added successfully");
    } catch (err) {
      toast.error("Failed to add company");
    } finally {
      setSubmitting(false);
    }
  }, [formData, addCompany, resetForm]);

  const handleDelete = useCallback((companyId) => {
    setCompanies(prev => prev.filter(c => c.id !== companyId));
  }, [setCompanies]);

  const filteredCompanies = companies.filter(c => 
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.industry.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <Layout>
        <LoadingSpinner className="h-64" />
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-semibold text-[#0C1B2A] font-['Outfit'] tracking-tight">
              Companies
            </h1>
            <p className="text-[#4A5568] mt-1 text-sm sm:text-base">Manage client companies for longitudinal tracking</p>
          </div>
          <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
            <DialogTrigger asChild>
              <button
                data-testid="add-company-btn"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 btn-liquid rounded-xl w-full sm:w-auto"
              >
                <Plus size={18} />
                Add Company
              </button>
            </DialogTrigger>
            <DialogContent className="glass-heavy border-[#E2E8F0] text-[#0C1B2A] max-w-md rounded-2xl">
              <DialogHeader>
                <DialogTitle className="text-xl font-semibold font-['Outfit']">
                  Add New Company
                </DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <label className="text-sm text-[#4A5568]">Company Name *</label>
                  <input
                    type="text"
                    data-testid="company-name-input"
                    value={formData.name}
                    onChange={(e) => handleFormChange("name", e.target.value)}
                    className="w-full px-4 py-3 glass-input rounded-xl outline-none"
                    placeholder="Acme Corporation"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-[#4A5568]">Industry *</label>
                  <select
                    data-testid="company-industry-select"
                    value={formData.industry}
                    onChange={(e) => handleFormChange("industry", e.target.value)}
                    className="w-full px-4 py-3 glass-input rounded-xl outline-none"
                    required
                  >
                    <option value="">Select industry</option>
                    {INDUSTRIES.map(ind => (
                      <option key={ind} value={ind}>{ind}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-[#4A5568]">Portfolio Size (approx.)</label>
                  <input
                    type="text"
                    data-testid="company-portfolio-input"
                    value={formData.portfolio_size}
                    onChange={(e) => handleFormChange("portfolio_size", e.target.value)}
                    className="w-full px-4 py-3 glass-input rounded-xl outline-none"
                    placeholder="e.g., 500 products"
                  />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <label className="text-sm text-[#4A5568]">Company Size</label>
                    <input
                      type="text"
                      data-testid="company-size-input"
                      value={formData.company_size}
                      onChange={(e) => handleFormChange("company_size", e.target.value)}
                      className="w-full px-4 py-3 glass-input rounded-xl outline-none"
                      placeholder="e.g., 450 employees"
                    />
                    <p className="text-[11px] text-[#8896A5] italic">Shown on the report cover and Portfolio Context card.</p>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm text-[#4A5568]">Active Products</label>
                    <input
                      type="text"
                      data-testid="company-active-products-input"
                      value={formData.active_products}
                      onChange={(e) => handleFormChange("active_products", e.target.value)}
                      className="w-full px-4 py-3 glass-input rounded-xl outline-none"
                      placeholder="e.g., 28 active SKUs"
                    />
                    <p className="text-[11px] text-[#8896A5] italic">Optional \u2014 appears in the PDF Portfolio Context.</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-[#4A5568]">Primary PPM Challenge</label>
                  <textarea
                    data-testid="company-challenge-input"
                    value={formData.primary_challenge}
                    onChange={(e) => handleFormChange("primary_challenge", e.target.value)}
                    className="w-full px-4 py-3 glass-input rounded-xl outline-none resize-none"
                    rows={3}
                    placeholder="Describe their main PPM challenge..."
                  />
                </div>
                <button
                  type="submit"
                  data-testid="submit-company-btn"
                  disabled={submitting}
                  className="w-full py-3 px-6 btn-liquid rounded-xl disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {submitting ? "Adding..." : "Add Company"}
                </button>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Search */}
        <div className="relative max-w-md">
          <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-[#8896A5]" />
          <input
            type="text"
            data-testid="company-search-input"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-12 pr-4 py-3 glass-input rounded-xl outline-none"
            placeholder="Search companies..."
          />
        </div>

        {/* Companies Grid */}
        {filteredCompanies.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 stagger-children">
            {filteredCompanies.map((company) => (
              <CompanyCard key={company.id} company={company} onDelete={handleDelete} />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={Building2}
            title="No companies found"
            description="Add your first company to start tracking assessments"
          />
        )}
      </div>
    </Layout>
  );
};

export default CompaniesPage;
