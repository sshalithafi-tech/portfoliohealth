import { Link } from "react-router-dom";
import { useAuth } from "../App";
import { 
  ClipboardCheck, 
  Zap, 
  Clock, 
  FileText, 
  ArrowRight,
  Target,
  BarChart3
} from "lucide-react";

import LogoMark from "../components/LogoMark";

const LandingPage = () => {
  const { user } = useAuth();

  return (
    <div className="min-h-screen relative">
      {/* Hero Background */}
      <div className="absolute inset-0 z-0" style={{
        background: "radial-gradient(ellipse 70% 50% at 30% 0%, rgba(201, 168, 76, 0.06) 0%, transparent 60%), radial-gradient(ellipse 50% 40% at 70% 100%, rgba(96, 165, 250, 0.04) 0%, transparent 50%)"
      }} />

      {/* Glass Header */}
      <header className="glass-surface-highlight fixed top-0 left-0 right-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4 flex items-center justify-between">
          <div className="flex items-center gap-2 sm:gap-3 min-w-0">
            <LogoMark className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg sm:rounded-xl shrink-0" radius={18} />
            <div className="hidden sm:block">
              <h1 className="text-white font-semibold font-['Outfit']">PortfolioHealth</h1>
              <p className="text-xs text-white/40">PPM Assessment</p>
            </div>
          </div>
          <div className="flex items-center gap-2 sm:gap-4">
            {user ? (
              <Link
                to="/dashboard"
                data-testid="go-to-dashboard-btn"
                className="px-4 sm:px-5 py-2 btn-liquid rounded-lg text-sm sm:text-base"
              >
                Dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  data-testid="login-nav-btn"
                  className="px-3 sm:px-4 py-2 text-white/65 hover:text-white transition-colors text-sm sm:text-base"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  data-testid="register-nav-btn"
                  className="px-4 sm:px-5 py-2 btn-liquid rounded-lg text-sm sm:text-base"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <div className="relative z-10 pt-24 sm:pt-32 pb-12 sm:pb-20 px-4 sm:px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="flex items-center justify-center gap-4 mb-6 sm:mb-8">
            <LogoMark className="w-16 sm:w-20 h-16 sm:h-20 rounded-2xl drop-shadow-[0_0_20px_rgba(201,168,76,0.35)]" radius={22} />
          </div>
          <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-light text-white font-['Outfit'] tracking-tight mb-4 sm:mb-6">
            Portfolio<span className="font-semibold text-[#C9A84C]">Health</span>
            <span className="block text-2xl sm:text-3xl md:text-4xl mt-2 text-white/50">Advisor</span>
          </h1>
          <p className="text-base sm:text-lg text-white/60 max-w-2xl mx-auto mb-8 sm:mb-12 px-2">
            Assess your organisation's readiness for data-driven Product Portfolio Management decisions using the PPM Capability Maturity Framework.
          </p>
          
          {/* Two CTA Options */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 max-w-3xl mx-auto">
            {/* Quick Assessment */}
            <Link
              to="/quick-assessment"
              data-testid="quick-assessment-cta"
              className="group p-6 sm:p-8 glass-card rounded-2xl text-left hover:border-[#C9A84C]/30"
            >
              <div className="w-14 h-14 rounded-xl bg-[#C9A84C]/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Zap size={28} className="text-[#C9A84C]" />
              </div>
              <h2 className="text-xl sm:text-2xl font-semibold text-white mb-2 font-['Outfit']">
                Quick Check
              </h2>
              <p className="text-white/50 mb-4 text-sm sm:text-base">
                10-minute rapid screening with instant results
              </p>
              <div className="flex flex-wrap gap-3 mb-6">
                <span className="px-3 py-1 bg-white/[0.06] rounded-full text-xs text-white/60 flex items-center gap-1 border border-white/[0.06]">
                  <Clock size={12} /> 10 min
                </span>
                <span className="px-3 py-1 bg-white/[0.06] rounded-full text-xs text-white/60 border border-white/[0.06]">
                  15 questions
                </span>
                <span className="px-3 py-1 bg-white/[0.06] rounded-full text-xs text-white/60 border border-white/[0.06]">
                  No login required
                </span>
              </div>
              <div className="flex items-center gap-2 text-[#C9A84C] font-medium group-hover:gap-3 transition-all">
                Start Quick Check <ArrowRight size={18} />
              </div>
            </Link>

            {/* Full Assessment */}
            <Link
              to={user ? "/assessments" : "/login"}
              data-testid="full-assessment-cta"
              className="group p-6 sm:p-8 glass-card rounded-2xl text-left hover:border-[#34D399]/30"
            >
              <div className="w-14 h-14 rounded-xl bg-[#34D399]/15 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <ClipboardCheck size={28} className="text-[#34D399]" />
              </div>
              <h2 className="text-2xl font-semibold text-white mb-2 font-['Outfit']">
                Full Assessment
              </h2>
              <p className="text-white/50 mb-4">
                AI-guided deep-dive with comprehensive roadmap
              </p>
              <div className="flex flex-wrap gap-3 mb-6">
                <span className="px-3 py-1 bg-white/[0.06] rounded-full text-xs text-white/60 flex items-center gap-1 border border-white/[0.06]">
                  <Clock size={12} /> 60-90 min
                </span>
                <span className="px-3 py-1 bg-white/[0.06] rounded-full text-xs text-white/60 border border-white/[0.06]">
                  AI-powered
                </span>
                <span className="px-3 py-1 bg-white/[0.06] rounded-full text-xs text-white/60 border border-white/[0.06]">
                  Detailed report
                </span>
              </div>
              <div className="flex items-center gap-2 text-[#34D399] font-medium group-hover:gap-3 transition-all">
                {user ? "Start Full Assessment" : "Sign In to Start"} <ArrowRight size={18} />
              </div>
            </Link>
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="relative z-10 py-12 sm:py-20 px-4 sm:px-6 border-t border-white/[0.06]">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-xl sm:text-2xl font-semibold text-white text-center mb-8 sm:mb-12 font-['Outfit']">
            The PPDT Framework
          </h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6">
            {[
              { icon: Target, label: "People", desc: "Culture, roles & data literacy" },
              { icon: ClipboardCheck, label: "Process", desc: "Governance & lifecycle management" },
              { icon: BarChart3, label: "Data", desc: "Quality, integration & profitability" },
              { icon: FileText, label: "Technology", desc: "Systems integration & decision support" }
            ].map(({ icon: Icon, label, desc }) => (
              <div key={label} className="p-4 sm:p-6 glass-card rounded-xl text-center">
                <div className="w-10 sm:w-12 h-10 sm:h-12 rounded-lg bg-[#C9A84C]/10 flex items-center justify-center mx-auto mb-3 sm:mb-4">
                  <Icon size={20} className="text-[#C9A84C] sm:hidden" />
                  <Icon size={24} className="text-[#C9A84C] hidden sm:block" />
                </div>
                <h3 className="text-base sm:text-lg font-semibold text-white mb-1 sm:mb-2">{label}</h3>
                <p className="text-xs sm:text-sm text-white/50">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/[0.06] py-8 px-6">
        <div className="max-w-5xl mx-auto flex flex-col items-center gap-3 text-sm text-white/40">
          <p>Academically grounded in published PPM research · University of Oulu</p>
          <p className="text-xs text-white/25 text-center max-w-2xl">
            This tool is an independent academic research output developed as part of a Master's thesis at the University of Oulu (IEM–IPIC, 2026). Assessment methodology is grounded in peer-reviewed PPM research. Not affiliated with or endorsed by any commercial framework.
          </p>
          <p>© {new Date().getFullYear()} PortfolioHealth Advisor</p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
