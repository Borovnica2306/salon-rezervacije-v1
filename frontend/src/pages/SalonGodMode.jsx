import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import axios from "axios";
import { API, useAuth } from "../App";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Switch } from "../components/ui/switch";
import {
  Shield, Scissors, ChevronLeft, Loader2, Eye, EyeOff,
  ToggleLeft, Tag, Server, Lock
} from "lucide-react";

const SalonGodMode = () => {
  const { slug } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [tenant, setTenant] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("features");

  // Password change
  const [newPassword, setNewPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);

  // Status change
  const [changingStatus, setChangingStatus] = useState(false);

  const token = localStorage.getItem("access_token");
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    loadData();
  }, [slug]);

  const loadData = async () => {
    setLoading(true);
    try {
      // Get all tenants and find the one matching slug
      const tenantsRes = await axios.get(`${API}/super/tenants`, { headers });
      const found = tenantsRes.data.find(t => t.slug === slug);
      if (!found) {
        toast.error("Salon nije pronađen");
        navigate("/super-admin", { replace: true });
        return;
      }
      setTenant(found);

      // Fetch categories for this tenant
      const catRes = await axios.get(`${API}/categories/config`, {
        headers: { ...headers, "X-Tenant-ID": found.tenant_id }
      });
      setCategories(catRes.data);
    } catch (error) {
      console.error("Load error:", error);
      toast.error("Greška pri učitavanju podataka");
    } finally {
      setLoading(false);
    }
  };

  const handleFeatureToggle = async (featureKey, currentValue) => {
    if (!tenant) return;
    const updated = { ...tenant.enabled_features, [featureKey]: !currentValue };
    try {
      await axios.put(`${API}/super/tenants/${tenant.tenant_id}/features`, updated, { headers });
      setTenant(prev => ({ ...prev, enabled_features: updated }));
      toast.success(`${FEATURE_LABELS[featureKey] || featureKey}: ${!currentValue ? "ON" : "OFF"}`);
    } catch (error) {
      toast.error("Greška pri promeni");
    }
  };

  const handleCategoryToggle = async (key, currentEnabled) => {
    if (!tenant) return;
    try {
      await axios.put(`${API}/categories/config`, { category: key, enabled: !currentEnabled }, {
        headers: { ...headers, "X-Tenant-ID": tenant.tenant_id }
      });
      setCategories(prev => prev.map(c => c.key === key ? { ...c, enabled: !currentEnabled } : c));
      toast.success(`${categories.find(c => c.key === key)?.label} — ${!currentEnabled ? "uključeno" : "isključeno"}`);
    } catch (error) {
      toast.error("Greška pri promeni kategorije");
    }
  };

  const handleStatusToggle = async () => {
    if (!tenant) return;
    const newStatus = (tenant.status || "active") === "active" ? "suspended" : "active";
    setChangingStatus(true);
    try {
      await axios.put(`${API}/super/tenants/${tenant.tenant_id}/status`, { status: newStatus }, { headers });
      setTenant(prev => ({ ...prev, status: newStatus }));
      toast.success(`Status: ${newStatus === "active" ? "Aktivan" : "Suspendovan"}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Greška");
    } finally {
      setChangingStatus(false);
    }
  };

  const handlePasswordChange = async () => {
    if (newPassword.length < 6) {
      toast.error("Lozinka mora imati najmanje 6 karaktera");
      return;
    }
    setChangingPassword(true);
    try {
      await axios.put(`${API}/super/tenants/${tenant.tenant_id}/owner-password`, { password: newPassword }, { headers });
      toast.success("Lozinka vlasnika uspešno promenjena");
      setNewPassword("");
      setShowPassword(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Greška pri promeni lozinke");
    } finally {
      setChangingPassword(false);
    }
  };

  const FEATURE_LABELS = {
    viber_notifications: "Viber/WhatsApp Notifikacije",
    ips_qr_payment: "IPS QR Plaćanje",
    manual_booking: "Manual Booking (Admin)",
    email_notifications: "Email Notifikacije",
    lazy_cancel: "Auto-otkazivanje (Lazy Cancel)",
  };

  const FEATURE_DESCRIPTIONS = {
    viber_notifications: "Direktni Viber i WhatsApp linkovi za komunikaciju sa klijentima",
    ips_qr_payment: "IPS QR kod za uplatu avansa po NBS standardu",
    manual_booking: "Admin može ručno kreirati rezervacije iz dashboarda",
    email_notifications: "Automatski email podsetnici i potvrde rezervacija",
    lazy_cancel: "Automatsko otkazivanje neplaćenih rezervacija nakon 3 sata",
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[#C5A880] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!tenant) return null;

  const isActive = (tenant.status || "active") === "active";
  const enabledCount = categories.filter(c => c.enabled).length;

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white" data-testid="salon-god-mode">
      {/* Banner */}
      <div className="bg-[#C5A880]/10 border-b border-[#C5A880]/30 px-4 py-3" data-testid="god-mode-banner">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <p className="text-sm text-[#C5A880]">
            {"Pregledate sistemska podešavanja za salon: "}
            <span className="font-medium text-white">{tenant.name}</span>
          </p>
          <a
            href="/super-admin"
            className="text-sm font-medium text-[#C5A880] hover:text-[#B89970] transition-colors flex items-center gap-1"
            data-testid="back-to-super-panel"
          >
            <ChevronLeft className="w-4 h-4" />
            {"Nazad na Super Panel"}
          </a>
        </div>
      </div>

      {/* Header */}
      <header className="border-b border-[#2A2A2D]">
        <div className="max-w-5xl mx-auto px-4 py-6">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 rounded-lg bg-[#C5A880]/20 flex items-center justify-center">
              <Shield className="w-5 h-5 text-[#C5A880]" />
            </div>
            <div>
              <h1 className="font-['Cormorant_Garamond'] text-2xl font-light">{tenant.name}</h1>
              <p className="text-xs text-[#6B7280] font-mono">/{tenant.slug} · {tenant.tenant_id}</p>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        {/* Tabs */}
        <div className="flex gap-1 mb-8 bg-[#141416] rounded-lg p-1 w-fit border border-[#2A2A2D]">
          <button onClick={() => setActiveTab("features")} className={`px-4 py-2.5 rounded-md text-sm font-medium transition-colors ${activeTab === "features" ? "bg-[#C5A880] text-black" : "text-[#9CA3AF] hover:text-white"}`} data-testid="godmode-tab-features">
            <ToggleLeft className="w-4 h-4 inline mr-1.5" />Feature Flags
          </button>
          <button onClick={() => setActiveTab("categories")} className={`px-4 py-2.5 rounded-md text-sm font-medium transition-colors ${activeTab === "categories" ? "bg-[#C5A880] text-black" : "text-[#9CA3AF] hover:text-white"}`} data-testid="godmode-tab-categories">
            <Tag className="w-4 h-4 inline mr-1.5" />Kategorije
          </button>
          <button onClick={() => setActiveTab("system")} className={`px-4 py-2.5 rounded-md text-sm font-medium transition-colors ${activeTab === "system" ? "bg-[#C5A880] text-black" : "text-[#9CA3AF] hover:text-white"}`} data-testid="godmode-tab-system">
            <Server className="w-4 h-4 inline mr-1.5" />{"Sistemski podaci"}
          </button>
        </div>

        {/* Feature Flags Tab */}
        {activeTab === "features" && (
          <div className="space-y-1" data-testid="godmode-features-panel">
            <div className="bg-[#141416] rounded-xl border border-[#2A2A2D] overflow-hidden">
              <div className="p-4 border-b border-[#2A2A2D]">
                <h3 className="font-medium text-white">Feature Flags</h3>
                <p className="text-xs text-[#6B7280] mt-0.5">{"Uključite ili isključite funkcionalnosti za ovaj salon"}</p>
              </div>
              <div className="divide-y divide-[#2A2A2D]">
                {Object.entries(tenant.enabled_features || {}).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between p-4 hover:bg-[#0A0A0B]/50 transition-colors" data-testid={`godmode-feature-${key}`}>
                    <div>
                      <span className="text-sm text-white font-medium">{FEATURE_LABELS[key] || key}</span>
                      {FEATURE_DESCRIPTIONS[key] && (
                        <p className="text-xs text-[#6B7280] mt-0.5">{FEATURE_DESCRIPTIONS[key]}</p>
                      )}
                    </div>
                    <Switch
                      checked={value}
                      onCheckedChange={() => handleFeatureToggle(key, value)}
                      className="data-[state=checked]:bg-[#C5A880]"
                      data-testid={`godmode-feature-toggle-${key}`}
                    />
                  </div>
                ))}
              </div>
            </div>
            <div className="p-4 bg-[#C5A880]/5 border border-[#C5A880]/20 rounded-xl mt-4">
              <p className="text-xs text-[#9CA3AF]">
                <strong className="text-[#C5A880]">Napomena:</strong>{" Promene se primenjuju odmah i utiču samo na salon "}<strong className="text-white">{tenant.name}</strong>.
              </p>
            </div>
          </div>
        )}

        {/* Categories Tab */}
        {activeTab === "categories" && (
          <div data-testid="godmode-categories-panel">
            <div className="bg-[#141416] rounded-xl border border-[#2A2A2D] overflow-hidden">
              <div className="p-4 border-b border-[#2A2A2D] flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-white">Kategorije usluga</h3>
                  <p className="text-xs text-[#6B7280] mt-0.5">{"Upravljanje kategorijama za ovaj salon"}</p>
                </div>
                <span className="text-xs text-[#C5A880]">{enabledCount} / {categories.length} aktivno</span>
              </div>
              <div className="divide-y divide-[#2A2A2D]">
                {categories.map((cat) => (
                  <div key={cat.key} className={`flex items-center justify-between p-5 transition-colors ${cat.enabled ? "" : "opacity-50"}`} data-testid={`godmode-category-${cat.key}`}>
                    <div>
                      <span className="font-medium text-base">{cat.label}</span>
                      <span className="hidden sm:inline ml-3 text-xs text-[#9CA3AF] font-mono">{cat.key}</span>
                    </div>
                    <Switch
                      checked={cat.enabled}
                      onCheckedChange={() => handleCategoryToggle(cat.key, cat.enabled)}
                      className="data-[state=checked]:bg-[#C5A880]"
                      data-testid={`godmode-category-toggle-${cat.key}`}
                    />
                  </div>
                ))}
              </div>
            </div>
            <div className="p-4 bg-[#C5A880]/5 border border-[#C5A880]/20 rounded-xl mt-4">
              <p className="text-xs text-[#9CA3AF]">
                <strong className="text-[#C5A880]">Napomena:</strong>{" Isključivanje kategorije sakriva usluge iz javnog prikaza samo za "}<strong className="text-white">{tenant.name}</strong>.
              </p>
            </div>
          </div>
        )}

        {/* System Tab */}
        {activeTab === "system" && (
          <div className="space-y-6" data-testid="godmode-system-panel">
            {/* Status */}
            <div className="bg-[#141416] rounded-xl border border-[#2A2A2D] overflow-hidden">
              <div className="p-4 border-b border-[#2A2A2D]">
                <h3 className="font-medium text-white">Status salona</h3>
              </div>
              <div className="p-5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className={`w-3 h-3 rounded-full ${isActive ? "bg-green-500" : "bg-red-500"}`} />
                  <span className="text-sm font-medium">{isActive ? "Aktivan" : "Suspendovan"}</span>
                  {!isActive && (
                    <span className="text-xs text-red-400">{"Klijenti ne mogu pristupiti stranici za zakazivanje"}</span>
                  )}
                </div>
                <Button
                  onClick={handleStatusToggle}
                  disabled={changingStatus}
                  variant={isActive ? "outline" : "default"}
                  className={isActive
                    ? "border-red-500/30 text-red-400 hover:bg-red-500/10 hover:text-red-300"
                    : "bg-green-600 hover:bg-green-700 text-white"
                  }
                  data-testid="toggle-status-btn"
                >
                  {changingStatus && <Loader2 className="w-4 h-4 animate-spin mr-1" />}
                  {isActive ? "Suspenduj" : "Aktiviraj"}
                </Button>
              </div>
            </div>

            {/* Owner info */}
            <div className="bg-[#141416] rounded-xl border border-[#2A2A2D] overflow-hidden">
              <div className="p-4 border-b border-[#2A2A2D]">
                <h3 className="font-medium text-white">{"Podaci o vlasniku"}</h3>
              </div>
              <div className="p-5 space-y-4">
                <div>
                  <label className="text-xs text-[#6B7280] block mb-1">Email vlasnika</label>
                  <p className="text-sm text-white font-mono bg-[#0A0A0B] px-3 py-2.5 rounded-lg border border-[#2A2A2D]" data-testid="owner-email-display">
                    {tenant.owner_email || "—"}
                  </p>
                </div>

                <div>
                  <label className="text-xs text-[#6B7280] block mb-1">{"Promena lozinke vlasnika"}</label>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7280]" />
                      <Input
                        type={showPassword ? "text" : "password"}
                        value={newPassword}
                        onChange={e => setNewPassword(e.target.value)}
                        placeholder="Nova lozinka (min 6 karaktera)"
                        className="pl-10 pr-10 bg-[#0A0A0B] border-[#2A2A2D] h-11"
                        data-testid="new-owner-password-input"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-[#6B7280] hover:text-white"
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    <Button
                      onClick={handlePasswordChange}
                      disabled={changingPassword || newPassword.length < 6}
                      className="bg-[#C5A880] hover:bg-[#B89970] text-black font-medium h-11 px-5"
                      data-testid="change-password-btn"
                    >
                      {changingPassword ? <Loader2 className="w-4 h-4 animate-spin" /> : "Promeni"}
                    </Button>
                  </div>
                </div>
              </div>
            </div>

            {/* Salon info summary */}
            <div className="bg-[#141416] rounded-xl border border-[#2A2A2D] overflow-hidden">
              <div className="p-4 border-b border-[#2A2A2D]">
                <h3 className="font-medium text-white">{"Informacije o salonu"}</h3>
              </div>
              <div className="p-5 grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-[#6B7280] block mb-1">Naziv</label>
                  <p className="text-sm text-white">{tenant.name}</p>
                </div>
                <div>
                  <label className="text-xs text-[#6B7280] block mb-1">Slug</label>
                  <p className="text-sm text-white font-mono">/{tenant.slug}</p>
                </div>
                <div>
                  <label className="text-xs text-[#6B7280] block mb-1">{"Država"}</label>
                  <p className="text-sm text-white">{tenant.country || "RS"}</p>
                </div>
                <div>
                  <label className="text-xs text-[#6B7280] block mb-1">Grad</label>
                  <p className="text-sm text-white">{tenant.city || "—"}</p>
                </div>
                <div>
                  <label className="text-xs text-[#6B7280] block mb-1">Tenant ID</label>
                  <p className="text-sm text-white font-mono text-xs">{tenant.tenant_id}</p>
                </div>
                <div>
                  <label className="text-xs text-[#6B7280] block mb-1">Kreiran</label>
                  <p className="text-sm text-white">{tenant.created_at ? new Date(tenant.created_at).toLocaleDateString("sr-Latn") : "—"}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default SalonGodMode;
