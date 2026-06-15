import { Link } from "react-router-dom";
import { Share2, Users, Gift, ChevronLeft } from "lucide-react";

const InfoPage = () => {
  return (
    <div className="min-h-screen bg-transparent text-white">
      <div className="max-w-lg mx-auto px-6 py-16">
        <Link
          to="/"
          className="flex items-center gap-1 text-[#9CA3AF] hover:text-white mb-10 transition-colors text-sm"
          data-testid="info-back-link"
        >
          <ChevronLeft className="w-4 h-4" />
          Nazad
        </Link>

        {/* Advice Card */}
        <div className="bg-[var(--color-surface)] border border-[#2A2A2D] rounded-xl p-5 space-y-3 mb-5" data-testid="booking-advice-card">
          <div className="flex items-start gap-3">
            <Share2 className="w-5 h-5 text-[var(--color-primary)] mt-0.5 shrink-0" />
            <div>
              <h3 className="font-medium text-white mb-1 text-lg">{"Kako da zakažete termin?"}</h3>
              <p className="text-sm text-[#9CA3AF] leading-relaxed">
                {"Proverite "}
                <span className="text-[var(--color-primary)]">Instagram</span>
                {", "}
                <span className="text-[var(--color-primary)]">Facebook</span>
                {" ili "}
                <span className="text-[var(--color-primary)]">Viber</span>
                {" profil vašeg željenog salona. Salon koji koristi našu platformu ima direktan link za zakazivanje u svojoj bio sekciji ili porukama."}
              </p>
            </div>
          </div>
        </div>

        {/* How it works */}
        <div className="bg-[var(--color-surface)] border border-[#2A2A2D] rounded-xl p-5 space-y-4 mb-5">
          <h3 className="font-medium text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-[var(--color-primary)]" />
            {"Kako to funkcioniše?"}
          </h3>
          <div className="space-y-3">
            <div className="flex gap-3 items-start">
              <span className="w-6 h-6 rounded-full bg-[var(--color-primary)]/20 text-[var(--color-primary)] text-xs font-bold flex items-center justify-center shrink-0">1</span>
              <p className="text-sm text-[#9CA3AF]">{"Salon vam deli svoj jedinstveni link za zakazivanje"}</p>
            </div>
            <div className="flex gap-3 items-start">
              <span className="w-6 h-6 rounded-full bg-[var(--color-primary)]/20 text-[var(--color-primary)] text-xs font-bold flex items-center justify-center shrink-0">2</span>
              <p className="text-sm text-[#9CA3AF]">{"Kliknete na link i izaberete uslugu, radnika i termin"}</p>
            </div>
            <div className="flex gap-3 items-start">
              <span className="w-6 h-6 rounded-full bg-[var(--color-primary)]/20 text-[var(--color-primary)] text-xs font-bold flex items-center justify-center shrink-0">3</span>
              <p className="text-sm text-[#9CA3AF]">{"Potvrdite rezervaciju — bez registracije!"}</p>
            </div>
          </div>
        </div>

        {/* Referral Section */}
        <div className="bg-gradient-to-br from-[#C5A880]/10 to-[#C5A880]/5 border border-[var(--color-primary)]/20 rounded-xl p-5 space-y-3" data-testid="referral-section">
          <div className="flex items-start gap-3">
            <Gift className="w-5 h-5 text-[var(--color-primary)] mt-0.5 shrink-0" />
            <div>
              <h3 className="font-medium text-white mb-1">{"Vaš salon nije na platformi?"}</h3>
              <p className="text-sm text-[#9CA3AF] leading-relaxed mb-3">
                {"Preporučite nas svom omiljenom salonu! Kada se registruju preko vaše preporuke, dobijate "}
                <span className="text-[var(--color-primary)] font-medium">besplatan termin</span>
                {" kao zahvalnost."}
              </p>
              <p className="text-xs text-[#6B7280]">
                {"Kontakt: "}
                <a href="mailto:bornaja23@gmail.com" className="text-[var(--color-primary)] hover:underline">bornaja23@gmail.com</a>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InfoPage;
