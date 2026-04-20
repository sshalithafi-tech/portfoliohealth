import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../App";
import { 
  LayoutDashboard, 
  ClipboardCheck, 
  Building2, 
  LogOut,
  Menu,
  X,
  ChevronRight,
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
    { path: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { path: "/assessments", label: "Assessments", icon: ClipboardCheck },
    { path: "/companies", label: "Companies", icon: Building2 },
    ...(user?.role === "admin" ? [{ path: "/admin", label: "Admin Data", icon: Shield }] : []),
  ];

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path + "/");

  return (
    <div className="min-h-screen">
      {/* Mobile Header */}
      <div className="lg:hidden h-14 glass-surface flex items-center justify-between px-3 relative z-50">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 text-white/50 hover:text-white transition-colors"
        >
          {sidebarOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
        <div className="flex items-center gap-2">
          <LogoMark className="w-8 h-8 rounded-lg" radius={14} />
          <span className="text-white font-semibold font-['Outfit'] text-sm">PortfolioHealth</span>
        </div>
        <div className="w-10" />
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Floating Glass Sidebar */}
      <aside className={`
        fixed top-0 left-0 h-full w-64 z-50
        lg:top-4 lg:left-4 lg:h-[calc(100vh-2rem)] lg:rounded-2xl
        glass-surface-highlight
        transform transition-transform duration-300 ease-in-out
        lg:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="h-16 flex items-center px-6 border-b border-white/[0.06]">
          <div className="flex items-center gap-3">
            <LogoMark className="w-10 h-10 rounded-xl" radius={18} />
            <div>
              <h1 className="text-white font-semibold font-['Outfit']">PortfolioHealth</h1>
              <p className="text-xs text-white/40">PPM Assessment</p>
            </div>
          </div>
        </div>

        <nav className="p-4 space-y-1">
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              data-testid={`nav-${label.toLowerCase()}`}
              onClick={() => setSidebarOpen(false)}
              className={`
                flex items-center gap-3 px-4 py-3 rounded-xl transition-all
                ${isActive(path)
                  ? 'bg-gradient-to-r from-[#60A5FA]/20 to-[#C9A84C]/10 text-[#C9A84C] border border-[#C9A84C]/20'
                  : 'text-white/50 hover:text-white hover:bg-white/[0.04]'
                }
              `}
            >
              <Icon size={20} />
              <span className="font-medium">{label}</span>
              {isActive(path) && <ChevronRight size={16} className="ml-auto" />}
            </Link>
          ))}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-white/[0.06]">
          <div className="flex items-center gap-3 px-4 py-3 mb-2">
            <div className="w-10 h-10 rounded-full bg-white/[0.06] flex items-center justify-center">
              <span className="text-[#C9A84C] font-semibold">
                {user?.name?.charAt(0)?.toUpperCase() || "U"}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-white font-medium truncate">{user?.name}</p>
              <p className="text-xs text-white/40 truncate">{user?.email}</p>
            </div>
            <NotificationBell />
          </div>
          <button
            onClick={handleLogout}
            data-testid="logout-btn"
            className="flex items-center gap-3 w-full px-4 py-3 text-white/50 hover:text-white hover:bg-white/[0.04] rounded-xl transition-all"
          >
            <LogOut size={20} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="lg:ml-[calc(16rem+2rem)] min-h-screen">
        <div className="p-4 sm:p-6 lg:p-8">
          {children}
        </div>
        
        {/* Footer */}
        <footer className="border-t border-white/[0.06] px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col items-center gap-2 sm:gap-3 text-xs sm:text-sm text-white/40">
            <p className="text-center">
              Academically grounded in published PPM research · University of Oulu
            </p>
            <p className="text-[10px] sm:text-xs text-white/25 text-center max-w-2xl">
              This tool is an independent academic research output developed as part of a Master's thesis at the University of Oulu (IEM–IPIC, 2026). Assessment methodology is grounded in peer-reviewed PPM research. Not affiliated with or endorsed by any commercial framework.
            </p>
            <p>
              © {new Date().getFullYear()} PortfolioHealth Advisor
            </p>
          </div>
        </footer>
      </main>
    </div>
  );
};

export default Layout;
