import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth, formatApiErrorDetail } from "../App";
import { Eye, EyeOff, LogIn } from "lucide-react";
import { toast } from "sonner";

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
      {/* Left side - Background */}
      <div 
        className="hidden lg:flex lg:w-1/2 relative"
        style={{
          backgroundImage: "url('https://images.unsplash.com/photo-1693430895886-dced76ef7b0b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NTJ8MHwxfHNlYXJjaHwxfHxhYnN0cmFjdCUyMGFyayUyMGJsdWUlMjBnZW9tZXRyaWN8ZW58MHx8fHwxNzc2MzQyOTQ3fDA&ixlib=rb-4.1.0&q=85')",
          backgroundSize: "cover",
          backgroundPosition: "center"
        }}
      >
        <div className="absolute inset-0 bg-black/60" />
        <div className="relative z-10 flex flex-col justify-center px-12">
          <h1 className="text-4xl font-light text-white mb-4 font-['Outfit']">
            PPDT Capability<br />
            <span className="font-semibold text-[#2f81f7]">Maturity Advisor</span>
          </h1>
          <p className="text-gray-300 text-lg max-w-md">
            Assess your organisation's readiness for data-driven Product Portfolio Management decisions.
          </p>
          <div className="mt-8 flex items-center gap-4">
            <div className="h-px flex-1 bg-gradient-to-r from-[#2f81f7] to-transparent" />
          </div>
          <p className="mt-4 text-sm text-gray-400">
            Based on Hannila's Product Wellbeing Framework
          </p>
        </div>
      </div>

      {/* Right side - Login form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-[#0B1120]">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-semibold text-white font-['Outfit'] tracking-tight">
              Welcome Back
            </h2>
            <p className="text-gray-400 mt-2">Sign in to continue your assessments</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm animate-fade-in">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <label className="text-sm text-gray-400">Email</label>
              <input
                type="email"
                data-testid="login-email-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-[#111827] border border-[#374151] rounded-lg text-white focus:ring-2 focus:ring-[#2f81f7] focus:border-transparent transition-all outline-none"
                placeholder="you@company.com"
                required
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm text-gray-400">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  data-testid="login-password-input"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 bg-[#111827] border border-[#374151] rounded-lg text-white focus:ring-2 focus:ring-[#2f81f7] focus:border-transparent transition-all outline-none pr-12"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              data-testid="login-submit-button"
              disabled={loading}
              className="w-full py-3 px-6 bg-[#2f81f7] text-white font-medium rounded-lg hover:bg-[#58a6ff] transition-all disabled:opacity-50 disabled:cursor-not-allowed btn-premium flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <LogIn size={20} />
                  Sign In
                </>
              )}
            </button>
          </form>

          <p className="mt-8 text-center text-gray-400">
            Don't have an account?{" "}
            <Link to="/register" className="text-[#2f81f7] hover:text-[#58a6ff] transition-colors">
              Create one
            </Link>
          </p>

          <div className="mt-12 pt-8 border-t border-[#374151]">
            <p className="text-xs text-gray-500 text-center">
              Product Wellbeing Framework · University of Oulu Research
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
