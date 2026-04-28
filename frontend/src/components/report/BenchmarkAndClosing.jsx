import { CONTACT_EMAIL } from "./constants";

export const BenchmarkAndNote = ({ report }) => (
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div className="p-6 glass-surface-highlight rounded-xl">
      <h2 className="text-lg font-semibold text-[#0C1B2A] mb-4 font-['Outfit']">Benchmark Context</h2>
      <p className="text-[#4A5568] text-sm leading-relaxed">{report.benchmark_context || "No benchmark data available."}</p>
    </div>
    <div className="p-6 glass-card rounded-xl hover:border-[#C9A84C]/20">
      <h2 className="text-lg font-semibold text-[#0C1B2A] mb-4 font-['Outfit']">Consultant's Note</h2>
      <p className="text-[#4A5568] italic text-sm leading-relaxed">"{report.consultant_note || "No consultant note available."}"</p>
    </div>
  </div>
);

export const ClosingStatement = () => (
  <div className="p-6 glass-card rounded-xl border border-[#C9A84C]/20 hover:border-[#C9A84C]/30">
    <p className="text-[#4A5568] text-sm leading-relaxed mb-3">
      Thank you for completing this capability maturity assessment. If you would like further analysis, expert input, or tailored recommendations based on your results, please reach out via email to arrange a follow-up consultation:
    </p>
    <a href={`mailto:${CONTACT_EMAIL}`} className="text-[#C9A84C] hover:text-[#D4B85C] font-medium text-sm transition-colors">{CONTACT_EMAIL}</a>
  </div>
);

export const ReportFooter = () => (
  <div className="text-center py-8 border-t border-[#E2E8F0]">
    <p className="text-sm text-[#8896A5]">Based on: PPM Capability Maturity Research · University of Oulu (2026)</p>
  </div>
);
