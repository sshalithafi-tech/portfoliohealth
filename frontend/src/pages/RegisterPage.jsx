import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth, formatApiErrorDetail } from "../App";
import { Eye, EyeOff, UserPlus } from "lucide-react";
import { toast } from "sonner";

const RegisterPage = () => {
  const { register } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    
    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }
    
    setLoading(true);
    try {
      await register(email, password, name);
      toast.success("Account created successfully!");
    } catch (err) {
      setError(formatApiErrorDetail(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left side - 3D Liquid shapes */}
      <div 
        className="hidden lg:flex lg:w-1/2 relative"
        style={{
          backgroundImage: "url('https://static.prod-images.emergentagent.com/jobs/ad26f002-f220-4b9d-b343-979dba7f2367/images/8c7dd872cf9afec460503fdced858c236170fec9136b7d8fb0d593cc6ad0e7c1.png')",
          backgroundSize: "cover",
          backgroundPosition: "center"
        }}
      >
        <div className="absolute inset-0 bg-[#05050A]/40" />
        <div className="relative z-10 flex flex-col justify-center px-12">
          <div className="flex items-center gap-4 mb-6">
            <img src="https://static.prod-images.emergentagent.com/jobs/ad26f002-f220-4b9d-b343-979dba7f2367/images/6407f98124d827501f865028cbbf81566506fd19a8f17f5fd5b271241d491414.png" alt="PortfolioHealth" className="w-14 h-14 rounded-2xl object-contain" />
            <div>
              <h1 className="text-3xl font-light text-white font-['Outfit']">
                Portfolio<span className="font-semibold text-[#00E5FF]">Health</span>
              </h1>
              <p className="text-white/50">Advisor</p>
            </div>
          </div>
          <p className="text-white/70 text-lg max-w-md">
            Join our platform to conduct professional PPM capability assessments for your clients.
          </p>
          <div className="mt-8">
            <div className="flex items-center gap-3 text-white/60">
              <div className="w-8 h-8 rounded-lg bg-[#00E5FF]/15 flex items-center justify-center">
                <span className="text-[#00E5FF] text-sm font-semibold">P</span>
              </div>
              <span>People · Process · Data · Technology</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right side - Register form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-[#05050A]">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-semibold text-white font-['Outfit'] tracking-tight">
              Create Account
            </h2>
            <p className="text-white/50 mt-2">Start conducting PPDT maturity assessments</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm animate-fade-in backdrop-blur-sm">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <label className="text-sm text-white/50">Full Name</label>
              <input
                type="text"
                data-testid="register-name-input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-3 glass-input rounded-xl outline-none"
                placeholder="John Smith"
                required
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm text-white/50">Email</label>
              <input
                type="email"
                data-testid="register-email-input"
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
                  data-testid="register-password-input"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 glass-input rounded-xl outline-none pr-12"
                  placeholder="Minimum 6 characters"
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
              data-testid="register-submit-button"
              disabled={loading}
              className="w-full py-3 px-6 btn-liquid rounded-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
              ) : (
                <>
                  <UserPlus size={20} />
                  Create Account
                </>
              )}
            </button>
          </form>

          <p className="mt-8 text-center text-white/50">
            Already have an account?{" "}
            <Link to="/login" className="text-[#00E5FF] hover:text-[#00E5FF]/80 transition-colors">
              Sign in
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

export default RegisterPage;
