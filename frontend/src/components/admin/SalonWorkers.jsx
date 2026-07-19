import React, { useState, useEffect } from "react";
import { toast } from "sonner";
import axios from "axios";
import { API, useTenant, getTenantHeaders, getToken } from "../../App";
import { Button } from "../ui/button";
import { Users, Edit2, Trash2, KeyRound, RotateCcw } from "lucide-react";

import WorkerFormDialog from "./WorkerFormDialog";
import WorkerAccountDialog from "./WorkerAccountDialog";
import DeleteWorkerDialog from "./DeleteWorkerDialog";

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
  const [accountDialogMode, setAccountDialogMode] = useState("create"); // "create" | "reset"
  const [accountTarget, setAccountTarget] = useState(null);
  const [accountEmail, setAccountEmail] = useState("");
  const [accountLoading, setAccountLoading] = useState(false);
  const [createdAccount, setCreatedAccount] = useState(null);
  const [copiedField, setCopiedField] = useState(null);
  const [workerAccounts, setWorkerAccounts] = useState({});

  const [form, setForm] = useState({
    name: "", categories: [], work_start: "09:00", work_end: "21:00",
    break_start: "", break_end: "", days_off: [],
  });

  const [categories, setCategories] = useState([]);
  const [salonSettings, setSalonSettings] = useState(null);

  const token = getToken();
  const headers = { Authorization: `Bearer ${token}`, ...getTenantHeaders(tenant?.tenant_id) };

  useEffect(() => { fetchData(); }, []);

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

      const accountStatuses = {};
      await Promise.all(empRes.data.map(async (emp) => {
        try {
          const r = await axios.get(`${API}/workers/${emp.id}/account`, { headers });
          accountStatuses[emp.id] = r.data;
        } catch { accountStatuses[emp.id] = { has_account: false }; }
      }));
      setWorkerAccounts(accountStatuses);
    } catch {
      toast.error("Greška pri učitavanju");
    } finally {
      setLoading(false);
    }
  };

  // Derived data
  const salonStart = salonSettings?.work_start || "09:00";
  const salonEnd = salonSettings?.work_end || "21:00";
  const salonClosedDays = salonSettings?.closed_days || [];

  const generateTimeOptions = (minTime, maxTime) => {
    const options = [];
    const [minH, minM] = minTime.split(":").map(Number);
    const [maxH, maxM] = maxTime.split(":").map(Number);
    for (let m = minH * 60 + minM; m <= maxH * 60 + maxM; m += 15) {
      options.push(`${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`);
    }
    return options;
  };

  const startOptions = generateTimeOptions(salonStart, salonEnd);
  const endOptions = generateTimeOptions(salonStart, salonEnd);

  const activeServices = services.filter(s => s.active);
  const servicesByCategory = {};
  activeServices.forEach(s => {
    if (!servicesByCategory[s.category]) servicesByCategory[s.category] = [];
    servicesByCategory[s.category].push(s);
  });

  const getCategoriesFromServices = (serviceIds) => {
    const cats = new Set();
    serviceIds.forEach(sid => {
      const svc = services.find(s => s.id === sid);
      if (svc) cats.add(svc.category);
    });
    return [...cats];
  };

  const getServiceIdsFromCategories = (selectedCats) => {
    return activeServices.filter(s => selectedCats.includes(s.category)).map(s => s.id);
  };

  const dayLabels = ["Ned", "Pon", "Uto", "Sre", "Čet", "Pet", "Sub"];

  // ===== Handlers =====

  const resetForm = () => {
    setForm({ name: "", categories: [], work_start: salonStart, work_end: salonEnd, break_start: "", break_end: "", days_off: [...salonClosedDays] });
    setEditingEmployee(null);
  };

  const handleEdit = (emp) => {
    setEditingEmployee(emp);
    setForm({
      name: emp.name,
      categories: getCategoriesFromServices(emp.services || []),
      work_start: emp.work_start, work_end: emp.work_end,
      break_start: emp.break_start || "", break_end: emp.break_end || "",
      days_off: emp.days_off || [],
    });
    setDialogOpen(true);
  };

  const handleSubmit = async () => {
    if (!form.name.trim()) { toast.error("Unesite ime radnika"); return; }
    try {
      const payload = {
        name: form.name, services: getServiceIdsFromCategories(form.categories),
        work_start: form.work_start, work_end: form.work_end,
        break_start: form.break_start || null, break_end: form.break_end || null,
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
    } catch { toast.error("Greška pri čuvanju"); }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API}/workers/${id}`, { headers });
      toast.success("Radnik je trajno obrisan");
      setDeleteConfirm(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Greška pri brisanju");
      setDeleteConfirm(null);
    }
  };

  const toggleCategory = (catKey) => {
    setForm(prev => ({ ...prev, categories: prev.categories.includes(catKey) ? prev.categories.filter(c => c !== catKey) : [...prev.categories, catKey] }));
  };
  const toggleDayOff = (day) => {
    setForm(prev => ({ ...prev, days_off: prev.days_off.includes(day) ? prev.days_off.filter(d => d !== day) : [...prev.days_off, day] }));
  };

  // ===== Account handlers =====

  const openAccountDialog = (emp, mode) => {
    setAccountTarget(emp);
    setAccountEmail("");
    setCreatedAccount(null);
    setCopiedField(null);
    setAccountDialogMode(mode);
    setAccountDialogOpen(true);
  };

  const handleCreateAccount = async () => {
    if (!accountEmail.trim() || !accountEmail.includes("@")) { toast.error("Unesite validan email"); return; }
    setAccountLoading(true);
    try {
      const res = await axios.post(`${API}/workers/${accountTarget.id}/create-account`, { email: accountEmail.trim() }, { headers });
      setCreatedAccount(res.data);
      toast.success(`Nalog kreiran za ${accountTarget.name}`);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Greška pri kreiranju naloga");
    } finally { setAccountLoading(false); }
  };

  const handleResetPassword = async () => {
    setAccountLoading(true);
    try {
      const res = await axios.put(`${API}/workers/${accountTarget.id}/reset-password`, {}, { headers });
      setCreatedAccount(res.data);
      toast.success(`Lozinka resetovana za ${accountTarget.name}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Greška pri resetovanju");
    } finally { setAccountLoading(false); }
  };

  const handleDeleteAccount = async (workerId) => {
    try {
      await axios.delete(`${API}/workers/${workerId}/account`, { headers });
      toast.success("Nalog radnika obrisan");
      fetchData();
    } catch (error) { toast.error(error.response?.data?.detail || "Greška"); }
  };

  const copyToClipboard = async (text, field) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    } catch { toast.error("Kopiranje nije uspelo"); }
  };

  // ===== Render =====

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <h2 className="font-['Cormorant_Garamond'] text-3xl font-light">Radnici</h2>
        <WorkerFormDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          editingEmployee={editingEmployee}
          form={form}
          setForm={setForm}
          categories={categories}
          servicesByCategory={servicesByCategory}
          salonClosedDays={salonClosedDays}
          startOptions={startOptions}
          endOptions={endOptions}
          dayLabels={dayLabels}
          toggleCategory={toggleCategory}
          toggleDayOff={toggleDayOff}
          onSubmit={handleSubmit}
          resetForm={resetForm}
        />
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
              className={`bg-[var(--color-surface)] rounded-xl border p-5 ${emp.active ? "border-[#2A2A2D]" : "border-red-400/30 opacity-60"}`}
              data-testid={`employee-${emp.id}`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#C5A880] to-[#8B7355] flex items-center justify-center text-black font-semibold text-lg">
                    {emp.name.charAt(0)}
                  </div>
                  <div>
                    <h3 className="font-medium">{emp.name}</h3>
                    <p className="text-sm text-[#9CA3AF]">{emp.work_start} - {emp.work_end}</p>
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button size="icon" variant="ghost" onClick={() => handleEdit(emp)} className="h-8 w-8 hover:bg-[var(--color-background)]" data-testid={`edit-employee-${emp.id}`}>
                    <Edit2 className="w-4 h-4" />
                  </Button>
                  <Button size="icon" variant="ghost" onClick={() => setDeleteConfirm(emp)} className="h-8 w-8 hover:bg-red-400/10 text-red-400" data-testid={`delete-employee-${emp.id}`}>
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {emp.break_start && emp.break_end && (
                <p className="text-xs text-[#9CA3AF] mb-2">Pauza: {emp.break_start} - {emp.break_end}</p>
              )}

              <p className="text-xs text-[#9CA3AF]">
                {getCategoriesFromServices(emp.services || []).map(c => categories.find(cat => cat.key === c)?.label || c).join(", ") || "Bez kategorija"}
              </p>

              {/* Worker Account Status */}
              <div className="mt-3 pt-3 border-t border-[#2A2A2D]">
                {workerAccounts[emp.id]?.has_account ? (
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <div className="w-1.5 h-1.5 rounded-full bg-green-400" />
                        <span className="text-[10px] text-green-400/80 font-medium">Nalog aktivan</span>
                        <span className="text-[10px] text-[#6B7280]">({workerAccounts[emp.id].email})</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => openAccountDialog(emp, "reset")}
                        className="flex items-center gap-1 text-[10px] text-amber-400/70 hover:text-amber-400 transition-colors"
                        data-testid={`reset-password-${emp.id}`}
                      >
                        <RotateCcw className="w-2.5 h-2.5" />
                        Resetuj lozinku
                      </button>
                      <button
                        onClick={() => handleDeleteAccount(emp.id)}
                        className="text-[10px] text-red-400/60 hover:text-red-400 transition-colors"
                        data-testid={`delete-account-${emp.id}`}
                      >
                        Ukloni nalog
                      </button>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => openAccountDialog(emp, "create")}
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

      <DeleteWorkerDialog worker={deleteConfirm} onClose={() => setDeleteConfirm(null)} onDelete={handleDelete} />

      <WorkerAccountDialog
        open={accountDialogOpen}
        onClose={() => { setAccountDialogOpen(false); setCreatedAccount(null); }}
        target={accountTarget}
        mode={accountDialogMode}
        accountEmail={accountEmail}
        setAccountEmail={setAccountEmail}
        accountLoading={accountLoading}
        onCreateAccount={handleCreateAccount}
        onResetPassword={handleResetPassword}
        createdAccount={createdAccount}
        copiedField={copiedField}
        onCopy={copyToClipboard}
      />
    </div>
  );
};

export default EmployeesPage;
