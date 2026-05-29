import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "../App";
import { Button } from "../components/ui/button";
import { Scissors, Building2, ChevronRight, MapPin, Loader2 } from "lucide-react";

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
  const [salons, setSalons] = useState([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleCountrySelect = async (country) => {
    setSelectedCountry(country);
    setLoading(true);
    try {
      const res = await axios.get(`${API}/tenants/by-country/${country.code}`);
      setSalons(res.data);
    } catch {
      setSalons([]);
    } finally {
      setLoading(false);
    }
  };

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
              Pronađite i zakažite termin u omiljenom salonu lepote
            </p>

            <div className="space-y-3">
              <Button
                onClick={() => setView("country")}
                className="w-full min-h-[56px] bg-[#C5A880] hover:bg-[#B89970] text-black font-medium text-base rounded-xl"
                data-testid="book-appointment-btn"
              >
                <Scissors className="w-5 h-5 mr-2" />
                Želim da zakažem termin
                <ChevronRight className="w-5 h-5 ml-2" />
              </Button>

              <Button
                onClick={() => setView("owners")}
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

      {/* Country Selection */}
      {view === "country" && (
        <div className="min-h-screen flex flex-col items-center justify-center px-6">
          <div className="w-full max-w-md mx-auto">
            <button
              onClick={() => { setView("hero"); setSelectedCountry(null); setSalons([]); }}
              className="flex items-center gap-1 text-[#9CA3AF] hover:text-white mb-6 transition-colors"
              data-testid="back-to-hero"
            >
              <ChevronRight className="w-4 h-4 rotate-180" />
              <span className="text-sm">Nazad</span>
            </button>

            <div className="flex items-center gap-2 mb-6">
              <MapPin className="w-5 h-5 text-[#C5A880]" />
              <h2 className="text-xl font-medium">Izaberite vašu zemlju</h2>
            </div>

            <div className="space-y-2">
              {COUNTRIES.map((c) => (
                <button
                  key={c.code}
                  onClick={() => handleCountrySelect(c)}
                  className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all text-left ${
                    selectedCountry?.code === c.code
                      ? "border-[#C5A880] bg-[#C5A880]/5"
                      : "border-[#2A2A2D] bg-[#141416] hover:border-[#C5A880]/40"
                  }`}
                  data-testid={`country-${c.code}`}
                >
                  <span className="text-2xl">{c.flag}</span>
                  <span className="font-medium flex-1">{c.name}</span>
                  <ChevronRight className="w-4 h-4 text-[#6B7280]" />
                </button>
              ))}
            </div>

            {/* Salon List */}
            {selectedCountry && (
              <div className="mt-6" data-testid="salon-list">
                <p className="text-sm text-[#9CA3AF] mb-3">
                  Saloni u zemlji: {selectedCountry.name}
                </p>
                {loading ? (
                  <div className="text-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto text-[#C5A880]" />
                  </div>
                ) : salons.length === 0 ? (
                  <div className="text-center py-8 text-[#6B7280] bg-[#141416] rounded-xl border border-[#2A2A2D]">
                    Nema registrovanih salona u ovoj zemlji.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {salons.map((s) => (
                      <button
                        key={s.slug}
                        onClick={() => navigate(`/${s.slug}`)}
                        className="w-full flex items-center justify-between p-4 rounded-xl border border-[#2A2A2D] bg-[#141416] hover:border-[#C5A880]/50 transition-all text-left"
                        data-testid={`salon-${s.slug}`}
                      >
                        <div>
                          <span className="font-medium text-white">{s.name}</span>
                          {s.city && <span className="text-xs text-[#6B7280] ml-2">{s.city}</span>}
                        </div>
                        <ChevronRight className="w-4 h-4 text-[#C5A880]" />
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Salon Owners Section */}
      {view === "owners" && (
        <div className="min-h-screen flex flex-col items-center justify-center px-6">
          <div className="w-full max-w-md mx-auto text-center">
            <button
              onClick={() => setView("hero")}
              className="flex items-center gap-1 text-[#9CA3AF] hover:text-white mb-6 transition-colors"
              data-testid="back-to-hero-owners"
            >
              <ChevronRight className="w-4 h-4 rotate-180" />
              <span className="text-sm">Nazad</span>
            </button>

            <Building2 className="w-12 h-12 text-[#C5A880] mx-auto mb-4" />
            <h2 className="text-2xl font-medium mb-3">Za vlasnike salona</h2>
            <p className="text-[#9CA3AF] mb-8 leading-relaxed">
              Registrujte svoj salon i omogućite klijentima online zakazivanje termina.
              Kontaktirajte nas za više informacija.
            </p>
            <div className="bg-[#141416] border border-[#2A2A2D] rounded-xl p-6 text-left">
              <p className="text-sm text-[#9CA3AF] mb-2">Kontakt za registraciju:</p>
              <p className="text-[#C5A880] font-medium">bornaja23@gmail.com</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LandingPage;
