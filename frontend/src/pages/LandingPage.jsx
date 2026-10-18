import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Sparkles, Building2, ChevronRight, LogIn, Play, Settings, Tag, Users, CalendarDays, MousePointerClick } from "lucide-react";

const OWNER_TUTORIALS = [
  {
    id: "setup",
    icon: Settings,
    title: "Osnovna podešavanja salona",
    desc: "Kako podesiti radno vreme, naziv i osnovne informacije o salonu.",
  },
  {
    id: "services",
    icon: Tag,
    title: "Dodavanje usluga i cena",
    desc: "Kreiranje kategorija, unos trajanja i cene svake usluge.",
  },
  {
    id: "workers",
    icon: Users,
    title: "Dodavanje radnika i rasporeda",
    desc: "Kreiranje radnika, smena, pauza i dodela usluga timu.",
  },
  {
    id: "calendar",
    icon: CalendarDays,
    title: "Pregled kalendara i rezervacija",
    desc: "Drag-and-drop raspored, otkazivanje i upravljanje terminima.",
  },
];

const VideoPlaceholder = ({ label }) => (
  <div className="relative aspect-video bg-[#0A0D14] rounded-xl border border-[#2A2A2D] flex items-center justify-center group cursor-pointer overflow-hidden">
    <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
    <div className="w-14 h-14 rounded-full bg-[var(--color-primary)]/20 border border-[var(--color-primary)]/40 flex items-center justify-center transition-transform group-hover:scale-110">
      <Play className="w-6 h-6 text-[var(--color-primary)] ml-0.5" />
    </div>
    <span className="absolute bottom-3 left-3 text-[11px] text-[#6B7280]">{label}</span>
  </div>
);

const LandingPage = () => {
  const [activeTutorial, setActiveTutorial] = useState("setup");
  const active = OWNER_TUTORIALS.find(t => t.id === activeTutorial) || OWNER_TUTORIALS[0];

  return (
    <div className="min-h-screen bg-transparent text-white flex flex-col">
      {/* Header */}
      <header className="px-6 py-4 flex justify-end relative z-10">
        <Link
          to="/login"
          className="flex items-center gap-1.5 text-[#6B7280] hover:text-[var(--color-primary)] transition-colors text-sm"
          data-testid="header-login-btn"
        >
          <LogIn className="w-4 h-4" />
          {"Uloguj se"}
        </Link>
      </header>

      {/* Hero */}
      <div className="flex flex-col items-center justify-center px-6 pt-8 pb-16">
        <div className="text-center max-w-md mx-auto">
          <div className="w-16 h-16 rounded-2xl bg-[var(--color-primary)]/10 border border-[var(--color-primary)]/20 flex items-center justify-center mx-auto mb-6">
            <Sparkles className="w-7 h-7 text-[var(--color-primary)]" />
          </div>
          <h1 className="font-['Cormorant_Garamond'] text-4xl sm:text-5xl font-light mb-3 tracking-tight">
            BeautyMePi
          </h1>
          <p className="text-[#9CA3AF] text-base mb-10 leading-relaxed">
            {"Automatsko zakazivanje i upravljanje vašim salonima na Pi Network mreži."}
          </p>

          <div className="space-y-3">
            <Link to="/beauty-studio-bor" data-testid="demo-salon-btn">
              <Button className="w-full min-h-[56px] bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black font-medium text-base rounded-xl">
                <Sparkles className="w-5 h-5 mr-2" />
                {"Isprobajte Demo Salon"}
                <ChevronRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Link to="/vlasnici" data-testid="salon-owners-btn">
              <Button
                variant="outline"
                className="w-full min-h-[56px] border-[#2A2A2D] hover:bg-[var(--color-surface)] text-[#9CA3AF] hover:text-white font-medium text-base rounded-xl"
              >
                <Building2 className="w-5 h-5 mr-2" />
                {"Za vlasnike salona"}
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Tutorials Section */}
      <div className="max-w-3xl mx-auto px-6 pb-20 w-full">
        <h2 className="font-['Cormorant_Garamond'] text-2xl sm:text-3xl font-light text-center mb-10">
          {"Kako BeautyMePi funkcioniše"}
        </h2>

        {/* A) Owners */}
        <div className="mb-12">
          <p className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-primary)] mb-4">Za vlasnike salona</p>

          {/* Tab bar */}
          <div className="flex gap-2 overflow-x-auto pb-2 mb-4 scrollbar-hide">
            {OWNER_TUTORIALS.map((tut) => {
              const Icon = tut.icon;
              const isActive = tut.id === activeTutorial;
              return (
                <button
                  key={tut.id}
                  onClick={() => setActiveTutorial(tut.id)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm whitespace-nowrap transition-all shrink-0 ${
                    isActive
                      ? "bg-[var(--color-primary)]/10 border border-[var(--color-primary)]/40 text-[var(--color-primary)]"
                      : "bg-[var(--color-surface)] border border-[#2A2A2D] text-[#9CA3AF] hover:border-[#3A3A3D]"
                  }`}
                  data-testid={`tutorial-tab-${tut.id}`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {tut.title}
                </button>
              );
            })}
          </div>

          {/* Active tutorial card */}
          <div className="bg-[var(--color-surface)] border border-[#2A2A2D] rounded-2xl overflow-hidden" data-testid="tutorial-active-card">
            <VideoPlaceholder label={active.title} />
            <div className="p-5">
              <div className="flex items-center gap-2.5 mb-2">
                <active.icon className="w-4 h-4 text-[var(--color-primary)]" />
                <h3 className="font-medium text-white">{active.title}</h3>
              </div>
              <p className="text-sm text-[#9CA3AF] leading-relaxed">{active.desc}</p>
            </div>
          </div>
        </div>

        {/* B) Clients */}
        <div>
          <p className="text-[10px] uppercase tracking-[0.15em] text-[var(--color-primary)] mb-4">Za klijente</p>
          <div className="bg-[var(--color-surface)] border border-[#2A2A2D] rounded-2xl overflow-hidden" data-testid="client-tutorial-card">
            <VideoPlaceholder label="Zakazivanje u 3 klika" />
            <div className="p-5">
              <div className="flex items-center gap-2.5 mb-2">
                <MousePointerClick className="w-4 h-4 text-[var(--color-primary)]" />
                <h3 className="font-medium text-white">Brzo zakazivanje termina</h3>
              </div>
              <p className="text-sm text-[#9CA3AF] leading-relaxed">
                Izaberite uslugu, radnika i slobodan termin — sve u par klikova, bez registracije.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
