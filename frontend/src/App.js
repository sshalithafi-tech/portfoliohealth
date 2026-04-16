import { useState, useEffect, useCallback, createContext, useContext } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import { Toaster } from "sonner";

// Pages
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import AssessmentsPage from "./pages/AssessmentsPage";
import AssessmentChatPage from "./pages/AssessmentChatPage";
import CompaniesPage from "./pages/CompaniesPage";
import ReportPage from "./pages/ReportPage";
import LandingPage from "./pages/LandingPage";
import QuickAssessmentPage from "./pages/QuickAssessmentPage";
import QuickResultsPage from "./pages/QuickResultsPage";
import AdminPage from "./pages/AdminPage";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Configure axios — use token from localStorage instead of cookies
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth Context
export const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};

// Format API error helper
export const formatApiErrorDetail = (detail) => {
  if (detail == null) return "Something went wrong. Please try again.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail
      .map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e)))
      .filter(Boolean)
      .join(" ");
  if (detail && typeof detail.msg === "string") return detail.msg;
  return String(detail);
};

// Auth Provider
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null); // null = checking, false = not authenticated
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/auth/me`);
      setUser(response.data);
    } catch (err) {
      setUser(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = useCallback(async (email, password) => {
    const response = await axios.post(`${BACKEND_URL}/api/auth/login`, { email, password });
    if (response.data.access_token) {
      localStorage.setItem("access_token", response.data.access_token);
    }
    setUser(response.data.user);
    return response.data.user;
  }, []);

  const register = useCallback(async (email, password, name) => {
    const response = await axios.post(`${BACKEND_URL}/api/auth/register`, { email, password, name });
    if (response.data.access_token) {
      localStorage.setItem("access_token", response.data.access_token);
    }
    setUser(response.data.user);
    return response.data.user;
  }, []);

  const logout = useCallback(async () => {
    try { await axios.post(`${BACKEND_URL}/api/auth/logout`); } catch {}
    localStorage.removeItem("access_token");
    setUser(false);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
};

// Protected Route
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse-glow w-12 h-12 rounded-full bg-[#00E5FF]/15 flex items-center justify-center">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#2f81f7] to-[#00E5FF]" />
        </div>
      </div>
    );
  }

  if (user === false) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

// Public Route (redirect if already logged in)
const PublicRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse-glow w-12 h-12 rounded-full bg-[#00E5FF]/15 flex items-center justify-center">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#2f81f7] to-[#00E5FF]" />
        </div>
      </div>
    );
  }

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

// Liquid background blobs that persist across all pages
const LiquidBackground = () => (
  <div className="liquid-bg">
    <div className="liquid-blob liquid-blob-1" />
    <div className="liquid-blob liquid-blob-2" />
    <div className="liquid-blob liquid-blob-3" />
  </div>
);

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <LiquidBackground />
        <Toaster position="top-right" richColors />
        <div className="relative z-10">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
            <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
            <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
            <Route path="/assessments" element={<ProtectedRoute><AssessmentsPage /></ProtectedRoute>} />
            <Route path="/assessments/:id" element={<ProtectedRoute><AssessmentChatPage /></ProtectedRoute>} />
            <Route path="/assessments/:id/report" element={<ProtectedRoute><ReportPage /></ProtectedRoute>} />
            <Route path="/companies" element={<ProtectedRoute><CompaniesPage /></ProtectedRoute>} />
            <Route path="/admin" element={<ProtectedRoute><AdminPage /></ProtectedRoute>} />
            <Route path="/quick-assessment" element={<QuickAssessmentPage />} />
            <Route path="/quick-assessment/:id/results" element={<QuickResultsPage />} />
          </Routes>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
