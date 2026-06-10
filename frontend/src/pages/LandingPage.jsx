import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Scissors, Building2, ChevronRight, MapPin, Share2, Users, Gift } from "lucide-react";

const COUNTRIES = [
  { code: "RS", name: "Srbija", flag: "🇷🇸" },
  { code: "HR", name: "Hrvatska", flag: "🇭🇷" },
  { code: "BA", name: "Bosna i Hercegovina", flag: "🇧🇦" },
  { code: "ME", name: "Crna Gora", flag: "🇲🇪" },
  { code: "DE", name: "Nemačka", flag: "🇩🇪" },
  { code: "AT", name: "Austrija", flag: "🇦🇹" },
  { code: "CH", name: "Švajcarska", flag: "🇨🇭" },
];

const LandingPage = () => {
  const [view, setView] = useState("hero");
  const [selectedCountry, setSelectedCountry] = useState(null);
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white">

      {/* Hero Section */}
      {view === "hero" && (
        <div className="min-h-screen flex flex-col items-center justify-center px-6">
          <div className="text-center max-w-md mx-auto">
            <div className="w-16 h-16 rounded-2xl bg-[#C5A880]/10 border border-[#C5A880]/20 flex items-center justify-center mx-auto mb-6">
              <Scissors className="w-7 h-7 text-[#C5A880]" />
            </div>
            <h1 className="font-['Cormorant_Garamond'] text-4xl sm:text-5xl font-light mb-3 tracking-tight">
              Beauty Booking
            </h1>
            <p className="text-[#9CA3AF] text-base mb-10 leading-relaxed">
              {"Pronađite i zakažite termin u omiljenom salonu lepote"}
            </p>

            <div className="space-y-3">
              <Button
                onClick={() => setView("country")}
                className="w-full min-h-[56px] bg-[#C5A880] hover:bg-[#B89970] text-black font-medium text-base rounded-xl"
                data-testid="book-appointment-btn"
              >
                <Scissors className="w-5 h-5 mr-2" />
                {"Želim da zakažem termin"}
                <ChevronRight className="w-5 h-5 ml-2" />
              </Button>

              <Button
                onClick={() => navigate("/login")}
                variant="outline"
                className="w-full min-h-[56px] border-[#2A2A2D] hover:bg-[#141416] text-[#9CA3AF] hover:text-white font-medium text-base rounded-xl"
                data-testid="salon-owners-btn"
              >
                <Building2 className="w-5 h-5 mr-2" />
                Za vlasnike salona
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Country Selection -> Advice */}
      {view === "country" && (
        <div className="min-h-screen flex flex-col items-center justify-center px-6">
          <div className="w-full max-w-md mx-auto">
            <button
              onClick={() => { setView("hero"); setSelectedCountry(null); }}
              className="flex items-center gap-1 text-[#9CA3AF] hover:text-white mb-6 transition-colors"
              data-testid="back-to-hero"
            >
              <ChevronRight className="w-4 h-4 rotate-180" />
              <span className="text-sm">Nazad</span>
            </button>

            {!selectedCountry ? (
              <>
                <div className="flex items-center gap-2 mb-6">
                  <MapPin className="w-5 h-5 text-[#C5A880]" />
                  <h2 className="text-xl font-medium">{"Izaberite vašu zemlju"}</h2>
                </div>

                <div className="space-y-2">
                  {COUNTRIES.map((c) => (
                    <button
                      key={c.code}
                      onClick={() => setSelectedCountry(c)}
                      className="w-full flex items-center gap-4 p-4 rounded-xl border border-[#2A2A2D] bg-[#141416] hover:border-[#C5A880]/40 transition-all text-left"
                      data-testid={`country-${c.code}`}
                    >
                      <span className="text-2xl">{c.flag}</span>
                      <span className="font-medium flex-1">{c.name}</span>
                      <ChevronRight className="w-4 h-4 text-[#6B7280]" />
                    </button>
                  ))}
                </div>
              </>
            ) : (
              <div className="space-y-5 animate-fade-in" data-testid="country-advice-section">
                <div className="flex items-center gap-2 mb-2">
                  <MapPin className="w-5 h-5 text-[#C5A880]" />
                  <h2 className="text-xl font-medium">{selectedCountry.flag} {selectedCountry.name}</h2>
                </div>

                {/* Advice Card */}
                <div className="bg-[#141416] border border-[#2A2A2D] rounded-xl p-5 space-y-3" data-testid="booking-advice-card">
                  <div className="flex items-start gap-3">
                    <Share2 className="w-5 h-5 text-[#C5A880] mt-0.5 shrink-0" />
                    <div>
                      <h3 className="font-medium text-white mb-1">{"Kako da zakažete termin?"}</h3>
                      <p className="text-sm text-[#9CA3AF] leading-relaxed">
                        {"Proverite "}
                        <span className="text-[#C5A880]">Instagram</span>
                        {", "}
                        <span className="text-[#C5A880]">Facebook</span>
                        {" ili "}
                        <span className="text-[#C5A880]">Viber</span>
                        {" profil vašeg željenog salona. Salon koji koristi našu platformu ima direktan link za zakazivanje u svojoj bio sekciji ili porukama."}
                      </p>
                    </div>
                  </div>
                </div>

                {/* How it works */}
                <div className="bg-[#141416] border border-[#2A2A2D] rounded-xl p-5 space-y-4">
                  <h3 className="font-medium text-white flex items-center gap-2">
                    <Users className="w-5 h-5 text-[#C5A880]" />
                    {"Kako to funkcioniše?"}
                  </h3>
                  <div className="space-y-3">
                    <div className="flex gap-3 items-start">
                      <span className="w-6 h-6 rounded-full bg-[#C5A880]/20 text-[#C5A880] text-xs font-bold flex items-center justify-center shrink-0">1</span>
                      <p className="text-sm text-[#9CA3AF]">{"Salon vam deli svoj jedinstveni link za zakazivanje"}</p>
                    </div>
                    <div className="flex gap-3 items-start">
                      <span className="w-6 h-6 rounded-full bg-[#C5A880]/20 text-[#C5A880] text-xs font-bold flex items-center justify-center shrink-0">2</span>
                      <p className="text-sm text-[#9CA3AF]">{"Kliknete na link i izaberete uslugu, radnika i termin"}</p>
                    </div>
                    <div className="flex gap-3 items-start">
                      <span className="w-6 h-6 rounded-full bg-[#C5A880]/20 text-[#C5A880] text-xs font-bold flex items-center justify-center shrink-0">3</span>
                      <p className="text-sm text-[#9CA3AF]">{"Potvrdite rezervaciju — bez registracije!"}</p>
                    </div>
                  </div>
                </div>

                {/* Referral Section */}
                <div className="bg-gradient-to-br from-[#C5A880]/10 to-[#C5A880]/5 border border-[#C5A880]/20 rounded-xl p-5 space-y-3" data-testid="referral-section">
                  <div className="flex items-start gap-3">
                    <Gift className="w-5 h-5 text-[#C5A880] mt-0.5 shrink-0" />
                    <div>
                      <h3 className="font-medium text-white mb-1">{"Vaš salon nije na platformi?"}</h3>
                      <p className="text-sm text-[#9CA3AF] leading-relaxed mb-3">
                        {"Preporučite nas svom omiljenom salonu! Kada se registruju preko vaše preporuke, dobijate "}
                        <span className="text-[#C5A880] font-medium">besplatan termin</span>
                        {" kao zahvalnost."}
                      </p>
                      <p className="text-xs text-[#6B7280]">
                        {"Kontakt: "}
                        <a href="mailto:bornaja23@gmail.com" className="text-[#C5A880] hover:underline">bornaja23@gmail.com</a>
                      </p>
                    </div>
                  </div>
                </div>

                <Button
                  onClick={() => setSelectedCountry(null)}
                  variant="outline"
                  className="w-full min-h-[48px] border-[#2A2A2D] hover:bg-[#141416] text-[#9CA3AF] hover:text-white rounded-xl"
                  data-testid="change-country-btn"
                >
                  <ChevronRight className="w-4 h-4 rotate-180 mr-1" />
                  {"Izaberite drugu zemlju"}
                </Button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LandingPage;
