import { BrowserRouter, Routes, Route, Navigate, useParams } from "react-router-dom";
import { Toaster } from "sonner";
import { createContext, useContext, useState, useEffect, lazy, Suspense } from "react";
import axios from "axios";

const BookingPage = lazy(() => import("./pages/BookingPage"));
const AdminLogin = lazy(() => import("./pages/AdminLogin"));
const AdminDashboard = lazy(() => import("./pages/AdminDashboard"));
const LandingPage = lazy(() => import("./pages/LandingPage"));
const SuperAdminPage = lazy(() => import("./pages/SuperAdminPage"));
const SalonGodMode = lazy(() => import("./pages/SalonGodMode"));

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

const PageLoader = () => (
  <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center">
    <div className="text-center">
      <div className="w-8 h-8 border-2 border-[#C5A880] border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
      <p className="text-[#9CA3AF] text-sm">Učitavanje...</p>
    </div>
  </div>
);

// Auth Context
const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

// Tenant Context
const TenantContext = createContext(null);
export const useTenant = () => useContext(TenantContext);

export const TenantProvider = ({ children }) => {
  const { slug } = useParams();
  const [tenant, setTenant] = useState(null);
  const [tenantLoading, setTenantLoading] = useState(true);

  useEffect(() => {
    if (!slug) {
      setTenantLoading(false);
      return;
    }
    const fetchTenant = async () => {
      try {
        const res = await axios.get(`${API}/tenants/by-slug/${slug}`);
        setTenant(res.data);
      } catch {
        setTenant(null);
      } finally {
        setTenantLoading(false);
      }
    };
    fetchTenant();
  }, [slug]);

  if (tenantLoading) return <PageLoader />;
  if (!tenant && slug) {
    return (
      <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center text-white">
        <div className="text-center">
          <h1 className="text-2xl mb-2">Salon nije pronađen</h1>
          <p className="text-[#9CA3AF]">"{slug}" ne postoji.</p>
        </div>
      </div>
    );
  }

  return (
    <TenantContext.Provider value={tenant}>
      {children}
    </TenantContext.Provider>
  );
};

// Axios interceptor to inject tenant header
export const getTenantHeaders = (tenantId) => {
  if (!tenantId) return {};
  return { "X-Tenant-ID": tenantId };
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        setLoading(false);
        return;
      }
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
        withCredentials: true,
      });
      setUser(response.data);
    } catch {
      localStorage.removeItem("access_token");
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const response = await axios.post(
      `${API}/auth/login`,
      { email, password },
      { withCredentials: true }
    );
    localStorage.setItem("access_token", response.data.access_token);
    setUser(response.data);
    return response.data;
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
    } catch (e) {
      console.error("Logout error:", e);
    }
    localStorage.removeItem("access_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
};

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  const { slug } = useParams();

  if (loading) {
    return <PageLoader />;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

const ProtectedSuperAdmin = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) return <PageLoader />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== "super_admin") return <Navigate to="/login" replace />;

  return children;
};

function App() {
  return (
    <AuthProvider>
      <div className="App min-h-screen bg-[#0A0A0B]">
        <Toaster
          position="top-center"
          toastOptions={{
            style: {
              background: "#141416",
              color: "#FFFFFF",
              border: "1px solid #2A2A2D",
            },
          }}
        />
        <BrowserRouter>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<AdminLogin />} />
              <Route
                path="/super-admin"
                element={
                  <ProtectedSuperAdmin>
                    <SuperAdminPage />
                  </ProtectedSuperAdmin>
                }
              />
              <Route
                path="/super-admin/salon/:slug"
                element={
                  <ProtectedSuperAdmin>
                    <SalonGodMode />
                  </ProtectedSuperAdmin>
                }
              />
              <Route path="/:slug" element={<TenantProvider><BookingPage /></TenantProvider>} />
              <Route path="/:slug/admin/login" element={<AdminLogin />} />
              <Route
                path="/:slug/admin/*"
                element={
                  <TenantProvider>
                    <ProtectedRoute>
                      <AdminDashboard />
                    </ProtectedRoute>
                  </TenantProvider>
                }
              />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </div>
    </AuthProvider>
  );
}

export default App;
