import { useState, useEffect, useMemo } from "react";
import { toast } from "sonner";
import axios from "axios";
import { API, useTenant, getTenantHeaders } from "../App";
import { Clock, Scissors, User, Phone, Calendar, ChevronRight, ChevronLeft, Check, X, Search, ChevronDown, Ban, Copy, Flower2, Gem, Sparkles, Zap, Droplet, Eye, Pencil, Mail, Shield, Plus } from "lucide-react";
import { PhoneInput, isValidPhone } from "../components/PhoneInput";
import { usePiAuth } from "../context/PiAuthContext";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { format, addDays, isSameDay } from "date-fns";
import { sr } from "date-fns/locale";
import { useParams } from "react-router-dom";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";

const PHONE_PREFIX = "+381";

function fallbackCopy(text) {
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.style.cssText = "position:fixed;opacity:0;left:-9999px";
  document.body.appendChild(ta);
  ta.select();
  document.execCommand("copy");
  document.body.removeChild(ta);
  toast.success("Kopirano!");
}

const BookingPage = () => {
  const tenant = useTenant();
  const { slug } = useParams();
  const { piUser, loading: piLoading, isSandbox } = usePiAuth();
  const tHeaders = getTenantHeaders(tenant?.tenant_id);
  const [step, setStep] = useState(1);
  const [services, setServices] = useState([]);
  const [workers, setWorkers] = useState([]);
  const [settings, setSettings] = useState(null);
  const [categories, setCategories] = useState([]);
  
  // Booking state
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedServices, setSelectedServices] = useState([]);
  // Map of serviceId -> workerId
  const [serviceWorkerMap, setServiceWorkerMap] = useState({});
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedTime, setSelectedTime] = useState(null);
  const [availableSlots, setAvailableSlots] = useState([]);
  const [dateSlotCounts, setDateSlotCounts] = useState({});
  const [clientPhone, setClientPhone] = useState("");
  const [clientEmail, setClientEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [blacklistError, setBlacklistError] = useState(false);
  const [bookingComplete, setBookingComplete] = useState(false);
  const [bookingDetails, setBookingDetails] = useState(null);
  const [piPaymentPending, setPiPaymentPending] = useState(false);
  const [piPaymentData, setPiPaymentData] = useState(null);
  const [showAddService, setShowAddService] = useState(false);

  // My Reservations state
  const [showMyReservations, setShowMyReservations] = useState(false);
  const [lookupPhone, setLookupPhone] = useState("");
  const [myReservations, setMyReservations] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const getE164Phone = (phone) => phone;

  const isValidEmail = (email) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  // Calculate totals
  const totalDuration = selectedServices.reduce((sum, s) => sum + s.duration, 0) + Math.max(0, selectedServices.length - 1) * 15;
  const totalPrice = selectedServices.reduce((sum, s) => sum + s.price, 0);

  // Check if all services have workers assigned
  const allServicesHaveWorkers = useMemo(() => {
    return selectedServices.length > 0 && 
           selectedServices.every(s => serviceWorkerMap[s.id]);
  }, [selectedServices, serviceWorkerMap]);

  // Get workers who can perform a specific service
  const getWorkersForService = (serviceId) => {
    return workers.filter(w => w.services.includes(serviceId));
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (allServicesHaveWorkers && selectedDate) {
      fetchAvailableSlots();
    } else {
      setAvailableSlots([]);
    }
  }, [serviceWorkerMap, selectedDate, allServicesHaveWorkers]);

  const fetchData = async () => {
    try {
      const [servicesRes, workersRes, settingsRes, categoriesRes] = await Promise.all([
        axios.get(`${API}/services`, { headers: tHeaders }),
        axios.get(`${API}/workers`, { headers: tHeaders }),
        axios.get(`${API}/settings`, { headers: tHeaders }),
        axios.get(`${API}/categories`, { headers: tHeaders }),
      ]);
      setServices(servicesRes.data);
      setWorkers(workersRes.data);
      setSettings(settingsRes.data);
      setCategories(categoriesRes.data);
    } catch (error) {
      toast.error("Greška pri učitavanju podataka");
    }
  };

  const fetchAvailableSlots = async () => {
    if (!selectedDate || !allServicesHaveWorkers) return;
    
    try {
      const pairs = selectedServices.map(s => ({
        service_id: s.id,
        worker_id: serviceWorkerMap[s.id]
      }));
      
      const response = await axios.post(`${API}/reservations/available-slots`, {
        service_worker_pairs: pairs,
        date: format(selectedDate, "yyyy-MM-dd"),
      }, { headers: tHeaders });
      setAvailableSlots(response.data.slots || []);
    } catch (error) {
      console.error("Error fetching slots:", error);
      setAvailableSlots([]);
    }
  };

  const fetchDateAvailability = async () => {
    if (!allServicesHaveWorkers) return;
    const pairs = selectedServices.map(s => ({
      service_id: s.id,
      worker_id: serviceWorkerMap[s.id]
    }));
    const counts = {};
    const requests = dates.map(d => {
      const key = format(d, "yyyy-MM-dd");
      return axios.post(`${API}/reservations/available-slots`, {
        service_worker_pairs: pairs,
        date: key,
      }, { headers: tHeaders }).then(r => { counts[key] = (r.data.slots || []).length; })
        .catch(() => { counts[key] = 0; });
    });
    await Promise.all(requests);
    setDateSlotCounts(counts);
  };

  useEffect(() => {
    if (step === 3 && allServicesHaveWorkers) {
      setDateSlotCounts({});
      fetchDateAvailability();
    }
  }, [step, allServicesHaveWorkers]);

  const handleServiceToggle = (service) => {
    setSelectedServices(prev => {
      const exists = prev.find(s => s.id === service.id);
      if (exists) {
        // Remove service and its worker assignment
        setServiceWorkerMap(map => {
          const newMap = { ...map };
          delete newMap[service.id];
          return newMap;
        });
        return prev.filter(s => s.id !== service.id);
      }
      return [...prev, service];
    });
    setSelectedTime(null);
  };

  const handleWorkerSelect = (serviceId, workerId) => {
    setServiceWorkerMap(prev => ({
      ...prev,
      [serviceId]: workerId
    }));
    setSelectedTime(null);
  };

  const removeServiceFromReview = (serviceId) => {
    setServiceWorkerMap(prev => {
      const newMap = { ...prev };
      delete newMap[serviceId];
      return newMap;
    });
    setSelectedServices(prev => {
      const updated = prev.filter(s => s.id !== serviceId);
      if (updated.length === 0) {
        setStep(1);
        setSelectedCategory(null);
        setSelectedDate(null);
        setSelectedTime(null);
      }
      return updated;
    });
    setSelectedTime(null);
  };

  const handleSubmit = async () => {
    if (!piUser?.username || !isValidPhone(clientPhone) || !isValidEmail(clientEmail)) {
      toast.error("Molimo unesite validan broj telefona i email adresu");
      return;
    }

    setIsSubmitting(true);
    try {
      const pairs = selectedServices.map(s => ({
        service_id: s.id,
        worker_id: serviceWorkerMap[s.id]
      }));
      
      const response = await axios.post(`${API}/reservations`, {
        service_worker_pairs: pairs,
        date: format(selectedDate, "yyyy-MM-dd"),
        time: selectedTime,
        client_name: `@${piUser.username}`,
        client_phone: getE164Phone(clientPhone),
        client_email: clientEmail.trim().toLowerCase(),
        pi_username: piUser.username,
        pi_uid: piUser.uid,
      }, { headers: tHeaders });
      
      const booking = response.data;
      setBookingDetails(booking);

      if (booking.payment_status === "pending_pi_payment" && booking.total_price > 0) {
        initiatePiPayment(booking);
      } else {
        setBookingComplete(true);
        toast.success("Rezervacija uspešno kreirana!");
      }
    } catch (error) {
      const detail = error.response?.data?.detail || "";
      if (detail.toLowerCase().includes("crn") || detail.toLowerCase().includes("blacklist") || detail.toLowerCase().includes("blokiran")) {
        setBlacklistError(true);
      } else {
        toast.error(detail || "Greška pri kreiranju rezervacije");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const initiatePiPayment = (booking) => {
    const totalPi = booking.total_price;
    const serviceName = booking.service_names?.join(", ") || "Usluga";
    const memo = `Rezervacija ${booking.booking_id} - ${serviceName}`;

    if (isSandbox) {
      setPiPaymentData({ booking, totalPi, serviceName, memo });
      setPiPaymentPending(true);
      return;
    }

    // Production Pi SDK
    try {
      window.Pi.createPayment({
        amount: totalPi,
        memo,
        metadata: { booking_id: booking.booking_id, tenant_id: tenant?.tenant_id },
      }, {
        onReadyForServerApproval: async (paymentId) => {
          console.log("[Pi] Ready for server approval:", paymentId);
          try {
            await axios.post(`${API}/payments/approve`, {
              paymentId,
              booking_id: booking.booking_id,
              is_sandbox: false,
            }, { headers: tHeaders });
          } catch (err) {
            console.error("[Pi] Server approve failed:", err);
          }
        },
        onReadyForServerCompletion: async (paymentId, txid) => {
          console.log("[Pi] Ready for completion:", paymentId, txid);
          try {
            await axios.post(`${API}/payments/complete`, {
              paymentId,
              txid,
              booking_id: booking.booking_id,
              is_sandbox: false,
            }, { headers: tHeaders });
            setBookingComplete(true);
            setPiPaymentPending(false);
            toast.success("Pi plaćanje uspešno!");
          } catch (err) {
            console.error("[Pi] Server complete failed:", err);
            toast.error("Greška pri potvrdi plaćanja");
          }
        },
        onCancel: (paymentId) => {
          console.log("[Pi] Payment cancelled:", paymentId);
          toast.error("Plaćanje otkazano");
          setPiPaymentPending(false);
        },
        onError: (error, payment) => {
          console.error("[Pi] Payment error:", error, payment);
          toast.error("Greška pri plaćanju");
          setPiPaymentPending(false);
        },
      });
    } catch (err) {
      console.error("[Pi] createPayment failed:", err);
      toast.error("Pi SDK greška");
    }
  };

  const handleSandboxApprove = async () => {
    const fakePaymentId = `sandbox_pay_${Date.now()}`;
    console.log("[Pi Sandbox] Payment approved, paymentId:", fakePaymentId);

    try {
      await axios.post(`${API}/payments/approve`, {
        paymentId: fakePaymentId,
        booking_id: piPaymentData.booking.booking_id,
        is_sandbox: true,
      }, { headers: tHeaders });
    } catch (err) {
      console.error("[Pi Sandbox] Approve call failed:", err);
    }

    setPiPaymentPending(false);
    setTimeout(async () => {
      try {
        await axios.post(`${API}/payments/complete`, {
          paymentId: fakePaymentId,
          txid: `sandbox_tx_${Date.now()}`,
          booking_id: piPaymentData.booking.booking_id,
          is_sandbox: true,
        }, { headers: tHeaders });
      } catch (err) {
        console.error("[Pi Sandbox] Complete call failed:", err);
      }
      setBookingComplete(true);
      toast.success("Pi plaćanje uspešno! (Sandbox)");
    }, 1000);
  };

  const handleSandboxCancel = () => {
    setPiPaymentPending(false);
    toast.error("Plaćanje otkazano (Sandbox)");
  };

  const resetBooking = () => {
    setStep(1);
    setSelectedCategory(null);
    setSelectedServices([]);
    setServiceWorkerMap({});
    setSelectedDate(null);
    setSelectedTime(null);
    setClientPhone("");
    setClientEmail("");
    setPiPaymentPending(false);
    setPiPaymentData(null);
    setBookingComplete(false);
    setBookingDetails(null);
    setBlacklistError(false);
  };

  // My Reservations functions
  const searchMyReservations = async () => {
    if (!isValidPhone(lookupPhone)) {
      toast.error("Unesite validan broj telefona");
      return;
    }

    setIsSearching(true);
    setHasSearched(true);
    try {
      const response = await axios.post(`${API}/my-reservations`, {
        phone: getE164Phone(lookupPhone),
      }, { headers: tHeaders });
      setMyReservations(response.data);
    } catch (error) {
      toast.error("Greška pri pretraživanju");
      setMyReservations([]);
    } finally {
      setIsSearching(false);
    }
  };

  const cancelMyReservation = async (reservationId) => {
    try {
      await axios.put(`${API}/my-reservations/${reservationId}/cancel`, {
        phone: lookupPhone,
      }, { headers: tHeaders });
      toast.success("Rezervacija je uspešno otkazana");
      searchMyReservations();
    } catch (error) {
      const message = error.response?.data?.detail || "Greška pri otkazivanju";
      toast.error(message);
    }
  };

  const reportPayment = async (reservationId) => {
    try {
      await axios.patch(`${API}/reservations/${reservationId}/report-payment`, {}, { headers: tHeaders });
      toast.success("Uplata prijavljena! Salon će proveriti.");
      searchMyReservations();
    } catch (error) {
      const message = error.response?.data?.detail || "Greška pri prijavi uplate";
      toast.error(message);
    }
  };

  const closeMyReservations = () => {
    setShowMyReservations(false);
    setLookupPhone("");
    setMyReservations([]);
    setHasSearched(false);
  };

  // Check if selected slot is "urgent" (within 12 hours)
  const isUrgentSlot = useMemo(() => {
    if (!selectedDate || !selectedTime) return false;
    const slotDate = new Date(
      selectedDate.getFullYear(),
      selectedDate.getMonth(),
      selectedDate.getDate(),
      parseInt(selectedTime.split(":")[0]),
      parseInt(selectedTime.split(":")[1])
    );
    const hoursUntil = (slotDate - new Date()) / (1000 * 60 * 60);
    return hoursUntil > 0 && hoursUntil < 12;
  }, [selectedDate, selectedTime]);

  // Generate next 30 days
  const dates = Array.from({ length: 30 }, (_, i) => addDays(new Date(), i));

  // Group services by category
  const servicesByCategory = services.reduce((acc, service) => {
    if (!acc[service.category]) acc[service.category] = [];
    acc[service.category].push(service);
    return acc;
  }, {});

  const categoryLabels = Object.fromEntries(
    categories.map(c => [c.key, c.label])
  );

  const categoryImages = {
    hair: "https://images.unsplash.com/photo-1675034741473-afed58a142e8?w=400&q=80",
    massage: "https://images.unsplash.com/photo-1600334089648-b0d9d3028eb2?w=400&q=80",
    nails: "https://images.unsplash.com/photo-1659391542239-9648f307c0b1?w=400&q=80",
    makeup: "https://images.unsplash.com/photo-1487412947147-5cebf100ffc2?w=400&q=80",
    depilation: "https://images.unsplash.com/photo-1609840533741-62c180d0be79?w=400&q=80",
    cosmetics: "https://images.unsplash.com/photo-1761718210055-e83ca7e2c9ad?w=400&q=80",
    eyebrows: "https://images.unsplash.com/photo-1735151225764-eac694642dbf?w=400&q=80",
  };

  const CATEGORY_ICONS = {
    hair: Scissors,
    massage: Flower2,
    nails: Gem,
    makeup: Sparkles,
    depilation: Zap,
    cosmetics: Droplet,
    eyebrows: Eye,
  };

  // Get worker names for summary
  const getWorkerName = (workerId) => {
    const worker = workers.find(w => w.id === workerId);
    return worker?.name || "";
  };

  // --- Confirmation page helpers ---
  const CATEGORY_EMOJI = {
    hair: "\u2702\uFE0F",
    massage: "\uD83D\uDC86",
    nails: "\uD83D\uDC85",
    makeup: "\uD83D\uDC84",
    depilation: "\uD83E\uDEAE",
    cosmetics: "\uD83E\uDDF4",
    eyebrows: "\uD83D\uDC41\uFE0F",
  };

  const buildTimelineItems = () => {
    const blocks = bookingDetails?.worker_time_blocks || [];
    const pairs = bookingDetails?.service_worker_pairs || [];
    if (!blocks.length) return [];
    const items = [];
    blocks.forEach((block, idx) => {
      const pair = pairs[idx];
      const serviceData = services.find(s => s.id === block.service_id);
      const category = serviceData?.category || "hair";
      if (block.gap > 0 && idx > 0) {
        items.push({
          type: "buffer",
          startTime: blocks[idx - 1].end_time,
          endTime: block.start_time,
          duration: block.gap,
        });
      }
      items.push({
        type: "service",
        startTime: block.start_time,
        endTime: block.end_time,
        serviceName: pair?.service_name || "Usluga",
        workerName: pair?.worker_name || "",
        emoji: CATEGORY_EMOJI[category] || "\uD83D\uDC88",
        price: pair?.price || 0,
      });
    });
    return items;
  };

  const getGoogleCalendarUrl = () => {
    const d = bookingDetails.date.replace(/-/g, "");
    const st = bookingDetails.time.replace(":", "") + "00";
    const et = bookingDetails.end_time.replace(":", "") + "00";
    const title = `Termin - ${settings?.salon_name || "Beauty Salon"}`;
    const svcList = bookingDetails.service_names?.join(", ") || "";
    const desc = `Usluge: ${svcList}\nID: #${bookingDetails.booking_id}`;
    return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(title)}&dates=${d}T${st}/${d}T${et}&details=${encodeURIComponent(desc)}&ctz=Europe/Belgrade`;
  };

  const downloadICS = () => {
    const d = bookingDetails.date.replace(/-/g, "");
    const st = bookingDetails.time.replace(":", "") + "00";
    const et = bookingDetails.end_time.replace(":", "") + "00";
    const title = `Termin - ${settings?.salon_name || "Beauty Salon"}`;
    const svcList = bookingDetails.service_names?.join(", ") || "";
    const now = new Date().toISOString().replace(/[-:]/g, "").split(".")[0] + "Z";
    const ics = [
      "BEGIN:VCALENDAR",
      "VERSION:2.0",
      "PRODID:-//SalonBooking//RS",
      "BEGIN:VEVENT",
      `DTSTART;TZID=Europe/Belgrade:${d}T${st}`,
      `DTEND;TZID=Europe/Belgrade:${d}T${et}`,
      `DTSTAMP:${now}`,
      `SUMMARY:${title}`,
      `DESCRIPTION:Usluge: ${svcList}\\nID: #${bookingDetails.booking_id}`,
      "END:VEVENT",
      "END:VCALENDAR",
    ].join("\r\n");
    const blob = new Blob([ics], { type: "text/calendar;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `rezervacija-${bookingDetails.booking_id}.ics`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Sandbox Pi Wallet Modal
  const SandboxPaymentModal = () => {
    if (!piPaymentPending || !piPaymentData) return null;
    const { totalPi, serviceName, booking } = piPaymentData;
    return (
      <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" data-testid="sandbox-payment-modal">
        <div className="bg-[var(--color-surface)] border border-[#2A2A2D] rounded-2xl w-full max-w-sm overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-indigo-600 px-6 py-4 text-center">
            <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center mx-auto mb-2">
              <span className="text-xl font-bold text-white">π</span>
            </div>
            <h3 className="text-white font-medium text-lg">Pi Wallet</h3>
            <span className="text-white/60 text-[10px] px-2 py-0.5 bg-white/10 rounded-full">SANDBOX</span>
          </div>
          {/* Body */}
          <div className="px-6 py-5 space-y-4">
            <div className="text-center">
              <p className="text-[#9CA3AF] text-sm mb-1">{"Odobriti plaćanje?"}</p>
              <p className="text-3xl font-bold text-white">{totalPi} <span className="text-lg text-purple-400">π</span></p>
            </div>
            <div className="bg-[var(--color-background)] rounded-lg p-3 space-y-1.5">
              <div className="flex justify-between text-sm">
                <span className="text-[#6B7280]">Usluga</span>
                <span className="text-white text-right max-w-[60%] truncate">{serviceName}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-[#6B7280]">Rezervacija</span>
                <span className="text-white font-mono">#{booking.booking_id}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-[#6B7280]">Primalac</span>
                <span className="text-white">@salon</span>
              </div>
            </div>
          </div>
          {/* Actions */}
          <div className="px-6 pb-6 flex gap-3">
            <Button
              onClick={handleSandboxCancel}
              variant="outline"
              className="flex-1 border-[#2A2A2D] min-h-[48px]"
              data-testid="sandbox-cancel-btn"
            >
              {"Otkaži"}
            </Button>
            <Button
              onClick={handleSandboxApprove}
              className="flex-1 bg-purple-600 hover:bg-purple-700 text-white min-h-[48px] font-medium"
              data-testid="sandbox-approve-btn"
            >
              {"Odobri plaćanje"}
            </Button>
          </div>
        </div>
      </div>
    );
  };

  if (piLoading) {
    return (
      <div className="min-h-screen bg-transparent flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-[#9CA3AF] text-sm">{"Povezivanje sa Pi mrežom..."}</p>
        </div>
      </div>
    );
  }

  if (bookingComplete && bookingDetails) {
    const timelineItems = buildTimelineItems();
    const hasTimeline = timelineItems.length > 0;

    return (
      <div className="min-h-screen bg-transparent flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-[var(--color-surface)] rounded-2xl border border-[#2A2A2D] p-8 text-center animate-fade-in">
          <div className="w-16 h-16 rounded-full bg-[var(--color-primary)]/20 flex items-center justify-center mx-auto mb-6">
            <Check className="w-8 h-8 text-[var(--color-primary)]" />
          </div>
          <h1 className="font-['Cormorant_Garamond'] text-3xl font-light mb-2">Rezervacija Potvrđena</h1>

          {/* Booking ID with Copy */}
          {bookingDetails.booking_id && (
            <button
              onClick={() => {
                const text = bookingDetails.booking_id;
                try {
                  if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(text).then(() => {
                      toast.success("Kopirano!");
                    }).catch(() => {
                      fallbackCopy(text);
                    });
                  } else {
                    fallbackCopy(text);
                  }
                } catch {
                  fallbackCopy(text);
                }
              }}
              className="inline-flex items-center gap-2 bg-[var(--color-primary)]/10 border border-[var(--color-primary)]/30 rounded-lg px-4 py-2.5 mb-4 hover:bg-[var(--color-primary)]/20 transition-colors active:scale-95"
              data-testid="success-booking-id"
            >
              <span className="text-[#9CA3AF] text-sm">Vaš ID: </span>
              <span className="font-mono font-bold text-[var(--color-primary)] text-lg">#{bookingDetails.booking_id}</span>
              <Copy className="w-4 h-4 text-[var(--color-primary)] opacity-70" />
            </button>
          )}

          <p className="text-[#9CA3AF] mb-6">Hvala vam na rezervaciji!</p>

          {/* Date & Total Info */}
          <div className="bg-[var(--color-background)] rounded-xl p-5 text-left mb-4">
            <div className="flex justify-between mb-3">
              <span className="text-[#9CA3AF] text-sm">Datum:</span>
              <span className="font-medium text-sm">{bookingDetails.date}</span>
            </div>
            <div className="flex justify-between mb-3">
              <span className="text-[#9CA3AF] text-sm">Vreme:</span>
              <span className="font-medium text-sm">{bookingDetails.time} - {bookingDetails.end_time}</span>
            </div>
            <div className="flex justify-between mb-3">
              <span className="text-[#9CA3AF] text-sm">Trajanje:</span>
              <span className="font-medium text-sm">{bookingDetails.total_duration} min</span>
            </div>
            <div className="flex justify-between mb-3">
              <span className="text-[#9CA3AF] text-sm">Telefon:</span>
              <span className="font-medium text-sm">{bookingDetails.client_phone}</span>
            </div>
            <div className="flex justify-between mb-3">
              <span className="text-[#9CA3AF] text-sm">Email:</span>
              <span className="font-medium text-sm">{bookingDetails.client_email}</span>
            </div>
            <div className="border-t border-[#2A2A2D] pt-3 flex justify-between">
              <span className="text-[#9CA3AF] text-sm">Ukupno:</span>
              <span className="font-semibold text-[var(--color-primary)]">{bookingDetails.total_price ?? 0} π</span>
            </div>
          </div>

          {/* Visual Timeline */}
          <div className="bg-[var(--color-background)] rounded-xl p-5 text-left mb-4" data-testid="service-timeline">
            <span className="text-[#9CA3AF] text-xs uppercase tracking-wider">Vaš raspored</span>
            <div className="mt-4 relative">
              {/* Timeline vertical line */}
              <div className="absolute left-[19px] top-2 bottom-2 w-px bg-[#2A2A2D]" />

              <div className="space-y-0">
                {timelineItems.map((item, idx) => (
                  item.type === "service" ? (
                    <div key={idx} className="relative flex items-start gap-3 py-2.5" data-testid={`timeline-service-${idx}`}>
                      {/* Dot */}
                      <div className="relative z-10 w-[38px] h-[38px] rounded-full bg-[var(--color-primary)]/15 border border-[var(--color-primary)]/40 flex items-center justify-center flex-shrink-0 text-base">
                        {item.emoji}
                      </div>
                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm text-white">{item.serviceName}</div>
                        <div className="text-xs text-[#9CA3AF] mt-0.5">
                          {item.startTime} - {item.endTime} &middot; {item.workerName}
                        </div>
                      </div>
                      <div className="text-xs text-[var(--color-primary)] font-medium flex-shrink-0 pt-0.5">
                        {item.price ?? 0} π
                      </div>
                    </div>
                  ) : (
                    <div key={idx} className="relative flex items-center gap-3 py-1.5" data-testid={`timeline-buffer-${idx}`}>
                      {/* Buffer dot */}
                      <div className="relative z-10 w-[38px] h-[38px] rounded-full bg-[#1E1E22] border border-dashed border-[#3A3A3E] flex items-center justify-center flex-shrink-0 text-sm">
                        ☕
                      </div>
                      <div className="flex-1">
                        <div className="text-xs text-[#6B7280] italic">
                          Pauza {item.startTime} - {item.endTime} ({item.duration} min)
                        </div>
                      </div>
                    </div>
                  )
                ))}

                {/* Fallback: no timeline blocks (single service) */}
                {!hasTimeline && bookingDetails.service_worker_pairs?.map((pair, idx) => (
                  <div key={idx} className="relative flex items-start gap-3 py-2.5">
                    <div className="relative z-10 w-[38px] h-[38px] rounded-full bg-[var(--color-primary)]/15 border border-[var(--color-primary)]/40 flex items-center justify-center flex-shrink-0 text-base">
                      {CATEGORY_EMOJI[services.find(s => s.id === pair.service_id)?.category] || "\uD83D\uDC88"}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm text-white">{pair.service_name}</div>
                      <div className="text-xs text-[#9CA3AF] mt-0.5">
                        {bookingDetails.time} - {bookingDetails.end_time} &middot; {pair.worker_name}
                      </div>
                    </div>
                    <div className="text-xs text-[var(--color-primary)] font-medium flex-shrink-0 pt-0.5">
                      {pair.price ?? 0} π
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Add to Calendar */}
          <div className="flex gap-2 mb-4" data-testid="add-to-calendar">
            <a
              href={getGoogleCalendarUrl()}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 flex items-center justify-center gap-2 bg-[#1E1E22] hover:bg-[#2A2A2D] border border-[#2A2A2D] rounded-xl py-3 px-3 transition-colors text-sm"
              data-testid="google-calendar-btn"
            >
              <Calendar className="w-4 h-4 text-[var(--color-primary)]" />
              <span className="text-[#E5E7EB]">Google Calendar</span>
            </a>
            <button
              onClick={downloadICS}
              className="flex-1 flex items-center justify-center gap-2 bg-[#1E1E22] hover:bg-[#2A2A2D] border border-[#2A2A2D] rounded-xl py-3 px-3 transition-colors text-sm"
              data-testid="ics-download-btn"
            >
              <Calendar className="w-4 h-4 text-[var(--color-primary)]" />
              <span className="text-[#E5E7EB]">Apple / Outlook</span>
            </button>
          </div>

          {/* Confirmation */}
          <div className="bg-green-900/20 border border-green-500/30 rounded-xl p-5 mb-6 text-center" data-testid="pi-confirmation-section">
            <Check className="w-8 h-8 text-green-400 mx-auto mb-2" />
            <h3 className="text-green-400 font-medium mb-1">{"Rezervacija potvrđena"}</h3>
            <p className="text-[#9CA3AF] text-sm leading-relaxed">
              {"Vaš termin je uspešno zakazan. Dobićete obaveštenje sa detaljima."}
            </p>
          </div>

          <Button
            onClick={resetBooking}
            className="w-full bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black font-medium py-6"
            data-testid="new-booking-btn"
          >
            Nova Rezervacija
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-transparent">
      <SandboxPaymentModal />
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-[#2A2A2D]">
        <div className="max-w-lg mx-auto px-4 py-3 flex items-center justify-between">
          <span className="text-[#9CA3AF] text-xs">Beauty Studio Bor</span>
          <button
            onClick={() => setShowMyReservations(true)}
            className="text-[#9CA3AF] text-xs hover:text-[var(--color-primary)] transition-colors flex items-center gap-1"
            data-testid="my-reservations-btn"
          >
            <Calendar className="w-3 h-3" />
            Moje rezervacije
          </button>
        </div>
      </header>

      {/* Hero Section - only on step 1 */}
      {step === 1 && (
        <div className="max-w-lg mx-auto px-4 pt-8 pb-4 text-center animate-fade-in">
          <h1 className="font-['Cormorant_Garamond'] text-4xl sm:text-5xl font-light tracking-tight mb-3">
            Beauty Studio Bor
          </h1>
          <p className="text-[#9CA3AF] text-base">
            Izaberite usluge za početak
          </p>
        </div>
      )}

      {/* My Reservations Dialog */}
      <Dialog open={showMyReservations} onOpenChange={closeMyReservations}>
        <DialogContent className="bg-[var(--color-surface)] border-[#2A2A2D] max-w-md max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-['Cormorant_Garamond'] text-2xl">Moje Rezervacije</DialogTitle>
            <DialogDescription className="text-[#9CA3AF]">
              Unesite vaš broj telefona da pronađete vaše rezervacije
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            <div className="flex gap-2">
              <div className="flex-1">
                <PhoneInput
                  value={lookupPhone}
                  onChange={setLookupPhone}
                  data-testid="lookup-phone-input"
                />
              </div>
              <Button
                onClick={searchMyReservations}
                disabled={isSearching}
                className="bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black min-h-[48px]"
                data-testid="search-reservations-btn"
              >
                <Search className="w-4 h-4" />
              </Button>
            </div>

            {isSearching && (
              <div className="text-center py-8 text-[#9CA3AF]">
                Pretraživanje...
              </div>
            )}

            {!isSearching && hasSearched && myReservations.length === 0 && (
              <div className="text-center py-8 text-[#9CA3AF]">
                <Calendar className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>Nema pronađenih rezervacija za ovaj broj</p>
              </div>
            )}

            {!isSearching && myReservations.length > 0 && (
              <div className="space-y-3">
                {myReservations.map((res) => (
                  <div
                    key={res.id}
                    className="bg-[var(--color-background)] rounded-xl border border-[#2A2A2D] p-4"
                    data-testid={`my-reservation-${res.id}`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <p className="text-[var(--color-primary)] font-medium">
                          {res.date} u {res.time}
                        </p>
                        <p className="text-sm text-[#9CA3AF]">
                          {res.services?.join(", ")}
                        </p>
                      </div>
                      <span className="font-semibold text-[var(--color-primary)]">
                        {res.total_price ?? 0} π
                      </span>
                    </div>

                    {/* Payment status badge */}
                    <div className="mb-3">
                      {res.payment_status === "confirmed" && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-green-600/20 text-green-400" data-testid={`payment-badge-${res.id}`}>
                          <Check className="w-3 h-3" /> Uplata potvrđena
                        </span>
                      )}
                      {res.payment_status === "sent_for_verification" && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/15 text-amber-400" data-testid={`payment-badge-${res.id}`}>
                          <Clock className="w-3 h-3" /> Uplata u obradi - čeka se provera salona
                        </span>
                      )}
                    </div>

                    {/* Report payment button */}
                    {res.payment_status === "pending" && (
                      <Button
                        onClick={() => reportPayment(res.id)}
                        className="w-full bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black font-medium min-h-[48px] mb-2"
                        data-testid={`report-payment-${res.id}`}
                      >
                        <Check className="w-4 h-4 mr-2" />
                        Potvrdi uplatu avansa
                      </Button>
                    )}
                    
                    {res.can_cancel ? (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => cancelMyReservation(res.id)}
                        className="w-full border-red-400/30 text-red-400 hover:bg-red-400/10"
                        data-testid={`cancel-my-reservation-${res.id}`}
                      >
                        <X className="w-4 h-4 mr-1" />
                        Otkaži rezervaciju
                      </Button>
                    ) : (
                      <div className="text-center p-2 bg-[#2A2A2D]/30 rounded-lg">
                        <p className="text-xs text-[#9CA3AF]">
                          Otkazivanje je moguće najkasnije 24h pre termina.
                        </p>
                        <p className="text-xs text-[#9CA3AF] mt-1">
                          Za hitne izmene, pozovite salon.
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Progress Steps */}
      <div className="max-w-lg mx-auto px-4 py-4">
        <div className="flex items-center justify-between mb-6">
          {[1, 2, 3, 4].map((s) => (
            <div key={s} className="flex items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all ${
                  step >= s
                    ? "bg-[var(--color-primary)] text-black"
                    : "bg-[var(--color-surface)] text-[#9CA3AF] border border-[#2A2A2D]"
                }`}
              >
                {step > s ? <Check className="w-4 h-4" /> : s}
              </div>
              {s < 4 && (
                <div
                  className={`w-12 sm:w-16 h-0.5 mx-1 transition-all ${
                    step > s ? "bg-[var(--color-primary)]" : "bg-[#2A2A2D]"
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        {/* Step 1: Categories -> Services */}
        {step === 1 && !selectedCategory && (
          <div className="animate-fade-in">
            <div className="mb-6">
              <p className="overline mb-2">Korak 1</p>
              <h2 className="font-['Cormorant_Garamond'] text-3xl font-light">Izaberite Kategoriju</h2>
              <p className="text-[#9CA3AF] text-sm mt-2">Odaberite vrstu usluge koju želite</p>
            </div>
            <div className="grid grid-cols-2 gap-3 stagger-children">
              {categories.map((cat) => {
                const catServices = servicesByCategory[cat.key] || [];
                if (catServices.length === 0) return null;
                const count = catServices.length;
                const bgImage = categoryImages[cat.key];
                return (
                  <button
                    key={cat.key}
                    onClick={() => setSelectedCategory(cat.key)}
                    className="relative overflow-hidden rounded-2xl border border-[#2A2A2D] h-36 text-left transition-all hover:border-[var(--color-primary)]/50 active:scale-[0.97] group"
                    data-testid={`category-card-${cat.key}`}
                  >
                    {bgImage && (
                      <div
                        className="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-110"
                        style={{ backgroundImage: `url(${bgImage})` }}
                      />
                    )}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-black/10" />
                    <div className="relative h-full flex flex-col justify-end p-4">
                      <h3 className="font-medium text-base text-white drop-shadow-md">{cat.label}</h3>
                      <p className="text-xs text-white/70 mt-0.5">{count} {count === 1 ? "usluga" : count < 5 ? "usluge" : "usluga"}</p>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Show selected services summary if any */}
            {selectedServices.length > 0 && (
              <div className="mt-6 p-4 bg-[var(--color-surface)] rounded-xl border border-[var(--color-primary)]/30">
                <p className="text-sm text-[#9CA3AF] mb-2">Izabrane usluge:</p>
                <div className="space-y-1">
                  {selectedServices.map(s => (
                    <div key={s.id} className="flex justify-between text-sm">
                      <span>{s.name}</span>
                      <span className="text-[var(--color-primary)]">{s.price} π</span>
                    </div>
                  ))}
                </div>
                <div className="border-t border-[#2A2A2D] mt-3 pt-3 flex justify-between font-medium">
                  <span>Ukupno</span>
                  <span className="text-[var(--color-primary)]">{selectedServices.reduce((sum, s) => sum + s.price, 0)} π</span>
                </div>
              </div>
            )}
          </div>
        )}

        {step === 1 && selectedCategory && (
          <div className="animate-fade-in">
            <div className="mb-6">
              <button
                onClick={() => setSelectedCategory(null)}
                className="w-full flex items-center justify-center gap-2 py-3.5 rounded-xl border border-[#2A2A2D] bg-[var(--color-surface)] hover:border-[var(--color-primary)]/50 hover:bg-[#1A1A1D] transition-all mb-5"
                data-testid="back-to-categories-btn"
              >
                <ChevronLeft className="w-5 h-5 text-[var(--color-primary)]" />
                <span className="text-sm font-medium">Nazad na kategorije</span>
              </button>
              <h2 className="font-['Cormorant_Garamond'] text-3xl font-light flex items-center gap-3">
                {categoryImages[selectedCategory] && (
                  <div
                    className="w-10 h-10 rounded-lg bg-cover bg-center shrink-0"
                    style={{ backgroundImage: `url(${categoryImages[selectedCategory]})` }}
                  />
                )}
                {categoryLabels[selectedCategory] || selectedCategory}
              </h2>
            </div>

            <div className="space-y-2 stagger-children">
              {(servicesByCategory[selectedCategory] || []).map((service) => {
                const isSelected = selectedServices.find(s => s.id === service.id);
                const availableWorkers = getWorkersForService(service.id);
                return (
                  <button
                    key={service.id}
                    onClick={() => handleServiceToggle(service)}
                    disabled={availableWorkers.length === 0}
                    className={`w-full p-4 rounded-xl border text-left transition-all ${
                      isSelected
                        ? "border-[var(--color-primary)] bg-[var(--color-primary)]/10"
                        : availableWorkers.length === 0
                        ? "border-[#2A2A2D] bg-[var(--color-surface)] opacity-50 cursor-not-allowed"
                        : "border-[#2A2A2D] bg-[var(--color-surface)] hover:border-[var(--color-primary)]/50"
                    }`}
                    data-testid={`service-${service.id}`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium">{service.name}</p>
                        <p className="text-sm text-[#9CA3AF] mt-1">
                          <Clock className="w-3 h-3 inline mr-1" />
                          {service.duration} min
                          {availableWorkers.length === 0 && (
                            <span className="ml-2 text-red-400">• Nema radnika</span>
                          )}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-[var(--color-primary)]">{service.price} π</p>
                        {isSelected && (
                          <Check className="w-5 h-5 text-[var(--color-primary)] mt-1 ml-auto" />
                        )}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Selected services summary */}
            {selectedServices.length > 0 && (
              <div className="mt-6 p-4 bg-[var(--color-surface)] rounded-xl border border-[var(--color-primary)]/30">
                <p className="text-sm text-[#9CA3AF] mb-2">Izabrane usluge ({selectedServices.length}):</p>
                <div className="space-y-1">
                  {selectedServices.map(s => (
                    <div key={s.id} className="flex justify-between text-sm">
                      <span>{s.name} <span className="text-[#9CA3AF]">({categoryLabels[s.category] || s.category})</span></span>
                      <span className="text-[var(--color-primary)]">{s.price} π</span>
                    </div>
                  ))}
                </div>
                <div className="border-t border-[#2A2A2D] mt-3 pt-3 flex justify-between font-medium">
                  <span>Ukupno</span>
                  <span className="text-[var(--color-primary)]">{selectedServices.reduce((sum, s) => sum + s.price, 0)} π</span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 2: Worker Selection PER SERVICE */}
        {step === 2 && (
          <div className="animate-fade-in">
            <div className="mb-6">
              <p className="overline mb-2">Korak 2</p>
              <h2 className="font-['Cormorant_Garamond'] text-3xl font-light">Izaberite Radnike</h2>
              <p className="text-[#9CA3AF] text-sm mt-2">Izaberite radnika za svaku uslugu</p>
            </div>

            <div className="space-y-4 stagger-children">
              {selectedServices.map((service) => {
                const availableWorkers = getWorkersForService(service.id);
                const selectedWorkerId = serviceWorkerMap[service.id];
                
                return (
                  <div key={service.id} className="bg-[var(--color-surface)] rounded-xl border border-[#2A2A2D] p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <p className="font-medium">{service.name}</p>
                        <p className="text-xs text-[#9CA3AF]">
                          {service.duration} min • {service.price} π
                        </p>
                      </div>
                      {selectedWorkerId && (
                        <Check className="w-5 h-5 text-[var(--color-primary)]" />
                      )}
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2">
                      {availableWorkers.map((worker) => (
                        <button
                          key={worker.id}
                          onClick={() => handleWorkerSelect(service.id, worker.id)}
                          className={`p-3 rounded-lg border text-left transition-all ${
                            selectedWorkerId === worker.id
                              ? "border-[var(--color-primary)] bg-[var(--color-primary)]/10"
                              : "border-[#2A2A2D] bg-[var(--color-background)] hover:border-[var(--color-primary)]/50"
                          }`}
                          data-testid={`worker-${service.id}-${worker.id}`}
                        >
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#C5A880] to-[#8B7355] flex items-center justify-center text-black font-semibold text-sm">
                              {worker.name.charAt(0)}
                            </div>
                            <div>
                              <p className="font-medium text-sm">{worker.name}</p>
                              <p className="text-xs text-[#9CA3AF]">{worker.work_start}-{worker.work_end}</p>
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Add additional service button */}
            {!showAddService ? (
              <button
                onClick={() => setShowAddService(true)}
                className="w-full mt-4 p-3 rounded-xl border border-dashed border-[#2A2A2D] hover:border-[var(--color-primary)]/50 text-[#9CA3AF] hover:text-[var(--color-primary)] transition-all flex items-center justify-center gap-2"
                data-testid="add-service-btn"
              >
                <Plus className="w-4 h-4" />
                <span className="text-sm">{"Dodaj još jednu uslugu"}</span>
              </button>
            ) : (
              <div className="mt-4 bg-[var(--color-surface)] rounded-xl border border-[#2A2A2D] p-4 animate-fade-in" data-testid="add-service-picker">
                <div className="flex justify-between items-center mb-3">
                  <p className="text-sm font-medium">{"Izaberite dodatnu uslugu"}</p>
                  <button onClick={() => setShowAddService(false)} className="text-[#9CA3AF] hover:text-white">
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {services
                    .filter(s => s.active && !selectedServices.find(sel => sel.id === s.id))
                    .filter(s => getWorkersForService(s.id).length > 0)
                    .map(service => (
                      <button
                        key={service.id}
                        onClick={() => {
                          handleServiceToggle(service);
                          setShowAddService(false);
                        }}
                        className="w-full p-3 rounded-lg border border-[#2A2A2D] bg-[var(--color-background)] hover:border-[var(--color-primary)]/50 text-left transition-all"
                        data-testid={`add-service-${service.id}`}
                      >
                        <div className="flex justify-between items-center">
                          <div>
                            <p className="text-sm font-medium">{service.name}</p>
                            <p className="text-xs text-[#9CA3AF]">{service.duration} min</p>
                          </div>
                          <span className="text-sm text-[var(--color-primary)]">{service.price} π</span>
                        </div>
                      </button>
                    ))
                  }
                  {services.filter(s => s.active && !selectedServices.find(sel => sel.id === s.id) && getWorkersForService(s.id).length > 0).length === 0 && (
                    <p className="text-center text-[#6B7280] text-sm py-4">{"Nema dodatnih dostupnih usluga"}</p>
                  )}
                </div>
              </div>
            )}

            {/* Summary bar */}
            {selectedServices.length > 1 && (
              <div className="mt-4 p-3 bg-[var(--color-surface)] rounded-xl border border-[var(--color-primary)]/20">
                <div className="flex justify-between text-sm">
                  <span className="text-[#9CA3AF]">{selectedServices.length} usluge · {selectedServices.reduce((s, svc) => s + svc.duration, 0)} min</span>
                  <span className="text-[var(--color-primary)] font-medium">{selectedServices.reduce((s, svc) => s + svc.price, 0)} π</span>
                </div>
              </div>
            )}

            {!allServicesHaveWorkers && (
              <p className="text-center text-[#9CA3AF] text-sm mt-4">
                Izaberite radnika za svaku uslugu da biste nastavili
              </p>
            )}
          </div>
        )}

        {/* Step 3: Date & Time */}
        {step === 3 && (
          <div className="animate-fade-in">
            <div className="mb-6">
              <p className="overline mb-2">Korak 3</p>
              <h2 className="font-['Cormorant_Garamond'] text-3xl font-light">Izaberite Termin</h2>
            </div>

            {/* Date Selection */}
            <div className="mb-6">
              <p className="text-sm text-[#9CA3AF] mb-3">Datum</p>
              <div className="flex gap-2 overflow-x-auto pb-2 hide-scrollbar">
                {dates.map((date) => {
                  const isSelected = selectedDate && isSameDay(date, selectedDate);
                  const dateKey = format(date, "yyyy-MM-dd");
                  const slotCount = dateSlotCounts[dateKey];
                  const isFullyBooked = slotCount === 0 && slotCount !== undefined;
                  return (
                    <button
                      key={date.toISOString()}
                      onClick={() => {
                        if (isFullyBooked) return;
                        setSelectedDate(date);
                        setSelectedTime(null);
                      }}
                      disabled={isFullyBooked}
                      className={`flex-shrink-0 w-16 py-3 rounded-xl border text-center transition-all ${
                        isFullyBooked
                          ? "border-[#2A2A2D] bg-[var(--color-background)] opacity-40 cursor-not-allowed"
                          : isSelected
                          ? "border-[var(--color-primary)] bg-[var(--color-primary)]/10"
                          : "border-[#2A2A2D] bg-[var(--color-surface)] hover:border-[var(--color-primary)]/50"
                      }`}
                      data-testid={`date-${dateKey}`}
                    >
                      <p className="text-xs text-[#9CA3AF] uppercase">
                        {format(date, "EEE", { locale: sr })}
                      </p>
                      <p className="text-lg font-medium">{format(date, "d")}</p>
                      <p className="text-xs text-[#9CA3AF]">
                        {format(date, "MMM", { locale: sr })}
                      </p>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Time Selection */}
            {selectedDate && (
              <div className="animate-fade-in">
                <p className="text-sm text-[#9CA3AF] mb-3">Dostupni termini</p>
                {availableSlots.length > 0 ? (
                  <div className="grid grid-cols-4 gap-2">
                    {availableSlots.map((time) => {
                      const isSelected = selectedTime === time;
                      return (
                        <button
                          key={time}
                          onClick={() => setSelectedTime(time)}
                          className={`time-slot ${isSelected ? "selected" : ""}`}
                          data-testid={`time-${time}`}
                        >
                          {time}
                        </button>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-center py-8 text-[#9CA3AF]">
                    <Calendar className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>Nema dostupnih termina za ovaj datum</p>
                    <p className="text-xs mt-1">Proverite da li su svi radnici dostupni</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Step 4: Contact Info */}
        {step === 4 && (
          <div className="animate-fade-in">
            <div className="mb-6">
              <p className="overline mb-2">Korak 4</p>
              <h2 className="font-['Cormorant_Garamond'] text-3xl font-light">Vaši Podaci</h2>
            </div>

            <div className="space-y-4">
              {/* Pi Identity */}
              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Pi Nalog</label>
                <div className="flex items-center gap-3 bg-[var(--color-surface)] border border-[#2A2A2D] rounded-lg px-4 h-14" data-testid="pi-identity-card">
                  <Shield className="w-5 h-5 text-[var(--color-primary)]" />
                  <span className="text-white font-medium">@{piUser?.username || "—"}</span>
                  {isSandbox && (
                    <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-400">Sandbox</span>
                  )}
                </div>
              </div>

              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Broj Telefona</label>
                <PhoneInput
                  value={clientPhone}
                  onChange={setClientPhone}
                  showError={clientPhone.length > 0}
                  data-testid="client-phone-input"
                />
              </div>

              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Email Adresa</label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#9CA3AF]" />
                  <Input
                    type="email"
                    value={clientEmail}
                    onChange={(e) => setClientEmail(e.target.value)}
                    placeholder="primer@mail.com"
                    className={`pl-12 bg-[var(--color-surface)] focus:border-[var(--color-primary)] h-14 ${clientEmail && !isValidEmail(clientEmail) ? "border-red-400" : "border-[#2A2A2D]"}`}
                    data-testid="client-email-input"
                  />
                </div>
                {clientEmail && !isValidEmail(clientEmail) && (
                  <p className="text-xs text-red-400 mt-1" data-testid="email-error">Molimo unesite ispravnu email adresu (npr. ime@gmail.com)</p>
                )}
              </div>
            </div>

            {/* Blacklist Error */}
            {blacklistError && (
              <div className="mt-6 p-5 bg-red-500/10 border border-red-500/30 rounded-xl text-center" data-testid="blacklist-error">
                <Ban className="w-8 h-8 text-red-400 mx-auto mb-3" />
                <p className="font-medium text-red-400 mb-1">Zakazivanje nije moguće</p>
                <p className="text-sm text-[#9CA3AF]">
                  Nažalost, zakazivanje nije moguće sa ovog broja telefona. Molimo kontaktirajte salon direktno.
                </p>
              </div>
            )}

            {/* Booking Summary */}
            <div className="mt-8 bg-[var(--color-surface)] rounded-xl border border-[#2A2A2D] p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium">Pregled Rezervacije</h3>
                <button
                  onClick={() => { setStep(1); setSelectedCategory(null); }}
                  className="flex items-center gap-1.5 text-xs text-[var(--color-primary)] hover:text-[#B89970] transition-colors"
                  data-testid="edit-services-link"
                >
                  <Pencil className="w-3 h-3" />
                  Izmeni usluge
                </button>
              </div>
              <div className="space-y-3 text-sm">
                {/* Services with workers */}
                <div className="space-y-2">
                  {selectedServices.map(s => (
                    <div key={s.id} className="flex items-center justify-between">
                      <span className="text-[#9CA3AF]">{s.name}:</span>
                      <div className="flex items-center gap-2">
                        <span className="text-[var(--color-primary)]">{getWorkerName(serviceWorkerMap[s.id])}</span>
                        <button
                          onClick={() => removeServiceFromReview(s.id)}
                          className="w-6 h-6 rounded-full flex items-center justify-center text-[#6B7280] hover:text-red-400 hover:bg-red-400/10 transition-colors"
                          data-testid={`remove-service-review-${s.id}`}
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="border-t border-[#2A2A2D] pt-3 flex justify-between">
                  <span className="text-[#9CA3AF]">Datum:</span>
                  <span>{selectedDate && format(selectedDate, "d. MMMM yyyy", { locale: sr })}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#9CA3AF]">Vreme:</span>
                  <span>{selectedTime}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#9CA3AF]">Trajanje:</span>
                  <span>{totalDuration} min</span>
                </div>
                <div className="border-t border-[#2A2A2D] pt-3 flex justify-between">
                  <span className="font-medium">Ukupno:</span>
                  <span className="font-semibold text-[var(--color-primary)] text-lg">{totalPrice} π</span>
                </div>
              </div>
            </div>

            <p className="text-xs text-[#9CA3AF] mt-4 text-center">
              Klikom na "Potvrdi Rezervaciju" prihvatate uslove korišćenja.
              Avans je obavezan 24h pre termina.
            </p>

            {/* Urgent slot warning */}
            {isUrgentSlot && (
              <div className="mt-4 p-4 bg-orange-500/10 border border-orange-500/30 rounded-xl" data-testid="urgent-slot-warning">
                <p className="text-sm text-orange-400 font-medium mb-1">Napomena: Izabrali ste termin za danas.</p>
                <p className="text-xs text-[#9CA3AF]">
                  Molimo vas da odmah nakon zakazivanja pošaljete dokaz o uplati kako bismo osigurali vaše mesto, ili nas pozovite telefonom.
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Bottom Bar */}
      <div className="fixed bottom-0 left-0 right-0 bottom-sheet p-4 safe-area-pb">
        <div className="max-w-lg mx-auto">
          {/* Summary */}
          {selectedServices.length > 0 && step < 4 && (
            <div className="flex justify-between items-center mb-3 text-sm">
              <span className="text-[#9CA3AF]">
                {selectedServices.length} usluga · {totalDuration} min
              </span>
              <span className="font-semibold text-[var(--color-primary)]">{totalPrice} π</span>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex gap-3">
            {step > 1 && (
              <Button
                variant="outline"
                onClick={() => setStep(step - 1)}
                className="flex-1 h-14 border-[#2A2A2D] bg-transparent hover:bg-[var(--color-surface)]"
                data-testid="prev-step-btn"
              >
                <ChevronLeft className="w-5 h-5 mr-2" />
                Nazad
              </Button>
            )}

            {step < 4 ? (
              <Button
                onClick={() => setStep(step + 1)}
                disabled={
                  (step === 1 && selectedServices.length === 0) ||
                  (step === 2 && !allServicesHaveWorkers) ||
                  (step === 3 && !selectedTime)
                }
                className="flex-1 h-14 bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black font-medium disabled:opacity-50"
                data-testid="next-step-btn"
              >
                Dalje
                <ChevronRight className="w-5 h-5 ml-2" />
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={isSubmitting || !piUser?.username || !isValidPhone(clientPhone) || !isValidEmail(clientEmail)}
                className="flex-1 h-14 bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black font-medium disabled:opacity-50"
                data-testid="confirm-booking-btn"
              >
                {isSubmitting ? "Obrada..." : "Potvrdi Rezervaciju"}
              </Button>
            )}
          </div>
          
          {/* Footer inside bottom bar */}
          <div className="text-center pt-3 border-t border-[#2A2A2D] mt-3">
            <a 
              href={`/${slug}/admin`} 
              className="text-[#3A3A3D] text-xs hover:text-[#9CA3AF] transition-colors"
              data-testid="admin-link-footer"
            >
              Admin Login
            </a>
          </div>
        </div>
      </div>

      {/* Spacer for bottom bar */}
      <div className="h-44" />
    </div>
  );
};

export default BookingPage;
