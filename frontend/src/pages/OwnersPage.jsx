import { Link } from "react-router-dom";
import { Building2, ChevronLeft, Sparkles, BarChart3, Clock, Globe, ClipboardList, Users, Share2 } from "lucide-react";

const OwnersPage = () => {
  return (
    <div className="min-h-screen bg-transparent text-white">
      <div className="max-w-lg mx-auto px-6 py-16">
        <Link
          to="/"
          className="flex items-center gap-1 text-[#9CA3AF] hover:text-white mb-10 transition-colors text-sm"
          data-testid="owners-back-link"
        >
          <ChevronLeft className="w-4 h-4" />
          Nazad
        </Link>

        <div className="text-center mb-10">
          <div className="w-14 h-14 rounded-2xl bg-[var(--color-primary)]/10 border border-[var(--color-primary)]/20 flex items-center justify-center mx-auto mb-5">
            <Building2 className="w-7 h-7 text-[var(--color-primary)]" />
          </div>
          <h1 className="font-['Cormorant_Garamond'] text-3xl sm:text-4xl font-light mb-3">
            {"Za vlasnike salona"}
          </h1>
          <p className="text-[#9CA3AF] leading-relaxed">
            {"Digitalizujte vaš salon i omogućite klijentima zakazivanje termina 24/7."}
          </p>
        </div>

        <div className="space-y-4 mb-10">
          <div className="bg-[var(--color-surface)] border border-[#2A2A2D] rounded-xl p-4 flex items-start gap-3">
            <Clock className="w-5 h-5 text-[var(--color-primary)] mt-0.5 shrink-0" />
            <div>
              <h3 className="font-medium text-white text-sm mb-0.5">{"Online zakazivanje 24/7"}</h3>
              <p className="text-xs text-[#9CA3AF]">{"Klijenti zakazuju termine bez poziva, u bilo koje doba dana."}</p>
            </div>
          </div>
          <div className="bg-[var(--color-surface)] border border-[#2A2A2D] rounded-xl p-4 flex items-start gap-3">
            <BarChart3 className="w-5 h-5 text-[var(--color-primary)] mt-0.5 shrink-0" />
            <div>
              <h3 className="font-medium text-white text-sm mb-0.5">{"Admin dashboard"}</h3>
              <p className="text-xs text-[#9CA3AF]">{"Pregled rasporeda, upravljanje zaposlenima i uslugama na jednom mestu."}</p>
            </div>
          </div>
          <div className="bg-[var(--color-surface)] border border-[#2A2A2D] rounded-xl p-4 flex items-start gap-3">
            <Globe className="w-5 h-5 text-[var(--color-primary)] mt-0.5 shrink-0" />
            <div>
              <h3 className="font-medium text-white text-sm mb-0.5">{"Jedinstveni link za vaš salon"}</h3>
              <p className="text-xs text-[#9CA3AF]">{"Delite link na društvenim mrežama i klijenti direktno zakazuju."}</p>
            </div>
          </div>
        </div>

        {/* How To Section */}
        <div className="mb-10">
          <h2 className="font-['Cormorant_Garamond'] text-2xl font-light text-center mb-6">{"Kako funkcioniše"}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-[var(--color-surface)] border border-[#2A2A2D] rounded-xl p-4 text-center relative" data-testid="how-to-step-1">
              <span className="absolute -top-2.5 left-1/2 -translate-x-1/2 w-5 h-5 rounded-full bg-[var(--color-primary)] text-black text-[10px] font-bold flex items-center justify-center">1</span>
              <ClipboardList className="w-6 h-6 text-[var(--color-primary)] mx-auto mb-2.5 mt-1" />
              <h3 className="font-medium text-white text-sm mb-1">{"Registracija i podešavanje"}</h3>
              <p className="text-[11px] text-[#9CA3AF] leading-relaxed">{"Prijavite salon, podesite radno vreme i unesite usluge."}</p>
            </div>
            <div className="bg-[var(--color-surface)] border border-[#2A2A2D] rounded-xl p-4 text-center relative" data-testid="how-to-step-2">
              <span className="absolute -top-2.5 left-1/2 -translate-x-1/2 w-5 h-5 rounded-full bg-[var(--color-primary)] text-black text-[10px] font-bold flex items-center justify-center">2</span>
              <Users className="w-6 h-6 text-[var(--color-primary)] mx-auto mb-2.5 mt-1" />
              <h3 className="font-medium text-white text-sm mb-1">{"Dodavanje tima"}</h3>
              <p className="text-[11px] text-[#9CA3AF] leading-relaxed">{"Dodajte zaposlene i dodelite im njihove rasporede."}</p>
            </div>
            <div className="bg-[var(--color-surface)] border border-[#2A2A2D] rounded-xl p-4 text-center relative" data-testid="how-to-step-3">
              <span className="absolute -top-2.5 left-1/2 -translate-x-1/2 w-5 h-5 rounded-full bg-[var(--color-primary)] text-black text-[10px] font-bold flex items-center justify-center">3</span>
              <Share2 className="w-6 h-6 text-[var(--color-primary)] mx-auto mb-2.5 mt-1" />
              <h3 className="font-medium text-white text-sm mb-1">{"Podelite link"}</h3>
              <p className="text-[11px] text-[#9CA3AF] leading-relaxed">{"Dobijate jedinstveni link za salon koji stavljate na Instagram/Facebook za direktno zakazivanje."}</p>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-[#C5A880]/10 to-[#C5A880]/5 border border-[var(--color-primary)]/20 rounded-xl p-6 text-center" data-testid="owners-coming-soon">
          <Sparkles className="w-6 h-6 text-[var(--color-primary)] mx-auto mb-3" />
          <h2 className="font-medium text-white text-lg mb-2">{"Uskoro otvaramo registraciju"}</h2>
          <p className="text-sm text-[#9CA3AF] leading-relaxed mb-4">
            {"Prijavite se na listu čekanja i budite među prvima koji će registrovati svoj salon na platformi."}
          </p>
          <p className="text-xs text-[#6B7280]">
            {"Kontakt: "}
            <a href="mailto:bornaja23@gmail.com" className="text-[var(--color-primary)] hover:underline">bornaja23@gmail.com</a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default OwnersPage;
