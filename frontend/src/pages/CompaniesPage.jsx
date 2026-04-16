import { useState, useCallback } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import Layout from "../components/Layout";
import { useCompanies } from "../hooks/useData";
import { LoadingSpinner, EmptyState } from "../components/ScoreComponents";
import { 
  Plus, 
  Building2, 
  Calendar,
  ChevronRight,
  Search,
  ClipboardCheck
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

const CompanyCard = ({ company }) => (
  <div
    data-testid={`company-card-${company.id}`}
    className="p-6 glass-card rounded-xl group"
  >
    <div className="flex items-start justify-between">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-lg bg-[#2f81f7]/15 flex items-center justify-center">
          <Building2 size={24} className="text-[#2f81f7]" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white group-hover:text-[#00E5FF] transition-colors font-['Outfit']">
            {company.name}
          </h3>
          <p className="text-sm text-white/50">{company.industry}</p>
        </div>
      </div>
    </div>

    {company.portfolio_size && (
      <p className="mt-4 text-sm text-white/50">
        Portfolio: {company.portfolio_size}
      </p>
    )}

    {company.primary_challenge && (
      <p className="mt-2 text-sm text-white/30 line-clamp-2">
        {company.primary_challenge}
      </p>
    )}

    <div className="mt-4 pt-4 border-t border-white/[0.06] flex items-center justify-between">
      <div className="flex items-center gap-2 text-sm text-white/40">
        <Calendar size={14} />
        {new Date(company.created_at).toLocaleDateString()}
      </div>
      <Link
        to={`/assessments?company=${company.id}`}
        className="flex items-center gap-1 text-sm text-[#00E5FF] hover:text-[#00E5FF]/80 transition-colors"
      >
        <ClipboardCheck size={14} />
        Assessments
        <ChevronRight size={14} />
      </Link>
    </div>
  </div>
);

const CompaniesPage = () => {
  const { companies, loading, addCompany } = useCompanies();
  const [searchQuery, setSearchQuery] = useState("");
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [formData, setFormData] = useState({
    name: "", industry: "", portfolio_size: "", primary_challenge: ""
  });
  const [submitting, setSubmitting] = useState(false);

  const handleFormChange = useCallback((field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  const resetForm = useCallback(() => {
    setFormData({ name: "", industry: "", portfolio_size: "", primary_challenge: "" });
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
            <h1 className="text-2xl sm:text-3xl font-semibold text-white font-['Outfit'] tracking-tight">
              Companies
            </h1>
            <p className="text-white/50 mt-1 text-sm sm:text-base">Manage client companies for longitudinal tracking</p>
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
            <DialogContent className="glass-heavy border-white/10 text-white max-w-md rounded-2xl">
              <DialogHeader>
                <DialogTitle className="text-xl font-semibold font-['Outfit']">
                  Add New Company
                </DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <label className="text-sm text-white/50">Company Name *</label>
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
                  <label className="text-sm text-white/50">Industry *</label>
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
                  <label className="text-sm text-white/50">Portfolio Size (approx.)</label>
                  <input
                    type="text"
                    data-testid="company-portfolio-input"
                    value={formData.portfolio_size}
                    onChange={(e) => handleFormChange("portfolio_size", e.target.value)}
                    className="w-full px-4 py-3 glass-input rounded-xl outline-none"
                    placeholder="e.g., 500 products"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-white/50">Primary PPM Challenge</label>
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
          <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
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
              <CompanyCard key={company.id} company={company} />
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
