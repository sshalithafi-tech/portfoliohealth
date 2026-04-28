import { Building2, Briefcase, Users2, Layers, Package, Calendar, UserRound, Target } from "lucide-react";

const InfoTile = ({ icon: Icon, label, value, accent = "#C9A84C", testId }) => {
  if (!value) return null;
  return (
    <div
      data-testid={testId}
      className="flex items-start gap-3 p-3.5 rounded-xl bg-white/[0.025] border border-[#E2E8F0] hover:border-[#E2E8F0] transition-colors"
    >
      <div
        className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
        style={{ backgroundColor: `${accent}14`, border: `1px solid ${accent}22` }}
      >
        <Icon size={15} style={{ color: accent }} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[10px] uppercase tracking-[0.14em] text-[#8896A5] font-semibold">{label}</p>
        <p className="text-sm font-semibold text-[#0C1B2A] mt-0.5 font-['Outfit'] leading-snug truncate">
          {value}
        </p>
      </div>
    </div>
  );
};

export const PortfolioContext = ({ assessment, report }) => {
  const companyName = assessment.company_name;
  const industry = assessment.company_industry || assessment.industry;
  const companySize =
    assessment.company_size ||
    assessment.portfolio_size ||
    report?.company_size ||
    report?.portfolio_size;
  const businessModel = report?.business_model || assessment.business_model;
  const strategicPriority = report?.strategic_priority || assessment.strategic_priority;
  const activeProducts =
    report?.active_products ||
    assessment.active_products ||
    report?.num_products;
  const respondentRole = assessment.respondent_role;
  const respondentName = assessment.respondent_name;
  const reportDate = new Date(assessment.completed_at || assessment.created_at).toLocaleDateString(
    undefined,
    { year: "numeric", month: "short", day: "numeric" }
  );

  return (
    <div data-testid="portfolio-context-card" className="glass-surface-highlight rounded-2xl overflow-hidden">
      <div className="p-5 sm:p-6 border-b border-[#E2E8F0] bg-gradient-to-br from-[#C9A84C]/[0.05] to-transparent">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-[#C9A84C]/25 to-[#C9A84C]/5 border border-[#C9A84C]/25 flex items-center justify-center shrink-0">
              <Building2 size={20} className="text-[#C9A84C]" />
            </div>
            <div className="min-w-0">
              <p className="text-[10px] uppercase tracking-[0.18em] text-[#C9A84C] font-semibold">
                Portfolio Context
              </p>
              <h2 className="text-lg sm:text-xl font-semibold text-[#0C1B2A] font-['Outfit'] leading-tight truncate">
                {companyName}
              </h2>
              {industry && (
                <p className="text-xs text-[#8896A5] mt-0.5 truncate">{industry}</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-1.5 text-[11px] text-[#8896A5]">
            <Calendar size={12} />
            <span>{reportDate}</span>
          </div>
        </div>
      </div>

      <div className="p-5 sm:p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <InfoTile icon={Briefcase} label="Industry" value={industry} accent="#60A5FA" testId="ctx-industry" />
        <InfoTile icon={Users2} label="Company Size" value={companySize} accent="#A78BFA" testId="ctx-company-size" />
        <InfoTile icon={Layers} label="Business Model" value={businessModel} accent="#C9A84C" testId="ctx-business-model" />
        <InfoTile icon={Package} label="Active Products" value={activeProducts} accent="#34D399" testId="ctx-active-products" />
        <InfoTile icon={Target} label="Strategic Priority" value={strategicPriority} accent="#F97316" testId="ctx-strategic-priority" />
        <InfoTile
          icon={UserRound}
          label="Respondent"
          value={respondentName && respondentRole ? `${respondentName} · ${respondentRole}` : respondentName || respondentRole}
          accent="#60A5FA"
          testId="ctx-respondent"
        />
      </div>

      {report?.business_model_note && (
        <div className="px-5 sm:px-6 pb-5 -mt-1">
          <p
            data-testid="business-model-note"
            className="text-[11px] italic text-[#8896A5] leading-relaxed"
          >
            {report.business_model_note}
          </p>
        </div>
      )}
    </div>
  );
};

export default PortfolioContext;
