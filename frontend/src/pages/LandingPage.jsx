import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Scissors, Building2, ChevronRight, LogIn } from "lucide-react";

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white flex flex-col">
      {/* Header with discrete login */}
      <header className="px-6 py-4 flex justify-end relative z-10">
        <Link
          to="/login"
          className="flex items-center gap-1.5 text-[#6B7280] hover:text-[#C5A880] transition-colors text-sm"
          data-testid="header-login-btn"
        >
          <LogIn className="w-4 h-4" />
          {"Uloguj se"}
        </Link>
      </header>

      {/* Hero */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 -mt-16">
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
            <Link to="/info" data-testid="book-appointment-btn">
              <Button className="w-full min-h-[56px] bg-[#C5A880] hover:bg-[#B89970] text-black font-medium text-base rounded-xl">
                <Scissors className="w-5 h-5 mr-2" />
                {"Želim da zakažem termin"}
                <ChevronRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>

            <Link to="/vlasnici" data-testid="salon-owners-btn">
              <Button
                variant="outline"
                className="w-full min-h-[56px] border-[#2A2A2D] hover:bg-[#141416] text-[#9CA3AF] hover:text-white font-medium text-base rounded-xl"
              >
                <Building2 className="w-5 h-5 mr-2" />
                {"Za vlasnike salona"}
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
