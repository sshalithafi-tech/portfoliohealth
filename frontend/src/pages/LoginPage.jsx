import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth, formatApiErrorDetail } from "../App";
import { Eye, EyeOff, LogIn } from "lucide-react";
import { toast } from "sonner";
import LogoMark from "../components/LogoMark";

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
    <div className="min-h-screen flex">
      {/* Left side - Corporate branding */}
      <div 
        className="hidden lg:flex lg:w-1/2 relative"
        style={{
          background: "linear-gradient(135deg, #0A1628 0%, #0d1f3c 50%, #0A1628 100%)"
        }}
      >
        <div className="absolute inset-0" style={{ background: "radial-gradient(ellipse 60% 50% at 30% 40%, rgba(201, 168, 76, 0.08) 0%, transparent 60%)" }} />
        <div className="relative z-10 flex flex-col justify-center px-12">
          <div className="flex items-center gap-4 mb-6">
            <LogoMark className="w-14 h-14 rounded-2xl" radius={20} />
            <div>
              <h1 className="text-3xl font-light text-white font-['Outfit']">
                Portfolio<span className="font-semibold text-[#C9A84C]">Health</span>
              </h1>
              <p className="text-white/50">Advisor</p>
            </div>
          </div>
          <p className="text-white/70 text-lg max-w-md">
            Assess your organisation's readiness for data-driven Product Portfolio Management decisions.
          </p>
          <div className="mt-8 flex items-center gap-4">
            <div className="h-px flex-1 bg-gradient-to-r from-[#C9A84C]/50 to-transparent" />
          </div>
          <p className="mt-4 text-sm text-white/40">
            Academically grounded in published PPM research
          </p>
        </div>
      </div>

      {/* Right side - Login form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-8 bg-[#0A1628]">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="flex items-center justify-center gap-3 mb-6 lg:hidden">
            <LogoMark className="w-12 h-12 rounded-xl" radius={18} />
          </div>
          <div className="text-center mb-8">
            <h2 className="text-3xl font-semibold text-white font-['Outfit'] tracking-tight">
              Welcome Back
            </h2>
            <p className="text-white/50 mt-2">Sign in to continue your assessments</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm animate-fade-in backdrop-blur-sm">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <label className="text-sm text-white/50">Email</label>
              <input
                type="email"
                data-testid="login-email-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 glass-input rounded-xl outline-none"
                placeholder="you@company.com"
                required
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm text-white/50">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  data-testid="login-password-input"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 glass-input rounded-xl outline-none pr-12"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              data-testid="login-submit-button"
              disabled={loading}
              className="w-full py-3 px-6 btn-liquid rounded-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
              ) : (
                <>
                  <LogIn size={20} />
                  Sign In
                </>
              )}
            </button>
          </form>

          <p className="mt-8 text-center text-white/50">
            Don't have an account?{" "}
            <Link to="/register" className="text-[#C9A84C] hover:text-[#C9A84C]/80 transition-colors">
              Create one
            </Link>
          </p>

          <div className="mt-12 pt-8 border-t border-white/[0.06]">
            <p className="text-xs text-white/25 text-center">
              PPM Capability Maturity Framework · University of Oulu Research
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
