import { useState } from "react";
import { Link } from "react-router-dom";
import { ChevronLeft, Settings, Tag, Users, CalendarDays, Play, Sparkles, Send } from "lucide-react";

const TUTORIALS = [
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

const OwnersPage = () => {
  const [activeTab, setActiveTab] = useState("setup");
  const active = TUTORIALS.find(t => t.id === activeTab) || TUTORIALS[0];

  return (
    <div className="min-h-screen bg-transparent text-white">
      <div className="max-w-2xl mx-auto px-6 py-12">
        <Link
          to="/"
          className="flex items-center gap-1 text-[#9CA3AF] hover:text-white mb-10 transition-colors text-sm"
          data-testid="owners-back-link"
        >
          <ChevronLeft className="w-4 h-4" />
          Nazad
        </Link>

        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="font-['Cormorant_Garamond'] text-3xl sm:text-4xl font-light mb-3">
            {"Za vlasnike salona"}
          </h1>
          <p className="text-[#9CA3AF] leading-relaxed max-w-md mx-auto">
            {"Naučite kako da podesite i koristite BeautyMePi platformu za vaš salon."}
          </p>
        </div>

        {/* Video Tutorials */}
        <div className="mb-14">
          {/* Tab bar */}
          <div className="flex gap-2 overflow-x-auto pb-2 mb-4 scrollbar-hide">
            {TUTORIALS.map((tut) => {
              const Icon = tut.icon;
              const isActive = tut.id === activeTab;
              return (
                <button
                  key={tut.id}
                  onClick={() => setActiveTab(tut.id)}
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

          {/* Active tutorial */}
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

        {/* Activation CTA */}
        <div className="bg-gradient-to-br from-[var(--color-primary)]/8 to-transparent border border-[var(--color-primary)]/20 rounded-2xl p-8 text-center" data-testid="owners-activation-cta">
          <div className="w-12 h-12 rounded-xl bg-[var(--color-primary)]/10 flex items-center justify-center mx-auto mb-4">
            <Sparkles className="w-6 h-6 text-[var(--color-primary)]" />
          </div>
          <h2 className="font-['Cormorant_Garamond'] text-2xl font-light mb-2">
            {"Zatražite aktivaciju vašeg salona"}
          </h2>
          <p className="text-sm text-[#9CA3AF] leading-relaxed mb-6 max-w-sm mx-auto">
            {"Pošaljite nam poruku sa nazivom salona i kontakt podacima. Aktiviraćemo vaš profil u roku od 24h."}
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
            <span className="text-xs text-[#6B7280]">Pi username: @MarkoBornaja</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OwnersPage;
