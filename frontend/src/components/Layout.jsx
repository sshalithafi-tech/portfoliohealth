import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../App";
import { 
  LayoutDashboard, 
  ClipboardCheck, 
  Building2, 
  LogOut,
  Menu,
  X,
  ChevronRight
} from "lucide-react";
import { useState } from "react";

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
  ];

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path + "/");

  return (
    <div className="min-h-screen bg-[#0B1120]">
      {/* Mobile Header */}
      <div className="lg:hidden h-16 bg-[#111827] border-b border-[#374151] flex items-center justify-between px-4">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 text-gray-400 hover:text-white transition-colors"
        >
          {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#2f81f7] to-[#1a5fc9] flex items-center justify-center shadow-lg shadow-[#2f81f7]/20">
            <span className="text-white font-bold text-sm tracking-tight">PH</span>
          </div>
          <span className="text-white font-semibold font-['Outfit']">PortfolioHealth</span>
        </div>
        <div className="w-10" />
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed top-0 left-0 h-full w-64 bg-[#111827] border-r border-[#374151] z-50
        transform transition-transform duration-300 ease-in-out
        lg:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="h-16 flex items-center px-6 border-b border-[#374151]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#2f81f7] to-[#1a5fc9] flex items-center justify-center shadow-lg shadow-[#2f81f7]/20">
              <span className="text-white font-bold tracking-tight">PH</span>
            </div>
            <div>
              <h1 className="text-white font-semibold font-['Outfit']">PortfolioHealth</h1>
              <p className="text-xs text-gray-500">PPM Assessment</p>
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
                flex items-center gap-3 px-4 py-3 rounded-lg transition-all
                ${isActive(path)
                  ? 'bg-[#2f81f7]/20 text-[#2f81f7] border-l-2 border-[#2f81f7]'
                  : 'text-gray-400 hover:text-white hover:bg-[#1F2937]'
                }
              `}
            >
              <Icon size={20} />
              <span className="font-medium">{label}</span>
              {isActive(path) && <ChevronRight size={16} className="ml-auto" />}
            </Link>
          ))}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-[#374151]">
          <div className="flex items-center gap-3 px-4 py-3 mb-2">
            <div className="w-10 h-10 rounded-full bg-[#1F2937] flex items-center justify-center">
              <span className="text-[#2f81f7] font-semibold">
                {user?.name?.charAt(0)?.toUpperCase() || "U"}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-white font-medium truncate">{user?.name}</p>
              <p className="text-xs text-gray-500 truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            data-testid="logout-btn"
            className="flex items-center gap-3 w-full px-4 py-3 text-gray-400 hover:text-white hover:bg-[#1F2937] rounded-lg transition-all"
          >
            <LogOut size={20} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="lg:ml-64 min-h-screen">
        <div className="p-6 lg:p-8">
          {children}
        </div>
        
        {/* Footer */}
        <footer className="border-t border-[#374151] px-6 lg:px-8 py-6">
          <div className="flex flex-col items-center gap-3 text-sm text-gray-500">
            <p>
              Academically grounded in published PPM research · University of Oulu
            </p>
            <p className="text-xs text-gray-600 text-center max-w-2xl">
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
