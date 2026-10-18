import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "../components/ui/dialog";
import { Link } from "react-router-dom";
import { ChevronLeft, Settings, Tag, Users, CalendarDays, Sparkles, Send, ImageIcon, Maximize2 } from "lucide-react";

// Postavite skrinšotove u /app/frontend/public/mockups/ sa navedenim imenima
const FEATURES = [
  { id: "setup", icon: Settings, title: "Osnovna podešavanja", image: "/mockups/settings.png", desc: "Radno vreme, naziv, tema i osnovne informacije o salonu." },
  { id: "services", icon: Tag, title: "Usluge i cene", image: "/mockups/services.png", desc: "Kategorije, trajanje i cena svake usluge na jednom mestu." },
  { id: "workers", icon: Users, title: "Radnici i rasporedi", image: "/mockups/workers.png", desc: "Radnici, smene, pauze i nalozi za pristup timu." },
  { id: "calendar", icon: CalendarDays, title: "Kalendar i rezervacije", image: "/mockups/calendar.png", desc: "Pregled termina po radnicima uz drag-and-drop pomeranje." },
];

const MockupPlaceholder = ({ title }) => (
  <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-[#0A0D14]" data-testid="mockup-placeholder">
    <div className="w-12 h-12 rounded-xl bg-[var(--color-primary)]/10 border border-[var(--color-primary)]/30 flex items-center justify-center">
      <ImageIcon className="w-5 h-5 text-[var(--color-primary)]" />
    </div>
    <span className="text-xs text-[#6B7280]">Prikaz ekrana: {title}</span>
  </div>
);

const BrowserMockup = ({ feature, onZoom }) => {
  const [failed, setFailed] = useState({});
  return (
    <div className="relative" data-testid="feature-mockup">
      <div className="absolute -inset-4 bg-[var(--color-primary)]/15 blur-3xl rounded-3xl pointer-events-none" />
      <div className="relative rounded-xl border border-[#2A2A2D] bg-[#111318] shadow-2xl shadow-black/60 overflow-hidden">
        <div className="flex items-center gap-2 px-3 py-2.5 border-b border-[#2A2A2D] bg-[#0D0F14]">
          <span className="w-2.5 h-2.5 rounded-full bg-[#FF5F57]" />
          <span className="w-2.5 h-2.5 rounded-full bg-[#FEBC2E]" />
          <span className="w-2.5 h-2.5 rounded-full bg-[#28C840]" />
          <div className="ml-3 flex-1 h-5 rounded-md bg-[#1A1D24] flex items-center px-2 text-[10px] text-[#6B7280] truncate">
            beautymepi.app/vas-salon/admin
          </div>
        </div>
        <div className="relative aspect-[16/10] group">
          {failed[feature.id] ? (
            <MockupPlaceholder title={feature.title} />
          ) : (
            <img
              key={feature.id}
              src={feature.image}
              alt={feature.title}
              onError={() => setFailed((f) => ({ ...f, [feature.id]: true }))}
              onClick={onZoom}
              className="absolute inset-0 w-full h-full object-cover object-top cursor-zoom-in animate-in fade-in duration-500"
              data-testid={`mockup-image-${feature.id}`}
            />
          )}
          {!failed[feature.id] && (
            <button
              type="button"
              onClick={onZoom}
              className="absolute bottom-3 right-3 flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-black/70 backdrop-blur-md border border-white/10 text-xs text-white opacity-80 group-hover:opacity-100 transition-opacity"
              data-testid="mockup-zoom-btn"
            >
              <Maximize2 className="w-3.5 h-3.5" />
              Uvećaj
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

const OwnersPage = () => {
  const [activeTab, setActiveTab] = useState("setup");
  const [paused, setPaused] = useState(false);
  const [zoomOpen, setZoomOpen] = useState(false);
  const active = FEATURES.find((f) => f.id === activeTab) || FEATURES[0];

  useEffect(() => {
    if (paused || zoomOpen) return;
    const t = setTimeout(() => {
      const i = FEATURES.findIndex((f) => f.id === activeTab);
      setActiveTab(FEATURES[(i + 1) % FEATURES.length].id);
    }, 5000);
    return () => clearTimeout(t);
  }, [activeTab, paused, zoomOpen]);

  return (
    <div className="min-h-screen bg-transparent text-white">
      <div className="max-w-3xl mx-auto px-6 py-12">
        <Link to="/" className="flex items-center gap-1 text-[#9CA3AF] hover:text-white mb-10 transition-colors text-sm" data-testid="owners-back-link">
          <ChevronLeft className="w-4 h-4" />
          Nazad
        </Link>

        <div className="text-center mb-10">
          <h1 className="font-['Cormorant_Garamond'] text-3xl sm:text-4xl font-light mb-3">Za vlasnike salona</h1>
          <p className="text-[#9CA3AF] leading-relaxed max-w-md mx-auto">Pogledajte kako izgleda upravljanje vašim salonom u BeautyMePi aplikaciji.</p>
        </div>

        <section className="mb-16" data-testid="feature-showcase" onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)}>
          <h2 className="text-xs uppercase tracking-[0.2em] text-[#6B7280] mb-4 text-center">Prikaz funkcionalnosti</h2>
          <div className="flex gap-2 overflow-x-auto pb-2 mb-8 sm:justify-center scrollbar-hide">
            {FEATURES.map((f) => {
              const Icon = f.icon;
              const isActive = f.id === activeTab;
              return (
                <button
                  key={f.id}
                  onClick={() => setActiveTab(f.id)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm whitespace-nowrap transition-colors shrink-0 ${
                    isActive
                      ? "bg-[var(--color-primary)]/10 border border-[var(--color-primary)]/40 text-[var(--color-primary)]"
                      : "bg-[var(--color-surface)] border border-[#2A2A2D] text-[#9CA3AF] hover:border-[#3A3A3D]"
                  }`}
                  data-testid={`feature-tab-${f.id}`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {f.title}
                </button>
              );
            })}
          </div>

          <BrowserMockup feature={active} onZoom={() => setZoomOpen(true)} />
          <div className="flex justify-center gap-1.5 mt-5" data-testid="feature-progress">
            {FEATURES.map((f) => (
              <span key={f.id} className={`h-1 rounded-full transition-all duration-300 ${f.id === activeTab ? "w-6 bg-[var(--color-primary)]" : "w-1.5 bg-[#2A2A2D]"}`} />
            ))}
          </div>

          <div className="mt-6 text-center" data-testid="feature-active-desc">
            <h3 className="font-medium text-white mb-1">{active.title}</h3>
            <p className="text-sm text-[#9CA3AF]">{active.desc}</p>
          </div>
        </section>

        <Dialog open={zoomOpen} onOpenChange={setZoomOpen}>
          <DialogContent className="w-[96vw] max-w-6xl p-2 bg-[#0A0D14] border-[#2A2A2D]" data-testid="mockup-lightbox">
            <DialogTitle className="sr-only">{active.title}</DialogTitle>
            <DialogDescription className="sr-only">{active.desc}</DialogDescription>
            <img src={active.image} alt={active.title} className="w-full h-auto max-h-[88vh] object-contain rounded-lg" data-testid="mockup-lightbox-image" />
          </DialogContent>
        </Dialog>

        <div className="bg-gradient-to-br from-[var(--color-primary)]/8 to-transparent border border-[var(--color-primary)]/20 rounded-2xl p-8 text-center" data-testid="owners-activation-cta">
          <div className="w-12 h-12 rounded-xl bg-[var(--color-primary)]/10 flex items-center justify-center mx-auto mb-4">
            <Sparkles className="w-6 h-6 text-[var(--color-primary)]" />
          </div>
          <h2 className="font-['Cormorant_Garamond'] text-2xl font-light mb-2">Registracija salona uskoro</h2>
          <p className="text-sm text-[#9CA3AF] leading-relaxed mb-6 max-w-sm mx-auto">
            Pošaljite nam poruku sa nazivom salona i kontakt podacima. Aktiviraćemo vaš profil u roku od 24h.
          </p>
          <div className="flex flex-col items-center gap-3">
            <a
              href="mailto:bornaja23@gmail.com?subject=Aktivacija salona - BeautyMePi"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black font-medium text-sm transition-colors"
              data-testid="activation-email-btn"
            >
              <Send className="w-4 h-4" />
              bornaja23@gmail.com
            </a>
            <span className="text-xs text-[#9CA3AF]" data-testid="activation-pi-username">Pi username: @Markonijus23</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OwnersPage;
