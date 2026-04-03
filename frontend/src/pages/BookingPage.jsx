import { useState, useEffect } from "react";
import { toast } from "sonner";
import axios from "axios";
import { API } from "../App";
import { Clock, Scissors, User, Phone, Calendar, ChevronRight, ChevronLeft, Check, X } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { format, addDays, isSameDay } from "date-fns";
import { sr } from "date-fns/locale";

const BookingPage = () => {
  const [step, setStep] = useState(1);
  const [services, setServices] = useState([]);
  const [workers, setWorkers] = useState([]);
  const [settings, setSettings] = useState(null);
  
  // Booking state
  const [selectedServices, setSelectedServices] = useState([]);
  const [selectedWorker, setSelectedWorker] = useState(null); // null = "Anyone"
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedTime, setSelectedTime] = useState(null);
  const [availableSlots, setAvailableSlots] = useState({ slots: [], workers: {} });
  const [clientName, setClientName] = useState("");
  const [clientPhone, setClientPhone] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [bookingComplete, setBookingComplete] = useState(false);
  const [bookingDetails, setBookingDetails] = useState(null);

  // Calculate totals
  const totalDuration = selectedServices.reduce((sum, s) => sum + s.duration, 0);
  const totalPrice = selectedServices.reduce((sum, s) => sum + s.price, 0);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (selectedServices.length > 0 && selectedDate) {
      fetchAvailableSlots();
    }
  }, [selectedServices, selectedWorker, selectedDate]);

  const fetchData = async () => {
    try {
      const [servicesRes, workersRes, settingsRes] = await Promise.all([
        axios.get(`${API}/services`),
        axios.get(`${API}/workers`),
        axios.get(`${API}/settings`),
      ]);
      setServices(servicesRes.data);
      setWorkers(workersRes.data);
      setSettings(settingsRes.data);
    } catch (error) {
      toast.error("Greška pri učitavanju podataka");
    }
  };

  const fetchAvailableSlots = async () => {
    if (!selectedDate || selectedServices.length === 0) return;
    
    try {
      const response = await axios.post(`${API}/reservations/available-slots`, {
        services: selectedServices.map(s => s.id),
        worker_id: selectedWorker?.id || null,
        date: format(selectedDate, "yyyy-MM-dd"),
      });
      setAvailableSlots(response.data);
    } catch (error) {
      console.error("Error fetching slots:", error);
      setAvailableSlots({ slots: [], workers: {} });
    }
  };

  const handleServiceToggle = (service) => {
    setSelectedServices(prev => {
      const exists = prev.find(s => s.id === service.id);
      if (exists) {
        return prev.filter(s => s.id !== service.id);
      }
      return [...prev, service];
    });
    setSelectedTime(null);
  };

  const handleWorkerSelect = (worker) => {
    setSelectedWorker(prev => prev?.id === worker?.id ? null : worker);
    setSelectedTime(null);
  };

  const handleSubmit = async () => {
    if (!clientName.trim() || !clientPhone.trim()) {
      toast.error("Molimo unesite ime i broj telefona");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await axios.post(`${API}/reservations`, {
        services: selectedServices.map(s => s.id),
        worker_id: selectedWorker?.id || null,
        date: format(selectedDate, "yyyy-MM-dd"),
        time: selectedTime,
        client_name: clientName,
        client_phone: clientPhone,
      });
      
      setBookingDetails(response.data);
      setBookingComplete(true);
      toast.success("Rezervacija uspešno kreirana!");
    } catch (error) {
      const message = error.response?.data?.detail || "Greška pri kreiranju rezervacije";
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetBooking = () => {
    setStep(1);
    setSelectedServices([]);
    setSelectedWorker(null);
    setSelectedDate(null);
    setSelectedTime(null);
    setClientName("");
    setClientPhone("");
    setBookingComplete(false);
    setBookingDetails(null);
  };

  // Generate next 14 days
  const dates = Array.from({ length: 14 }, (_, i) => addDays(new Date(), i));

  // Group services by category
  const servicesByCategory = services.reduce((acc, service) => {
    if (!acc[service.category]) acc[service.category] = [];
    acc[service.category].push(service);
    return acc;
  }, {});

  const categoryLabels = {
    hair: "Frizura",
    massage: "Masaža",
    nails: "Nokti",
  };

  const categoryImages = {
    hair: "https://images.pexels.com/photos/973403/pexels-photo-973403.jpeg",
    massage: "https://images.pexels.com/photos/6187839/pexels-photo-6187839.jpeg",
    nails: "https://images.unsplash.com/photo-1658492055212-e1acbccfca5a?w=400",
  };

  if (bookingComplete && bookingDetails) {
    return (
      <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-[#141416] rounded-2xl border border-[#2A2A2D] p-8 text-center animate-fade-in">
          <div className="w-16 h-16 rounded-full bg-[#C5A880]/20 flex items-center justify-center mx-auto mb-6">
            <Check className="w-8 h-8 text-[#C5A880]" />
          </div>
          <h1 className="font-['Cormorant_Garamond'] text-3xl font-light mb-2">Rezervacija Potvrđena</h1>
          <p className="text-[#9CA3AF] mb-6">Hvala vam na rezervaciji!</p>
          
          <div className="bg-[#0A0A0B] rounded-xl p-6 text-left space-y-4 mb-6">
            <div className="flex justify-between">
              <span className="text-[#9CA3AF]">Datum:</span>
              <span className="font-medium">{bookingDetails.date}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#9CA3AF]">Vreme:</span>
              <span className="font-medium">{bookingDetails.time} - {bookingDetails.end_time}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#9CA3AF]">Radnik:</span>
              <span className="font-medium">{bookingDetails.worker_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#9CA3AF]">Usluge:</span>
              <span className="font-medium text-right">{bookingDetails.service_names.join(", ")}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#9CA3AF]">Trajanje:</span>
              <span className="font-medium">{bookingDetails.total_duration} min</span>
            </div>
            <div className="border-t border-[#2A2A2D] pt-4 flex justify-between">
              <span className="text-[#9CA3AF]">Ukupno:</span>
              <span className="font-semibold text-[#C5A880] text-lg">{bookingDetails.total_price.toLocaleString()} RSD</span>
            </div>
          </div>

          {bookingDetails.advance_required && !bookingDetails.advance_released && (
            <div className="bg-[#C5A880]/10 border border-[#C5A880]/30 rounded-xl p-4 mb-6 text-left">
              <p className="text-[#C5A880] text-sm font-medium mb-1">Avans obavezan</p>
              <p className="text-[#9CA3AF] text-sm">
                {settings?.advance_instructions || "Uplata avansa je obavezna 24h pre termina."}
              </p>
            </div>
          )}

          <Button
            onClick={resetBooking}
            className="w-full bg-[#C5A880] hover:bg-[#B89970] text-black font-medium py-6"
            data-testid="new-booking-btn"
          >
            Nova Rezervacija
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0A0A0B]">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-[#2A2A2D]">
        <div className="max-w-lg mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="font-['Cormorant_Garamond'] text-2xl font-light tracking-tight">
            {settings?.salon_name || "Beauty Salon"}
          </h1>
          <a 
            href="/admin/login" 
            className="text-[#9CA3AF] text-sm hover:text-[#C5A880] transition-colors"
            data-testid="admin-link"
          >
            Admin
          </a>
        </div>
      </header>

      {/* Progress Steps */}
      <div className="max-w-lg mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-8">
          {[1, 2, 3, 4].map((s) => (
            <div key={s} className="flex items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all ${
                  step >= s
                    ? "bg-[#C5A880] text-black"
                    : "bg-[#141416] text-[#9CA3AF] border border-[#2A2A2D]"
                }`}
              >
                {step > s ? <Check className="w-4 h-4" /> : s}
              </div>
              {s < 4 && (
                <div
                  className={`w-12 sm:w-16 h-0.5 mx-1 transition-all ${
                    step > s ? "bg-[#C5A880]" : "bg-[#2A2A2D]"
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        {/* Step 1: Services */}
        {step === 1 && (
          <div className="animate-fade-in">
            <div className="mb-6">
              <p className="overline mb-2">Korak 1</p>
              <h2 className="font-['Cormorant_Garamond'] text-3xl font-light">Izaberite Usluge</h2>
            </div>

            <div className="space-y-6 stagger-children">
              {Object.entries(servicesByCategory).map(([category, categoryServices]) => (
                <div key={category}>
                  <div className="flex items-center gap-3 mb-3">
                    <div 
                      className="w-12 h-12 rounded-lg bg-cover bg-center"
                      style={{ backgroundImage: `url(${categoryImages[category]})` }}
                    />
                    <h3 className="font-medium text-lg">{categoryLabels[category] || category}</h3>
                  </div>
                  <div className="space-y-2">
                    {categoryServices.map((service) => {
                      const isSelected = selectedServices.find(s => s.id === service.id);
                      return (
                        <button
                          key={service.id}
                          onClick={() => handleServiceToggle(service)}
                          className={`w-full p-4 rounded-xl border text-left transition-all ${
                            isSelected
                              ? "border-[#C5A880] bg-[#C5A880]/10"
                              : "border-[#2A2A2D] bg-[#141416] hover:border-[#C5A880]/50"
                          }`}
                          data-testid={`service-${service.id}`}
                        >
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-medium">{service.name}</p>
                              <p className="text-sm text-[#9CA3AF] mt-1">
                                <Clock className="w-3 h-3 inline mr-1" />
                                {service.duration} min
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="font-semibold text-[#C5A880]">{service.price.toLocaleString()} RSD</p>
                              {isSelected && (
                                <Check className="w-5 h-5 text-[#C5A880] mt-1 ml-auto" />
                              )}
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Worker Selection */}
        {step === 2 && (
          <div className="animate-fade-in">
            <div className="mb-6">
              <p className="overline mb-2">Korak 2</p>
              <h2 className="font-['Cormorant_Garamond'] text-3xl font-light">Izaberite Radnika</h2>
            </div>

            <div className="space-y-3 stagger-children">
              {/* Anyone option */}
              <button
                onClick={() => handleWorkerSelect(null)}
                className={`w-full p-4 rounded-xl border text-left transition-all ${
                  selectedWorker === null
                    ? "border-[#C5A880] bg-[#C5A880]/10"
                    : "border-[#2A2A2D] bg-[#141416] hover:border-[#C5A880]/50"
                }`}
                data-testid="worker-anyone"
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-[#2A2A2D] flex items-center justify-center">
                    <User className="w-6 h-6 text-[#9CA3AF]" />
                  </div>
                  <div>
                    <p className="font-medium">Bilo Ko</p>
                    <p className="text-sm text-[#9CA3AF]">Prvi slobodan radnik</p>
                  </div>
                  {selectedWorker === null && (
                    <Check className="w-5 h-5 text-[#C5A880] ml-auto" />
                  )}
                </div>
              </button>

              {workers.map((worker) => {
                // Check if worker can do all selected services
                const canDoAllServices = selectedServices.every(s =>
                  worker.services.includes(s.id)
                );
                
                return (
                  <button
                    key={worker.id}
                    onClick={() => canDoAllServices && handleWorkerSelect(worker)}
                    disabled={!canDoAllServices}
                    className={`w-full p-4 rounded-xl border text-left transition-all ${
                      selectedWorker?.id === worker.id
                        ? "border-[#C5A880] bg-[#C5A880]/10"
                        : canDoAllServices
                        ? "border-[#2A2A2D] bg-[#141416] hover:border-[#C5A880]/50"
                        : "border-[#2A2A2D] bg-[#141416] opacity-50 cursor-not-allowed"
                    }`}
                    data-testid={`worker-${worker.id}`}
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#C5A880] to-[#8B7355] flex items-center justify-center text-black font-semibold">
                        {worker.name.charAt(0)}
                      </div>
                      <div>
                        <p className="font-medium">{worker.name}</p>
                        <p className="text-sm text-[#9CA3AF]">
                          {worker.work_start} - {worker.work_end}
                        </p>
                      </div>
                      {selectedWorker?.id === worker.id && (
                        <Check className="w-5 h-5 text-[#C5A880] ml-auto" />
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
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
                  return (
                    <button
                      key={date.toISOString()}
                      onClick={() => {
                        setSelectedDate(date);
                        setSelectedTime(null);
                      }}
                      className={`flex-shrink-0 w-16 py-3 rounded-xl border text-center transition-all ${
                        isSelected
                          ? "border-[#C5A880] bg-[#C5A880]/10"
                          : "border-[#2A2A2D] bg-[#141416] hover:border-[#C5A880]/50"
                      }`}
                      data-testid={`date-${format(date, "yyyy-MM-dd")}`}
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
                {availableSlots.slots.length > 0 ? (
                  <div className="grid grid-cols-4 gap-2">
                    {availableSlots.slots.map((time) => {
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
              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Ime i Prezime</label>
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#9CA3AF]" />
                  <Input
                    value={clientName}
                    onChange={(e) => setClientName(e.target.value)}
                    placeholder="Unesite vaše ime"
                    className="pl-12 bg-[#141416] border-[#2A2A2D] focus:border-[#C5A880] h-14"
                    data-testid="client-name-input"
                  />
                </div>
              </div>

              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Broj Telefona</label>
                <div className="relative">
                  <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#9CA3AF]" />
                  <Input
                    value={clientPhone}
                    onChange={(e) => setClientPhone(e.target.value)}
                    placeholder="+381 6X XXX XXXX"
                    className="pl-12 bg-[#141416] border-[#2A2A2D] focus:border-[#C5A880] h-14"
                    data-testid="client-phone-input"
                  />
                </div>
              </div>
            </div>

            {/* Booking Summary */}
            <div className="mt-8 bg-[#141416] rounded-xl border border-[#2A2A2D] p-6">
              <h3 className="font-medium mb-4">Pregled Rezervacije</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-[#9CA3AF]">Usluge:</span>
                  <span className="text-right">{selectedServices.map(s => s.name).join(", ")}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#9CA3AF]">Radnik:</span>
                  <span>{selectedWorker?.name || "Bilo ko"}</span>
                </div>
                <div className="flex justify-between">
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
                  <span className="font-semibold text-[#C5A880] text-lg">{totalPrice.toLocaleString()} RSD</span>
                </div>
              </div>
            </div>

            <p className="text-xs text-[#9CA3AF] mt-4 text-center">
              Klikom na "Potvrdi Rezervaciju" prihvatate uslove korišćenja.
              Avans je obavezan 24h pre termina.
            </p>
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
              <span className="font-semibold text-[#C5A880]">{totalPrice.toLocaleString()} RSD</span>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex gap-3">
            {step > 1 && (
              <Button
                variant="outline"
                onClick={() => setStep(step - 1)}
                className="flex-1 h-14 border-[#2A2A2D] bg-transparent hover:bg-[#141416]"
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
                  (step === 3 && !selectedTime)
                }
                className="flex-1 h-14 bg-[#C5A880] hover:bg-[#B89970] text-black font-medium disabled:opacity-50"
                data-testid="next-step-btn"
              >
                Dalje
                <ChevronRight className="w-5 h-5 ml-2" />
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={isSubmitting || !clientName.trim() || !clientPhone.trim()}
                className="flex-1 h-14 bg-[#C5A880] hover:bg-[#B89970] text-black font-medium disabled:opacity-50"
                data-testid="confirm-booking-btn"
              >
                {isSubmitting ? "Obrada..." : "Potvrdi Rezervaciju"}
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Spacer for bottom bar */}
      <div className="h-32" />
    </div>
  );
};

export default BookingPage;
