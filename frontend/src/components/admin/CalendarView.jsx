import React, { useState, useEffect, useRef, useCallback } from "react";
import { toast } from "sonner";
import axios from "axios";
import { API, useAuth, useTenant, getTenantHeaders, getToken } from "../../App";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import {
  Calendar as CalendarIcon, Users, Clock, Ban, Check, ChevronLeft, ChevronRight,
  Plus, Bell, Loader2, Download, RotateCcw, CalendarDays
} from "lucide-react";
import { format, addDays, subDays, isSameDay, startOfMonth, endOfMonth, startOfWeek, endOfWeek, eachDayOfInterval, isBefore, startOfDay } from "date-fns";
import { srLatn as sr } from "date-fns/locale";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "../ui/dialog";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../ui/table";
import ManualBookingModal from "./ManualBookingModal";

const SLOT_HEIGHT = 32;
const COLORS = ["#C5A880", "#7C9EB2", "#A8C686", "#D4A574", "#B294BB", "#86C1B9", "#DCA68B"];

const CalendarView = () => {
  const { user } = useAuth();
  const tenant = useTenant();
  const isWorker = user?.role === "worker";
  const [reservations, setReservations] = useState([]);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [loading, setLoading] = useState(true);
  const [blacklist, setBlacklist] = useState([]);
  const [workers, setWorkers] = useState([]);
  const [, setServices] = useState([]);
  const [settings, setSettings] = useState(null);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [cancelTarget, setCancelTarget] = useState(null);
  const [manualBookingOpen, setManualBookingOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("grid");
  const [archiveSearch, setArchiveSearch] = useState("");
  const [selectedRes, setSelectedRes] = useState(null);
  const [sendingReminders, setSendingReminders] = useState(false);

  const [dragData, setDragData] = useState(null);
  const [dropTarget, setDropTarget] = useState(null);
  const [dateDropTarget, setDateDropTarget] = useState(null);
  const [rescheduleModal, setRescheduleModal] = useState(null);
  const [rescheduling, setRescheduling] = useState(false);

  const today = startOfDay(new Date());
  const maxWorkerDate = addDays(today, 7);

  const token = getToken();
  const headers = { Authorization: `Bearer ${token}`, ...getTenantHeaders(tenant?.tenant_id) };
  const gridRef = useRef(null);

  useEffect(() => {
    fetchWorkers();
    fetchServices();
    fetchSettings();
  }, []);

  useEffect(() => {
    fetchReservations();
    fetchBlacklist();
  }, [selectedDate]);

  useEffect(() => {
    if (!loading && activeTab === "grid" && gridRef.current) {
      const now = new Date();
      const mins = now.getHours() * 60 + now.getMinutes();
      const ws = settings ? ttm(settings.work_start) : 540;
      const scrollTo = ((mins - ws) / 30) * SLOT_HEIGHT;
      gridRef.current.scrollTop = Math.max(0, scrollTo - SLOT_HEIGHT * 2);
    }
  }, [loading, activeTab, selectedDate]);

  const ttm = (t) => {
    if (!t) return 0;
    const [h, m] = t.split(":").map(Number);
    return h * 60 + m;
  };
  
  const mtt = (m) => `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;

  const fetchSettings = async () => { try { const r = await axios.get(`${API}/settings`, { headers }); setSettings(r.data); } catch (e) { console.error(e); } };
  const fetchWorkers = async () => { try { const r = await axios.get(`${API}/workers`, { headers }); setWorkers(r.data); } catch (e) { console.error(e); } };
  const fetchServices = async () => { try { const r = await axios.get(`${API}/services`, { headers }); setServices(r.data); } catch (e) { console.error(e); } };
  
  const fetchReservations = async () => {
    setLoading(true);
    try {
      const params = isWorker ? {} : { date: format(selectedDate, "yyyy-MM-dd") };
      const r = await axios.get(`${API}/reservations`, { params, headers });
      setReservations(r.data);
    } catch (e) {
      toast.error("Greška pri učitavanju");
    } finally {
      setLoading(false);
    }
  };

  const fetchBlacklist = async () => { try { const r = await axios.get(`${API}/blacklist`, { headers }); setBlacklist(r.data.map(b => b.phone)); } catch (e) { console.error(e); } };
  
  const handleSendReminders = async () => {
    setSendingReminders(true);
    try {
      const r = await axios.post(`${API}/admin/reservations/trigger-reminders`, {}, { headers });
      const d = r.data;
      toast.success(`Sutra (${d.date}): ${d.total_reservations} termina`);
    } catch (e) {
      toast.error("Greška pri proveri podsetnika");
    } finally {
      setSendingReminders(false);
    }
  };

  const handleCancel = async (id) => {
    try {
      await axios.put(`${API}/reservations/${id}/cancel`, {}, { headers });
      toast.success("Otkazano");
      setCancelDialogOpen(false);
      setCancelTarget(null);
      setSelectedRes(null);
      fetchReservations();
    } catch (e) {
      toast.error("Greška");
    }
  };

  const openCancelDialog = (res) => { setCancelTarget(res); setCancelDialogOpen(true); };
  const handleBlacklist = async (phone) => { try { await axios.post(`${API}/blacklist?phone=${encodeURIComponent(phone)}`, {}, { headers }); toast.success("Blokirano"); fetchBlacklist(); } catch (e) { toast.error("Greška"); } };
  const handleRemoveFromBlacklist = async (phone) => { try { await axios.delete(`${API}/blacklist/${encodeURIComponent(phone)}`, { headers }); toast.success("Odblokirano"); fetchBlacklist(); } catch (e) { toast.error("Greška"); } };

  const handleExportCSV = () => {
    const all = [...activeReservations, ...archivedReservations];
    if (all.length === 0) { toast.error("Nema podataka za export"); return; }
    const header = "Booking ID,Datum,Vreme,Kraj,Klijent,Telefon,Email,Usluge,Radnik,Ukupna cena,Status,Plaćanje,Kreiran";
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
      r.created_at || ""
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

  const getServiceIdsForReservation = (res) => {
    return (res.service_worker_pairs || []).map(p => p.service_id).filter(Boolean);
  };

  const workerCanDoServices = useCallback((workerId, serviceIds) => {
    const worker = workers.find(w => w.id === workerId);
    if (!worker) return false;
    return serviceIds.every(sid => worker.services?.includes(sid));
  }, [workers]);

  const handleDragStart = (e, res, block) => {
    if (isWorker) { e.preventDefault(); return; }
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("application/json", JSON.stringify({ res, block }));
    setDragData({ res, block, serviceIds: getServiceIdsForReservation(res) });
  };

  const handleDragOver = (e, workerId, slotMin) => {
    e.preventDefault();
    if (isWorker || !dragData) return;
    const canDrop = workerCanDoServices(workerId, dragData.serviceIds);
    e.dataTransfer.dropEffect = canDrop ? "move" : "none";
    if (canDrop) setDropTarget({ workerId, slotMin });
  };

  const handleDateDragOver = (e, targetDate) => {
    e.preventDefault();
    if (isWorker) return;
    if (isBefore(targetDate, today)) return;
    e.dataTransfer.dropEffect = "move";
    setDateDropTarget(format(targetDate, "yyyy-MM-dd"));
  };

  const handleDateDrop = (e, targetDate) => {
    e.preventDefault();
    setDateDropTarget(null);
    if (isWorker) return;

    let currentDrag = dragData;
    if (!currentDrag) {
      try {
        const raw = e.dataTransfer.getData("application/json");
        if (raw) {
          const parsed = JSON.parse(raw);
          currentDrag = { res: parsed.res, block: parsed.block, serviceIds: getServiceIdsForReservation(parsed.res) };
        }
      } catch (err) {
        console.error("Greska pri citanju drag podataka", err);
      }
    }

    if (!currentDrag || !currentDrag.res) return;

    const originalDate = currentDrag.res.date;
    const todayStr = format(new Date(), "yyyy-MM-dd");
    if (originalDate < todayStr) {
      toast.error("Nije moguće premestiti rezervaciju iz prošlog dana.");
      setDragData(null);
      return;
    }

    if (isBefore(targetDate, today)) {
      toast.error("Nije moguće premestiti rezervaciju u prošlost.");
      setDragData(null);
      return;
    }

    const formattedTargetDate = format(targetDate, "yyyy-MM-dd");
    const defaultWorkerId = currentDrag.res.worker_id || currentDrag.res.service_worker_pairs?.[0]?.worker_id;
    const targetWorker = workers.find(w => w.id === defaultWorkerId) || workers[0];

    setRescheduleModal({
      res: currentDrag.res,
      oldTime: `${format(selectedDate, "dd.MM.")} u ${currentDrag.res.time}`,
      oldWorker: currentDrag.res.worker_name || currentDrag.res.service_worker_pairs?.[0]?.worker_name || "",
      newDate: formattedTargetDate,
      newTime: currentDrag.res.time || "09:00",
      newWorkerId: targetWorker?.id,
      newWorker: targetWorker?.name || "",
    });

    setDragData(null);
  };

  const handleDrop = (e, workerId, slotMin) => {
    e.preventDefault();
    if (isWorker) return;

    let currentDrag = dragData;
    if (!currentDrag) {
      try {
        const raw = e.dataTransfer.getData("application/json");
        if (raw) {
          const parsed = JSON.parse(raw);
          currentDrag = { res: parsed.res, block: parsed.block, serviceIds: getServiceIdsForReservation(parsed.res) };
        }
      } catch (err) {
        console.error("Greska pri citanju drag podataka", err);
      }
    }

    if (!currentDrag || !currentDrag.res) return;

    const originalDate = currentDrag.res.date;
    const todayStr = format(new Date(), "yyyy-MM-dd");
    if (originalDate < todayStr) {
      toast.error("Nije moguće premestiti rezervaciju iz prošlog dana.");
      setDragData(null);
      setDropTarget(null);
      return;
    }

    if (isPast) {
      toast.error("Nije moguće premestiti rezervaciju u prošli dan.");
      setDragData(null);
      setDropTarget(null);
      return;
    }
    if (isToday && slotMin < nowMins) {
      toast.error("Nije moguće premestiti rezervaciju u prošlo vreme.");
      setDragData(null);
      setDropTarget(null);
      return;
    }

    if (!workerCanDoServices(workerId, currentDrag.serviceIds)) {
      toast.error("Radnik ne pruža ovu uslugu");
      setDragData(null);
      setDropTarget(null);
      return;
    }

    const duration = currentDrag.res.total_duration || 30;
    const newStartMin = slotMin;
    const newEndMin = slotMin + duration;
    const workerBlocks = buildWorkerBlocks(workerId);
    const hasOverlap = workerBlocks.some(b =>
      b.res.id !== currentDrag.res.id && newStartMin < b.endMin && newEndMin > b.startMin
    );
    if (hasOverlap) {
      toast.error("Ovaj termin je već zauzet kod izabranog radnika.");
      setDragData(null);
      setDropTarget(null);
      return;
    }

    const newTime = mtt(slotMin);
    const targetWorker = workers.find(w => w.id === workerId);

    const blocks = currentDrag.res.worker_time_blocks || [];
    let draggedBlockIndex = -1;
    if (blocks.length > 1 && currentDrag.block) {
      draggedBlockIndex = blocks.findIndex(b =>
        b.worker_id === currentDrag.block.res?.worker_time_blocks?.find(
          wb => wb.start_time === mtt(currentDrag.block.startMin) && wb.worker_id === currentDrag.block.res?.worker_id
        )?.worker_id && b.start_time === mtt(currentDrag.block.startMin)
      );
      if (draggedBlockIndex === -1) {
        draggedBlockIndex = blocks.findIndex(b => b.start_time === mtt(currentDrag.block.startMin));
      }
    }

    setRescheduleModal({
      res: currentDrag.res,
      oldTime: currentDrag.res.time,
      oldWorker: currentDrag.res.worker_name || currentDrag.res.service_worker_pairs?.[0]?.worker_name || "",
      newDate: format(selectedDate, "yyyy-MM-dd"),
      newTime,
      newWorkerId: workerId,
      newWorker: targetWorker?.name || "",
      blockIndex: draggedBlockIndex >= 0 ? draggedBlockIndex : undefined,
    });
    setDragData(null);
    setDropTarget(null);
  };

  const handleDragEnd = () => { setDragData(null); setDropTarget(null); setDateDropTarget(null); };

  const handleRescheduleConfirm = async () => {
    if (!rescheduleModal) return;

    // Provera da li je izabrano vreme u prošlosti za današnji dan
    if (rescheduleModal.newDate === format(now, "yyyy-MM-dd")) {
      const selectedMins = ttm(rescheduleModal.newTime);
      if (selectedMins < nowMins) {
        toast.error("Nije moguće premestiti rezervaciju u prošlo vreme.");
        return;
      }
    }

    setRescheduling(true);
    try {
      const payload = {
        new_time: rescheduleModal.newTime,
        new_worker_id: rescheduleModal.newWorkerId,
      };
      if (rescheduleModal.newDate) {
        payload.new_date = rescheduleModal.newDate;
      }
      if (rescheduleModal.blockIndex !== undefined) {
        payload.block_index = rescheduleModal.blockIndex;
      }
      await axios.put(`${API}/reservations/${rescheduleModal.res.id}/reschedule`, payload, { headers });
      toast.success("Termin uspešno premešten");
      
      const targetDateObj = rescheduleModal.newDate ? new Date(rescheduleModal.newDate + "T00:00:00") : selectedDate;
      setRescheduleModal(null);
      
      setSelectedDate(targetDateObj);
      fetchReservations();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Greška pri premeštanju");
    } finally {
      setRescheduling(false);
    }
  };

  const workStart = settings ? ttm(settings.work_start) : 540;
  const workEnd = settings ? ttm(settings.work_end) : 1260;
  const timeSlots = [];
  for (let m = workStart; m < workEnd; m += 30) timeSlots.push(m);

  const now = new Date();
  const nowMins = now.getHours() * 60 + now.getMinutes();
  const isToday = format(selectedDate, "yyyy-MM-dd") === format(now, "yyyy-MM-dd");
  const isPast = isBefore(startOfDay(selectedDate), today);

  const displayWorkers = isWorker
    ? workers.filter(w => w.id === user?.worker_id)
    : workers;

  const displayReservations = isWorker
    ? reservations.filter(r => r.date === format(selectedDate, "yyyy-MM-dd"))
    : reservations;

  const activeReservations = displayReservations.filter(r => { if (!isToday) return !isPast; return nowMins < ttm(r.end_time) + 30; });
  const archivedReservations = displayReservations.filter(r => { if (!isToday) return isPast; return nowMins >= ttm(r.end_time) + 30; });

  const buildWorkerBlocks = (wid) => {
    const blocks = [];
    displayReservations.forEach((res, rIdx) => {
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

  const isWorkerDimmed = (workerId) => {
    if (!dragData) return false;
    return !workerCanDoServices(workerId, dragData.serviceIds);
  };

  const canGoPrev = isWorker ? format(selectedDate, "yyyy-MM-dd") > format(today, "yyyy-MM-dd") : true;
  const canGoNext = isWorker ? format(selectedDate, "yyyy-MM-dd") < format(maxWorkerDate, "yyyy-MM-dd") : true;

  const handlePrevDay = () => { if (!canGoPrev) return; setSelectedDate(subDays(selectedDate, 1)); };
  const handleNextDay = () => { if (!canGoNext) return; setSelectedDate(addDays(selectedDate, 1)); };
  const handleToday = () => setSelectedDate(new Date());

  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(monthStart);
  const calendarStart = startOfWeek(monthStart, { weekStartsOn: 1 });
  const calendarEnd = endOfWeek(monthEnd, { weekStartsOn: 1 });
  const calendarDays = eachDayOfInterval({ start: calendarStart, end: calendarEnd });

  return (
    <div className="animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div>
          <h2 className="font-['Cormorant_Garamond'] text-3xl font-light">{isWorker ? "Moj Raspored" : "Rezervacije"}</h2>
          <p className="text-[#9CA3AF]">{format(selectedDate, "EEEE, d. MMMM yyyy", { locale: sr })}</p>
          {isWorker && <p className="text-[10px] text-blue-400/60 mt-0.5">Prikaz narednih 7 dana</p>}
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {!isWorker && (
            <>
              <Button onClick={handleSendReminders} disabled={sendingReminders} variant="outline" className="border-[#2A2A2D] hover:bg-[var(--color-surface)] text-[#9CA3AF] hover:text-white" data-testid="send-reminders-btn">
                {sendingReminders ? <Loader2 className="w-4 h-4 mr-1.5 animate-spin" /> : <Bell className="w-4 h-4 mr-1.5" />}
                Podsetnici za sutra
              </Button>
              <Button 
                onClick={() => {
                  if (isPast) {
                    toast.error("Nije moguće kreirati rezervaciju u prošlosti.");
                    return;
                  }
                  setManualBookingOpen(true);
                }} 
                className="bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black font-medium" 
                data-testid="admin-new-reservation-btn"
              >
                <Plus className="w-4 h-4 mr-1" /> Nova Rezervacija
              </Button>
            </>
          )}
          <Button variant="outline" size="icon" onClick={handlePrevDay} disabled={!canGoPrev} className="border-[#2A2A2D] hover:bg-[var(--color-surface)] disabled:opacity-30" data-testid="prev-day-btn"><ChevronLeft className="w-4 h-4" /></Button>
          <Button variant="outline" onClick={handleToday} className="border-[#2A2A2D] hover:bg-[var(--color-surface)]" data-testid="today-btn">Danas</Button>
          <Button variant="outline" size="icon" onClick={handleNextDay} disabled={!canGoNext} className="border-[#2A2A2D] hover:bg-[var(--color-surface)] disabled:opacity-30" data-testid="next-day-btn"><ChevronRight className="w-4 h-4" /></Button>
        </div>
      </div>

      {!isWorker && (
        <div className="flex items-center gap-3 mb-4 flex-wrap">
          <div className="flex gap-1 bg-[var(--color-background)] rounded-lg p-1 w-fit" data-testid="view-tabs">
            <button onClick={() => setActiveTab("grid")} className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === "grid" ? "bg-[var(--color-primary)] text-black" : "text-[#9CA3AF] hover:text-white"}`} data-testid="tab-grid">
              <CalendarIcon className="w-4 h-4 inline mr-1.5" />Mreža{activeReservations.length > 0 && <span className="ml-1.5 text-xs opacity-70">({activeReservations.length})</span>}
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
      )}

      {!isWorker && (
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
      )}

      {/* MODAL ZA PREMEŠTANJE SA PADAJUĆIM MENIJEM I DATUMOM */}
      {!isWorker && (
        <Dialog open={!!rescheduleModal} onOpenChange={(v) => !v && setRescheduleModal(null)}>
          <DialogContent className="bg-[var(--color-surface)] border-[#2A2A2D] max-w-sm" data-testid="reschedule-modal">
            <DialogHeader>
              <DialogTitle className="text-white">Premesti termin?</DialogTitle>
              <DialogDescription className="text-[#9CA3AF]">
                Za klijenta: <strong className="text-white">{rescheduleModal?.res?.client_name}</strong>
              </DialogDescription>
            </DialogHeader>
            {rescheduleModal && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                    <p className="text-[10px] text-red-400 uppercase tracking-wider mb-1">Staro</p>
                    <p className="text-sm text-white font-medium">{rescheduleModal.oldTime}</p>
                    <p className="text-xs text-[#9CA3AF]">{rescheduleModal.oldWorker}</p>
                  </div>
                  <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3">
                    <p className="text-[10px] text-green-400 uppercase tracking-wider mb-1">Novo</p>
                    <p className="text-sm text-white font-medium">
                      {rescheduleModal.newDate ? format(new Date(rescheduleModal.newDate + "T00:00:00"), "dd.MM.yyyy") : ""}
                    </p>
                    <p className="text-xs text-[#9CA3AF]">{rescheduleModal.newWorker}</p>
                  </div>
                </div>

                {/* Padajući meni sa slotovima u 24h formatu */}
                <div className="space-y-1.5">
                  <label className="text-xs text-[#9CA3AF]">Novo vreme početka:</label>
                  <select
                    value={rescheduleModal.newTime}
                    onChange={(e) => setRescheduleModal({ ...rescheduleModal, newTime: e.target.value })}
                    className="w-full h-10 px-3 rounded-md bg-[var(--color-background)] border border-[#2A2A2D] text-white text-sm focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
                  >
                    {timeSlots.map((m) => {
                      const timeStr = mtt(m);
                      const isPastSlot = rescheduleModal.newDate === format(now, "yyyy-MM-dd") && m < nowMins;
                      return (
                        <option 
                          key={m} 
                          value={timeStr} 
                          disabled={isPastSlot} 
                          className={`bg-[var(--color-surface)] text-white ${isPastSlot ? "opacity-40 text-gray-500" : ""}`}
                        >
                          {timeStr} {isPastSlot ? "(Prošlo vreme)" : ""}
                        </option>
                      );
                    })}
                  </select>
                </div>

                <p className="text-xs text-[#6B7280]">Klijent će dobiti email obaveštenje o novom terminu.</p>
                <div className="flex gap-3">
                  <Button variant="outline" className="flex-1 border-[#2A2A2D]" onClick={() => setRescheduleModal(null)} disabled={rescheduling}>Otkaži</Button>
                  <Button className="flex-1 bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black font-medium" onClick={handleRescheduleConfirm} disabled={rescheduling} data-testid="reschedule-confirm-btn">
                    {rescheduling ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Check className="w-4 h-4 mr-1" />}
                    Potvrdi
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
      )}

      <Dialog open={!!selectedRes} onOpenChange={(v) => !v && setSelectedRes(null)}>
        <DialogContent className="bg-[var(--color-surface)] border-[#2A2A2D] max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <span className="font-mono text-[var(--color-primary)] text-sm bg-[var(--color-primary)]/10 px-2 py-0.5 rounded">#{selectedRes?.booking_id}</span>
              {selectedRes?.client_name}
              {selectedRes?.is_rescheduled && <RotateCcw className="w-3.5 h-3.5 text-amber-400" title="Premesten" />}
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
                      {block.gap > 0 && idx > 0 && <div className="text-[10px] text-[#6B7280] italic pl-1 py-0.5">Pauza ({block.gap} min)</div>}
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
              {!isWorker && (
                <div className="flex gap-2 pt-2 border-t border-[#2A2A2D]">
                  <button onClick={() => { setSelectedRes(null); openCancelDialog(selectedRes); }} className="flex-1 px-3 py-2 rounded-lg text-xs font-medium bg-red-500/10 text-red-400 hover:bg-red-500/20">Otkaži rezervaciju</button>
                  {!blacklist.includes(selectedRes.client_phone) ? (
                    <button onClick={() => handleBlacklist(selectedRes.client_phone)} className="flex-1 px-3 py-2 rounded-lg text-xs font-medium bg-red-500/10 text-red-400 hover:bg-red-500/20"><Ban className="w-3 h-3 inline mr-1" />Blokiraj</button>
                  ) : (
                    <button onClick={() => handleRemoveFromBlacklist(selectedRes.client_phone)} className="flex-1 px-3 py-2 rounded-lg text-xs font-medium bg-green-500/10 text-green-400 hover:bg-green-500/20"><Check className="w-3 h-3 inline mr-1" />Odblokiraj</button>
                  )}
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {activeTab === "grid" && (
        loading ? <div className="text-center py-12 text-[#9CA3AF]">Ucitavanje...</div> :
        displayWorkers.length === 0 ? (
          <div className="text-center py-12 bg-[var(--color-surface)] rounded-xl border border-[#2A2A2D]"><Users className="w-12 h-12 mx-auto text-[#9CA3AF] mb-4" /><p className="text-[#9CA3AF]">{isWorker ? "Nemate dodeljene smene" : "Nema aktivnih radnika"}</p></div>
        ) : (
          <div className="flex flex-col lg:flex-row gap-4 items-start">
            
            {/* LEFT SIDEBAR: Mini-Kalendar */}
            {!isWorker && (
              <div className="w-full lg:w-60 shrink-0 bg-[var(--color-surface)] p-3 rounded-xl border border-[#2A2A2D] space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-white flex items-center gap-1.5">
                    <CalendarDays className="w-3.5 h-3.5 text-[var(--color-primary)]" />
                    {format(currentMonth, "MMMM yyyy", { locale: sr })}
                  </span>
                  <div className="flex gap-1">
                    <button onClick={() => setCurrentMonth(subDays(startOfMonth(currentMonth), 1))} className="p-1 text-[#9CA3AF] hover:text-white rounded hover:bg-[#2A2A2D]">
                      <ChevronLeft className="w-3.5 h-3.5" />
                    </button>
                    <button onClick={() => setCurrentMonth(addDays(endOfMonth(currentMonth), 1))} className="p-1 text-[#9CA3AF] hover:text-white rounded hover:bg-[#2A2A2D]">
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {dragData && (
                  <div className="space-y-1.5 bg-[var(--color-primary)]/10 p-2 rounded-lg border border-[var(--color-primary)]/30">
                    <div className="text-[10px] text-[var(--color-primary)] font-semibold text-center">Spustite rezervaciju na željeni datum 👇</div>
                  </div>
                )}

                <div className="grid grid-cols-7 gap-1 text-center">
                  {["P", "U", "S", "Č", "P", "S", "N"].map((d, i) => (
                    <div key={i} className="text-[10px] text-[#6B7280] font-medium py-1">{d}</div>
                  ))}
                  {calendarDays.map((day, idx) => {
                    const isSelected = isSameDay(day, selectedDate);
                    const isCurrentDay = isSameDay(day, today);
                    const isBeforeToday = isBefore(day, today);
                    const formattedDateStr = format(day, "yyyy-MM-dd");
                    const isHoveredTarget = dateDropTarget === formattedDateStr;

                    return (
                      <div
                        key={idx}
                        onClick={() => setSelectedDate(day)}
                        onDragOver={(e) => handleDateDragOver(e, day)}
                        onDrop={(e) => handleDateDrop(e, day)}
                        data-testid={`mini-cal-day-${formattedDateStr}`}
                        className={`text-xs py-1.5 rounded-md cursor-pointer transition-all relative ${
                          isSelected ? "bg-[var(--color-primary)] text-black font-semibold" :
                          isCurrentDay ? "border border-[var(--color-primary)] text-[var(--color-primary)]" :
                          isBeforeToday ? "text-[#4B5563]" : "text-[#D1D5DB] hover:bg-[#2A2A2D]"
                        } ${isHoveredTarget ? "ring-2 ring-[var(--color-primary)] bg-[var(--color-primary)] text-white font-bold scale-110 z-10" : ""}`}
                      >
                        {format(day, "d")}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* MAIN GRID */}
            <div className="flex-1 w-full bg-[var(--color-surface)] rounded-xl border border-[#2A2A2D] overflow-hidden" data-testid="timeline-grid">
              <div className="overflow-auto max-h-[72vh]" ref={gridRef} data-testid="grid-body">
                <div className="flex sticky top-0 z-20 bg-[var(--color-surface)] border-b border-[#2A2A2D] w-full min-w-max">
                  <div className="w-16 flex-shrink-0 p-2 text-center text-[10px] text-[#6B7280] border-r border-[#2A2A2D] sticky left-0 z-30 bg-[var(--color-surface)]">Vreme</div>
                  {displayWorkers.map(w => (
                    <div key={w.id} className={`flex-1 min-w-[130px] flex-shrink-0 p-2 text-center border-r border-[#2A2A2D] last:border-r-0 transition-opacity ${isWorkerDimmed(w.id) ? "opacity-25" : ""}`}>
                      <div className="text-xs font-medium text-white truncate">{w.name}</div>
                      <div className="text-[10px] text-[#6B7280]">{w.work_start}-{w.work_end}</div>
                    </div>
                  ))}
                </div>
                <div className="relative w-full min-w-max">
                  {nowLineTop > 0 && nowLineTop < timeSlots.length * SLOT_HEIGHT && (
                    <div className="absolute left-0 right-0 z-[5] pointer-events-none" style={{ top: `${nowLineTop}px` }}>
                      <div className="flex items-center"><div className="w-2 h-2 rounded-full bg-red-500 -ml-1" /><div className="flex-1 h-px bg-red-500/60" /></div>
                    </div>
                  )}
                  {timeSlots.map((slotMin) => (
                    <div key={slotMin} className="flex border-b border-[#1E1E22]" style={{ height: `${SLOT_HEIGHT}px` }}>
                      <div className="w-16 flex-shrink-0 flex items-start justify-center pt-1 text-[10px] text-[#6B7280] border-r border-[#1E1E22] sticky left-0 z-10 bg-[var(--color-surface)]">{mtt(slotMin)}</div>
                      {displayWorkers.map(w => {
                        const blocks = buildWorkerBlocks(w.id);
                        const cellBlocks = blocks.filter(b => b.startMin >= slotMin && b.startMin < slotMin + 30);
                        const dimmed = isWorkerDimmed(w.id);
                        const isDropHere = !isWorker && dropTarget?.workerId === w.id && dropTarget?.slotMin === slotMin;
                        return (
                          <div
                            key={w.id}
                            className={`flex-1 min-w-[130px] flex-shrink-0 border-r border-[#1E1E22] last:border-r-0 relative transition-all ${dimmed ? "opacity-20 bg-red-900/10" : ""} ${isDropHere ? "bg-[var(--color-primary)]/10" : ""}`}
                            onDragOver={isWorker ? undefined : (e) => handleDragOver(e, w.id, slotMin)}
                            onDragLeave={isWorker ? undefined : () => setDropTarget(null)}
                            onDrop={isWorker ? undefined : (e) => handleDrop(e, w.id, slotMin)}
                            style={isWorker ? { pointerEvents: "auto" } : undefined}
                          >
                            {cellBlocks.map((block, bIdx) => {
                              const topOff = ((block.startMin - slotMin) / 30) * SLOT_HEIGHT;
                              const blockH = Math.max(((block.endMin - block.startMin) / 30) * SLOT_HEIGHT, 22);
                              const blockColor = block.color;
                              const isRescheduled = block.res.is_rescheduled;
                              const canDragThisBlock = !isWorker;
                              return (
                                <div
                                  key={bIdx}
                                  draggable={canDragThisBlock}
                                  onDragStart={canDragThisBlock ? (e) => handleDragStart(e, block.res, block) : undefined}
                                  onDragEnd={canDragThisBlock ? handleDragEnd : undefined}
                                  onClick={isWorker ? undefined : () => setSelectedRes(block.res)}
                                  className={`absolute left-1 right-1 rounded px-1.5 py-0.5 overflow-hidden transition-all ${
                                    isWorker
                                      ? "cursor-default select-none"
                                      : `cursor-grab hover:brightness-110 hover:shadow-lg ${dragData?.res?.id === block.res.id ? "opacity-50 ring-2 ring-[var(--color-primary)]" : ""}`
                                  }`}
                                  style={{
                                    top: `${topOff}px`,
                                    height: `${blockH}px`,
                                    backgroundColor: `${blockColor}18`,
                                    borderLeft: `3px solid ${blockColor}`,
                                    zIndex: 5,
                                  }}
                                  data-testid={`grid-block-${block.res.id}`}
                                >
                                  <div className="text-[10px] font-medium truncate flex items-center gap-1" style={{ color: blockColor }}>
                                    {isRescheduled && <RotateCcw className="w-2.5 h-2.5 shrink-0" />}
                                    {block.serviceName}
                                  </div>
                                  {blockH > 24 && <div className="text-[9px] text-[#9CA3AF] truncate leading-tight">{block.res.client_name}</div>}
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

          </div>
        )
      )}

      {activeTab === "archive" && (
        <div data-testid="archive-view">
          <div className="mb-4">
            <Input placeholder="Pretrazi po imenu, telefonu, ID-u..." value={archiveSearch} onChange={e => setArchiveSearch(e.target.value)} className="bg-[var(--color-surface)] border-[#2A2A2D] text-white" />
          </div>
          <div className="bg-[var(--color-surface)] rounded-xl border border-[#2A2A2D] overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="border-[#2A2A2D] hover:bg-transparent">
                  <TableHead className="text-[#9CA3AF]">ID / Datum</TableHead>
                  <TableHead className="text-[#9CA3AF]">Klijent</TableHead>
                  <TableHead className="text-[#9CA3AF]">Usluge i radnici</TableHead>
                  <TableHead className="text-[#9CA3AF]">Vreme</TableHead>
                  <TableHead className="text-[#9CA3AF]">Cena</TableHead>
                  <TableHead className="text-[#9CA3AF] text-right">Akcija</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredArchive.length === 0 ? (
                  <TableRow><TableCell colSpan={6} className="text-center py-8 text-[#9CA3AF]">Nema arhiviranih rezervacija</TableCell></TableRow>
                ) : (
                  filteredArchive.map(res => (
                    <TableRow key={res.id} className="border-[#2A2A2D] hover:bg-[var(--color-background)]/50">
                      <TableCell>
                        <span className="font-mono text-[var(--color-primary)] text-xs">#{res.booking_id}</span>
                        <div className="text-[10px] text-[#6B7280]">{res.date}</div>
                      </TableCell>
                      <TableCell>
                        <div className="text-white text-sm font-medium">{res.client_name}</div>
                        <div className="text-xs text-[#9CA3AF]">{res.client_phone}</div>
                      </TableCell>
                      <TableCell>
                        <div className="text-xs text-white">{res.service_names?.join(", ")}</div>
                        <div className="text-[10px] text-[#6B7280]">
                          {res.service_worker_pairs?.map(p => `${p.service_name} (${p.worker_name})`).join(" · ")}
                        </div>
                      </TableCell>
                      <TableCell className="text-xs text-[#9CA3AF]">{res.time} - {res.end_time}</TableCell>
                      <TableCell className="text-xs font-medium text-[var(--color-primary)]">{res.total_price ?? 0} π</TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="sm" onClick={() => setSelectedRes(res)} className="text-xs text-[#9CA3AF] hover:text-white">Detalji</Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      )}
    </div>
  );
};

export default CalendarView;
