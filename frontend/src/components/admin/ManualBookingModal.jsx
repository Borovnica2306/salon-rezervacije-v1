import React, { useState, useEffect } from "react";
import { toast } from "sonner";
import axios from "axios";
import { API, useTenant, getTenantHeaders, getToken } from "../../App";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { X, Plus, Edit2, AlertTriangle } from "lucide-react";
import { format, addDays } from "date-fns";
import { sr } from "date-fns/locale";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "../ui/dialog";

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

  const token = getToken();
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
      }, { headers });
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
      <DialogContent className="bg-[var(--color-surface)] border-[#2A2A2D] max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <Plus className="w-5 h-5 text-[var(--color-primary)]" />
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
            <div key={s} className={`h-1 flex-1 rounded-full transition-colors ${s <= step ? "bg-[var(--color-primary)]" : "bg-[#2A2A2D]"}`} />
          ))}
        </div>

        {/* STEP 1: Services + Workers */}
        {step === 1 && (
          <div className="space-y-4">
            {/* Current pairs */}
            {selectedPairs.length > 0 && (
              <div className="space-y-2">
                {selectedPairs.map((pair, idx) => (
                  <div key={idx} className="flex items-center justify-between bg-[var(--color-background)] rounded-lg px-3 py-2" data-testid={`manual-pair-${idx}`}>
                    <div className="text-sm">
                      <span className="text-white">{pair.service.name}</span>
                      <span className="text-[#9CA3AF] mx-1">&rarr;</span>
                      <span className="text-[var(--color-primary)]">{pair.worker.name}</span>
                      <span className="text-[#6B7280] text-xs ml-2">({pair.service.duration} min)</span>
                    </div>
                    <button onClick={() => removePair(idx)} className="text-[#9CA3AF] hover:text-red-400 p-1" data-testid={`remove-pair-${idx}`}>
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
                <div className="text-xs text-[#9CA3AF] text-right">
                  Ukupno: {totalDuration} min &middot; {totalPrice} π
                </div>
              </div>
            )}

            {/* Add new pair */}
            <div className="bg-[var(--color-background)] rounded-lg p-3 space-y-3">
              <select
                value={tempServiceId}
                onChange={e => { setTempServiceId(e.target.value); setTempWorkerId(""); }}
                className="w-full bg-[#1E1E22] border border-[#2A2A2D] rounded-lg px-3 py-2 text-sm text-white min-h-[48px]"
                data-testid="manual-service-select"
              >
                <option value="">Izaberite uslugu...</option>
                {services.map(s => (
                  <option key={s.id} value={s.id}>{s.name} ({s.duration} min - {s.price} π)</option>
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
                className="w-full bg-[#1E1E22] border border-[#2A2A2D] hover:bg-[#2A2A2D] text-[var(--color-primary)] disabled:opacity-40 min-h-[48px]"
                size="sm"
                data-testid="manual-add-pair-btn"
              >
                <Plus className="w-4 h-4 mr-1" /> Dodaj uslugu
              </Button>
            </div>

            <Button
              onClick={handleNextStep}
              disabled={!canProceedStep1}
              className="w-full bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black font-medium disabled:opacity-40 min-h-[48px]"
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
                Dostupni termini {loadingSlots && <span className="text-[var(--color-primary)]">(učitavanje...)</span>}
              </label>
              {availableSlots.length > 0 ? (
                <div className="grid grid-cols-4 gap-2 max-h-48 overflow-y-auto">
                  {availableSlots.map(slot => (
                    <button
                      key={slot}
                      onClick={() => setSelectedTime(slot)}
                      className={`px-2 py-2 text-xs rounded-lg border transition-colors ${
                        selectedTime === slot
                          ? "bg-[var(--color-primary)] text-black border-[var(--color-primary)] font-medium"
                          : "bg-[#1E1E22] border-[#2A2A2D] text-[#E5E7EB] hover:border-[var(--color-primary)]/50"
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
                <div className="mt-3 bg-[var(--color-background)] rounded-lg p-3 space-y-1">
                  {detail.time_blocks?.map((b, i) => (
                    <div key={i}>
                      {b.gap > 0 && (
                        <div className="flex items-center gap-1 text-[10px] text-[#6B7280] italic pl-1 py-0.5">
                          ☕ Pauza ({b.gap} min)
                        </div>
                      )}
                      <div className="flex justify-between text-xs">
                        <span className="text-white">{b.start_time}-{b.end_time} {selectedPairs[i]?.service.name}</span>
                        <span className="text-[var(--color-primary)]">{selectedPairs[i]?.worker.name}</span>
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
                className="flex-1 bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black font-medium disabled:opacity-40 min-h-[48px]"
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
            <div className="bg-[var(--color-background)] rounded-lg p-3 text-sm space-y-1">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[#9CA3AF] text-xs uppercase tracking-wider">Pregled</span>
                <button
                  onClick={() => setStep(1)}
                  className="flex items-center gap-1 text-xs text-[var(--color-primary)] hover:text-[#B89970] transition-colors"
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
                    <span className="text-[#9CA3AF]">{pair.service.name} <span className="text-[var(--color-primary)]">{pair.worker.name}</span></span>
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
                <span className="text-[var(--color-primary)] font-medium">{totalPrice} π</span>
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
                className="flex-1 bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black font-medium disabled:opacity-40 min-h-[48px]"
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


export default ManualBookingModal;
