import React, { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import axios from "axios";
import { API, useAuth, getToken } from "../App";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import {
  Shield, Building2, Plus, LogOut, Loader2,
  ChevronRight, Search, Globe
} from "lucide-react";

const SuperAdminPage = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user && user.role !== "super_admin") {
      navigate("/login", { replace: true });
    }
  }, [user, navigate]);

  if (!user || user.role !== "super_admin") return null;

  return (
    <div className="min-h-screen bg-[var(--color-background)] text-white" data-testid="super-admin-page">
      {/* Header */}
      <header className="border-b border-[#2A2A2D] bg-[var(--color-background)]/90 backdrop-blur-sm sticky top-0 z-30">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-[var(--color-primary)]/20 flex items-center justify-center">
              <Shield className="w-5 h-5 text-[var(--color-primary)]" />
            </div>
            <div>
              <h1 className="font-['Cormorant_Garamond'] text-lg font-medium">Super Admin</h1>
              <p className="text-[10px] text-[#6B7280]">{user.email}</p>
            </div>
          </div>
          <Button
            variant="ghost"
            onClick={async () => { await logout(); navigate("/login", { replace: true }); }}
            className="text-[#9CA3AF] hover:text-white"
            data-testid="sa-logout-btn"
          >
            <LogOut className="w-4 h-4 mr-2" />
            Odjava
          </Button>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        <SalonListPanel />
      </main>
    </div>
  );
};

const SalonListPanel = () => {
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newSalon, setNewSalon] = useState({ name: "", email: "", password: "", country: "RS", city: "" });
  const [searchQuery, setSearchQuery] = useState("");
  const [countryFilter, setCountryFilter] = useState("");

  const token = getToken();
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchTenants().finally(() => setLoading(false));
  }, []);

  const fetchTenants = async () => {
    try {
      const res = await axios.get(`${API}/super/tenants`, { headers });
      setTenants(res.data);
    } catch (error) {
      console.error("Error fetching tenants:", error);
    }
  };

  const handleCreateSalon = async () => {
    if (!newSalon.name.trim() || !newSalon.email.trim() || !newSalon.password.trim()) {
      toast.error("Sva polja su obavezna"); return;
    }
    setCreating(true);
    try {
      await axios.post(`${API}/super/tenants`, newSalon, { headers });
      toast.success(`Salon "${newSalon.name}" kreiran!`);
      setShowCreateModal(false);
      setNewSalon({ name: "", email: "", password: "", country: "RS", city: "" });
      fetchTenants();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Greška pri kreiranju");
    } finally {
      setCreating(false);
    }
  };

  const SALON_COUNTRIES = [
    { code: "RS", name: "Srbija" }, { code: "HR", name: "Hrvatska" },
    { code: "BA", name: "BiH" }, { code: "ME", name: "Crna Gora" },
    { code: "DE", name: "Nemačka" }, { code: "AT", name: "Austrija" },
    { code: "CH", name: "Švajcarska" },
  ];

  const filteredTenants = useMemo(() => {
    let result = tenants;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(t =>
        t.name.toLowerCase().includes(q) ||
        t.slug.toLowerCase().includes(q) ||
        (t.city || "").toLowerCase().includes(q) ||
        (t.owner_email || "").toLowerCase().includes(q)
      );
    }
    if (countryFilter) {
      result = result.filter(t => (t.country || "RS") === countryFilter);
    }
    return result;
  }, [tenants, searchQuery, countryFilter]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-8 h-8 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="animate-fade-in" data-testid="salon-list-panel">
      <div className="mb-8">
        <h2 className="font-['Cormorant_Garamond'] text-3xl font-light mb-2">{"Upravljanje Salonima"}</h2>
        <p className="text-[#9CA3AF]">{"Pregled, pretraga i upravljanje salonima na platformi."}</p>
      </div>

      {/* Top row */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm text-[#9CA3AF]">
          {filteredTenants.length === tenants.length
            ? `${tenants.length} registrovanih salona`
            : `${filteredTenants.length} od ${tenants.length} salona`
          }
        </span>
        <Button onClick={() => setShowCreateModal(true)} className="bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black font-medium" data-testid="create-salon-btn">
          <Plus className="w-4 h-4 mr-1" /> {"Dodaj novi salon"}
        </Button>
      </div>

      {/* Search & Filter */}
      <div className="flex gap-3 items-center mb-4" data-testid="salon-filters">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7280]" />
          <Input
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder={"Pretraži salone..."}
            className="pl-10 bg-[var(--color-surface)] border-[#2A2A2D] h-11 text-sm"
            data-testid="salon-search-input"
          />
        </div>
        <select
          value={countryFilter}
          onChange={e => setCountryFilter(e.target.value)}
          className="bg-[var(--color-surface)] border border-[#2A2A2D] rounded-lg px-3 text-white h-11 text-sm min-w-[140px]"
          data-testid="salon-country-filter"
        >
          <option value="">{"Sve zemlje"}</option>
          {SALON_COUNTRIES.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
        </select>
      </div>

      {/* Salon list */}
      <div className="space-y-3">
        {filteredTenants.map((t) => {
          const isActive = (t.status || "active") === "active";
          return (
            <div key={t.tenant_id} className="bg-[var(--color-surface)] rounded-xl border border-[#2A2A2D] p-4 flex items-center justify-between group hover:border-[var(--color-primary)]/30 transition-colors" data-testid={`salon-row-${t.tenant_id}`}>
              <div className="min-w-0 flex-1">
                <h3 className="font-medium text-white">{t.name}</h3>
                <p className="text-xs text-[#6B7280] font-mono mt-0.5">/{t.slug} · {t.country || "RS"}{t.city ? ` · ${t.city}` : ""}</p>
                {t.owner_email && <p className="text-xs text-[#9CA3AF] mt-1">{t.owner_email}</p>}
              </div>
              <div className="flex items-center gap-2">
                <a
                  href={`/${t.slug}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-[#9CA3AF] hover:text-white flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-[#2A2A2D] hover:border-[#9CA3AF]/50 transition-colors"
                  data-testid={`salon-client-link-${t.tenant_id}`}
                  title="Otvori klijentski booking u novom tabu"
                >
                  <Globe className="w-3.5 h-3.5" />
                </a>
                <a
                  href={`/super-admin/salon/${t.slug}`}
                  className="text-xs text-[var(--color-primary)] hover:underline flex items-center gap-1 px-3 py-1.5 rounded-lg border border-[var(--color-primary)]/30 hover:bg-[var(--color-primary)]/10 transition-colors"
                  data-testid={`salon-link-${t.tenant_id}`}
                >
                  Panel <ChevronRight className="w-3 h-3" />
                </a>
                <span className={`text-xs px-2 py-1 rounded-full ${isActive ? "bg-green-600/20 text-green-400" : "bg-red-600/20 text-red-400"}`}>
                  {isActive ? "Aktivan" : "Suspendovan"}
                </span>
              </div>
            </div>
          );
        })}

        {filteredTenants.length === 0 && tenants.length > 0 && (
          <div className="text-center py-12 text-[#6B7280] bg-[var(--color-surface)] rounded-xl border border-[#2A2A2D]">
            {"Nema rezultata za zadati filter."}
          </div>
        )}

        {tenants.length === 0 && (
          <div className="text-center py-12 text-[#9CA3AF] bg-[var(--color-surface)] rounded-xl border border-[#2A2A2D]">{"Nema registrovanih salona."}</div>
        )}
      </div>

      {/* Create Salon Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={() => setShowCreateModal(false)}>
          <div className="bg-[var(--color-surface)] border border-[#2A2A2D] rounded-xl p-6 w-full max-w-md space-y-4" onClick={e => e.stopPropagation()} data-testid="create-salon-modal">
            <h3 className="text-lg font-medium">Novi Salon</h3>
            <div>
              <label className="text-sm text-[#9CA3AF] mb-1 block">Naziv salona</label>
              <Input value={newSalon.name} onChange={e => setNewSalon({...newSalon, name: e.target.value})} placeholder="Beauty Studio Novi Sad" className="bg-[var(--color-background)] border-[#2A2A2D] min-h-[48px]" data-testid="new-salon-name" />
            </div>
            <div>
              <label className="text-sm text-[#9CA3AF] mb-1 block">Email vlasnika (admin login)</label>
              <Input type="email" value={newSalon.email} onChange={e => setNewSalon({...newSalon, email: e.target.value})} placeholder="vlasnik@salon.com" className="bg-[var(--color-background)] border-[#2A2A2D] min-h-[48px]" data-testid="new-salon-email" />
            </div>
            <div>
              <label className="text-sm text-[#9CA3AF] mb-1 block">Lozinka</label>
              <Input type="password" value={newSalon.password} onChange={e => setNewSalon({...newSalon, password: e.target.value})} placeholder="Minimum 6 karaktera" className="bg-[var(--color-background)] border-[#2A2A2D] min-h-[48px]" data-testid="new-salon-password" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-sm text-[#9CA3AF] mb-1 block">{"Država"}</label>
                <select value={newSalon.country} onChange={e => setNewSalon({...newSalon, country: e.target.value})} className="w-full bg-[var(--color-background)] border border-[#2A2A2D] rounded-lg px-3 text-white min-h-[48px] text-sm" data-testid="new-salon-country">
                  {SALON_COUNTRIES.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label className="text-sm text-[#9CA3AF] mb-1 block">Grad</label>
                <Input value={newSalon.city} onChange={e => setNewSalon({...newSalon, city: e.target.value})} placeholder="Novi Sad" className="bg-[var(--color-background)] border-[#2A2A2D] min-h-[48px]" data-testid="new-salon-city" />
              </div>
            </div>
            <div className="flex gap-2 pt-2">
              <Button variant="outline" onClick={() => setShowCreateModal(false)} className="flex-1 border-[#2A2A2D] min-h-[48px]">{"Otkaži"}</Button>
              <Button onClick={handleCreateSalon} disabled={creating} className="flex-1 bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black font-medium min-h-[48px]" data-testid="submit-create-salon">
                {creating ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Plus className="w-4 h-4 mr-1" />}
                Kreiraj
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SuperAdminPage;
