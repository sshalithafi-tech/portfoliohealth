import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../App";
import {
  LayoutDashboard,
  ClipboardCheck,
  Building2,
  BarChart3,
  LogOut,
  Menu,
  X,
  Shield
} from "lucide-react";
import { useState } from "react";
import NotificationBell from "./NotificationBell";
import LogoMark from "./LogoMark";

const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const navItems = [
    { path: "/dashboard",  label: "Dashboard",   icon: LayoutDashboard },
    { path: "/assessments",label: "Assessments", icon: ClipboardCheck },
    { path: "/companies",  label: "Companies",   icon: Building2 },
    { path: "/benchmarks", label: "Benchmarks",  icon: BarChart3 },
    ...(user?.role === "admin" ? [{ path: "/admin", label: "Admin Data", icon: Shield }] : []),
  ];

  const isActive = (path) =>
    location.pathname === path || location.pathname.startsWith(path + "/");

  return (
    <div className="min-h-screen" style={{ background: "transparent" }}>
      {/* Mobile Header */}
      <div className="print-hide lg:hidden h-14 bg-white border-b border-[#E5E7EB] flex items-center justify-between px-3 relative z-50">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 text-[#4B5563] hover:text-[#0C1B2A] transition-colors"
          data-testid="mobile-sidebar-toggle"
        >
          {sidebarOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
        <div className="flex items-center gap-2">
          <Link to="/dashboard" data-testid="mobile-logo-home" className="flex items-center gap-2">
            <LogoMark className="w-8 h-8 rounded-lg" radius={14} />
            <span className="text-[#0C1B2A] font-semibold font-['Outfit'] text-sm">
              PortfolioHealth
            </span>
          </Link>
        </div>
        <div className="w-10" />
      </div>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="print-hide fixed inset-0 bg-[#0C1B2A]/30 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar — paper-cream surface with gold left accent rail */}
      <aside
        className={`
          print-hide fixed top-0 left-0 h-full w-64 z-50
          lg:top-5 lg:left-5 lg:h-[calc(100vh-2.5rem)] lg:rounded-2xl
          bg-white border border-[#E5E7EB]
          shadow-[0_12px_32px_rgba(20,16,8,0.08),0_2px_6px_rgba(20,16,8,0.05)]
          transform transition-transform duration-300 ease-in-out
          lg:translate-x-0 overflow-hidden
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        {/* Cyan left rail */}
        <div className="absolute top-0 left-0 w-[3px] h-full bg-gradient-to-b from-[#0891B2] via-[#67E8F9] to-transparent" />

        {/* Brand block */}
        <div className="h-20 flex items-center px-6 border-b border-[#EEF1F5]">
          <Link
            to="/dashboard"
            data-testid="sidebar-logo-home"
            onClick={() => setSidebarOpen(false)}
            className="flex items-center gap-3 group"
          >
            <LogoMark className="w-11 h-11 rounded-xl transition-transform group-hover:scale-[1.05]" radius={20} />
            <div>
              <h1 className="text-[#0C1B2A] font-semibold font-['Outfit'] tracking-tight group-hover:text-[#0891B2] transition-colors">
                PortfolioHealth
              </h1>
              <p className="text-[10px] uppercase tracking-[0.18em] text-[#0E7490] font-semibold mt-0.5">
                PPM Assessment
              </p>
            </div>
          </Link>
        </div>

        {/* Eyebrow + nav */}
        <div className="px-6 pt-5 pb-2">
          <span className="eyebrow">Workspace</span>
        </div>
        <nav className="px-4 space-y-1">
          {navItems.map(({ path, label, icon: Icon }) => {
            const active = isActive(path);
            return (
              <Link
                key={path}
                to={path}
                data-testid={`nav-${label.toLowerCase().replace(/\s+/g, '-')}`}
                onClick={() => setSidebarOpen(false)}
                className={`
                  group relative flex items-center gap-3 px-4 py-3 rounded-xl
                  font-medium transition-all duration-200
                  ${active
                    ? 'bg-gradient-to-r from-[#ECFEFF] to-white text-[#0E7490] shadow-[inset_0_0_0_1px_rgba(8, 145, 178,0.30)]'
                    : 'text-[#4B5563] hover:text-[#0C1B2A] hover:bg-[#F7F8FA]'
                  }
                `}
              >
                {active && (
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-r-full bg-[#0891B2]" />
                )}
                <Icon size={18} className={active ? "text-[#0E7490]" : "text-[#6B7280] group-hover:text-[#0C1B2A]"} />
                <span className="font-['Outfit']">{label}</span>
              </Link>
            );
          })}
        </nav>

        {/* User block bottom */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-[#EEF1F5] bg-[#F7F8FA]/60">
          <div className="flex items-center gap-3 px-3 py-2 mb-2 rounded-xl bg-white border border-[#EEF1F5]">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[#ECFEFF] to-[#67E8F9] border border-[#0891B2]/40 flex items-center justify-center">
              <span className="text-[#0E7490] font-bold font-['Outfit'] text-sm">
                {user?.name?.charAt(0)?.toUpperCase() || "U"}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-[#0C1B2A] font-medium truncate font-['Outfit']">{user?.name}</p>
              <p className="text-[11px] text-[#6B7280] truncate">{user?.email}</p>
            </div>
            <NotificationBell />
          </div>
          <button
            onClick={handleLogout}
            data-testid="logout-btn"
            className="flex items-center gap-3 w-full px-4 py-2.5 text-[#4B5563] hover:text-[#B23C2A] hover:bg-white rounded-xl transition-all font-['Outfit'] font-medium text-sm"
          >
            <LogOut size={16} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="lg:ml-[calc(16rem+2.5rem)] min-h-screen">
        <div className="p-4 sm:p-6 lg:p-10">
          {children}
        </div>

        {/* Footer — refined navy strip */}
        <footer className="print-hide mt-8 border-t border-[#E5E7EB] bg-[#0C1B2A] text-white/65 px-4 sm:px-6 lg:px-10 py-7">
          <div className="max-w-5xl mx-auto flex flex-col items-center gap-2 text-xs sm:text-sm text-center">
            <div className="gold-rule w-full max-w-md opacity-80">
              <span className="diamond" />
            </div>
            <p className="text-[#67E8F9] font-['Outfit'] tracking-wide font-medium">
              Academically grounded in published PPM research · University of Oulu
            </p>
            <p className="text-[10px] sm:text-xs text-white/45 max-w-2xl leading-relaxed">
              This tool is an independent academic research output developed as part of a Master&apos;s thesis at the University of Oulu (IEM–IPIC, 2026). Assessment methodology is grounded in peer-reviewed PPM research. Not affiliated with or endorsed by any commercial framework.
            </p>
            <p className="text-white/35 mt-1">© {new Date().getFullYear()} PortfolioHealth Advisor</p>
          </div>
        </footer>
      </main>
    </div>
  );
};

export default Layout;
