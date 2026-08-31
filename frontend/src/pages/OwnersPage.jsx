import { useState } from "react";
import { Link } from "react-router-dom";
import { Building2, ChevronLeft, Sparkles, BarChart3, Clock, Globe, ClipboardList, Users, Share2, X, ChevronRight } from "lucide-react";

const GUIDE_STEPS = [
  {
    icon: ClipboardList,
    title: "Registracija i podešavanje",
    short: "Prijavite salon, podesite radno vreme i unesite usluge.",
    sections: [
      {
        heading: "Kreiranje salona",
        items: [
          "Super Admin kreira novi salon u sistemu sa nazivom, gradom i emailom vlasnika.",
          "Automatski se generiše jedinstveni slug (npr. beauty-studio-bor) koji postaje deo vašeg booking linka.",
        ],
      },
      {
        heading: "Podešavanje radnog vremena",
        items: [
          "U Admin Dashboard > Podešavanja unesite početak i kraj radnog vremena salona.",
          "Ovo je globalni okvir — radnici ne mogu imati smene izvan ovih granica.",
        ],
      },
      {
        heading: "Kreiranje usluga",
        items: [
          "Idite na Admin Dashboard > Usluge i kliknite 'Dodaj uslugu'.",
          "Unesite naziv, izaberite kategoriju (Kosa, Nokti, Kozmetika...), trajanje u minutima i cenu.",
          "Usluge možete naknadno deaktivirati bez brisanja — neće se prikazivati klijentima.",
        ],
      },
    ],
  },
  {
    icon: Users,
    title: "Dodavanje tima",
    short: "Dodajte zaposlene i dodelite im njihove rasporede.",
    sections: [
      {
        heading: "Kreiranje radnika",
        items: [
          "U Admin Dashboard > Radnici kliknite 'Dodaj Radnika'.",
          "Unesite ime, odaberite kategorije usluga koje radnik pruža, radno vreme i neradne dane.",
          "Pauza se podešava odvojeno (npr. 13:00–13:30) i automatski se blokira u kalendaru.",
        ],
      },
      {
        heading: "Kreiranje naloga za prijavu",
        items: [
          "Na kartici radnika kliknite 'Kreiraj nalog za prijavu'.",
          "Unesite email radnika — sistem automatski generiše privremenu lozinku.",
          "Kopirajte lozinku i prosledite radniku. Pri prvom loginu, moraće da postavi svoju lozinku.",
        ],
      },
      {
        heading: "Uloge i pristup",
        items: [
          "Radnik (Worker) vidi samo svoj raspored za narednih 7 dana u read-only modu.",
          "Ne može menjati, otkazivati ili dodavati rezervacije — to ostaje na adminu.",
          "Admin može u svakom trenutku resetovati lozinku radnika ili obrisati nalog.",
        ],
      },
    ],
  },
  {
    icon: Share2,
    title: "Podelite link",
    short: "Dobijate jedinstveni link za salon koji stavljate na Instagram/Facebook.",
    sections: [
      {
        heading: "Vaš jedinstveni URL",
        items: [
          "Svaki salon dobija link u formatu: vasadomena.com/beauty-studio-bor",
          "Ovaj link vodi direktno na stranicu za zakazivanje — klijent ne mora da se registruje.",
        ],
      },
      {
        heading: "Gde ga podeliti",
        items: [
          "Instagram bio — stavite link u bio sekciju vašeg poslovnog profila.",
          "Facebook stranica — dodajte kao 'Book Now' dugme ili u opis.",
          "Viber/WhatsApp grupa — pošaljite link u grupu sa stalnim klijentima.",
          "Google Maps — dodajte link u opis vaše lokacije.",
        ],
      },
      {
        heading: "Kako klijent zakazuje",
        items: [
          "Klijent otvara link, bira usluge i radnike, vidi slobodne termine u realnom vremenu.",
          "Sistem automatski sprečava dupla zakazivanja i poštuje pauze i neradne dane.",
          "Klijent unosi ime, telefon i email — potvrda dolazi odmah.",
        ],
      },
    ],
  },
];

const GuideModal = ({ step, onClose }) => {
  if (!step) return null;
  const Icon = step.icon;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose} data-testid="guide-modal-backdrop">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />
      <div
        className="relative bg-[var(--color-surface)] border border-[#2A2A2D] rounded-2xl w-full max-w-md max-h-[85vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
        data-testid="guide-modal-content"
      >
        {/* Header */}
        <div className="sticky top-0 z-10 bg-[var(--color-surface)] border-b border-[#2A2A2D] px-5 py-4 flex items-center justify-between rounded-t-2xl">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[var(--color-primary)]/10 flex items-center justify-center">
              <Icon className="w-4 h-4 text-[var(--color-primary)]" />
            </div>
            <h2 className="font-['Cormorant_Garamond'] text-xl font-light">{step.title}</h2>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg hover:bg-[var(--color-background)] flex items-center justify-center transition-colors"
            data-testid="guide-modal-close"
          >
            <X className="w-4 h-4 text-[#9CA3AF]" />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-4 space-y-5">
          {step.sections.map((section, sIdx) => (
            <div key={sIdx}>
              <h3 className="text-sm font-medium text-[var(--color-primary)] mb-2.5 flex items-center gap-1.5">
                <ChevronRight className="w-3.5 h-3.5" />
                {section.heading}
              </h3>
              <ul className="space-y-2">
                {section.items.map((item, iIdx) => (
                  <li key={iIdx} className="flex items-start gap-2.5 text-[13px] text-[#BFBFC4] leading-relaxed">
                    <span className="w-1 h-1 rounded-full bg-[#6B7280] mt-2 shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-[var(--color-surface)] border-t border-[#2A2A2D] px-5 py-3 rounded-b-2xl">
          <button
            onClick={onClose}
            className="w-full py-2.5 rounded-lg bg-[var(--color-background)] hover:bg-[var(--color-primary)]/10 text-sm text-[#9CA3AF] hover:text-white transition-colors"
            data-testid="guide-modal-close-btn"
          >
            Zatvori
          </button>
        </div>
      </div>
    </div>
  );
};

const OwnersPage = () => {
  const [activeGuide, setActiveGuide] = useState(null);

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

        {/* How To Section — Interactive */}
        <div className="mb-10">
          <h2 className="font-['Cormorant_Garamond'] text-2xl font-light text-center mb-2">{"Kako funkcioniše"}</h2>
          <p className="text-[11px] text-[#6B7280] text-center mb-6">Kliknite na korak za detaljna uputstva</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {GUIDE_STEPS.map((step, idx) => {
              const Icon = step.icon;
              return (
                <button
                  key={idx}
                  onClick={() => setActiveGuide(step)}
                  className="bg-[var(--color-surface)] border border-[#2A2A2D] rounded-xl p-4 text-center relative cursor-pointer transition-all duration-200 hover:border-[var(--color-primary)]/50 hover:bg-[var(--color-primary)]/5 active:scale-[0.97] group"
                  data-testid={`how-to-step-${idx + 1}`}
                >
                  <span className="absolute -top-2.5 left-1/2 -translate-x-1/2 w-5 h-5 rounded-full bg-[var(--color-primary)] text-black text-[10px] font-bold flex items-center justify-center">{idx + 1}</span>
                  <Icon className="w-6 h-6 text-[var(--color-primary)] mx-auto mb-2.5 mt-1 transition-transform group-hover:scale-110" />
                  <h3 className="font-medium text-white text-sm mb-1">{step.title}</h3>
                  <p className="text-[11px] text-[#9CA3AF] leading-relaxed">{step.short}</p>
                </button>
              );
            })}
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

      <GuideModal step={activeGuide} onClose={() => setActiveGuide(null)} />
    </div>
  );
};

export default OwnersPage;
