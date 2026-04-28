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
    <div className="min-h-screen bg-white">
      {/* Mobile Header */}
      <div className="lg:hidden h-14 bg-white border-b border-[#E2E8F0] flex items-center justify-between px-3 relative z-50">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 text-[#4A5568] hover:text-[#0C1B2A] transition-colors"
        >
          {sidebarOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
        <div className="flex items-center gap-2">
          <LogoMark className="w-8 h-8 rounded-lg" radius={14} />
          <span className="text-[#0C1B2A] font-semibold font-['Outfit'] text-sm">PortfolioHealth</span>
        </div>
        <div className="w-10" />
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Floating Light Sidebar */}
      <aside className={`
        fixed top-0 left-0 h-full w-64 z-50 bg-white
        lg:top-4 lg:left-4 lg:h-[calc(100vh-2rem)] lg:rounded-2xl
        border border-[#E2E8F0] shadow-[0_4px_20px_rgba(12,27,42,0.06)]
        transform transition-transform duration-300 ease-in-out
        lg:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="h-16 flex items-center px-6 border-b border-[#E2E8F0]">
          <div className="flex items-center gap-3">
            <LogoMark className="w-10 h-10 rounded-xl" radius={18} />
            <div>
              <h1 className="text-[#0C1B2A] font-semibold font-['Outfit']">PortfolioHealth</h1>
              <p className="text-xs text-[#8896A5]">PPM Assessment</p>
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
                  ? 'bg-[#F7F0DC] text-[#A88A2E] border border-[#E8D49A] font-semibold'
                  : 'text-[#4A5568] hover:text-[#0C1B2A] hover:bg-[#F8F9FA] border border-transparent'
                }
              `}
            >
              <Icon size={20} />
              <span>{label}</span>
              {isActive(path) && <ChevronRight size={16} className="ml-auto" />}
            </Link>
          ))}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-[#E2E8F0]">
          <div className="flex items-center gap-3 px-4 py-3 mb-2">
            <div className="w-10 h-10 rounded-full bg-[#F7F0DC] border border-[#E8D49A] flex items-center justify-center">
              <span className="text-[#A88A2E] font-semibold">
                {user?.name?.charAt(0)?.toUpperCase() || "U"}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-[#0C1B2A] font-medium truncate">{user?.name}</p>
              <p className="text-xs text-[#8896A5] truncate">{user?.email}</p>
            </div>
            <NotificationBell />
          </div>
          <button
            onClick={handleLogout}
            data-testid="logout-btn"
            className="flex items-center gap-3 w-full px-4 py-3 text-[#4A5568] hover:text-[#0C1B2A] hover:bg-[#F8F9FA] rounded-xl transition-all"
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
        <footer className="border-t border-[#E2E8F0] px-4 sm:px-6 lg:px-8 py-6 bg-[#F8F9FA]">
          <div className="flex flex-col items-center gap-2 sm:gap-3 text-xs sm:text-sm text-[#4A5568]">
            <p className="text-center">
              Academically grounded in published PPM research · University of Oulu
            </p>
            <p className="text-[10px] sm:text-xs text-[#8896A5] text-center max-w-2xl">
              This tool is an independent academic research output developed as part of a Master's thesis at the University of Oulu (IEM–IPIC, 2026). Assessment methodology is grounded in peer-reviewed PPM research. Not affiliated with or endorsed by any commercial framework.
            </p>
            <p className="text-[#8896A5]">
              © {new Date().getFullYear()} PortfolioHealth Advisor
            </p>
          </div>
        </footer>
      </main>
    </div>
  );
};

export default Layout;
