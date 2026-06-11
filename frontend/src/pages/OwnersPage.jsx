import { Building2, ChevronLeft, Sparkles, BarChart3, Clock, Globe } from "lucide-react";
import { Button } from "../components/ui/button";

const OwnersPage = () => {
  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white">
      <div className="max-w-lg mx-auto px-6 py-16">
        <a
          href="/"
          className="flex items-center gap-1 text-[#9CA3AF] hover:text-white mb-10 transition-colors text-sm"
          data-testid="owners-back-link"
        >
          <ChevronLeft className="w-4 h-4" />
          Nazad
        </a>

        <div className="text-center mb-10">
          <div className="w-14 h-14 rounded-2xl bg-[#C5A880]/10 border border-[#C5A880]/20 flex items-center justify-center mx-auto mb-5">
            <Building2 className="w-7 h-7 text-[#C5A880]" />
          </div>
          <h1 className="font-['Cormorant_Garamond'] text-3xl sm:text-4xl font-light mb-3">
            {"Za vlasnike salona"}
          </h1>
          <p className="text-[#9CA3AF] leading-relaxed">
            {"Digitalizujte vaš salon i omogućite klijentima zakazivanje termina 24/7."}
          </p>
        </div>

        <div className="space-y-4 mb-10">
          <div className="bg-[#141416] border border-[#2A2A2D] rounded-xl p-4 flex items-start gap-3">
            <Clock className="w-5 h-5 text-[#C5A880] mt-0.5 shrink-0" />
            <div>
              <h3 className="font-medium text-white text-sm mb-0.5">{"Online zakazivanje 24/7"}</h3>
              <p className="text-xs text-[#9CA3AF]">{"Klijenti zakazuju termine bez poziva, u bilo koje doba dana."}</p>
            </div>
          </div>
          <div className="bg-[#141416] border border-[#2A2A2D] rounded-xl p-4 flex items-start gap-3">
            <BarChart3 className="w-5 h-5 text-[#C5A880] mt-0.5 shrink-0" />
            <div>
              <h3 className="font-medium text-white text-sm mb-0.5">{"Admin dashboard"}</h3>
              <p className="text-xs text-[#9CA3AF]">{"Pregled rasporeda, upravljanje zaposlenima i uslugama na jednom mestu."}</p>
            </div>
          </div>
          <div className="bg-[#141416] border border-[#2A2A2D] rounded-xl p-4 flex items-start gap-3">
            <Globe className="w-5 h-5 text-[#C5A880] mt-0.5 shrink-0" />
            <div>
              <h3 className="font-medium text-white text-sm mb-0.5">{"Jedinstveni link za vaš salon"}</h3>
              <p className="text-xs text-[#9CA3AF]">{"Delite link na društvenim mrežama i klijenti direktno zakazuju."}</p>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-[#C5A880]/10 to-[#C5A880]/5 border border-[#C5A880]/20 rounded-xl p-6 text-center" data-testid="owners-coming-soon">
          <Sparkles className="w-6 h-6 text-[#C5A880] mx-auto mb-3" />
          <h2 className="font-medium text-white text-lg mb-2">{"Uskoro otvaramo registraciju"}</h2>
          <p className="text-sm text-[#9CA3AF] leading-relaxed mb-4">
            {"Prijavite se na listu čekanja i budite među prvima koji će registrovati svoj salon na platformi."}
          </p>
          <p className="text-xs text-[#6B7280]">
            {"Kontakt: "}
            <a href="mailto:bornaja23@gmail.com" className="text-[#C5A880] hover:underline">bornaja23@gmail.com</a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default OwnersPage;
