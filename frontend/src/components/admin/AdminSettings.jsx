import React, { useState, useEffect } from "react";
import { toast } from "sonner";
import axios from "axios";
import { API, useAuth, useTenant, getTenantHeaders, getToken } from "../../App";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Settings, CreditCard } from "lucide-react";
import { PhoneInput } from "../PhoneInput";

const SettingsPage = () => {
  const tenant = useTenant();
  const { user } = useAuth();
  const isSuperAdmin = user?.role === "super_admin";
  const [settings, setSettings] = useState({
    salon_name: "",
    work_start: "09:00",
    work_end: "21:00",
    advance_instructions: "",
    pi_wallet_address: "",
    smtp_server: "smtp.gmail.com",
    smtp_port: 587,
    smtp_user: "",
    smtp_password: "",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const token = getToken();
  const headers = { Authorization: `Bearer ${token}`, ...getTenantHeaders(tenant?.tenant_id) };

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`, { headers });
      setSettings(response.data);
    } catch (error) {
      toast.error("Greška pri učitavanju");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = { ...settings };
      if (!isSuperAdmin) {
        delete payload.smtp_server;
        delete payload.smtp_port;
        delete payload.smtp_user;
        delete payload.smtp_password;
        delete payload.salon_name;
      }
      await axios.put(`${API}/settings`, payload, { headers });
      // Super admin: sync tenant name
      if (isSuperAdmin && settings.salon_name) {
        await axios.put(`${API}/super/tenants/${tenant?.tenant_id}/name`, 
          { name: settings.salon_name }, { headers }).catch(() => {});
      }
      toast.success("Podešavanja sačuvana");
    } catch (error) {
      toast.error("Greška pri čuvanju");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12 text-[#9CA3AF]">Učitavanje...</div>;
  }

  return (
    <div className="animate-fade-in max-w-2xl">
      <h2 className="font-['Cormorant_Garamond'] text-3xl font-light mb-6">Podešavanja</h2>

      <div className="bg-[var(--color-surface)] rounded-xl border border-[#2A2A2D] p-6 space-y-6">
        <div>
          <label className="text-sm text-[#9CA3AF] mb-2 block">Naziv Salona</label>
          <Input
            value={settings.salon_name}
            onChange={(e) => setSettings({ ...settings, salon_name: e.target.value })}
            placeholder="Beauty Salon"
            disabled={!isSuperAdmin}
            className={`bg-[var(--color-background)] border-[#2A2A2D] ${!isSuperAdmin ? "opacity-60 cursor-not-allowed" : ""}`}
            data-testid="settings-salon-name"
          />
          {!isSuperAdmin && (
            <p className="text-[10px] text-[#6B7280] mt-1">Za promenu naziva kontaktirajte podršku.</p>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-[#9CA3AF] mb-2 block">Radno vreme od</label>
            <Input
              type="time"
              value={settings.work_start}
              onChange={(e) => setSettings({ ...settings, work_start: e.target.value })}
              className="bg-[var(--color-background)] border-[#2A2A2D]"
              data-testid="settings-work-start"
            />
          </div>
          <div>
            <label className="text-sm text-[#9CA3AF] mb-2 block">Radno vreme do</label>
            <Input
              type="time"
              value={settings.work_end}
              onChange={(e) => setSettings({ ...settings, work_end: e.target.value })}
              className="bg-[var(--color-background)] border-[#2A2A2D]"
              data-testid="settings-work-end"
            />
          </div>
        </div>

        <div className="border-t border-[#2A2A2D] pt-6">
          <h3 className="font-medium mb-4 flex items-center gap-2">
            <CreditCard className="w-4 h-4 text-[var(--color-primary)]" />
            Pi Wallet
          </h3>
          <div className="space-y-4">
            {/* Security Banner */}
            <div className="bg-red-950/60 border border-red-500/30 rounded-xl p-4" data-testid="pi-security-banner">
              <p className="text-red-400 font-medium text-sm mb-2 flex items-center gap-2">
                <span className="text-base">&#9888;&#65039;</span>
                {"VAŽNO SIGURNOSNO UPOZORENJE"}
              </p>
              <ul className="text-xs text-red-300/80 space-y-1.5 leading-relaxed">
                <li>{"• Unesite isključivo vašu JAVNU adresu Pi novčanika (ona počinje slovom 'G' i služi za primanje uplata)."}</li>
                <li>{"• NIKADA i ni na jednom mestu u ovoj aplikaciji nemojte upisivati svoju lozinku od 24 reči (passphrase). Ova aplikacija vas nikada neće pitati za te reči. Ako vam bilo ko traži te reči – u pitanju je prevara!"}</li>
              </ul>
            </div>

            <div>
              <label className="text-sm text-[#9CA3AF] mb-2 block">{"Javna adresa Pi novčanika"}</label>
              <Input
                value={settings.pi_wallet_address}
                onChange={(e) => setSettings({ ...settings, pi_wallet_address: e.target.value })}
                placeholder="GABCDEFGHIJKLMNOPQRSTUVWXYZ234567..."
                className="bg-[var(--color-background)] border-[#2A2A2D] font-mono text-sm"
                data-testid="settings-pi-wallet"
              />
              {settings.pi_wallet_address && settings.pi_wallet_address.length < 20 && (
                <p className="text-[10px] text-red-400 mt-1">{"Adresa mora imati najmanje 20 karaktera"}</p>
              )}
            </div>
          </div>
        </div>

        {/* Integrations Section - Super Admin Only */}
        {isSuperAdmin && (
        <div className="border-t border-[#2A2A2D] pt-6">
          <h3 className="font-medium mb-4 flex items-center gap-2">
            <Settings className="w-4 h-4 text-[var(--color-primary)]" />
            Integracije i Obaveštenja
          </h3>

          <div className="space-y-5">
            {/* SMTP Configuration */}
            <div className="bg-[var(--color-background)] rounded-lg p-4 space-y-4">
              <p className="text-xs text-[#9CA3AF] uppercase tracking-wider">Email (SMTP)</p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-[#9CA3AF] mb-1.5 block">SMTP Server</label>
                  <Input
                    value={settings.smtp_server}
                    onChange={(e) => setSettings({ ...settings, smtp_server: e.target.value })}
                    placeholder="smtp.gmail.com"
                    className="bg-[var(--color-surface)] border-[#2A2A2D] min-h-[48px]"
                    data-testid="settings-smtp-server"
                  />
                </div>
                <div>
                  <label className="text-sm text-[#9CA3AF] mb-1.5 block">SMTP Port</label>
                  <Input
                    type="number"
                    value={settings.smtp_port}
                    onChange={(e) => setSettings({ ...settings, smtp_port: parseInt(e.target.value) || 587 })}
                    placeholder="587"
                    className="bg-[var(--color-surface)] border-[#2A2A2D] min-h-[48px]"
                    data-testid="settings-smtp-port"
                  />
                </div>
              </div>
              <div>
                <label className="text-sm text-[#9CA3AF] mb-1.5 block">Email za slanje</label>
                <Input
                  type="email"
                  value={settings.smtp_user}
                  onChange={(e) => setSettings({ ...settings, smtp_user: e.target.value })}
                  placeholder="salon@gmail.com"
                  className="bg-[var(--color-surface)] border-[#2A2A2D] min-h-[48px]"
                  data-testid="settings-smtp-user"
                />
              </div>
              <div>
                <label className="text-sm text-[#9CA3AF] mb-1.5 block">Lozinka Aplikacije</label>
                <Input
                  type="password"
                  value={settings.smtp_password}
                  onChange={(e) => setSettings({ ...settings, smtp_password: e.target.value })}
                  placeholder="16-cifreni Gmail App Password"
                  className="bg-[var(--color-surface)] border-[#2A2A2D] min-h-[48px]"
                  data-testid="settings-smtp-password"
                />
                <p className="text-[10px] text-[#6B7280] mt-1">Generišite na: myaccount.google.com/apppasswords</p>
              </div>
            </div>

            {/* Viber Configuration - removed, moved to general section */}
          </div>
        </div>
        )}

        <Button
          onClick={handleSave}
          disabled={saving}
          className="w-full bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black"
          data-testid="save-settings-btn"
        >
          {saving ? "Čuvanje..." : "Sačuvaj Podešavanja"}
        </Button>
      </div>
    </div>
  );
};



export default SettingsPage;
