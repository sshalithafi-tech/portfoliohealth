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

const LandingPage = () => {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-[#0B1120]">
      {/* Header */}
      <header className="border-b border-[#374151] bg-[#111827]/80 backdrop-blur-sm fixed top-0 left-0 right-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-[#2f81f7] flex items-center justify-center">
              <span className="text-white font-bold">P</span>
            </div>
            <div>
              <h1 className="text-white font-semibold font-['Outfit']">PortfolioHealth</h1>
              <p className="text-xs text-gray-500">PPM Assessment</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {user ? (
              <Link
                to="/dashboard"
                data-testid="go-to-dashboard-btn"
                className="px-5 py-2 bg-[#2f81f7] text-white rounded-lg hover:bg-[#58a6ff] transition-colors font-medium"
              >
                Dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  data-testid="login-nav-btn"
                  className="px-4 py-2 text-gray-300 hover:text-white transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  data-testid="register-nav-btn"
                  className="px-5 py-2 bg-[#2f81f7] text-white rounded-lg hover:bg-[#58a6ff] transition-colors font-medium"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <div className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-light text-white font-['Outfit'] tracking-tight mb-6">
            PortfolioHealth
            <span className="block font-semibold text-[#2f81f7]">Advisor</span>
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-12">
            Assess your organisation's readiness for data-driven Product Portfolio Management decisions using the PPM Capability Maturity Framework.
          </p>
          
          {/* Two Options */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl mx-auto">
            {/* Quick Assessment */}
            <Link
              to="/quick-assessment"
              data-testid="quick-assessment-cta"
              className="group p-8 bg-gradient-to-br from-[#2f81f7]/20 to-[#111827] border border-[#2f81f7]/50 rounded-2xl text-left hover:border-[#2f81f7] transition-all card-hover"
            >
              <div className="w-14 h-14 rounded-xl bg-[#2f81f7]/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Zap size={28} className="text-[#2f81f7]" />
              </div>
              <h2 className="text-2xl font-semibold text-white mb-2 font-['Outfit']">
                Quick Check
              </h2>
              <p className="text-gray-400 mb-4">
                10-minute rapid screening with instant results
              </p>
              <div className="flex flex-wrap gap-3 mb-6">
                <span className="px-3 py-1 bg-[#1F2937] rounded-full text-xs text-gray-300 flex items-center gap-1">
                  <Clock size={12} /> 10 min
                </span>
                <span className="px-3 py-1 bg-[#1F2937] rounded-full text-xs text-gray-300">
                  15 questions
                </span>
                <span className="px-3 py-1 bg-[#1F2937] rounded-full text-xs text-gray-300">
                  No login required
                </span>
              </div>
              <div className="flex items-center gap-2 text-[#2f81f7] font-medium group-hover:gap-3 transition-all">
                Start Quick Check <ArrowRight size={18} />
              </div>
            </Link>

            {/* Full Assessment */}
            <Link
              to={user ? "/assessments" : "/login"}
              data-testid="full-assessment-cta"
              className="group p-8 bg-[#111827] border border-[#374151] rounded-2xl text-left hover:border-[#238636] transition-all card-hover"
            >
              <div className="w-14 h-14 rounded-xl bg-[#238636]/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <ClipboardCheck size={28} className="text-[#238636]" />
              </div>
              <h2 className="text-2xl font-semibold text-white mb-2 font-['Outfit']">
                Full Assessment
              </h2>
              <p className="text-gray-400 mb-4">
                AI-guided deep-dive with comprehensive roadmap
              </p>
              <div className="flex flex-wrap gap-3 mb-6">
                <span className="px-3 py-1 bg-[#1F2937] rounded-full text-xs text-gray-300 flex items-center gap-1">
                  <Clock size={12} /> 60-90 min
                </span>
                <span className="px-3 py-1 bg-[#1F2937] rounded-full text-xs text-gray-300">
                  AI-powered
                </span>
                <span className="px-3 py-1 bg-[#1F2937] rounded-full text-xs text-gray-300">
                  Detailed report
                </span>
              </div>
              <div className="flex items-center gap-2 text-[#238636] font-medium group-hover:gap-3 transition-all">
                {user ? "Start Full Assessment" : "Sign In to Start"} <ArrowRight size={18} />
              </div>
            </Link>
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="py-20 px-6 border-t border-[#374151]">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-semibold text-white text-center mb-12 font-['Outfit']">
            The PPDT Framework
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { icon: Target, label: "People", desc: "Culture, roles & data literacy" },
              { icon: ClipboardCheck, label: "Process", desc: "Governance & lifecycle management" },
              { icon: BarChart3, label: "Data", desc: "Quality, integration & profitability" },
              { icon: FileText, label: "Technology", desc: "Systems integration & decision support" }
            ].map(({ icon: Icon, label, desc }) => (
              <div key={label} className="p-6 bg-[#111827] border border-[#374151] rounded-xl text-center">
                <div className="w-12 h-12 rounded-lg bg-[#2f81f7]/20 flex items-center justify-center mx-auto mb-4">
                  <Icon size={24} className="text-[#2f81f7]" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{label}</h3>
                <p className="text-sm text-gray-400">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-[#374151] py-8 px-6">
        <div className="max-w-5xl mx-auto flex flex-col items-center gap-3 text-sm text-gray-500">
          <p>Academically grounded in published PPM research · University of Oulu</p>
          <p className="text-xs text-gray-600 text-center max-w-2xl">
            This tool is an independent academic research output developed as part of a Master's thesis at the University of Oulu (IEM–IPIC, 2026). Assessment methodology is grounded in peer-reviewed PPM research. Not affiliated with or endorsed by any commercial framework.
          </p>
          <p>© {new Date().getFullYear()} PortfolioHealth Advisor</p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
