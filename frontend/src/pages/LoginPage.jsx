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
    <div className="min-h-screen flex bg-white">
      {/* Left side — light hero */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-white border-r border-[#E2E8F0]">
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse 60% 50% at 25% 30%, rgba(201, 168, 76, 0.18) 0%, transparent 60%)",
          }}
        />
        <div className="relative z-10 flex flex-col justify-center px-12">
          <div className="flex items-center gap-4 mb-6">
            <LogoMark className="w-14 h-14 rounded-2xl" radius={20} />
            <div>
              <h1 className="text-3xl font-light text-[#0C1B2A] font-['Outfit']">
                Portfolio<span className="font-semibold text-[#A88A2E]">Health</span>
              </h1>
              <p className="text-[#8896A5]">Advisor</p>
            </div>
          </div>
          <p className="text-[#4A5568] text-lg max-w-md leading-relaxed">
            Assess your organisation's readiness for data-driven Product Portfolio Management decisions.
          </p>
          <div className="mt-8 flex items-center gap-4">
            <div className="h-px flex-1 bg-gradient-to-r from-[#C9A84C]/55 to-transparent" />
          </div>
          <p className="mt-4 text-sm text-[#8896A5]">
            Academically grounded in published PPM research
          </p>
        </div>
      </div>

      {/* Right side — form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-8 bg-white">
        <div className="w-full max-w-md">
          <div className="flex items-center justify-center gap-3 mb-6 lg:hidden">
            <LogoMark className="w-12 h-12 rounded-xl" radius={18} />
          </div>
          <div className="text-center mb-8">
            <h2 className="text-3xl font-semibold text-[#0C1B2A] font-['Outfit'] tracking-tight">
              Welcome Back
            </h2>
            <p className="text-[#8896A5] mt-2">Sign in to continue your assessments</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
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
                className="w-full px-4 py-3 glass-input rounded-xl outline-none"
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
                  className="w-full px-4 py-3 glass-input rounded-xl outline-none pr-12"
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
              className="w-full py-3 px-6 btn-liquid rounded-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-[#C9A84C]/40 border-t-[#C9A84C] rounded-full animate-spin" />
              ) : (
                <>
                  <LogIn size={20} />
                  Sign In
                </>
              )}
            </button>
          </form>

          <p className="mt-8 text-center text-[#4A5568]">
            Don't have an account?{" "}
            <Link to="/register" className="text-[#A88A2E] font-semibold hover:text-[#0C1B2A] transition-colors">
              Create one
            </Link>
          </p>

          <div className="mt-12 pt-8 border-t border-[#E2E8F0]">
            <p className="text-xs text-[#8896A5] text-center">
              PPM Capability Maturity Framework · University of Oulu Research
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
