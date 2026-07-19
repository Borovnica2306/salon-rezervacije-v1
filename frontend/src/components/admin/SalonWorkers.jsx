import React, { useState, useEffect } from "react";
import { toast } from "sonner";
import axios from "axios";
import { API, useTenant, getTenantHeaders, getToken } from "../../App";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Users, Plus, Edit2, Trash2, AlertTriangle, KeyRound, Copy, Check, X as XIcon } from "lucide-react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription,
} from "../ui/dialog";

const EmployeesPage = () => {
  const tenant = useTenant();
  const [employees, setEmployees] = useState([]);
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  // Worker account state
  const [accountDialogOpen, setAccountDialogOpen] = useState(false);
  const [accountTarget, setAccountTarget] = useState(null);
  const [accountEmail, setAccountEmail] = useState("");
  const [accountLoading, setAccountLoading] = useState(false);
  const [createdAccount, setCreatedAccount] = useState(null);
  const [copiedField, setCopiedField] = useState(null);
  const [workerAccounts, setWorkerAccounts] = useState({});
  const [form, setForm] = useState({
    name: "",
    categories: [],
    work_start: "09:00",
    work_end: "21:00",
    break_start: "",
    break_end: "",
    days_off: [],
  });

  const [categories, setCategories] = useState([]);
  const [salonSettings, setSalonSettings] = useState(null);

  const token = getToken();
  const headers = { Authorization: `Bearer ${token}`, ...getTenantHeaders(tenant?.tenant_id) };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [empRes, servRes, catRes, settRes] = await Promise.all([
        axios.get(`${API}/workers?active_only=false`, { headers }),
        axios.get(`${API}/services?active_only=false`, { headers }),
        axios.get(`${API}/categories`, { headers }),
        axios.get(`${API}/settings`, { headers }),
      ]);
      setEmployees(empRes.data);
      setServices(servRes.data);
      setCategories(catRes.data);
      setSalonSettings(settRes.data);

      // Fetch account status for each worker
      const accountStatuses = {};
      await Promise.all(empRes.data.map(async (emp) => {
        try {
          const r = await axios.get(`${API}/workers/${emp.id}/account`, { headers });
          accountStatuses[emp.id] = r.data;
        } catch { accountStatuses[emp.id] = { has_account: false }; }
      }));
      setWorkerAccounts(accountStatuses);
    } catch (error) {
      toast.error("Greška pri učitavanju");
    } finally {
      setLoading(false);
    }
  };

  // Generate time options within salon hours (15-min intervals)
  const salonStart = salonSettings?.work_start || "09:00";
  const salonEnd = salonSettings?.work_end || "21:00";
  const salonClosedDays = salonSettings?.closed_days || [];

  const generateTimeOptions = (minTime, maxTime) => {
    const options = [];
    const [minH, minM] = minTime.split(":").map(Number);
    const [maxH, maxM] = maxTime.split(":").map(Number);
    const startMin = minH * 60 + minM;
    const endMin = maxH * 60 + maxM;
    for (let m = startMin; m <= endMin; m += 15) {
      const h = Math.floor(m / 60);
      const mi = m % 60;
      options.push(`${String(h).padStart(2, "0")}:${String(mi).padStart(2, "0")}`);
    }
    return options;
  };

  const startOptions = generateTimeOptions(salonStart, salonEnd);
  const endOptions = generateTimeOptions(salonStart, salonEnd);

  // Group ACTIVE services by category
  const activeServices = services.filter(s => s.active);
  const servicesByCategory = {};
  activeServices.forEach(s => {
    if (!servicesByCategory[s.category]) servicesByCategory[s.category] = [];
    servicesByCategory[s.category].push(s);
  });

  // Derive categories from worker's service list (for edit mode)
  // A category is checked if the worker has ANY service from that category
  const getCategoriesFromServices = (serviceIds) => {
    const cats = new Set();
    serviceIds.forEach(sid => {
      const svc = services.find(s => s.id === sid);
      if (svc) cats.add(svc.category);
    });
    return [...cats];
  };

  // Resolve service IDs from selected categories (only active services)
  const getServiceIdsFromCategories = (selectedCats) => {
    return activeServices
      .filter(s => selectedCats.includes(s.category))
      .map(s => s.id);
  };

  const resetForm = () => {
    setForm({
      name: "",
      categories: [],
      work_start: salonStart,
      work_end: salonEnd,
      break_start: "",
      break_end: "",
      days_off: [...salonClosedDays],
    });
    setEditingEmployee(null);
  };

  const handleEdit = (emp) => {
    setEditingEmployee(emp);
    setForm({
      name: emp.name,
      categories: getCategoriesFromServices(emp.services || []),
      work_start: emp.work_start,
      work_end: emp.work_end,
      break_start: emp.break_start || "",
      break_end: emp.break_end || "",
      days_off: emp.days_off || [],
    });
    setDialogOpen(true);
  };

  const handleSubmit = async () => {
    if (!form.name.trim()) {
      toast.error("Unesite ime radnika");
      return;
    }

    try {
      const resolvedServices = getServiceIdsFromCategories(form.categories);
      const payload = {
        name: form.name,
        services: resolvedServices,
        work_start: form.work_start,
        work_end: form.work_end,
        break_start: form.break_start || null,
        break_end: form.break_end || null,
        days_off: form.days_off,
      };

      if (editingEmployee) {
        await axios.put(`${API}/workers/${editingEmployee.id}`, payload, { headers });
        toast.success("Radnik ažuriran");
      } else {
        await axios.post(`${API}/workers`, payload, { headers });
        toast.success("Radnik dodat");
      }
      
      setDialogOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error("Greška pri čuvanju");
    }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API}/workers/${id}`, { headers });
      toast.success("Radnik je trajno obrisan");
      setDeleteConfirm(null);
      fetchData();
    } catch (error) {
      const msg = error.response?.data?.detail || "Greška pri brisanju";
      toast.error(msg);
      setDeleteConfirm(null);
    }
  };

  const toggleCategory = (catKey) => {
    setForm(prev => ({
      ...prev,
      categories: prev.categories.includes(catKey)
        ? prev.categories.filter(c => c !== catKey)
        : [...prev.categories, catKey],
    }));
  };

  const toggleDayOff = (day) => {
    setForm(prev => ({
      ...prev,
      days_off: prev.days_off.includes(day)
        ? prev.days_off.filter(d => d !== day)
        : [...prev.days_off, day],
    }));
  };

  const dayLabels = ["Ned", "Pon", "Uto", "Sre", "Čet", "Pet", "Sub"];

  const openAccountDialog = (emp) => {
    setAccountTarget(emp);
    setAccountEmail("");
    setCreatedAccount(null);
    setCopiedField(null);
    setAccountDialogOpen(true);
  };

  const handleCreateAccount = async () => {
    if (!accountEmail.trim() || !accountEmail.includes("@")) {
      toast.error("Unesite validan email");
      return;
    }
    setAccountLoading(true);
    try {
      const res = await axios.post(
        `${API}/workers/${accountTarget.id}/create-account`,
        { email: accountEmail.trim() },
        { headers }
      );
      setCreatedAccount(res.data);
      toast.success(`Nalog kreiran za ${accountTarget.name}`);
      fetchData();
    } catch (error) {
      const msg = error.response?.data?.detail || "Greška pri kreiranju naloga";
      toast.error(msg);
    } finally {
      setAccountLoading(false);
    }
  };

  const handleDeleteAccount = async (workerId) => {
    try {
      await axios.delete(`${API}/workers/${workerId}/account`, { headers });
      toast.success("Nalog radnika obrisan");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Greška");
    }
  };

  const copyToClipboard = async (text, field) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    } catch {
      toast.error("Kopiranje nije uspelo");
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <h2 className="font-['Cormorant_Garamond'] text-3xl font-light">Radnici</h2>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black" data-testid="add-employee-btn">
              <Plus className="w-4 h-4 mr-2" />
              Dodaj Radnika
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-[var(--color-surface)] border-[#2A2A2D] max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-['Cormorant_Garamond'] text-2xl">
                {editingEmployee ? "Izmeni Radnika" : "Novi Radnik"}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Ime</label>
                <Input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Ime radnika"
                  className="bg-[var(--color-background)] border-[#2A2A2D]"
                  data-testid="employee-name-input"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-[#9CA3AF] mb-2 block">{"Početak rada"}</label>
                  <select
                    value={form.work_start}
                    onChange={(e) => {
                      const val = e.target.value;
                      setForm(prev => ({
                        ...prev,
                        work_start: val,
                        work_end: prev.work_end < val ? val : prev.work_end,
                      }));
                    }}
                    className="w-full bg-[var(--color-background)] border border-[#2A2A2D] rounded-lg px-3 h-10 text-white text-sm focus:border-[var(--color-primary)] focus:outline-none"
                    data-testid="employee-work-start"
                  >
                    {startOptions.map(t => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-sm text-[#9CA3AF] mb-2 block">{"Kraj rada"}</label>
                  <select
                    value={form.work_end}
                    onChange={(e) => setForm({ ...form, work_end: e.target.value })}
                    className="w-full bg-[var(--color-background)] border border-[#2A2A2D] rounded-lg px-3 h-10 text-white text-sm focus:border-[var(--color-primary)] focus:outline-none"
                    data-testid="employee-work-end"
                  >
                    {endOptions.filter(t => t >= form.work_start).map(t => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
              </div>
              <p className="text-[10px] text-[#6B7280] -mt-2">
                {"Ograničeno radnim vremenom salona: "}{salonStart}{" — "}{salonEnd}
              </p>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-[#9CA3AF] mb-2 block">Pauza od</label>
                  <select
                    value={form.break_start}
                    onChange={(e) => setForm({ ...form, break_start: e.target.value })}
                    className="w-full bg-[var(--color-background)] border border-[#2A2A2D] rounded-lg px-3 h-10 text-white text-sm focus:border-[var(--color-primary)] focus:outline-none"
                    data-testid="employee-break-start"
                  >
                    <option value="">{"—"}</option>
                    {startOptions.filter(t => t >= form.work_start && t < form.work_end).map(t => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-sm text-[#9CA3AF] mb-2 block">Pauza do</label>
                  <select
                    value={form.break_end}
                    onChange={(e) => setForm({ ...form, break_end: e.target.value })}
                    className="w-full bg-[var(--color-background)] border border-[#2A2A2D] rounded-lg px-3 h-10 text-white text-sm focus:border-[var(--color-primary)] focus:outline-none"
                    data-testid="employee-break-end"
                  >
                    <option value="">{"—"}</option>
                    {startOptions.filter(t => t > (form.break_start || form.work_start) && t <= form.work_end).map(t => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Slobodni dani</label>
                <div className="flex flex-wrap gap-2">
                  {dayLabels.map((label, idx) => {
                    const salonClosed = salonClosedDays.includes(idx);
                    const isOff = form.days_off.includes(idx);
                    return (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => !salonClosed && toggleDayOff(idx)}
                        disabled={salonClosed}
                        className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                          salonClosed
                            ? "bg-[var(--color-background)] border border-[#2A2A2D] text-[#3A3A3D] cursor-not-allowed line-through"
                            : isOff
                              ? "bg-[var(--color-primary)] text-black"
                              : "bg-[var(--color-background)] border border-[#2A2A2D] text-[#9CA3AF]"
                        }`}
                        title={salonClosed ? "Salon je zatvoren ovog dana" : ""}
                      >
                        {label}
                      </button>
                    );
                  })}
                </div>
                {salonClosedDays.length > 0 && (
                  <p className="text-[10px] text-[#6B7280] mt-1">{"Precrtani dani: salon je zatvoren."}</p>
                )}
              </div>

              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Kategorije usluga</label>
                <div className="space-y-2">
                  {categories.map((cat) => {
                    const catServices = servicesByCategory[cat.key] || [];
                    const isSelected = form.categories.includes(cat.key);
                    return (
                      <button
                        key={cat.key}
                        type="button"
                        onClick={() => toggleCategory(cat.key)}
                        className={`w-full p-3 rounded-lg text-left text-sm transition-colors ${
                          isSelected
                            ? "bg-[var(--color-primary)]/10 border border-[var(--color-primary)]"
                            : "bg-[var(--color-background)] border border-[#2A2A2D] hover:border-[var(--color-primary)]/50"
                        }`}
                        data-testid={`category-toggle-${cat.key}`}
                      >
                        <span className="font-medium">{cat.label}</span>
                        <span className="text-[#6B7280] ml-2 text-xs">({catServices.length} usluga)</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              <Button
                onClick={handleSubmit}
                className="w-full bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black"
                data-testid="save-employee-btn"
              >
                {editingEmployee ? "Sačuvaj Izmene" : "Dodaj Radnika"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="text-center py-12 text-[#9CA3AF]">Učitavanje...</div>
      ) : employees.length === 0 ? (
        <div className="text-center py-12 bg-[var(--color-surface)] rounded-xl border border-[#2A2A2D]">
          <Users className="w-12 h-12 mx-auto text-[#9CA3AF] mb-4" />
          <p className="text-[#9CA3AF]">Nema radnika</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 stagger-children">
          {employees.map((emp) => (
            <div
              key={emp.id}
              className={`bg-[var(--color-surface)] rounded-xl border p-5 ${
                emp.active ? "border-[#2A2A2D]" : "border-red-400/30 opacity-60"
              }`}
              data-testid={`employee-${emp.id}`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#C5A880] to-[#8B7355] flex items-center justify-center text-black font-semibold text-lg">
                    {emp.name.charAt(0)}
                  </div>
                  <div>
                    <h3 className="font-medium">{emp.name}</h3>
                    <p className="text-sm text-[#9CA3AF]">
                      {emp.work_start} - {emp.work_end}
                    </p>
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => handleEdit(emp)}
                    className="h-8 w-8 hover:bg-[var(--color-background)]"
                    data-testid={`edit-employee-${emp.id}`}
                  >
                    <Edit2 className="w-4 h-4" />
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => setDeleteConfirm(emp)}
                    className="h-8 w-8 hover:bg-red-400/10 text-red-400"
                    data-testid={`delete-employee-${emp.id}`}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              
              {emp.break_start && emp.break_end && (
                <p className="text-xs text-[#9CA3AF] mb-2">
                  Pauza: {emp.break_start} - {emp.break_end}
                </p>
              )}
              
              <p className="text-xs text-[#9CA3AF]">
                {getCategoriesFromServices(emp.services || []).map(c => categories.find(cat => cat.key === c)?.label || c).join(", ") || "Bez kategorija"}
              </p>

              {/* Worker Account Status */}
              <div className="mt-3 pt-3 border-t border-[#2A2A2D]">
                {workerAccounts[emp.id]?.has_account ? (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-green-400" />
                      <span className="text-[10px] text-green-400/80 font-medium">Nalog aktivan</span>
                      <span className="text-[10px] text-[#6B7280]">({workerAccounts[emp.id].email})</span>
                    </div>
                    <button
                      onClick={() => handleDeleteAccount(emp.id)}
                      className="text-[10px] text-red-400/60 hover:text-red-400 transition-colors"
                      data-testid={`delete-account-${emp.id}`}
                    >
                      Ukloni nalog
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => openAccountDialog(emp)}
                    className="flex items-center gap-1.5 text-[11px] text-[var(--color-primary)] hover:text-[var(--color-secondary)] transition-colors"
                    data-testid={`create-account-${emp.id}`}
                  >
                    <KeyRound className="w-3 h-3" />
                    Kreiraj nalog za prijavu
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteConfirm} onOpenChange={(open) => !open && setDeleteConfirm(null)}>
        <DialogContent className="bg-[var(--color-surface)] border-[#2A2A2D] max-w-sm">
          <DialogHeader>
            <DialogTitle className="font-['Cormorant_Garamond'] text-2xl flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              Potvrda brisanja
            </DialogTitle>
            <DialogDescription className="text-[#9CA3AF]">
              Da li ste sigurni da želite trajno da obrišete radnika <span className="text-white font-medium">{deleteConfirm?.name}</span>? Ova akcija se ne može poništiti.
            </DialogDescription>
          </DialogHeader>
          <div className="flex gap-3 mt-4">
            <Button
              variant="outline"
              onClick={() => setDeleteConfirm(null)}
              className="flex-1 border-[#2A2A2D] bg-transparent hover:bg-[var(--color-background)]"
              data-testid="cancel-delete-btn"
            >
              Otkaži
            </Button>
            <Button
              onClick={() => handleDelete(deleteConfirm?.id)}
              className="flex-1 bg-red-500 hover:bg-red-600 text-white"
              data-testid="confirm-delete-btn"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Obriši
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Create Worker Account Dialog */}
      <Dialog open={accountDialogOpen} onOpenChange={(open) => { if (!open) { setAccountDialogOpen(false); setCreatedAccount(null); } }}>
        <DialogContent className="bg-[var(--color-surface)] border-[#2A2A2D] max-w-sm" data-testid="create-account-dialog">
          <DialogHeader>
            <DialogTitle className="font-['Cormorant_Garamond'] text-2xl flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-[var(--color-primary)]" />
              {createdAccount ? "Nalog kreiran" : "Kreiraj nalog"}
            </DialogTitle>
            <DialogDescription className="text-[#9CA3AF]">
              {createdAccount
                ? `Lozinka je prikazana samo jednom. Sačuvajte je.`
                : `Kreiraj nalog za prijavu radnika ${accountTarget?.name}`
              }
            </DialogDescription>
          </DialogHeader>

          {!createdAccount ? (
            <div className="space-y-4 mt-2">
              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Email za prijavu</label>
                <Input
                  type="email"
                  value={accountEmail}
                  onChange={(e) => setAccountEmail(e.target.value)}
                  placeholder="radnik@email.com"
                  className="bg-[var(--color-background)] border-[#2A2A2D]"
                  data-testid="worker-account-email-input"
                />
              </div>
              <Button
                onClick={handleCreateAccount}
                disabled={accountLoading}
                className="w-full bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black font-medium"
                data-testid="worker-account-create-btn"
              >
                {accountLoading ? "Kreiranje..." : "Kreiraj nalog"}
              </Button>
            </div>
          ) : (
            <div className="space-y-3 mt-2">
              <div className="bg-[var(--color-background)] rounded-lg p-4 space-y-3">
                <div>
                  <label className="text-[10px] text-[#6B7280] uppercase tracking-wider mb-1 block">Email</label>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-white font-mono">{createdAccount.email}</span>
                    <button onClick={() => copyToClipboard(createdAccount.email, "email")} className="p-1 hover:bg-[var(--color-surface)] rounded transition-colors" data-testid="copy-email-btn">
                      {copiedField === "email" ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5 text-[#9CA3AF]" />}
                    </button>
                  </div>
                </div>
                <div>
                  <label className="text-[10px] text-[#6B7280] uppercase tracking-wider mb-1 block">Privremena lozinka</label>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-[var(--color-primary)] font-mono font-bold">{createdAccount.temp_password}</span>
                    <button onClick={() => copyToClipboard(createdAccount.temp_password, "password")} className="p-1 hover:bg-[var(--color-surface)] rounded transition-colors" data-testid="copy-password-btn">
                      {copiedField === "password" ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5 text-[#9CA3AF]" />}
                    </button>
                  </div>
                </div>
              </div>
              <p className="text-[10px] text-amber-400/70">Ova lozinka se prikazuje samo jednom. Prosledite je radniku lično.</p>
              <Button
                onClick={() => { setAccountDialogOpen(false); setCreatedAccount(null); }}
                variant="outline"
                className="w-full border-[#2A2A2D]"
                data-testid="close-account-dialog-btn"
              >
                Zatvori
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};


export default EmployeesPage;
