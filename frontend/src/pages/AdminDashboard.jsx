import React, { useState, useEffect } from "react";
import { Routes, Route, Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import axios from "axios";
import { API, useAuth, useTenant, getTenantHeaders } from "../App";
import { PhoneInput } from "../components/PhoneInput";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { 
  Calendar, Users, Scissors, Settings, LogOut, Menu, X,
  Clock, Phone, User, Ban, Check, ChevronLeft, ChevronRight,
  Plus, Edit2, Trash2, DollarSign, Shield, AlertTriangle, CreditCard,
  SlidersHorizontal, Copy, Bell, Loader2, Download
} from "lucide-react";
import { format, addDays, subDays, parseISO } from "date-fns";
import { sr } from "date-fns/locale";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogDescription,
} from "../components/ui/dialog";
import { Switch } from "../components/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";

const AdminDashboard = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { logout, user } = useAuth();
  const tenant = useTenant();
  const { slug } = useParams();
  const basePath = `/${slug}/admin`;

  const handleLogout = async () => {
    await logout();
    navigate(`/${slug}/admin/login`);
  };

  const baseNavItems = [
    { path: basePath, label: "Rezervacije", icon: Calendar },
    { path: `${basePath}/blacklist`, label: "Crna Lista", icon: Shield },
    { path: `${basePath}/employees`, label: "Radnici", icon: Users },
    { path: `${basePath}/services`, label: "Usluge", icon: Scissors },
    { path: `${basePath}/settings`, label: "Podešavanja", icon: Settings },
  ];

  const navItems = user?.role === "super_admin"
    ? [...baseNavItems, { path: `${basePath}/system`, label: "Super Admin", icon: SlidersHorizontal }]
    : baseNavItems;

  return (
    <div className="min-h-screen bg-[#0A0A0B]">
      {/* Mobile Header */}
      <header className="lg:hidden sticky top-0 z-50 bg-[#0A0A0B]/95 backdrop-blur-md border-b border-[#2A2A2D]">
        <div className="flex items-center justify-between p-4">
          <h1 className="font-['Cormorant_Garamond'] text-xl font-light">Dashboard</h1>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 hover:bg-[#141416] rounded-lg transition-colors"
            data-testid="mobile-menu-toggle"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
        
        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <nav className="border-t border-[#2A2A2D] p-4 space-y-2 animate-fade-in">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                  location.pathname === item.path
                    ? "bg-[#C5A880]/10 text-[#C5A880]"
                    : "hover:bg-[#141416] text-[#9CA3AF]"
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
        <aside className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 bg-[#141416] border-r border-[#2A2A2D]">
          <div className="p-6 border-b border-[#2A2A2D]">
            <h1 className="font-['Cormorant_Garamond'] text-2xl font-light">Beauty Salon</h1>
            <p className="text-sm text-[#9CA3AF] mt-1">{user?.email}</p>
          </div>

          <nav className="flex-1 p-4 space-y-2">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                  location.pathname === item.path
                    ? "bg-[#C5A880]/10 text-[#C5A880]"
                    : "hover:bg-[#0A0A0B] text-[#9CA3AF]"
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
        <main className="flex-1 lg:ml-64 p-4 lg:p-8">
          <Routes>
            <Route index element={<ReservationsPage />} />
            <Route path="blacklist" element={<BlacklistPage />} />
            <Route path="employees" element={<EmployeesPage />} />
            <Route path="services" element={<ServicesPage />} />
            <Route path="settings" element={<SettingsPage />} />
            {user?.role === "super_admin" && (
              <Route path="system" element={<SystemConfigPage />} />
            )}
          </Routes>
        </main>
      </div>
    </div>
  );
};

// ==================== MANUAL BOOKING MODAL ====================
const ManualBookingModal = ({ open, onClose, onSuccess, workers, selectedDate }) => {
  const tenant = useTenant();
  const [step, setStep] = useState(1); // 1:services, 2:date/time, 3:client
  const [services, setServices] = useState([]);
  const [selectedPairs, setSelectedPairs] = useState([]); // [{service, worker}]
  const [date, setDate] = useState(format(selectedDate, "yyyy-MM-dd"));
  const [availableSlots, setAvailableSlots] = useState([]);
  const [slotDetails, setSlotDetails] = useState({});
  const [selectedTime, setSelectedTime] = useState("");
  const [clientName, setClientName] = useState("");
  const [clientPhone, setClientPhone] = useState("+381");
  const [submitting, setSubmitting] = useState(false);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [warnings, setWarnings] = useState([]);
  const [showForceConfirm, setShowForceConfirm] = useState(false);

  const token = localStorage.getItem("access_token");
  const headers = { Authorization: `Bearer ${token}`, ...getTenantHeaders(tenant?.tenant_id) };

  // Temp state for adding a pair
  const [tempServiceId, setTempServiceId] = useState("");
  const [tempWorkerId, setTempWorkerId] = useState("");

  useEffect(() => {
    if (open) {
      axios.get(`${API}/services`, { headers }).then(r => setServices(r.data)).catch(() => {});
      setStep(1);
      setSelectedPairs([]);
      setSelectedTime("");
      setClientName("");
      setClientPhone("+381");
      setWarnings([]);
      setShowForceConfirm(false);
      setDate(format(selectedDate, "yyyy-MM-dd"));
    }
  }, [open]);

  const handleAdminPhoneChange = (value) => {
    let cleaned = value.replace(/[^\d+]/g, '');
    if (!cleaned.startsWith('+381')) {
      const digitsOnly = cleaned.replace(/\D/g, '');
      let normalized = digitsOnly;
      if (normalized.startsWith('381')) normalized = normalized.substring(3);
      if (normalized.startsWith('0')) normalized = normalized.substring(1);
      cleaned = '+381' + normalized;
    } else {
      const after = cleaned.substring(4).replace(/\D/g, '');
      const normalized = after.startsWith('0') ? after.substring(1) : after;
      cleaned = '+381' + normalized;
    }
    if (cleaned.length > 13) cleaned = cleaned.substring(0, 13);
    setClientPhone(cleaned);
  };

  // Fetch available slots when pairs or date change
  useEffect(() => {
    if (selectedPairs.length > 0 && date && step === 2) {
      fetchSlots();
    }
  }, [selectedPairs, date, step]);

  const fetchSlots = async () => {
    setLoadingSlots(true);
    try {
      const pairs = selectedPairs.map(p => ({ service_id: p.service.id, worker_id: p.worker.id }));
      const res = await axios.post(`${API}/reservations/available-slots`, {
        service_worker_pairs: pairs,
        date,
      });
      setAvailableSlots(res.data.slots || []);
      setSlotDetails(res.data.slot_details || {});
    } catch {
      setAvailableSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  };

  const addPair = () => {
    const svc = services.find(s => s.id === tempServiceId);
    const wrk = workers.find(w => w.id === tempWorkerId);
    if (!svc || !wrk) return;
    setSelectedPairs(prev => [...prev, { service: svc, worker: wrk }]);
    setTempServiceId("");
    setTempWorkerId("");
  };

  const removePair = (idx) => {
    setSelectedPairs(prev => prev.filter((_, i) => i !== idx));
  };

  const removePairFromReview = (idx) => {
    setSelectedPairs(prev => prev.filter((_, i) => i !== idx));
    setSelectedTime("");
    setStep(1);
  };

  const workersForService = (serviceId) => {
    return workers.filter(w => w.services?.includes(serviceId));
  };

  const canProceedStep1 = selectedPairs.length > 0 || (tempServiceId && tempWorkerId);

  const handleNextStep = () => {
    if (tempServiceId && tempWorkerId) {
      const svc = services.find(s => s.id === tempServiceId);
      const wrk = workers.find(w => w.id === tempWorkerId);
      if (svc && wrk) {
        setSelectedPairs(prev => [...prev, { service: svc, worker: wrk }]);
      }
      setTempServiceId("");
      setTempWorkerId("");
    }
    setStep(2);
  };

  const totalDuration = selectedPairs.reduce((s, p) => s + p.service.duration, 0) + Math.max(0, selectedPairs.length - 1) * 15;
  const totalPrice = selectedPairs.reduce((s, p) => s + p.service.price, 0);

  const handleSubmit = async (force = false) => {
    setSubmitting(true);
    setWarnings([]);
    setShowForceConfirm(false);
    try {
      const payload = {
        service_worker_pairs: selectedPairs.map(p => ({ service_id: p.service.id, worker_id: p.worker.id })),
        date,
        time: selectedTime,
        client_name: clientName.trim(),
        client_phone: clientPhone.trim(),
        force,
      };
      await axios.post(`${API}/admin/reservations`, payload, { headers });
      toast.success("Rezervacija kreirana!");
      onSuccess();
      onClose();
    } catch (error) {
      if (error.response?.status === 409) {
        const msgs = error.response.data.detail.split("|");
        setWarnings(msgs);
        setShowForceConfirm(true);
      } else {
        toast.error(error.response?.data?.detail || "Greška pri kreiranju rezervacije");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const detail = slotDetails[selectedTime];

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="bg-[#141416] border-[#2A2A2D] max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <Plus className="w-5 h-5 text-[#C5A880]" />
            Ručna Rezervacija
          </DialogTitle>
          <DialogDescription className="text-[#9CA3AF]">
            {step === 1 && "Korak 1: Izaberite usluge i radnike"}
            {step === 2 && "Korak 2: Izaberite datum i termin"}
            {step === 3 && "Korak 3: Podaci o klijentu"}
          </DialogDescription>
        </DialogHeader>

        {/* Step indicator */}
        <div className="flex items-center gap-1 mb-4">
          {[1, 2, 3].map(s => (
            <div key={s} className={`h-1 flex-1 rounded-full transition-colors ${s <= step ? "bg-[#C5A880]" : "bg-[#2A2A2D]"}`} />
          ))}
        </div>

        {/* STEP 1: Services + Workers */}
        {step === 1 && (
          <div className="space-y-4">
            {/* Current pairs */}
            {selectedPairs.length > 0 && (
              <div className="space-y-2">
                {selectedPairs.map((pair, idx) => (
                  <div key={idx} className="flex items-center justify-between bg-[#0A0A0B] rounded-lg px-3 py-2" data-testid={`manual-pair-${idx}`}>
                    <div className="text-sm">
                      <span className="text-white">{pair.service.name}</span>
                      <span className="text-[#9CA3AF] mx-1">&rarr;</span>
                      <span className="text-[#C5A880]">{pair.worker.name}</span>
                      <span className="text-[#6B7280] text-xs ml-2">({pair.service.duration} min)</span>
                    </div>
                    <button onClick={() => removePair(idx)} className="text-[#9CA3AF] hover:text-red-400 p-1" data-testid={`remove-pair-${idx}`}>
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
                <div className="text-xs text-[#9CA3AF] text-right">
                  Ukupno: {totalDuration} min &middot; {totalPrice.toLocaleString()} RSD
                </div>
              </div>
            )}

            {/* Add new pair */}
            <div className="bg-[#0A0A0B] rounded-lg p-3 space-y-3">
              <select
                value={tempServiceId}
                onChange={e => { setTempServiceId(e.target.value); setTempWorkerId(""); }}
                className="w-full bg-[#1E1E22] border border-[#2A2A2D] rounded-lg px-3 py-2 text-sm text-white min-h-[48px]"
                data-testid="manual-service-select"
              >
                <option value="">Izaberite uslugu...</option>
                {services.map(s => (
                  <option key={s.id} value={s.id}>{s.name} ({s.duration} min - {s.price.toLocaleString()} RSD)</option>
                ))}
              </select>

              {tempServiceId && (
                <select
                  value={tempWorkerId}
                  onChange={e => setTempWorkerId(e.target.value)}
                  className="w-full bg-[#1E1E22] border border-[#2A2A2D] rounded-lg px-3 py-2 text-sm text-white min-h-[48px]"
                  data-testid="manual-worker-select"
                >
                  <option value="">Izaberite radnika...</option>
                  {workersForService(tempServiceId).map(w => (
                    <option key={w.id} value={w.id}>{w.name}</option>
                  ))}
                </select>
              )}

              <Button
                onClick={addPair}
                disabled={!tempServiceId || !tempWorkerId}
                className="w-full bg-[#1E1E22] border border-[#2A2A2D] hover:bg-[#2A2A2D] text-[#C5A880] disabled:opacity-40 min-h-[48px]"
                size="sm"
                data-testid="manual-add-pair-btn"
              >
                <Plus className="w-4 h-4 mr-1" /> Dodaj uslugu
              </Button>
            </div>

            <Button
              onClick={handleNextStep}
              disabled={!canProceedStep1}
              className="w-full bg-[#C5A880] hover:bg-[#B89970] text-black font-medium disabled:opacity-40 min-h-[48px]"
              data-testid="manual-step1-next"
            >
              Dalje
            </Button>
          </div>
        )}

        {/* STEP 2: Date + Time */}
        {step === 2 && (
          <div className="space-y-4">
            <div>
              <label className="text-xs text-[#9CA3AF] mb-1 block">Datum</label>
              <input
                type="date"
                value={date}
                onChange={e => { setDate(e.target.value); setSelectedTime(""); }}
                className="w-full bg-[#1E1E22] border border-[#2A2A2D] rounded-lg px-3 py-2.5 text-sm text-white min-h-[48px]"
                data-testid="manual-date-input"
              />
            </div>

            <div>
              <label className="text-xs text-[#9CA3AF] mb-1 block">
                Dostupni termini {loadingSlots && <span className="text-[#C5A880]">(učitavanje...)</span>}
              </label>
              {availableSlots.length > 0 ? (
                <div className="grid grid-cols-4 gap-2 max-h-48 overflow-y-auto">
                  {availableSlots.map(slot => (
                    <button
                      key={slot}
                      onClick={() => setSelectedTime(slot)}
                      className={`px-2 py-2 text-xs rounded-lg border transition-colors ${
                        selectedTime === slot
                          ? "bg-[#C5A880] text-black border-[#C5A880] font-medium"
                          : "bg-[#1E1E22] border-[#2A2A2D] text-[#E5E7EB] hover:border-[#C5A880]/50"
                      }`}
                      data-testid={`manual-slot-${slot}`}
                    >
                      {slot}
                    </button>
                  ))}
                </div>
              ) : !loadingSlots ? (
                <div className="text-center text-[#6B7280] text-sm py-6">
                  Nema dostupnih termina za ovaj datum
                </div>
              ) : null}

              {/* Show selected slot details */}
              {selectedTime && detail && (
                <div className="mt-3 bg-[#0A0A0B] rounded-lg p-3 space-y-1">
                  {detail.time_blocks?.map((b, i) => (
                    <div key={i}>
                      {b.gap > 0 && (
                        <div className="flex items-center gap-1 text-[10px] text-[#6B7280] italic pl-1 py-0.5">
                          ☕ Pauza ({b.gap} min)
                        </div>
                      )}
                      <div className="flex justify-between text-xs">
                        <span className="text-white">{b.start_time}-{b.end_time} {selectedPairs[i]?.service.name}</span>
                        <span className="text-[#C5A880]">{selectedPairs[i]?.worker.name}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep(1)} className="flex-1 border-[#2A2A2D] hover:bg-[#1E1E22] min-h-[48px]">Nazad</Button>
              <Button
                onClick={() => setStep(3)}
                disabled={!selectedTime}
                className="flex-1 bg-[#C5A880] hover:bg-[#B89970] text-black font-medium disabled:opacity-40 min-h-[48px]"
                data-testid="manual-step2-next"
              >
                Dalje
              </Button>
            </div>
          </div>
        )}

        {/* STEP 3: Client info + Confirm */}
        {step === 3 && (
          <div className="space-y-4">
            {/* Summary */}
            <div className="bg-[#0A0A0B] rounded-lg p-3 text-sm space-y-1">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[#9CA3AF] text-xs uppercase tracking-wider">Pregled</span>
                <button
                  onClick={() => setStep(1)}
                  className="flex items-center gap-1 text-xs text-[#C5A880] hover:text-[#B89970] transition-colors"
                  data-testid="admin-edit-services-link"
                >
                  <Edit2 className="w-3 h-3" />
                  Izmeni usluge
                </button>
              </div>
              <div className="flex justify-between">
                <span className="text-[#9CA3AF]">Datum:</span>
                <span className="text-white">{date}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#9CA3AF]">Vreme:</span>
                <span className="text-white">{selectedTime} - {detail?.end_time || ""}</span>
              </div>
              <div className="space-y-1 pt-1">
                {selectedPairs.map((pair, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <span className="text-[#9CA3AF]">{pair.service.name} <span className="text-[#C5A880]">{pair.worker.name}</span></span>
                    <button
                      onClick={() => removePairFromReview(idx)}
                      className="w-5 h-5 rounded-full flex items-center justify-center text-[#6B7280] hover:text-red-400 hover:bg-red-400/10 transition-colors"
                      data-testid={`admin-remove-pair-review-${idx}`}
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
              <div className="flex justify-between border-t border-[#2A2A2D] pt-1 mt-1">
                <span className="text-[#9CA3AF]">Ukupno:</span>
                <span className="text-[#C5A880] font-medium">{totalPrice.toLocaleString()} RSD</span>
              </div>
            </div>

            <div>
              <label className="text-xs text-[#9CA3AF] mb-1 block">Ime klijenta</label>
              <Input
                value={clientName}
                onChange={e => setClientName(e.target.value)}
                placeholder="Ime i prezime"
                className="bg-[#1E1E22] border-[#2A2A2D] text-white min-h-[48px]"
                data-testid="manual-client-name"
              />
            </div>

            <div>
              <label className="text-xs text-[#9CA3AF] mb-1 block">Broj telefona</label>
              <Input
                value={clientPhone}
                onChange={e => handleAdminPhoneChange(e.target.value)}
                placeholder="+381641234567"
                className="bg-[#1E1E22] border-[#2A2A2D] text-white min-h-[48px]"
                data-testid="manual-client-phone"
              />
              <p className="text-xs text-[#9CA3AF] mt-1">Format: +381 i zatim broj bez nule</p>
            </div>

            {/* Warnings from backend */}
            {warnings.length > 0 && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 space-y-1" data-testid="manual-warnings">
                <div className="flex items-center gap-2 text-red-400 text-sm font-medium">
                  <AlertTriangle className="w-4 h-4" /> Upozorenje
                </div>
                {warnings.map((w, i) => (
                  <p key={i} className="text-red-300 text-xs">{w}</p>
                ))}
              </div>
            )}

            {showForceConfirm && (
              <Button
                onClick={() => handleSubmit(true)}
                disabled={submitting}
                className="w-full bg-red-600 hover:bg-red-700 text-white font-medium min-h-[48px]"
                data-testid="manual-force-submit"
              >
                {submitting ? "Kreiranje..." : "Zakaži svejedno (Override)"}
              </Button>
            )}

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep(2)} className="flex-1 border-[#2A2A2D] hover:bg-[#1E1E22] min-h-[48px]">Nazad</Button>
              <Button
                onClick={() => handleSubmit(false)}
                disabled={!clientName.trim() || clientPhone.length < 12 || submitting}
                className="flex-1 bg-[#C5A880] hover:bg-[#B89970] text-black font-medium disabled:opacity-40 min-h-[48px]"
                data-testid="manual-submit-btn"
              >
                {submitting ? "Kreiranje..." : "Potvrdi Rezervaciju"}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

// Reservations Page
const SLOT_HEIGHT = 48;
const COLORS = ["#C5A880", "#7C9EB2", "#A8C686", "#D4A574", "#B294BB", "#86C1B9", "#DCA68B"];

const ReservationsPage = () => {
  const { user } = useAuth();
  const tenant = useTenant();
  const [reservations, setReservations] = useState([]);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [loading, setLoading] = useState(true);
  const [blacklist, setBlacklist] = useState([]);
  const [workers, setWorkers] = useState([]);
  const [settings, setSettings] = useState(null);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [cancelTarget, setCancelTarget] = useState(null);
  const [manualBookingOpen, setManualBookingOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("grid");
  const [archiveSearch, setArchiveSearch] = useState("");
  const [selectedRes, setSelectedRes] = useState(null);
  const [sendingReminders, setSendingReminders] = useState(false);

  const token = localStorage.getItem("access_token");
  const headers = { Authorization: `Bearer ${token}`, ...getTenantHeaders(tenant?.tenant_id) };
  const gridRef = React.useRef(null);

  useEffect(() => { fetchWorkers(); fetchSettings(); }, []);
  useEffect(() => { fetchReservations(); fetchBlacklist(); }, [selectedDate]);

  useEffect(() => {
    if (!loading && activeTab === "grid" && gridRef.current) {
      const now = new Date();
      const mins = now.getHours() * 60 + now.getMinutes();
      const ws = settings ? ttm(settings.work_start) : 540;
      const scrollTo = ((mins - ws) / 30) * SLOT_HEIGHT;
      gridRef.current.scrollTop = Math.max(0, scrollTo - SLOT_HEIGHT * 2);
    }
  }, [loading, activeTab, selectedDate]);

  const ttm = (t) => { const [h, m] = t.split(":").map(Number); return h * 60 + m; };
  const mtt = (m) => `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;

  const fetchSettings = async () => {
    try { const r = await axios.get(`${API}/settings`, { headers }); setSettings(r.data); } catch (e) { console.error(e); }
  };
  const fetchWorkers = async () => {
    try { const r = await axios.get(`${API}/workers`, { headers }); setWorkers(r.data); } catch (e) { console.error(e); }
  };
  const fetchReservations = async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${API}/reservations`, { params: { date: format(selectedDate, "yyyy-MM-dd") }, headers });
      setReservations(r.data);
    } catch (e) { toast.error("Greška pri učitavanju"); } finally { setLoading(false); }
  };
  const fetchBlacklist = async () => {
    try { const r = await axios.get(`${API}/blacklist`, { headers }); setBlacklist(r.data.map(b => b.phone)); } catch (e) { console.error(e); }
  };
  const handleTogglePayment = async (id) => {
    try { await axios.put(`${API}/reservations/${id}/payment-status`, {}, { headers }); fetchReservations(); } catch (e) { toast.error("Greška"); }
  };
  const handleConfirmPayment = async (id) => {
    try { await axios.patch(`${API}/admin/reservations/${id}/confirm-payment`, {}, { headers }); toast.success("Uplata potvrđena"); setSelectedRes(null); fetchReservations(); } catch (e) { toast.error("Greška"); }
  };
  const handleSendReminders = async () => {
    setSendingReminders(true);
    try {
      const r = await axios.post(`${API}/admin/reservations/trigger-reminders`, {}, { headers });
      const d = r.data;
      toast.success(`Sutra (${d.date}): ${d.total_reservations} termina (${d.confirmed} potvrđenih, ${d.pending} čeka uplatu)`);
    } catch (e) {
      toast.error("Greška pri proveri podsetnika");
    } finally {
      setSendingReminders(false);
    }
  };
  const handleCancel = async (id) => {
    try { await axios.put(`${API}/reservations/${id}/cancel`, {}, { headers }); toast.success("Otkazano"); setCancelDialogOpen(false); setCancelTarget(null); setSelectedRes(null); fetchReservations(); } catch (e) { toast.error("Greška"); }
  };
  const openCancelDialog = (res) => { setCancelTarget(res); setCancelDialogOpen(true); };
  const handleBlacklist = async (phone) => {
    try { await axios.post(`${API}/blacklist?phone=${encodeURIComponent(phone)}`, {}, { headers }); toast.success("Blokirano"); fetchBlacklist(); } catch (e) { toast.error("Greška"); }
  };
  const handleRemoveFromBlacklist = async (phone) => {
    try { await axios.delete(`${API}/blacklist/${encodeURIComponent(phone)}`, { headers }); toast.success("Odblokirano"); fetchBlacklist(); } catch (e) { toast.error("Greška"); }
  };

  const handleExportCSV = () => {
    const all = [...activeReservations, ...archivedReservations];
    if (all.length === 0) { toast.error("Nema podataka za export"); return; }
    const header = "Booking ID,Datum,Vreme,Kraj,Klijent,Telefon,Email,Usluge,Radnik,Ukupna cena,Status,Placanje,Kreiran";
    const rows = all.map(r => [
      r.booking_id || "",
      r.date || "",
      r.time || "",
      r.end_time || "",
      `"${(r.client_name || "").replace(/"/g, '""')}"`,
      r.client_phone || "",
      r.client_email || "",
      `"${(r.service_names || []).join(", ").replace(/"/g, '""')}"`,
      `"${(r.service_worker_pairs || []).map(p => p.worker_name).join(", ").replace(/"/g, '""')}"`,
      r.total_price || 0,
      r.status || "",
      r.payment_status || "",
      r.created_at || "",
    ].join(","));
    const csv = "\uFEFF" + header + "\n" + rows.join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `rezervacije_${format(selectedDate, "yyyy-MM-dd")}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success(`Exportovano ${all.length} rezervacija`);
  };

  const workStart = settings ? ttm(settings.work_start) : 540;
  const workEnd = settings ? ttm(settings.work_end) : 1260;
  const timeSlots = [];
  for (let m = workStart; m < workEnd; m += 30) timeSlots.push(m);

  const now = new Date();
  const nowMins = now.getHours() * 60 + now.getMinutes();
  const isToday = format(selectedDate, "yyyy-MM-dd") === format(now, "yyyy-MM-dd");
  const isPast = selectedDate < new Date(now.getFullYear(), now.getMonth(), now.getDate());

  const activeReservations = reservations.filter(r => {
    if (!isToday) return !isPast;
    return nowMins < ttm(r.end_time) + 30;
  });
  const archivedReservations = reservations.filter(r => {
    if (!isToday) return isPast;
    return nowMins >= ttm(r.end_time) + 30;
  });

  const buildWorkerBlocks = (wid) => {
    const blocks = [];
    reservations.forEach((res, rIdx) => {
      const color = COLORS[rIdx % COLORS.length];
      const isArch = isToday && nowMins >= ttm(res.end_time) + 30;
      if (res.worker_time_blocks && res.worker_time_blocks.length > 0) {
        res.worker_time_blocks.forEach(block => {
          if (block.worker_id === wid) {
            const pair = res.service_worker_pairs?.find(p => p.service_id === block.service_id);
            blocks.push({ res, startMin: ttm(block.start_time), endMin: ttm(block.end_time), serviceName: pair?.service_name || "", color, bookingId: res.booking_id, isArchived: isArch });
          }
        });
      } else if (res.worker_id === wid || res.service_worker_pairs?.some(p => p.worker_id === wid)) {
        blocks.push({ res, startMin: ttm(res.time), endMin: ttm(res.end_time), serviceName: res.service_names?.join(", ") || "", color, bookingId: res.booking_id, isArchived: isArch });
      }
    });
    return blocks;
  };

  const filteredArchive = archivedReservations.filter(r => {
    if (!archiveSearch) return true;
    const q = archiveSearch.toLowerCase();
    return r.client_name?.toLowerCase().includes(q) || r.client_phone?.includes(q) || r.booking_id?.toLowerCase().includes(q) || r.service_names?.some(s => s.toLowerCase().includes(q));
  });

  const nowLineTop = isToday ? ((nowMins - workStart) / 30) * SLOT_HEIGHT : -1;

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div>
          <h2 className="font-['Cormorant_Garamond'] text-3xl font-light">Rezervacije</h2>
          <p className="text-[#9CA3AF]">{format(selectedDate, "EEEE, d. MMMM yyyy", { locale: sr })}</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Button
            onClick={handleSendReminders}
            disabled={sendingReminders}
            variant="outline"
            className="border-[#2A2A2D] hover:bg-[#141416] text-[#9CA3AF] hover:text-white"
            data-testid="send-reminders-btn"
          >
            {sendingReminders ? <Loader2 className="w-4 h-4 mr-1.5 animate-spin" /> : <Bell className="w-4 h-4 mr-1.5" />}
            Podsetnici za sutra
          </Button>
          <Button onClick={() => setManualBookingOpen(true)} className="bg-[#C5A880] hover:bg-[#B89970] text-black font-medium" data-testid="admin-new-reservation-btn">
            <Plus className="w-4 h-4 mr-1" /> Nova Rezervacija
          </Button>
          <Button variant="outline" size="icon" onClick={() => setSelectedDate(subDays(selectedDate, 1))} className="border-[#2A2A2D] hover:bg-[#141416]" data-testid="prev-day-btn"><ChevronLeft className="w-4 h-4" /></Button>
          <Button variant="outline" onClick={() => setSelectedDate(new Date())} className="border-[#2A2A2D] hover:bg-[#141416]" data-testid="today-btn">Danas</Button>
          <Button variant="outline" size="icon" onClick={() => setSelectedDate(addDays(selectedDate, 1))} className="border-[#2A2A2D] hover:bg-[#141416]" data-testid="next-day-btn"><ChevronRight className="w-4 h-4" /></Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <div className="flex gap-1 bg-[#0A0A0B] rounded-lg p-1 w-fit" data-testid="view-tabs">
          <button onClick={() => setActiveTab("grid")} className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === "grid" ? "bg-[#C5A880] text-black" : "text-[#9CA3AF] hover:text-white"}`} data-testid="tab-grid">
            <Calendar className="w-4 h-4 inline mr-1.5" />Mreža{activeReservations.length > 0 && <span className="ml-1.5 text-xs opacity-70">({activeReservations.length})</span>}
          </button>
          <button onClick={() => setActiveTab("archive")} className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === "archive" ? "bg-[#C5A880] text-black" : "text-[#9CA3AF] hover:text-white"}`} data-testid="tab-archive">
            <Clock className="w-4 h-4 inline mr-1.5" />Arhiva{archivedReservations.length > 0 && <span className="ml-1.5 text-xs opacity-70">({archivedReservations.length})</span>}
          </button>
        </div>
        {user?.role === "super_admin" && (
          <Button
            onClick={handleExportCSV}
            variant="outline"
            size="sm"
            className="border-[#2A2A2D] hover:bg-[#141416] text-[#9CA3AF] hover:text-white"
            data-testid="export-csv-btn"
          >
            <Download className="w-4 h-4 mr-1.5" />
            Export CSV
          </Button>
        )}
      </div>

      {/* Cancel Dialog */}
      <Dialog open={cancelDialogOpen} onOpenChange={setCancelDialogOpen}>
        <DialogContent className="bg-[#141416] border-[#2A2A2D]">
          <DialogHeader><DialogTitle className="text-white">Otkazivanje rezervacije</DialogTitle><DialogDescription className="text-[#9CA3AF]">Da li ste sigurni?</DialogDescription></DialogHeader>
          {cancelTarget && (
            <div className="bg-[#0A0A0B] rounded-lg p-4 space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-[#9CA3AF]">ID:</span><span className="font-mono text-[#C5A880]">#{cancelTarget.booking_id}</span></div>
              <div className="flex justify-between"><span className="text-[#9CA3AF]">Klijent:</span><span className="text-white">{cancelTarget.client_name}</span></div>
              <div className="flex justify-between"><span className="text-[#9CA3AF]">Vreme:</span><span className="text-white">{cancelTarget.time} - {cancelTarget.end_time}</span></div>
              <div className="flex justify-between"><span className="text-[#9CA3AF]">Usluge:</span><span className="text-white">{cancelTarget.service_names?.join(", ")}</span></div>
            </div>
          )}
          <div className="flex gap-3 mt-2">
            <Button variant="outline" className="flex-1 border-[#2A2A2D] hover:bg-[#1E1E22]" onClick={() => setCancelDialogOpen(false)} data-testid="cancel-dialog-dismiss">Ne, zadrži</Button>
            <Button className="flex-1 bg-red-600 hover:bg-red-700 text-white" onClick={() => cancelTarget && handleCancel(cancelTarget.id)} data-testid="cancel-dialog-confirm">Da, otkaži</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Detail Dialog */}
      <Dialog open={!!selectedRes} onOpenChange={(v) => !v && setSelectedRes(null)}>
        <DialogContent className="bg-[#141416] border-[#2A2A2D] max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <span className="font-mono text-[#C5A880] text-sm bg-[#C5A880]/10 px-2 py-0.5 rounded">#{selectedRes?.booking_id}</span>
              {selectedRes?.client_name}
            </DialogTitle>
            <DialogDescription className="text-[#9CA3AF]">{selectedRes?.time} - {selectedRes?.end_time} &middot; {selectedRes?.total_duration} min</DialogDescription>
          </DialogHeader>
          {selectedRes && (
            <div className="space-y-3">
              <div className="bg-[#0A0A0B] rounded-lg p-3 space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-[#9CA3AF]">Telefon:</span><span className="text-white">{selectedRes.client_phone}</span></div>
                <div className="flex justify-between"><span className="text-[#9CA3AF]">Ukupno:</span><span className="text-[#C5A880] font-medium">{selectedRes.total_price?.toLocaleString()} RSD</span></div>
              </div>
              <div className="space-y-1">
                {selectedRes.worker_time_blocks?.length > 0 ? selectedRes.worker_time_blocks.map((block, idx) => {
                  const pair = selectedRes.service_worker_pairs?.[idx];
                  return (
                    <div key={idx}>
                      {block.gap > 0 && idx > 0 && <div className="text-[10px] text-[#6B7280] italic pl-1 py-0.5">☕ Pauza ({block.gap} min)</div>}
                      <div className="flex justify-between text-xs bg-[#0A0A0B] rounded px-2 py-1.5">
                        <span className="text-white">{block.start_time}-{block.end_time} {pair?.service_name}</span>
                        <span className="text-[#C5A880]">{pair?.worker_name}</span>
                      </div>
                    </div>
                  );
                }) : selectedRes.service_worker_pairs?.map((pair, idx) => (
                  <div key={idx} className="flex justify-between text-xs bg-[#0A0A0B] rounded px-2 py-1.5">
                    <span className="text-white">{pair.service_name}</span><span className="text-[#C5A880]">{pair.worker_name}</span>
                  </div>
                ))}
              </div>
              <div className="flex gap-2 pt-2 border-t border-[#2A2A2D]">
                <button onClick={() => { handleTogglePayment(selectedRes.id); setSelectedRes(null); }} className={`flex-1 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${selectedRes.payment_status === "confirmed" || selectedRes.payment_status === "paid" ? "bg-green-600/20 text-green-400" : selectedRes.payment_status === "sent_for_verification" ? "bg-amber-500/15 text-amber-400" : "bg-[#1E1E22] text-[#9CA3AF]"}`} data-testid={`detail-payment-${selectedRes.id}`}>
                  {selectedRes.payment_status === "confirmed" || selectedRes.payment_status === "paid" ? "Plaćeno" : selectedRes.payment_status === "sent_for_verification" ? "Čeka proveru" : "Čeka uplatu"}
                </button>
                <button onClick={() => { setSelectedRes(null); openCancelDialog(selectedRes); }} className="px-3 py-2 rounded-lg text-xs font-medium bg-red-500/10 text-red-400 hover:bg-red-500/20" data-testid={`detail-cancel-${selectedRes.id}`}>Otkaži</button>
                {!blacklist.includes(selectedRes.client_phone) ? (
                  <button onClick={() => handleBlacklist(selectedRes.client_phone)} className="px-3 py-2 rounded-lg text-xs font-medium bg-red-500/10 text-red-400 hover:bg-red-500/20"><Ban className="w-3 h-3 inline mr-1" />Blokiraj</button>
                ) : (
                  <button onClick={() => handleRemoveFromBlacklist(selectedRes.client_phone)} className="px-3 py-2 rounded-lg text-xs font-medium bg-green-500/10 text-green-400 hover:bg-green-500/20"><Check className="w-3 h-3 inline mr-1" />Odblokiraj</button>
                )}
              </div>
              {/* Confirm Payment Button */}
              {selectedRes.payment_status === "sent_for_verification" && (
                <button
                  onClick={() => handleConfirmPayment(selectedRes.id)}
                  className="w-full mt-2 px-3 py-3 rounded-lg text-sm font-medium bg-green-600 hover:bg-green-700 text-white transition-colors min-h-[48px]"
                  data-testid={`confirm-payment-${selectedRes.id}`}
                >
                  <Check className="w-4 h-4 inline mr-2" />
                  Potvrdi uplatu
                </button>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      <ManualBookingModal open={manualBookingOpen} onClose={() => setManualBookingOpen(false)} onSuccess={() => fetchReservations()} workers={workers} selectedDate={selectedDate} />

      {/* ===== GRID TAB ===== */}
      {activeTab === "grid" && (
        loading ? <div className="text-center py-12 text-[#9CA3AF]">Učitavanje...</div> :
        workers.length === 0 ? (
          <div className="text-center py-12 bg-[#141416] rounded-xl border border-[#2A2A2D]"><Users className="w-12 h-12 mx-auto text-[#9CA3AF] mb-4" /><p className="text-[#9CA3AF]">Nema aktivnih radnika</p></div>
        ) : (
          <div className="bg-[#141416] rounded-xl border border-[#2A2A2D]" data-testid="timeline-grid">
            <div className="overflow-auto max-h-[70vh]" ref={gridRef} data-testid="grid-body">
              {/* Header - sticky top */}
              <div className="flex sticky top-0 z-20 bg-[#141416] border-b border-[#2A2A2D]">
                <div className="w-16 flex-shrink-0 p-2 text-center text-[10px] text-[#6B7280] border-r border-[#2A2A2D] sticky left-0 z-30 bg-[#141416]">Vreme</div>
                {workers.map(w => (
                  <div key={w.id} className="flex-1 min-w-[120px] flex-shrink-0 p-2 text-center border-r border-[#2A2A2D] last:border-r-0">
                    <div className="text-xs font-medium text-white truncate">{w.name}</div>
                    <div className="text-[10px] text-[#6B7280]">{w.work_start}-{w.work_end}</div>
                  </div>
                ))}
              </div>
              {/* Body */}
              <div className="relative">
                {nowLineTop > 0 && nowLineTop < timeSlots.length * SLOT_HEIGHT && (
                  <div className="absolute left-0 right-0 z-[5] pointer-events-none" style={{ top: `${nowLineTop}px` }} data-testid="now-line">
                    <div className="flex items-center"><div className="w-2 h-2 rounded-full bg-red-500 -ml-1" /><div className="flex-1 h-px bg-red-500/60" /></div>
                  </div>
                )}
                {timeSlots.map((slotMin) => (
                  <div key={slotMin} className="flex border-b border-[#1E1E22]" style={{ height: `${SLOT_HEIGHT}px` }}>
                    <div className="w-16 flex-shrink-0 flex items-start justify-center pt-1 text-[10px] text-[#6B7280] border-r border-[#1E1E22] sticky left-0 z-10 bg-[#141416]">{mtt(slotMin)}</div>
                    {workers.map(w => {
                      const blocks = buildWorkerBlocks(w.id);
                      const cellBlocks = blocks.filter(b => b.startMin >= slotMin && b.startMin < slotMin + 30);
                      return (
                        <div key={w.id} className="flex-1 min-w-[120px] flex-shrink-0 border-r border-[#1E1E22] last:border-r-0 relative">
                          {cellBlocks.map((block, bIdx) => {
                            const topOff = ((block.startMin - slotMin) / 30) * SLOT_HEIGHT;
                            const blockH = Math.max(((block.endMin - block.startMin) / 30) * SLOT_HEIGHT, 24);
                            const isPaid = block.res.payment_status === "confirmed" || block.res.payment_status === "paid";
                            const isVerifying = block.res.payment_status === "sent_for_verification";
                            const blockColor = isVerifying ? "#F59E0B" : isPaid ? "#22C55E" : block.color;
                            return (
                              <div key={bIdx} onClick={() => setSelectedRes(block.res)}
                                className={`absolute left-1 right-1 rounded-md px-1.5 py-0.5 cursor-pointer overflow-hidden transition-all hover:brightness-110 hover:shadow-lg ${block.isArchived ? "opacity-40" : ""}`}
                                style={{ top: `${topOff}px`, height: `${blockH}px`, backgroundColor: `${blockColor}18`, borderLeft: `3px solid ${blockColor}`, zIndex: 5 }}
                                data-testid={`grid-block-${block.res.id}`}>
                                <div className="text-[10px] font-medium truncate" style={{ color: blockColor }}>{block.serviceName}</div>
                                {blockH > 28 && <div className="text-[9px] text-[#9CA3AF] truncate">{block.res.client_name}</div>}
                                {blockH > 42 && <div className="flex items-center gap-1 mt-0.5"><span className="text-[9px] font-mono text-[#6B7280]">#{block.bookingId}</span>{isPaid && <Check className="w-2.5 h-2.5 text-green-400" />}{isVerifying && <Clock className="w-2.5 h-2.5 text-amber-400" />}</div>}
                              </div>
                            );
                          })}
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )
      )}

      {/* ===== ARCHIVE TAB ===== */}
      {activeTab === "archive" && (
        <div data-testid="archive-view">
          <div className="mb-4">
            <Input placeholder="Pretraži po imenu, telefonu, ID-u..." value={archiveSearch} onChange={e => setArchiveSearch(e.target.value)} className="bg-[#141416] border-[#2A2A2D] text-white max-w-sm" data-testid="archive-search" />
          </div>
          {filteredArchive.length === 0 ? (
            <div className="text-center py-12 bg-[#141416] rounded-xl border border-[#2A2A2D]"><Clock className="w-12 h-12 mx-auto text-[#9CA3AF] mb-4" /><p className="text-[#9CA3AF]">{isPast ? "Nema rezervacija" : "Nema arhiviranih termina"}</p></div>
          ) : (
            <div className="bg-[#141416] rounded-xl border border-[#2A2A2D] overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="border-[#2A2A2D] hover:bg-transparent">
                    <TableHead className="text-[#9CA3AF]">ID</TableHead><TableHead className="text-[#9CA3AF]">Vreme</TableHead><TableHead className="text-[#9CA3AF]">Klijent</TableHead><TableHead className="text-[#9CA3AF]">Usluge</TableHead><TableHead className="text-[#9CA3AF] text-right">Cena</TableHead><TableHead className="text-[#9CA3AF]">Uplata</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredArchive.sort((a, b) => a.time.localeCompare(b.time)).map(res => (
                    <TableRow key={res.id} className="border-[#2A2A2D] opacity-70 hover:opacity-100 cursor-pointer" onClick={() => setSelectedRes(res)} data-testid={`archive-row-${res.id}`}>
                      <TableCell><span className="font-mono text-xs text-[#C5A880]">#{res.booking_id}</span></TableCell>
                      <TableCell><span className="text-sm text-[#C5A880]">{res.time}-{res.end_time}</span></TableCell>
                      <TableCell><span className="text-sm">{res.client_name}</span><br /><span className="text-xs text-[#6B7280]">{res.client_phone}</span></TableCell>
                      <TableCell><span className="text-xs text-[#9CA3AF]">{res.service_names?.join(", ")}</span></TableCell>
                      <TableCell className="text-right text-sm font-medium text-[#C5A880]">{res.total_price?.toLocaleString()} RSD</TableCell>
                      <TableCell><span className={`px-2 py-1 rounded-full text-[10px] ${res.payment_status === "confirmed" || res.payment_status === "paid" ? "bg-green-600/20 text-green-400" : res.payment_status === "sent_for_verification" ? "bg-amber-500/15 text-amber-400" : "bg-[#2A2A2D] text-[#9CA3AF]"}`}>{res.payment_status === "confirmed" || res.payment_status === "paid" ? "Plaćeno" : res.payment_status === "sent_for_verification" ? "Čeka proveru" : "Čeka"}</span></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
// Employees Page
const EmployeesPage = () => {
  const tenant = useTenant();
  const [employees, setEmployees] = useState([]);
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
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

  const token = localStorage.getItem("access_token");
  const headers = { Authorization: `Bearer ${token}`, ...getTenantHeaders(tenant?.tenant_id) };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [empRes, servRes, catRes] = await Promise.all([
        axios.get(`${API}/workers?active_only=false`, { headers }),
        axios.get(`${API}/services?active_only=false`, { headers }),
        axios.get(`${API}/categories`, { headers }),
      ]);
      setEmployees(empRes.data);
      setServices(servRes.data);
      setCategories(catRes.data);
    } catch (error) {
      toast.error("Greška pri učitavanju");
    } finally {
      setLoading(false);
    }
  };

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
      work_start: "09:00",
      work_end: "21:00",
      break_start: "",
      break_end: "",
      days_off: [],
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

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <h2 className="font-['Cormorant_Garamond'] text-3xl font-light">Radnici</h2>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="bg-[#C5A880] hover:bg-[#B89970] text-black" data-testid="add-employee-btn">
              <Plus className="w-4 h-4 mr-2" />
              Dodaj Radnika
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-[#141416] border-[#2A2A2D] max-h-[90vh] overflow-y-auto">
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
                  className="bg-[#0A0A0B] border-[#2A2A2D]"
                  data-testid="employee-name-input"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-[#9CA3AF] mb-2 block">Početak rada</label>
                  <Input
                    type="time"
                    value={form.work_start}
                    onChange={(e) => setForm({ ...form, work_start: e.target.value })}
                    className="bg-[#0A0A0B] border-[#2A2A2D]"
                    data-testid="employee-work-start"
                  />
                </div>
                <div>
                  <label className="text-sm text-[#9CA3AF] mb-2 block">Kraj rada</label>
                  <Input
                    type="time"
                    value={form.work_end}
                    onChange={(e) => setForm({ ...form, work_end: e.target.value })}
                    className="bg-[#0A0A0B] border-[#2A2A2D]"
                    data-testid="employee-work-end"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-[#9CA3AF] mb-2 block">Pauza od</label>
                  <Input
                    type="time"
                    value={form.break_start}
                    onChange={(e) => setForm({ ...form, break_start: e.target.value })}
                    className="bg-[#0A0A0B] border-[#2A2A2D]"
                    data-testid="employee-break-start"
                  />
                </div>
                <div>
                  <label className="text-sm text-[#9CA3AF] mb-2 block">Pauza do</label>
                  <Input
                    type="time"
                    value={form.break_end}
                    onChange={(e) => setForm({ ...form, break_end: e.target.value })}
                    className="bg-[#0A0A0B] border-[#2A2A2D]"
                    data-testid="employee-break-end"
                  />
                </div>
              </div>

              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Slobodni dani</label>
                <div className="flex flex-wrap gap-2">
                  {dayLabels.map((label, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => toggleDayOff(idx)}
                      className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                        form.days_off.includes(idx)
                          ? "bg-[#C5A880] text-black"
                          : "bg-[#0A0A0B] border border-[#2A2A2D] text-[#9CA3AF]"
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
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
                            ? "bg-[#C5A880]/10 border border-[#C5A880]"
                            : "bg-[#0A0A0B] border border-[#2A2A2D] hover:border-[#C5A880]/50"
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
                className="w-full bg-[#C5A880] hover:bg-[#B89970] text-black"
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
        <div className="text-center py-12 bg-[#141416] rounded-xl border border-[#2A2A2D]">
          <Users className="w-12 h-12 mx-auto text-[#9CA3AF] mb-4" />
          <p className="text-[#9CA3AF]">Nema radnika</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 stagger-children">
          {employees.map((emp) => (
            <div
              key={emp.id}
              className={`bg-[#141416] rounded-xl border p-5 ${
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
                    className="h-8 w-8 hover:bg-[#0A0A0B]"
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
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteConfirm} onOpenChange={(open) => !open && setDeleteConfirm(null)}>
        <DialogContent className="bg-[#141416] border-[#2A2A2D] max-w-sm">
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
              className="flex-1 border-[#2A2A2D] bg-transparent hover:bg-[#0A0A0B]"
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
    </div>
  );
};
const ServicesPage = () => {
  const tenant = useTenant();
  const [services, setServices] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingService, setEditingService] = useState(null);
  const [form, setForm] = useState({
    name: "",
    category: "hair",
    duration: 30,
    price: 0,
    description: "",
  });

  const token = localStorage.getItem("access_token");
  const headers = { Authorization: `Bearer ${token}`, ...getTenantHeaders(tenant?.tenant_id) };

  useEffect(() => {
    if (tenant?.tenant_id) {
      fetchServices();
      fetchCategories();
    }
  }, [tenant?.tenant_id]);

  const fetchCategories = async () => {
    try {
      const res = await axios.get(`${API}/categories`, { headers });
      setCategories(res.data);
    } catch (error) {
      console.error("Error fetching categories:", error);
    }
  };

  const fetchServices = async () => {
    try {
      const response = await axios.get(`${API}/services?active_only=false`, { headers });
      setServices(response.data);
    } catch (error) {
      toast.error("Greška pri učitavanju");
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setForm({
      name: "",
      category: "hair",
      duration: 30,
      price: 0,
      description: "",
    });
    setEditingService(null);
  };

  const handleEdit = (service) => {
    setEditingService(service);
    setForm({
      name: service.name,
      category: service.category,
      duration: service.duration,
      price: service.price,
      description: service.description || "",
    });
    setDialogOpen(true);
  };

  const handleSubmit = async () => {
    if (!form.name.trim()) {
      toast.error("Unesite naziv usluge");
      return;
    }

    try {
      if (editingService) {
        await axios.put(`${API}/services/${editingService.id}`, form, { headers });
        toast.success("Usluga ažurirana");
      } else {
        await axios.post(`${API}/services`, form, { headers });
        toast.success("Usluga dodata");
      }
      
      setDialogOpen(false);
      resetForm();
      fetchServices();
    } catch (error) {
      toast.error("Greška pri čuvanju");
    }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API}/services/${id}`, { headers });
      toast.success("Usluga je trajno obrisana");
      fetchServices();
    } catch (error) {
      toast.error("Greška pri brisanju");
    }
  };

  const categoryLabels = Object.fromEntries(
    categories.map(c => [c.key, c.label])
  );

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <h2 className="font-['Cormorant_Garamond'] text-3xl font-light">Usluge</h2>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="bg-[#C5A880] hover:bg-[#B89970] text-black" data-testid="add-service-btn">
              <Plus className="w-4 h-4 mr-2" />
              Dodaj Uslugu
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-[#141416] border-[#2A2A2D]">
            <DialogHeader>
              <DialogTitle className="font-['Cormorant_Garamond'] text-2xl">
                {editingService ? "Izmeni Uslugu" : "Nova Usluga"}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Naziv</label>
                <Input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Naziv usluge"
                  className="bg-[#0A0A0B] border-[#2A2A2D]"
                  data-testid="service-name-input"
                />
              </div>

              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Kategorija</label>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(categoryLabels).map(([key, label]) => (
                    <button
                      key={key}
                      type="button"
                      onClick={() => setForm({ ...form, category: key })}
                      className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                        form.category === key
                          ? "bg-[#C5A880] text-black"
                          : "bg-[#0A0A0B] border border-[#2A2A2D] text-[#9CA3AF]"
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-[#9CA3AF] mb-2 block">Trajanje (min)</label>
                  <Input
                    type="number"
                    value={form.duration}
                    onChange={(e) => setForm({ ...form, duration: parseInt(e.target.value) || 0 })}
                    className="bg-[#0A0A0B] border-[#2A2A2D]"
                    data-testid="service-duration-input"
                  />
                </div>
                <div>
                  <label className="text-sm text-[#9CA3AF] mb-2 block">Cena (RSD)</label>
                  <Input
                    type="number"
                    value={form.price}
                    onChange={(e) => setForm({ ...form, price: parseFloat(e.target.value) || 0 })}
                    className="bg-[#0A0A0B] border-[#2A2A2D]"
                    data-testid="service-price-input"
                  />
                </div>
              </div>

              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Opis (opciono)</label>
                <Input
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="Kratak opis usluge"
                  className="bg-[#0A0A0B] border-[#2A2A2D]"
                  data-testid="service-description-input"
                />
              </div>

              <Button
                onClick={handleSubmit}
                className="w-full bg-[#C5A880] hover:bg-[#B89970] text-black"
                data-testid="save-service-btn"
              >
                {editingService ? "Sačuvaj Izmene" : "Dodaj Uslugu"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="text-center py-12 text-[#9CA3AF]">Učitavanje...</div>
      ) : services.length === 0 ? (
        <div className="text-center py-12 bg-[#141416] rounded-xl border border-[#2A2A2D]">
          <Scissors className="w-12 h-12 mx-auto text-[#9CA3AF] mb-4" />
          <p className="text-[#9CA3AF]">Nema usluga</p>
        </div>
      ) : (
        <div className="space-y-4 stagger-children">
          {Object.entries(categoryLabels).map(([category, label]) => {
            const categoryServices = services.filter(s => s.category === category);
            if (categoryServices.length === 0) return null;
            
            return (
              <div key={category}>
                <h3 className="text-sm text-[#9CA3AF] uppercase tracking-wider mb-3">{label}</h3>
                <div className="space-y-2">
                  {categoryServices.map((service) => (
                    <div
                      key={service.id}
                      className={`bg-[#141416] rounded-xl border p-4 ${
                        service.active ? "border-[#2A2A2D]" : "border-red-400/30 opacity-60"
                      }`}
                      data-testid={`service-item-${service.id}`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 flex-1">
                          <h4 className="font-medium truncate">{service.name}</h4>
                          <p className="text-sm text-[#9CA3AF]">
                            <Clock className="w-3 h-3 inline mr-1" />
                            {service.duration} min
                          </p>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <span className="font-semibold text-[#C5A880] text-sm whitespace-nowrap">
                            {service.price.toLocaleString()} RSD
                          </span>
                          <div className="flex gap-1">
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => handleEdit(service)}
                              className="h-8 w-8 hover:bg-[#0A0A0B]"
                              data-testid={`edit-service-${service.id}`}
                            >
                              <Edit2 className="w-4 h-4" />
                            </Button>
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => handleDelete(service.id)}
                              className="h-8 w-8 hover:bg-red-400/10 text-red-400"
                              data-testid={`delete-service-${service.id}`}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

// Settings Page
const SettingsPage = () => {
  const tenant = useTenant();
  const { user } = useAuth();
  const isSuperAdmin = user?.role === "super_admin";
  const [settings, setSettings] = useState({
    salon_name: "",
    work_start: "09:00",
    work_end: "21:00",
    advance_instructions: "",
    bank_account: "",
    payment_recipient: "",
    smtp_server: "smtp.gmail.com",
    smtp_port: 587,
    smtp_user: "",
    smtp_password: "",
    viber_phone: "",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const token = localStorage.getItem("access_token");
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

      <div className="bg-[#141416] rounded-xl border border-[#2A2A2D] p-6 space-y-6">
        <div>
          <label className="text-sm text-[#9CA3AF] mb-2 block">Naziv Salona</label>
          <Input
            value={settings.salon_name}
            onChange={(e) => setSettings({ ...settings, salon_name: e.target.value })}
            placeholder="Beauty Salon"
            disabled={!isSuperAdmin}
            className={`bg-[#0A0A0B] border-[#2A2A2D] ${!isSuperAdmin ? "opacity-60 cursor-not-allowed" : ""}`}
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
              className="bg-[#0A0A0B] border-[#2A2A2D]"
              data-testid="settings-work-start"
            />
          </div>
          <div>
            <label className="text-sm text-[#9CA3AF] mb-2 block">Radno vreme do</label>
            <Input
              type="time"
              value={settings.work_end}
              onChange={(e) => setSettings({ ...settings, work_end: e.target.value })}
              className="bg-[#0A0A0B] border-[#2A2A2D]"
              data-testid="settings-work-end"
            />
          </div>
        </div>

        <div>
          <label className="text-sm text-[#9CA3AF] mb-2 block">Instrukcije za Avans</label>
          <textarea
            value={settings.advance_instructions}
            onChange={(e) => setSettings({ ...settings, advance_instructions: e.target.value })}
            placeholder="Unesite instrukcije za uplatu avansa..."
            rows={4}
            className="w-full bg-[#0A0A0B] border border-[#2A2A2D] rounded-lg p-3 text-white resize-none focus:border-[#C5A880] focus:outline-none"
            data-testid="settings-advance-instructions"
          />
        </div>

        <div className="border-t border-[#2A2A2D] pt-6">
          <h3 className="font-medium mb-4 flex items-center gap-2">
            <CreditCard className="w-4 h-4 text-[#C5A880]" />
            Podaci za uplatu
          </h3>
          <div className="space-y-4">
            <div>
              <label className="text-sm text-[#9CA3AF] mb-2 block">Tekući račun</label>
              <Input
                value={settings.bank_account}
                onChange={(e) => setSettings({ ...settings, bank_account: e.target.value })}
                placeholder="265-1234567890123-12"
                className="bg-[#0A0A0B] border-[#2A2A2D]"
                data-testid="settings-bank-account"
              />
            </div>
            <div>
              <label className="text-sm text-[#9CA3AF] mb-2 block">Primalac uplate</label>
              <Input
                value={settings.payment_recipient}
                onChange={(e) => setSettings({ ...settings, payment_recipient: e.target.value })}
                placeholder="Ime salona ili vlasnika"
                className="bg-[#0A0A0B] border-[#2A2A2D]"
                data-testid="settings-payment-recipient"
              />
            </div>
          </div>
        </div>

        {/* Salon Phone */}
        <div className="border-t border-[#2A2A2D] pt-6">
          <div>
            <label className="text-sm text-[#9CA3AF] mb-1.5 block">Telefon salona (Viber/WhatsApp)</label>
            <PhoneInput
              value={settings.viber_phone}
              onChange={(v) => setSettings({ ...settings, viber_phone: v })}
              data-testid="settings-viber-phone"
            />
            <p className="text-[10px] text-[#6B7280] mt-1">Koristi se za Viber/WhatsApp dugmad na potvrdi rezervacije.</p>
          </div>
        </div>

        {/* Integrations Section - Super Admin Only */}
        {isSuperAdmin && (
        <div className="border-t border-[#2A2A2D] pt-6">
          <h3 className="font-medium mb-4 flex items-center gap-2">
            <Settings className="w-4 h-4 text-[#C5A880]" />
            Integracije i Obaveštenja
          </h3>

          <div className="space-y-5">
            {/* SMTP Configuration */}
            <div className="bg-[#0A0A0B] rounded-lg p-4 space-y-4">
              <p className="text-xs text-[#9CA3AF] uppercase tracking-wider">Email (SMTP)</p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-[#9CA3AF] mb-1.5 block">SMTP Server</label>
                  <Input
                    value={settings.smtp_server}
                    onChange={(e) => setSettings({ ...settings, smtp_server: e.target.value })}
                    placeholder="smtp.gmail.com"
                    className="bg-[#141416] border-[#2A2A2D] min-h-[48px]"
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
                    className="bg-[#141416] border-[#2A2A2D] min-h-[48px]"
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
                  className="bg-[#141416] border-[#2A2A2D] min-h-[48px]"
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
                  className="bg-[#141416] border-[#2A2A2D] min-h-[48px]"
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
          className="w-full bg-[#C5A880] hover:bg-[#B89970] text-black"
          data-testid="save-settings-btn"
        >
          {saving ? "Čuvanje..." : "Sačuvaj Podešavanja"}
        </Button>
      </div>
    </div>
  );
};

// Blacklist Page
const BlacklistPage = () => {
  const tenant = useTenant();
  const [blacklist, setBlacklist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newPhone, setNewPhone] = useState("");
  const [isAdding, setIsAdding] = useState(false);

  const token = localStorage.getItem("access_token");
  const headers = { Authorization: `Bearer ${token}`, ...getTenantHeaders(tenant?.tenant_id) };

  useEffect(() => {
    fetchBlacklist();
  }, []);

  const fetchBlacklist = async () => {
    try {
      const response = await axios.get(`${API}/blacklist`, { headers });
      setBlacklist(response.data);
    } catch (error) {
      toast.error("Greška pri učitavanju crne liste");
    } finally {
      setLoading(false);
    }
  };

  const handleAddToBlacklist = async () => {
    if (!newPhone.trim()) {
      toast.error("Unesite broj telefona");
      return;
    }

    setIsAdding(true);
    try {
      await axios.post(`${API}/blacklist?phone=${encodeURIComponent(newPhone)}`, {}, { headers });
      toast.success("Broj dodat na crnu listu");
      setNewPhone("");
      fetchBlacklist();
    } catch (error) {
      toast.error("Greška pri dodavanju na crnu listu");
    } finally {
      setIsAdding(false);
    }
  };

  const handleRemoveFromBlacklist = async (phone) => {
    try {
      await axios.delete(`${API}/blacklist/${encodeURIComponent(phone)}`, { headers });
      toast.success("Broj uklonjen sa crne liste");
      fetchBlacklist();
    } catch (error) {
      toast.error("Greška pri uklanjanju sa crne liste");
    }
  };

  return (
    <div className="animate-fade-in">
      <h2 className="font-['Cormorant_Garamond'] text-3xl font-light mb-6">Crna Lista</h2>
      
      <p className="text-[#9CA3AF] mb-6">
        Blokirani brojevi telefona ne mogu praviti nove rezervacije u salonu.
      </p>

      {/* Add new phone */}
      <div className="bg-[#141416] rounded-xl border border-[#2A2A2D] p-6 mb-6">
        <h3 className="font-medium mb-4">Dodaj broj na crnu listu</h3>
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#9CA3AF]" />
            <Input
              value={newPhone}
              onChange={(e) => setNewPhone(e.target.value)}
              placeholder="+381 6X XXX XXXX"
              className="pl-12 bg-[#0A0A0B] border-[#2A2A2D] focus:border-[#C5A880] w-full"
              data-testid="blacklist-phone-input"
              onKeyDown={(e) => e.key === "Enter" && handleAddToBlacklist()}
            />
          </div>
          <Button
            onClick={handleAddToBlacklist}
            disabled={isAdding}
            className="bg-red-500 hover:bg-red-600 text-white w-full sm:w-auto"
            data-testid="add-to-blacklist-btn"
          >
            <Ban className="w-4 h-4 mr-2" />
            Blokiraj
          </Button>
        </div>
      </div>

      {/* Blacklist table */}
      {loading ? (
        <div className="text-center py-12 text-[#9CA3AF]">Učitavanje...</div>
      ) : blacklist.length === 0 ? (
        <div className="text-center py-12 bg-[#141416] rounded-xl border border-[#2A2A2D]">
          <Shield className="w-12 h-12 mx-auto text-[#9CA3AF] mb-4" />
          <p className="text-[#9CA3AF]">Nema blokiranih brojeva</p>
        </div>
      ) : (
        <div className="bg-[#141416] rounded-xl border border-[#2A2A2D] overflow-hidden">
          {/* Desktop Table */}
          <div className="hidden sm:block">
            <Table>
              <TableHeader>
                <TableRow className="border-[#2A2A2D] hover:bg-transparent">
                  <TableHead className="text-[#9CA3AF]">Broj telefona</TableHead>
                  <TableHead className="text-[#9CA3AF]">Datum blokiranja</TableHead>
                  <TableHead className="text-[#9CA3AF] text-right">Akcija</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {blacklist.map((item, index) => (
                  <TableRow key={index} className="border-[#2A2A2D]" data-testid={`blacklist-row-${index}`}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <Ban className="w-4 h-4 text-red-400" />
                        {item.phone}
                      </div>
                    </TableCell>
                    <TableCell className="text-[#9CA3AF]">
                      {item.created_at ? format(new Date(item.created_at), "d. MMM yyyy HH:mm", { locale: sr }) : "-"}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleRemoveFromBlacklist(item.phone)}
                        className="border-green-400/30 text-green-400 hover:bg-green-400/10"
                        data-testid={`unblock-${index}`}
                      >
                        <Check className="w-4 h-4 mr-1" />
                        Odblokiraj
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Mobile Card Layout */}
          <div className="sm:hidden divide-y divide-[#2A2A2D]">
            {blacklist.map((item, index) => (
              <div key={index} className="p-4 flex items-center justify-between gap-3" data-testid={`blacklist-mobile-${index}`}>
                <div className="min-w-0">
                  <div className="flex items-center gap-2 font-medium">
                    <Ban className="w-4 h-4 text-red-400 shrink-0" />
                    <span className="truncate">{item.phone}</span>
                  </div>
                  <div className="text-xs text-[#9CA3AF] mt-1">
                    {item.created_at ? format(new Date(item.created_at), "d. MMM yyyy HH:mm", { locale: sr }) : "-"}
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleRemoveFromBlacklist(item.phone)}
                  className="border-green-400/30 text-green-400 hover:bg-green-400/10 shrink-0"
                >
                  <Check className="w-4 h-4 mr-1" />
                  Odblokiraj
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;

// System Config Page (Super-Admin only)
const SystemConfigPage = () => {
  const tenant = useTenant();
  const { user } = useAuth();
  const [categories, setCategories] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("features");

  const token = localStorage.getItem("access_token");
  const headers = { Authorization: `Bearer ${token}`, ...getTenantHeaders(tenant?.tenant_id) };

  useEffect(() => {
    Promise.all([fetchConfig(), fetchTenants()]).finally(() => setLoading(false));
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await axios.get(`${API}/categories/config`, { headers });
      setCategories(res.data);
    } catch (error) {
      console.error("Error fetching categories config:", error);
    }
  };

  const fetchTenants = async () => {
    try {
      const res = await axios.get(`${API}/super/tenants`, { headers });
      setTenants(res.data);
    } catch (error) {
      console.error("Error fetching tenants:", error);
    }
  };

  const handleCategoryToggle = async (key, currentEnabled) => {
    try {
      await axios.put(`${API}/categories/config`, { category: key, enabled: !currentEnabled }, { headers });
      setCategories(prev => prev.map(c => c.key === key ? { ...c, enabled: !currentEnabled } : c));
      toast.success(`${categories.find(c => c.key === key)?.label} — ${!currentEnabled ? "uključeno" : "isključeno"}`);
    } catch (error) {
      toast.error("Greška pri promeni konfiguracije");
    }
  };

  const handleFeatureToggle = async (tenantId, featureKey, currentValue, tenantFeatures) => {
    const updated = { ...tenantFeatures, [featureKey]: !currentValue };
    try {
      await axios.put(`${API}/super/tenants/${tenantId}/features`, updated, { headers });
      setTenants(prev => prev.map(t => t.tenant_id === tenantId ? { ...t, enabled_features: updated } : t));
      toast.success(`${featureKey}: ${!currentValue ? "ON" : "OFF"}`);
    } catch (error) {
      toast.error("Greška");
    }
  };

  const FEATURE_LABELS = {
    viber_notifications: "Viber/WhatsApp Notifikacije",
    ips_qr_payment: "IPS QR Plaćanje",
    manual_booking: "Manual Booking (Admin)",
    email_notifications: "Email Notifikacije",
    lazy_cancel: "Auto-otkazivanje (Lazy Cancel)",
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-8 h-8 border-2 border-[#C5A880] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const enabledCount = categories.filter(c => c.enabled).length;

  return (
    <div className="animate-fade-in" data-testid="system-config-page">
      <div className="mb-8">
        <h2 className="font-['Cormorant_Garamond'] text-3xl font-light mb-2">Super Admin Panel</h2>
        <p className="text-[#9CA3AF]">Upravljanje tenantima, feature flagovima i kategorijama.</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-[#0A0A0B] rounded-lg p-1 w-fit">
        <button onClick={() => setActiveTab("features")} className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === "features" ? "bg-[#C5A880] text-black" : "text-[#9CA3AF] hover:text-white"}`} data-testid="tab-features">
          <Shield className="w-4 h-4 inline mr-1.5" />Feature Flags
        </button>
        <button onClick={() => setActiveTab("categories")} className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === "categories" ? "bg-[#C5A880] text-black" : "text-[#9CA3AF] hover:text-white"}`} data-testid="tab-categories">
          <Scissors className="w-4 h-4 inline mr-1.5" />Kategorije
        </button>
      </div>

      {/* Feature Flags Tab */}
      {activeTab === "features" && (
        <div className="space-y-6">
          {tenants.map((t) => (
            <div key={t.tenant_id} className="bg-[#141416] rounded-xl border border-[#2A2A2D] overflow-hidden" data-testid={`tenant-card-${t.tenant_id}`}>
              <div className="p-4 border-b border-[#2A2A2D] flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-white">{t.name}</h3>
                  <p className="text-xs text-[#6B7280] font-mono mt-0.5">/{t.slug} &middot; {t.tenant_id}</p>
                </div>
                <span className="text-xs px-2 py-1 rounded-full bg-green-600/20 text-green-400">Aktivan</span>
              </div>
              <div className="divide-y divide-[#2A2A2D]">
                {Object.entries(t.enabled_features || {}).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between p-4" data-testid={`feature-${t.tenant_id}-${key}`}>
                    <div>
                      <span className="text-sm text-white">{FEATURE_LABELS[key] || key}</span>
                      <span className="ml-2 text-[10px] text-[#6B7280] font-mono">{key}</span>
                    </div>
                    <Switch
                      checked={value}
                      onCheckedChange={() => handleFeatureToggle(t.tenant_id, key, value, t.enabled_features)}
                      className="data-[state=checked]:bg-[#C5A880]"
                      data-testid={`feature-toggle-${t.tenant_id}-${key}`}
                    />
                  </div>
                ))}
              </div>
            </div>
          ))}
          {tenants.length === 0 && (
            <div className="text-center py-12 text-[#9CA3AF]">Nema registrovanih salona.</div>
          )}
        </div>
      )}

      {/* Categories Tab */}
      {activeTab === "categories" && (
        <>
          <div className="bg-[#141416] rounded-xl border border-[#2A2A2D] overflow-hidden">
            <div className="p-4 border-b border-[#2A2A2D] flex items-center justify-between">
              <span className="text-sm text-[#9CA3AF]">Master kategorije</span>
              <span className="text-xs text-[#C5A880]">{enabledCount} / {categories.length} aktivno</span>
            </div>
            <div className="divide-y divide-[#2A2A2D]">
              {categories.map((cat) => (
                <div key={cat.key} className={`flex items-center justify-between p-5 transition-colors ${cat.enabled ? "" : "opacity-50"}`} data-testid={`category-row-${cat.key}`}>
                  <div>
                    <span className="font-medium text-base sm:text-lg">{cat.label}</span>
                    <span className="hidden sm:inline ml-3 text-xs text-[#9CA3AF] font-mono">{cat.key}</span>
                  </div>
                  <Switch checked={cat.enabled} onCheckedChange={() => handleCategoryToggle(cat.key, cat.enabled)} className="data-[state=checked]:bg-[#C5A880]" data-testid={`category-toggle-${cat.key}`} />
                </div>
              ))}
            </div>
          </div>
          <div className="mt-6 p-4 bg-[#C5A880]/10 border border-[#C5A880]/30 rounded-xl">
            <p className="text-sm text-[#9CA3AF]">
              <strong className="text-[#C5A880]">Napomena:</strong> Isključivanje kategorije sakriva usluge iz javnog prikaza, ali ih ne briše iz baze podataka.
            </p>
          </div>
        </>
      )}
    </div>
  );
};
