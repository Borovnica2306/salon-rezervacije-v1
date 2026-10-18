import React, { useState } from "react";
import { Routes, Route, Link, Navigate, useLocation, useNavigate, useParams } from "react-router-dom";
import { useAuth, useTenant } from "../App";
import { Calendar, Users, Scissors, Settings, LogOut, Menu, X, Shield } from "lucide-react";

import ReservationsPage from "../components/admin/CalendarView";
import BlacklistPage from "../components/admin/BlacklistPage";
import EmployeesPage from "../components/admin/SalonWorkers";
import ServicesPage from "../components/admin/SalonServices";
import SettingsPage from "../components/admin/AdminSettings";

const AdminDashboard = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { logout, user } = useAuth();
  const tenant = useTenant();
  const { slug } = useParams();
  const basePath = `/${slug}/admin`;

  const isWorker = user?.role === "worker";

  const handleLogout = async () => {
    // Capture redirect info BEFORE logout clears user state
    const role = user?.role;
    const targetSlug = slug;
    await logout();
    if (role === "super_admin") {
      navigate("/login");
    } else {
      navigate(`/${targetSlug}/admin/login`);
    }
  };

  const isSuperAdminViewing = user?.role === "super_admin";

  const allNavItems = [
    { path: basePath, label: "Rezervacije", icon: Calendar, workerVisible: true },
    { path: `${basePath}/blacklist`, label: "Crna Lista", icon: Shield, workerVisible: false },
    { path: `${basePath}/employees`, label: "Radnici", icon: Users, workerVisible: false },
    { path: `${basePath}/services`, label: "Usluge", icon: Scissors, workerVisible: false },
    { path: `${basePath}/settings`, label: "Podešavanja", icon: Settings, workerVisible: false },
  ];

  const navItems = isWorker ? allNavItems.filter(item => item.workerVisible) : allNavItems;

  return (
    <div className="min-h-screen bg-transparent">
      {/* Super Admin Banner */}
      {isSuperAdminViewing && (
        <div className="bg-[var(--color-primary)]/10 border-b border-[var(--color-primary)]/30 px-4 py-2.5 flex items-center justify-between" data-testid="super-admin-banner">
          <p className="text-sm text-[var(--color-primary)]">
            {"Pregledate salon kao Super Admin"}
          </p>
          <a
            href="/super-admin"
            className="text-sm font-medium text-[var(--color-primary)] hover:text-[var(--color-secondary)] transition-colors flex items-center gap-1"
            data-testid="back-to-super-panel-link"
          >
            {"Nazad na Super Panel"}
          </a>
        </div>
      )}

      {/* Worker Banner */}
      {isWorker && (
        <div className="bg-blue-500/10 border-b border-blue-500/30 px-4 py-2.5 flex items-center justify-between" data-testid="worker-banner">
          <p className="text-sm text-blue-400">
            {"Pregled rasporeda — samo za čitanje"}
          </p>
          <span className="text-xs text-blue-400/70 font-mono">{user?.name}</span>
        </div>
      )}

      {/* Mobile Header */}
      <header className="lg:hidden sticky top-0 z-50 bg-[var(--color-background)]/95 backdrop-blur-md border-b border-[#2A2A2D]">
        <div className="flex items-center justify-between p-4">
          <h1 className="font-['Cormorant_Garamond'] text-xl font-light">Dashboard</h1>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 hover:bg-[var(--color-surface)] rounded-lg transition-colors"
            data-testid="mobile-menu-toggle"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
        {mobileMenuOpen && (
          <nav className="border-t border-[#2A2A2D] p-4 space-y-2 animate-fade-in">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                  location.pathname === item.path
                    ? "bg-[var(--color-primary)]/10 text-[var(--color-primary)]"
                    : "hover:bg-[var(--color-surface)] text-[#9CA3AF]"
                }`}
              >
                <item.icon className="w-5 h-5" />
                {item.label}
              </Link>
            ))}
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 p-3 rounded-lg text-red-400 hover:bg-red-400/10 w-full"
              data-testid="logout-btn"
            >
              <LogOut className="w-5 h-5" />
              Odjava
            </button>
          </nav>
        )}
      </header>

      <div className="flex">
        {/* Desktop Sidebar */}
        <aside className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 bg-[var(--color-surface)] border-r border-[#2A2A2D]">
          <div className="p-6 border-b border-[#2A2A2D]">
            <h1 className="font-['Cormorant_Garamond'] text-2xl font-light">{isWorker ? "Moj Raspored" : "Beauty Salon"}</h1>
            <p className="text-sm text-[#9CA3AF] mt-1">{user?.email}</p>
            {isWorker && <span className="inline-block mt-1 text-[10px] font-medium uppercase tracking-wider text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded">Radnik</span>}
          </div>
          <nav className="flex-1 p-4 space-y-2">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                  location.pathname === item.path
                    ? "bg-[var(--color-primary)]/10 text-[var(--color-primary)]"
                    : "hover:bg-[var(--color-background)] text-[#9CA3AF]"
                }`}
                data-testid={`nav-${item.label.toLowerCase()}`}
              >
                <item.icon className="w-5 h-5" />
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="p-4 border-t border-[#2A2A2D]">
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 p-3 rounded-lg text-red-400 hover:bg-red-400/10 w-full transition-colors"
              data-testid="desktop-logout-btn"
            >
              <LogOut className="w-5 h-5" />
              Odjava
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 min-w-0 lg:ml-64 p-4 lg:p-8">
          <Routes>
            <Route index element={<ReservationsPage />} />
            {!isWorker && (
              <>
                <Route path="blacklist" element={<BlacklistPage />} />
                <Route path="employees" element={<EmployeesPage />} />
                <Route path="services" element={<ServicesPage />} />
                <Route path="settings" element={<SettingsPage />} />
              </>
            )}
            {/* Worker trying admin-only routes → redirect to reservations */}
            {isWorker && <Route path="*" element={<Navigate to={basePath} replace />} />}
          </Routes>
        </main>
      </div>
    </div>
  );
};

export default AdminDashboard;
