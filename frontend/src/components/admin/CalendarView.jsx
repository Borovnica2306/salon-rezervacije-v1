import React, { useState, useEffect, useRef, useCallback } from "react";
import { toast } from "sonner";
import axios from "axios";
import { API, useAuth, useTenant, getTenantHeaders, getToken } from "../../App";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import {
  Calendar, Users, Clock, Ban, Check, ChevronLeft, ChevronRight,
  Plus, Bell, Loader2, Download, Phone, User, X, RotateCcw
} from "lucide-react";
import { format, addDays, subDays } from "date-fns";
import { sr } from "date-fns/locale";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "../ui/dialog";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../ui/table";
import ManualBookingModal from "./ManualBookingModal";

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
  const [services, setServices] = useState([]);
  const [settings, setSettings] = useState(null);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [cancelTarget, setCancelTarget] = useState(null);
  const [manualBookingOpen, setManualBookingOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("grid");
  const [archiveSearch, setArchiveSearch] = useState("");
  const [selectedRes, setSelectedRes] = useState(null);
  const [sendingReminders, setSendingReminders] = useState(false);

  // Drag-and-drop state
  const [dragData, setDragData] = useState(null);
  const [dropTarget, setDropTarget] = useState(null);
  const [rescheduleModal, setRescheduleModal] = useState(null);
  const [rescheduling, setRescheduling] = useState(false);

  const token = getToken();
  const headers = { Authorization: `Bearer ${token}`, ...getTenantHeaders(tenant?.tenant_id) };
  const gridRef = useRef(null);

  useEffect(() => { fetchWorkers(); fetchServices(); fetchSettings(); }, []);
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

  const fetchSettings = async () => { try { const r = await axios.get(`${API}/settings`, { headers }); setSettings(r.data); } catch (e) { console.error(e); } };
  const fetchWorkers = async () => { try { const r = await axios.get(`${API}/workers`, { headers }); setWorkers(r.data); } catch (e) { console.error(e); } };
  const fetchServices = async () => { try { const r = await axios.get(`${API}/services`, { headers }); setServices(r.data); } catch (e) { console.error(e); } };
  const fetchReservations = async () => {
    setLoading(true);
    try { const r = await axios.get(`${API}/reservations`, { params: { date: format(selectedDate, "yyyy-MM-dd") }, headers }); setReservations(r.data); }
    catch (e) { toast.error("Greška pri učitavanju"); } finally { setLoading(false); }
  };
  const fetchBlacklist = async () => { try { const r = await axios.get(`${API}/blacklist`, { headers }); setBlacklist(r.data.map(b => b.phone)); } catch (e) { console.error(e); } };
  const handleTogglePayment = async (id) => { try { await axios.put(`${API}/reservations/${id}/payment-status`, {}, { headers }); fetchReservations(); } catch (e) { toast.error("Greška"); } };
  const handleConfirmPayment = async (id) => { try { await axios.patch(`${API}/admin/reservations/${id}/confirm-payment`, {}, { headers }); toast.success("Uplata potvrđena"); setSelectedRes(null); fetchReservations(); } catch (e) { toast.error("Greška"); } };
  const handleSendReminders = async () => {
    setSendingReminders(true);
    try { const r = await axios.post(`${API}/admin/reservations/trigger-reminders`, {}, { headers }); const d = r.data; toast.success(`Sutra (${d.date}): ${d.total_reservations} termina`); }
    catch (e) { toast.error("Greška pri proveri podsetnika"); } finally { setSendingReminders(false); }
  };
  const handleCancel = async (id) => { try { await axios.put(`${API}/reservations/${id}/cancel`, {}, { headers }); toast.success("Otkazano"); setCancelDialogOpen(false); setCancelTarget(null); setSelectedRes(null); fetchReservations(); } catch (e) { toast.error("Greška"); } };
  const openCancelDialog = (res) => { setCancelTarget(res); setCancelDialogOpen(true); };
  const handleBlacklist = async (phone) => { try { await axios.post(`${API}/blacklist?phone=${encodeURIComponent(phone)}`, {}, { headers }); toast.success("Blokirano"); fetchBlacklist(); } catch (e) { toast.error("Greška"); } };
  const handleRemoveFromBlacklist = async (phone) => { try { await axios.delete(`${API}/blacklist/${encodeURIComponent(phone)}`, { headers }); toast.success("Odblokirano"); fetchBlacklist(); } catch (e) { toast.error("Greška"); } };

  const handleExportCSV = () => {
    const all = [...activeReservations, ...archivedReservations];
    if (all.length === 0) { toast.error("Nema podataka za export"); return; }
    const header = "Booking ID,Datum,Vreme,Kraj,Klijent,Telefon,Email,Usluge,Radnik,Ukupna cena,Status,Placanje,Kreiran";
    const rows = all.map(r => [r.booking_id||"",r.date||"",r.time||"",r.end_time||"",`"${(r.client_name||"").replace(/"/g,'""')}"`,r.client_phone||"",r.client_email||"",`"${(r.service_names||[]).join(", ").replace(/"/g,'""')}"`,`"${(r.service_worker_pairs||[]).map(p=>p.worker_name).join(", ").replace(/"/g,'""')}"`,r.total_price||0,r.status||"",r.payment_status||"",r.created_at||""].join(","));
    const csv = "\uFEFF" + header + "\n" + rows.join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = `rezervacije_${format(selectedDate, "yyyy-MM-dd")}.csv`; a.click(); URL.revokeObjectURL(url);
    toast.success(`Exportovano ${all.length} rezervacija`);
  };

  // === Drag-and-drop helpers ===
  const getServiceIdsForReservation = (res) => {
    return (res.service_worker_pairs || []).map(p => p.service_id).filter(Boolean);
  };

  const workerCanDoServices = useCallback((workerId, serviceIds) => {
    const worker = workers.find(w => w.id === workerId);
    if (!worker) return false;
    return serviceIds.every(sid => worker.services?.includes(sid));
  }, [workers]);

  const handleDragStart = (e, res, block) => {
    e.dataTransfer.effectAllowed = "move";
    setDragData({ res, block, serviceIds: getServiceIdsForReservation(res) });
  };

  const handleDragOver = (e, workerId, slotMin) => {
    e.preventDefault();
    if (!dragData) return;
    const canDrop = workerCanDoServices(workerId, dragData.serviceIds);
    e.dataTransfer.dropEffect = canDrop ? "move" : "none";
    if (canDrop) setDropTarget({ workerId, slotMin });
  };

  const handleDragLeave = () => { /* dropTarget cleared on drop/end */ };

  const handleDrop = (e, workerId, slotMin) => {
    e.preventDefault();
    if (!dragData) return;
    if (!workerCanDoServices(workerId, dragData.serviceIds)) {
      toast.error("Radnik ne pruža ovu uslugu");
      setDragData(null);
      setDropTarget(null);
      return;
    }
    const newTime = mtt(slotMin);
    const targetWorker = workers.find(w => w.id === workerId);
    setRescheduleModal({
      res: dragData.res,
      oldTime: dragData.res.time,
      oldWorker: dragData.res.worker_name || dragData.res.service_worker_pairs?.[0]?.worker_name || "",
      newTime,
      newWorkerId: workerId,
      newWorker: targetWorker?.name || "",
    });
    setDragData(null);
    setDropTarget(null);
  };

  const handleDragEnd = () => { setDragData(null); setDropTarget(null); };

  const handleRescheduleConfirm = async () => {
    if (!rescheduleModal) return;
    setRescheduling(true);
    try {
      await axios.put(`${API}/reservations/${rescheduleModal.res.id}/reschedule`, {
        new_time: rescheduleModal.newTime,
        new_worker_id: rescheduleModal.newWorkerId,
      }, { headers });
      toast.success("Termin uspešno premešten");
      setRescheduleModal(null);
      fetchReservations();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Greška pri premeštanju");
    } finally {
      setRescheduling(false);
    }
  };

  // === Computed ===
  const workStart = settings ? ttm(settings.work_start) : 540;
  const workEnd = settings ? ttm(settings.work_end) : 1260;
  const timeSlots = [];
  for (let m = workStart; m < workEnd; m += 30) timeSlots.push(m);

  const now = new Date();
  const nowMins = now.getHours() * 60 + now.getMinutes();
  const isToday = format(selectedDate, "yyyy-MM-dd") === format(now, "yyyy-MM-dd");
  const isPast = selectedDate < new Date(now.getFullYear(), now.getMonth(), now.getDate());

  const activeReservations = reservations.filter(r => { if (!isToday) return !isPast; return nowMins < ttm(r.end_time) + 30; });
  const archivedReservations = reservations.filter(r => { if (!isToday) return isPast; return nowMins >= ttm(r.end_time) + 30; });

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

  // Check if a worker column should be dimmed during drag
  const isWorkerDimmed = (workerId) => {
    if (!dragData) return false;
    return !workerCanDoServices(workerId, dragData.serviceIds);
  };

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div>
          <h2 className="font-['Cormorant_Garamond'] text-3xl font-light">Rezervacije</h2>
          <p className="text-[#9CA3AF]">{format(selectedDate, "EEEE, d. MMMM yyyy", { locale: sr })}</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Button onClick={handleSendReminders} disabled={sendingReminders} variant="outline" className="border-[#2A2A2D] hover:bg-[var(--color-surface)] text-[#9CA3AF] hover:text-white" data-testid="send-reminders-btn">
            {sendingReminders ? <Loader2 className="w-4 h-4 mr-1.5 animate-spin" /> : <Bell className="w-4 h-4 mr-1.5" />}
            Podsetnici za sutra
          </Button>
          <Button onClick={() => setManualBookingOpen(true)} className="bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black font-medium" data-testid="admin-new-reservation-btn">
            <Plus className="w-4 h-4 mr-1" /> Nova Rezervacija
          </Button>
          <Button variant="outline" size="icon" onClick={() => setSelectedDate(subDays(selectedDate, 1))} className="border-[#2A2A2D] hover:bg-[var(--color-surface)]" data-testid="prev-day-btn"><ChevronLeft className="w-4 h-4" /></Button>
          <Button variant="outline" onClick={() => setSelectedDate(new Date())} className="border-[#2A2A2D] hover:bg-[var(--color-surface)]" data-testid="today-btn">Danas</Button>
          <Button variant="outline" size="icon" onClick={() => setSelectedDate(addDays(selectedDate, 1))} className="border-[#2A2A2D] hover:bg-[var(--color-surface)]" data-testid="next-day-btn"><ChevronRight className="w-4 h-4" /></Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <div className="flex gap-1 bg-[var(--color-background)] rounded-lg p-1 w-fit" data-testid="view-tabs">
          <button onClick={() => setActiveTab("grid")} className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === "grid" ? "bg-[var(--color-primary)] text-black" : "text-[#9CA3AF] hover:text-white"}`} data-testid="tab-grid">
            <Calendar className="w-4 h-4 inline mr-1.5" />Mreža{activeReservations.length > 0 && <span className="ml-1.5 text-xs opacity-70">({activeReservations.length})</span>}
          </button>
          <button onClick={() => setActiveTab("archive")} className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === "archive" ? "bg-[var(--color-primary)] text-black" : "text-[#9CA3AF] hover:text-white"}`} data-testid="tab-archive">
            <Clock className="w-4 h-4 inline mr-1.5" />Arhiva{archivedReservations.length > 0 && <span className="ml-1.5 text-xs opacity-70">({archivedReservations.length})</span>}
          </button>
        </div>
        {user?.role === "super_admin" && (
          <Button onClick={handleExportCSV} variant="outline" size="sm" className="border-[#2A2A2D] hover:bg-[var(--color-surface)] text-[#9CA3AF] hover:text-white" data-testid="export-csv-btn">
            <Download className="w-4 h-4 mr-1.5" />Export CSV
          </Button>
        )}
      </div>

      {/* Cancel Dialog */}
      <Dialog open={cancelDialogOpen} onOpenChange={setCancelDialogOpen}>
        <DialogContent className="bg-[var(--color-surface)] border-[#2A2A2D]">
          <DialogHeader><DialogTitle className="text-white">Otkazivanje rezervacije</DialogTitle><DialogDescription className="text-[#9CA3AF]">Da li ste sigurni?</DialogDescription></DialogHeader>
          {cancelTarget && (
            <div className="bg-[var(--color-background)] rounded-lg p-4 space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-[#9CA3AF]">ID:</span><span className="font-mono text-[var(--color-primary)]">#{cancelTarget.booking_id}</span></div>
              <div className="flex justify-between"><span className="text-[#9CA3AF]">Klijent:</span><span className="text-white">{cancelTarget.client_name}</span></div>
              <div className="flex justify-between"><span className="text-[#9CA3AF]">Vreme:</span><span className="text-white">{cancelTarget.time} - {cancelTarget.end_time}</span></div>
            </div>
          )}
          <div className="flex gap-3 mt-2">
            <Button variant="outline" className="flex-1 border-[#2A2A2D]" onClick={() => setCancelDialogOpen(false)}>Ne, zadrži</Button>
            <Button className="flex-1 bg-red-600 hover:bg-red-700 text-white" onClick={() => cancelTarget && handleCancel(cancelTarget.id)}>Da, otkaži</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Reschedule Confirmation Modal */}
      <Dialog open={!!rescheduleModal} onOpenChange={(v) => !v && setRescheduleModal(null)}>
        <DialogContent className="bg-[var(--color-surface)] border-[#2A2A2D] max-w-sm" data-testid="reschedule-modal">
          <DialogHeader>
            <DialogTitle className="text-white">{"Premesti termin?"}</DialogTitle>
            <DialogDescription className="text-[#9CA3AF]">
              {"Da li ste sigurni da želite da promenite termin za klijenta"} <strong className="text-white">{rescheduleModal?.res?.client_name}</strong>?
            </DialogDescription>
          </DialogHeader>
          {rescheduleModal && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                  <p className="text-[10px] text-red-400 uppercase tracking-wider mb-1">Staro</p>
                  <p className="text-sm text-white font-medium">{rescheduleModal.oldTime}</p>
                  <p className="text-xs text-[#9CA3AF]">{rescheduleModal.oldWorker}</p>
                </div>
                <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3">
                  <p className="text-[10px] text-green-400 uppercase tracking-wider mb-1">Novo</p>
                  <p className="text-sm text-white font-medium">{rescheduleModal.newTime}</p>
                  <p className="text-xs text-[#9CA3AF]">{rescheduleModal.newWorker}</p>
                </div>
              </div>
              <p className="text-xs text-[#6B7280]">{"Klijent će dobiti email obaveštenje o novom terminu."}</p>
              <div className="flex gap-3">
                <Button variant="outline" className="flex-1 border-[#2A2A2D]" onClick={() => setRescheduleModal(null)} disabled={rescheduling}>{"Otkaži"}</Button>
                <Button className="flex-1 bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black font-medium" onClick={handleRescheduleConfirm} disabled={rescheduling} data-testid="reschedule-confirm-btn">
                  {rescheduling ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Check className="w-4 h-4 mr-1" />}
                  {"Potvrdi"}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Detail Dialog */}
      <Dialog open={!!selectedRes} onOpenChange={(v) => !v && setSelectedRes(null)}>
        <DialogContent className="bg-[var(--color-surface)] border-[#2A2A2D] max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <span className="font-mono text-[var(--color-primary)] text-sm bg-[var(--color-primary)]/10 px-2 py-0.5 rounded">#{selectedRes?.booking_id}</span>
              {selectedRes?.client_name}
              {selectedRes?.is_rescheduled && <RotateCcw className="w-3.5 h-3.5 text-amber-400" title="Premešten" />}
            </DialogTitle>
            <DialogDescription className="text-[#9CA3AF]">{selectedRes?.time} - {selectedRes?.end_time} · {selectedRes?.total_duration} min</DialogDescription>
          </DialogHeader>
          {selectedRes && (
            <div className="space-y-3">
              <div className="bg-[var(--color-background)] rounded-lg p-3 space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-[#9CA3AF]">Telefon:</span><span className="text-white">{selectedRes.client_phone}</span></div>
                <div className="flex justify-between"><span className="text-[#9CA3AF]">Ukupno:</span><span className="text-[var(--color-primary)] font-medium">{selectedRes.total_price ?? 0} π</span></div>
              </div>
              <div className="space-y-1">
                {selectedRes.worker_time_blocks?.length > 0 ? selectedRes.worker_time_blocks.map((block, idx) => {
                  const pair = selectedRes.service_worker_pairs?.[idx];
                  return (
                    <div key={idx}>
                      {block.gap > 0 && idx > 0 && <div className="text-[10px] text-[#6B7280] italic pl-1 py-0.5">☕ Pauza ({block.gap} min)</div>}
                      <div className="flex justify-between text-xs bg-[var(--color-background)] rounded px-2 py-1.5">
                        <span className="text-white">{block.start_time}-{block.end_time} {pair?.service_name}</span>
                        <span className="text-[var(--color-primary)]">{pair?.worker_name}</span>
                      </div>
                    </div>
                  );
                }) : selectedRes.service_worker_pairs?.map((pair, idx) => (
                  <div key={idx} className="flex justify-between text-xs bg-[var(--color-background)] rounded px-2 py-1.5">
                    <span className="text-white">{pair.service_name}</span><span className="text-[var(--color-primary)]">{pair.worker_name}</span>
                  </div>
                ))}
              </div>
              <div className="flex gap-2 pt-2 border-t border-[#2A2A2D]">
                <button onClick={() => { handleTogglePayment(selectedRes.id); setSelectedRes(null); }} className={`flex-1 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${selectedRes.payment_status === "confirmed" || selectedRes.payment_status === "paid" ? "bg-green-600/20 text-green-400" : selectedRes.payment_status === "sent_for_verification" ? "bg-amber-500/15 text-amber-400" : "bg-[#1E1E22] text-[#9CA3AF]"}`}>
                  {selectedRes.payment_status === "confirmed" || selectedRes.payment_status === "paid" ? "Plaćeno" : selectedRes.payment_status === "sent_for_verification" ? "Čeka proveru" : selectedRes.payment_status === "pending_pi_payment" ? "Čeka Pi uplatu" : "Čeka uplatu"}
                </button>
                <button onClick={() => { setSelectedRes(null); openCancelDialog(selectedRes); }} className="px-3 py-2 rounded-lg text-xs font-medium bg-red-500/10 text-red-400 hover:bg-red-500/20">Otkaži</button>
                {!blacklist.includes(selectedRes.client_phone) ? (
                  <button onClick={() => handleBlacklist(selectedRes.client_phone)} className="px-3 py-2 rounded-lg text-xs font-medium bg-red-500/10 text-red-400 hover:bg-red-500/20"><Ban className="w-3 h-3 inline mr-1" />Blokiraj</button>
                ) : (
                  <button onClick={() => handleRemoveFromBlacklist(selectedRes.client_phone)} className="px-3 py-2 rounded-lg text-xs font-medium bg-green-500/10 text-green-400 hover:bg-green-500/20"><Check className="w-3 h-3 inline mr-1" />Odblokiraj</button>
                )}
              </div>
              {selectedRes.payment_status === "sent_for_verification" && (
                <button onClick={() => handleConfirmPayment(selectedRes.id)} className="w-full mt-2 px-3 py-3 rounded-lg text-sm font-medium bg-green-600 hover:bg-green-700 text-white transition-colors min-h-[48px]">
                  <Check className="w-4 h-4 inline mr-2" />Potvrdi uplatu
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
          <div className="text-center py-12 bg-[var(--color-surface)] rounded-xl border border-[#2A2A2D]"><Users className="w-12 h-12 mx-auto text-[#9CA3AF] mb-4" /><p className="text-[#9CA3AF]">Nema aktivnih radnika</p></div>
        ) : (
          <div className="bg-[var(--color-surface)] rounded-xl border border-[#2A2A2D]" data-testid="timeline-grid">
            <div className="overflow-auto max-h-[70vh]" ref={gridRef} data-testid="grid-body">
              {/* Header */}
              <div className="flex sticky top-0 z-20 bg-[var(--color-surface)] border-b border-[#2A2A2D]">
                <div className="w-16 flex-shrink-0 p-2 text-center text-[10px] text-[#6B7280] border-r border-[#2A2A2D] sticky left-0 z-30 bg-[var(--color-surface)]">Vreme</div>
                {workers.map(w => (
                  <div key={w.id} className={`flex-1 min-w-[120px] flex-shrink-0 p-2 text-center border-r border-[#2A2A2D] last:border-r-0 transition-opacity ${isWorkerDimmed(w.id) ? "opacity-25" : ""}`}>
                    <div className="text-xs font-medium text-white truncate">{w.name}</div>
                    <div className="text-[10px] text-[#6B7280]">{w.work_start}-{w.work_end}</div>
                  </div>
                ))}
              </div>
              {/* Body */}
              <div className="relative">
                {nowLineTop > 0 && nowLineTop < timeSlots.length * SLOT_HEIGHT && (
                  <div className="absolute left-0 right-0 z-[5] pointer-events-none" style={{ top: `${nowLineTop}px` }}>
                    <div className="flex items-center"><div className="w-2 h-2 rounded-full bg-red-500 -ml-1" /><div className="flex-1 h-px bg-red-500/60" /></div>
                  </div>
                )}
                {timeSlots.map((slotMin) => (
                  <div key={slotMin} className="flex border-b border-[#1E1E22]" style={{ height: `${SLOT_HEIGHT}px` }}>
                    <div className="w-16 flex-shrink-0 flex items-start justify-center pt-1 text-[10px] text-[#6B7280] border-r border-[#1E1E22] sticky left-0 z-10 bg-[var(--color-surface)]">{mtt(slotMin)}</div>
                    {workers.map(w => {
                      const blocks = buildWorkerBlocks(w.id);
                      const cellBlocks = blocks.filter(b => b.startMin >= slotMin && b.startMin < slotMin + 30);
                      const dimmed = isWorkerDimmed(w.id);
                      const isDropHere = dropTarget?.workerId === w.id && dropTarget?.slotMin === slotMin;
                      return (
                        <div
                          key={w.id}
                          className={`flex-1 min-w-[120px] flex-shrink-0 border-r border-[#1E1E22] last:border-r-0 relative transition-all ${dimmed ? "opacity-20 bg-red-900/10" : ""} ${isDropHere ? "bg-[var(--color-primary)]/10" : ""}`}
                          onDragOver={(e) => handleDragOver(e, w.id, slotMin)}
                          onDragLeave={handleDragLeave}
                          onDrop={(e) => handleDrop(e, w.id, slotMin)}
                        >
                          {cellBlocks.map((block, bIdx) => {
                            const topOff = ((block.startMin - slotMin) / 30) * SLOT_HEIGHT;
                            const blockH = Math.max(((block.endMin - block.startMin) / 30) * SLOT_HEIGHT, 24);
                            const isPaid = block.res.payment_status === "confirmed" || block.res.payment_status === "paid";
                            const isVerifying = block.res.payment_status === "sent_for_verification";
                            const blockColor = isVerifying ? "#F59E0B" : isPaid ? "#22C55E" : block.color;
                            const isRescheduled = block.res.is_rescheduled;
                            return (
                              <div
                                key={bIdx}
                                draggable={!block.isArchived}
                                onDragStart={(e) => !block.isArchived && handleDragStart(e, block.res, block)}
                                onDragEnd={handleDragEnd}
                                onClick={() => setSelectedRes(block.res)}
                                className={`absolute left-1 right-1 rounded-md px-1.5 py-0.5 cursor-grab overflow-hidden transition-all hover:brightness-110 hover:shadow-lg ${block.isArchived ? "opacity-40 cursor-default" : ""} ${dragData?.res?.id === block.res.id ? "opacity-50 ring-2 ring-[var(--color-primary)]" : ""}`}
                                style={{ top: `${topOff}px`, height: `${blockH}px`, backgroundColor: `${blockColor}18`, borderLeft: `3px solid ${blockColor}`, zIndex: 5 }}
                                data-testid={`grid-block-${block.res.id}`}
                              >
                                <div className="text-[10px] font-medium truncate flex items-center gap-1" style={{ color: blockColor }}>
                                  {isRescheduled && <RotateCcw className="w-2.5 h-2.5 shrink-0" />}
                                  {block.serviceName}
                                </div>
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
            <Input placeholder="Pretraži po imenu, telefonu, ID-u..." value={archiveSearch} onChange={e => setArchiveSearch(e.target.value)} className="bg-[var(--color-surface)] border-[#2A2A2D] text-white max-w-sm" data-testid="archive-search" />
          </div>
          {filteredArchive.length === 0 ? (
            <div className="text-center py-12 bg-[var(--color-surface)] rounded-xl border border-[#2A2A2D]"><Clock className="w-12 h-12 mx-auto text-[#9CA3AF] mb-4" /><p className="text-[#9CA3AF]">{isPast ? "Nema rezervacija" : "Nema arhiviranih termina"}</p></div>
          ) : (
            <div className="bg-[var(--color-surface)] rounded-xl border border-[#2A2A2D] overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="border-[#2A2A2D] hover:bg-transparent">
                    <TableHead className="text-[#9CA3AF]">ID</TableHead><TableHead className="text-[#9CA3AF]">Vreme</TableHead><TableHead className="text-[#9CA3AF]">Klijent</TableHead><TableHead className="text-[#9CA3AF]">Usluge</TableHead><TableHead className="text-[#9CA3AF] text-right">Cena</TableHead><TableHead className="text-[#9CA3AF]">Uplata</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredArchive.sort((a, b) => a.time.localeCompare(b.time)).map(res => (
                    <TableRow key={res.id} className="border-[#2A2A2D] opacity-70 hover:opacity-100 cursor-pointer" onClick={() => setSelectedRes(res)}>
                      <TableCell><span className="font-mono text-xs text-[var(--color-primary)]">#{res.booking_id}</span></TableCell>
                      <TableCell><span className="text-sm text-[var(--color-primary)]">{res.time}-{res.end_time}</span></TableCell>
                      <TableCell><span className="text-sm">{res.client_name}</span><br /><span className="text-xs text-[#6B7280]">{res.client_phone}</span></TableCell>
                      <TableCell><span className="text-xs text-[#9CA3AF]">{res.service_names?.join(", ")}</span></TableCell>
                      <TableCell className="text-right text-sm font-medium text-[var(--color-primary)]">{res.total_price ?? 0} π</TableCell>
                      <TableCell><span className={`px-2 py-1 rounded-full text-[10px] ${res.payment_status === "confirmed" || res.payment_status === "paid" ? "bg-green-600/20 text-green-400" : res.payment_status === "sent_for_verification" ? "bg-amber-500/15 text-amber-400" : res.payment_status === "pending_pi_payment" ? "bg-purple-500/20 text-purple-400" : "bg-[#2A2A2D] text-[#9CA3AF]"}`}>{res.payment_status === "confirmed" || res.payment_status === "paid" ? "Plaćeno" : res.payment_status === "sent_for_verification" ? "Čeka proveru" : res.payment_status === "pending_pi_payment" ? "Pi" : "Čeka"}</span></TableCell>
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

export default ReservationsPage;
