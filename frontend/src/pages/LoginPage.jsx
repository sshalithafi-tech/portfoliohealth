import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth, formatApiErrorDetail } from "../App";
import { Eye, EyeOff, LogIn, Target, Layers, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import LogoMark from "../components/LogoMark";

/* Premium brand panel shared by Login + Register */
const BrandPanel = ({ tagline, points }) => (
  <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
    {/* base gradient */}
    <div
      className="absolute inset-0"
      style={{
        background:
          "linear-gradient(155deg, #091622 0%, #0C1B2A 45%, #12293D 100%)",
      }}
    />
    {/* cyan glow */}
    <div
      className="absolute inset-0 pointer-events-none"
      style={{
        background:
          "radial-gradient(ellipse 55% 45% at 22% 22%, rgba(8,145,178,0.35) 0%, transparent 62%), radial-gradient(ellipse 50% 40% at 85% 90%, rgba(103,232,249,0.16) 0%, transparent 60%)",
      }}
    />
    {/* subtle grid */}
    <div
      className="absolute inset-0 opacity-[0.06] pointer-events-none"
      style={{
        backgroundImage:
          "linear-gradient(rgba(255,255,255,0.6) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.6) 1px, transparent 1px)",
        backgroundSize: "44px 44px",
      }}
    />
    <div className="relative z-10 flex flex-col justify-between px-14 py-16 w-full">
      <div>
        <div className="flex items-center gap-4">
          <LogoMark className="w-14 h-14 rounded-2xl shadow-lg" radius={20} />
          <div>
            <h1 className="text-3xl font-light text-white font-['Outfit'] leading-none">
              Portfolio<span className="font-semibold text-[#67E8F9]">Health</span>
            </h1>
            <p className="text-[#8FA3B5] text-sm mt-1 tracking-wide">Advisor</p>
          </div>
        </div>

        <p className="mt-12 text-[#E2E8F0] text-2xl font-light leading-snug max-w-md font-['Outfit']">
          {tagline}
        </p>

        <div className="mt-10 space-y-5 max-w-md">
          {points.map((p) => (
            <div key={p.t} className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-white/[0.06] border border-white/10 flex items-center justify-center text-[#67E8F9] shrink-0">
                {p.icon}
              </div>
              <div>
                <p className="text-white font-medium text-[15px]">{p.t}</p>
                <p className="text-[#8FA3B5] text-sm leading-relaxed">{p.b}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="pt-10 border-t border-white/10">
        <p className="text-xs text-[#6B7C8E] leading-relaxed max-w-sm">
          PPM Capability Maturity Framework · Research-grounded instrument developed
          as part of an IEM Master's thesis, University of Oulu.
        </p>
      </div>
    </div>
  </div>
);

const LoginPage = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      toast.success("Welcome back!");
    } catch (err) {
      setError(formatApiErrorDetail(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-[#F7F8FA]">
      <BrandPanel
        tagline="Diagnose exactly where your product portfolio decision-making breaks down."
        points={[
          { icon: <Target size={18} />, t: "Dual maturity score", b: "Equal-weighted baseline + business-model contextual score." },
          { icon: <Layers size={18} />, t: "Four PPDT pillars", b: "People · Process · Data · Technology, evaluated in depth." },
          { icon: <ShieldCheck size={18} />, t: "Bottleneck-first roadmap", b: "A sequenced, evidence-based improvement plan." },
        ]}
      />

      {/* Right side — form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-3xl border border-[#E5E7EB] shadow-[0_20px_60px_-25px_rgba(12,27,42,0.35)] p-8 sm:p-10">
            <div className="flex items-center justify-center gap-3 mb-6 lg:hidden">
              <LogoMark className="w-12 h-12 rounded-xl" radius={18} />
            </div>
            <div className="mb-8">
              <span className="inline-flex items-center gap-2 text-[11px] font-semibold tracking-wider uppercase text-[#0E7490] bg-[#ECFEFF] border border-[#67E8F9]/50 rounded-full px-3 py-1">
                <span className="w-1.5 h-1.5 rounded-full bg-[#0891B2]" /> Sign in
              </span>
              <h2 className="text-3xl font-semibold text-[#0C1B2A] font-['Outfit'] tracking-tight mt-4">
                Welcome back
              </h2>
              <p className="text-[#8896A5] mt-2">Sign in to continue your assessments.</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm animate-fade-in">
                  {error}
                </div>
              )}

              <div className="space-y-2">
                <label className="text-sm font-medium text-[#4A5568]">Email</label>
                <input
                  type="email"
                  data-testid="login-email-input"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-[#F7F8FA] border border-[#E5E7EB] outline-none text-[#0C1B2A] placeholder-[#B0BAC5] focus:border-[#0891B2] focus:bg-white focus:ring-4 focus:ring-[#0891B2]/10 transition-all"
                  placeholder="you@company.com"
                  required
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-[#4A5568]">Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    data-testid="login-password-input"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-[#F7F8FA] border border-[#E5E7EB] outline-none text-[#0C1B2A] placeholder-[#B0BAC5] pr-12 focus:border-[#0891B2] focus:bg-white focus:ring-4 focus:ring-[#0891B2]/10 transition-all"
                    placeholder="••••••••"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#8896A5] hover:text-[#0C1B2A] transition-colors"
                  >
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                data-testid="login-submit-button"
                disabled={loading}
                className="w-full py-3.5 px-6 rounded-xl text-white font-semibold flex items-center justify-center gap-2 shadow-[0_10px_25px_-8px_rgba(8,145,178,0.6)] hover:shadow-[0_14px_30px_-8px_rgba(8,145,178,0.7)] hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 transition-all"
                style={{ background: "linear-gradient(135deg, #0891B2 0%, #0E7490 100%)" }}
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    <LogIn size={20} />
                    Sign In
                  </>
                )}
              </button>
            </form>

            <p className="mt-7 text-center text-[#4A5568]">
              Don't have an account?{" "}
              <Link to="/register" className="text-[#0E7490] font-semibold hover:text-[#0C1B2A] transition-colors">
                Create one
              </Link>
            </p>
          </div>

          <p className="mt-6 text-xs text-[#8896A5] text-center">
            PPM Capability Maturity Framework · University of Oulu Research
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
