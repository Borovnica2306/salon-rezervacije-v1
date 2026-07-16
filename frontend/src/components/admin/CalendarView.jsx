import React, { useState, useEffect } from "react";
import { toast } from "sonner";
import axios from "axios";
import { API, useAuth, useTenant, getTenantHeaders, getToken } from "../../App";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import {
  Calendar, Users, Clock, Ban, Check, ChevronLeft, ChevronRight,
  Plus, Bell, Loader2, Download, Phone, User, X
} from "lucide-react";
import { format, addDays, subDays, parseISO } from "date-fns";
import { sr } from "date-fns/locale";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription,
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
  const [settings, setSettings] = useState(null);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [cancelTarget, setCancelTarget] = useState(null);
  const [manualBookingOpen, setManualBookingOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("grid");
  const [archiveSearch, setArchiveSearch] = useState("");
  const [selectedRes, setSelectedRes] = useState(null);
  const [sendingReminders, setSendingReminders] = useState(false);

  const token = getToken();
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
            className="border-[#2A2A2D] hover:bg-[var(--color-surface)] text-[#9CA3AF] hover:text-white"
            data-testid="send-reminders-btn"
          >
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
          <Button
            onClick={handleExportCSV}
            variant="outline"
            size="sm"
            className="border-[#2A2A2D] hover:bg-[var(--color-surface)] text-[#9CA3AF] hover:text-white"
            data-testid="export-csv-btn"
          >
            <Download className="w-4 h-4 mr-1.5" />
            Export CSV
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
        <DialogContent className="bg-[var(--color-surface)] border-[#2A2A2D] max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <span className="font-mono text-[var(--color-primary)] text-sm bg-[var(--color-primary)]/10 px-2 py-0.5 rounded">#{selectedRes?.booking_id}</span>
              {selectedRes?.client_name}
            </DialogTitle>
            <DialogDescription className="text-[#9CA3AF]">{selectedRes?.time} - {selectedRes?.end_time} &middot; {selectedRes?.total_duration} min</DialogDescription>
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
                <button onClick={() => { handleTogglePayment(selectedRes.id); setSelectedRes(null); }} className={`flex-1 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${selectedRes.payment_status === "confirmed" || selectedRes.payment_status === "paid" ? "bg-green-600/20 text-green-400" : selectedRes.payment_status === "sent_for_verification" ? "bg-amber-500/15 text-amber-400" : "bg-[#1E1E22] text-[#9CA3AF]"}`} data-testid={`detail-payment-${selectedRes.id}`}>
                  {selectedRes.payment_status === "confirmed" || selectedRes.payment_status === "paid" ? "Plaćeno" : selectedRes.payment_status === "sent_for_verification" ? "Čeka proveru" : selectedRes.payment_status === "pending_pi_payment" ? "Čeka Pi uplatu" : "Čeka uplatu"}
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
          <div className="text-center py-12 bg-[var(--color-surface)] rounded-xl border border-[#2A2A2D]"><Users className="w-12 h-12 mx-auto text-[#9CA3AF] mb-4" /><p className="text-[#9CA3AF]">Nema aktivnih radnika</p></div>
        ) : (
          <div className="bg-[var(--color-surface)] rounded-xl border border-[#2A2A2D]" data-testid="timeline-grid">
            <div className="overflow-auto max-h-[70vh]" ref={gridRef} data-testid="grid-body">
              {/* Header - sticky top */}
              <div className="flex sticky top-0 z-20 bg-[var(--color-surface)] border-b border-[#2A2A2D]">
                <div className="w-16 flex-shrink-0 p-2 text-center text-[10px] text-[#6B7280] border-r border-[#2A2A2D] sticky left-0 z-30 bg-[var(--color-surface)]">Vreme</div>
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
                    <div className="w-16 flex-shrink-0 flex items-start justify-center pt-1 text-[10px] text-[#6B7280] border-r border-[#1E1E22] sticky left-0 z-10 bg-[var(--color-surface)]">{mtt(slotMin)}</div>
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
                    <TableRow key={res.id} className="border-[#2A2A2D] opacity-70 hover:opacity-100 cursor-pointer" onClick={() => setSelectedRes(res)} data-testid={`archive-row-${res.id}`}>
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
// Employees Page


export default ReservationsPage;
