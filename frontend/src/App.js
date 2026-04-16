import { useState, useEffect, createContext, useContext } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
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

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Configure axios defaults
axios.defaults.withCredentials = true;

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

  const checkAuth = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/auth/me`);
      setUser(response.data);
    } catch (err) {
      setUser(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const login = async (email, password) => {
    const response = await axios.post(`${BACKEND_URL}/api/auth/login`, { email, password });
    setUser(response.data);
    return response.data;
  };

  const register = async (email, password, name) => {
    const response = await axios.post(`${BACKEND_URL}/api/auth/register`, { email, password, name });
    setUser(response.data);
    return response.data;
  };

  const logout = async () => {
    await axios.post(`${BACKEND_URL}/api/auth/logout`);
    setUser(false);
  };

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
      <div className="min-h-screen flex items-center justify-center bg-[#0B1120]">
        <div className="animate-pulse-glow w-12 h-12 rounded-full bg-[#2f81f7]/20 flex items-center justify-center">
          <div className="w-6 h-6 rounded-full bg-[#2f81f7]" />
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
      <div className="min-h-screen flex items-center justify-center bg-[#0B1120]">
        <div className="animate-pulse-glow w-12 h-12 rounded-full bg-[#2f81f7]/20 flex items-center justify-center">
          <div className="w-6 h-6 rounded-full bg-[#2f81f7]" />
        </div>
      </div>
    );
  }

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster position="top-right" richColors />
        <Routes>
          <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
          <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/assessments" element={<ProtectedRoute><AssessmentsPage /></ProtectedRoute>} />
          <Route path="/assessments/:id" element={<ProtectedRoute><AssessmentChatPage /></ProtectedRoute>} />
          <Route path="/assessments/:id/report" element={<ProtectedRoute><ReportPage /></ProtectedRoute>} />
          <Route path="/companies" element={<ProtectedRoute><CompaniesPage /></ProtectedRoute>} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
