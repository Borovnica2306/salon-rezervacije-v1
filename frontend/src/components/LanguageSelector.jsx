import { useState, useRef, useEffect } from "react";
import { useLang, SUPPORTED_LANGUAGES } from "../i18n";
import { Globe } from "lucide-react";

const LanguageSelector = () => {
  const { lang, setLang } = useLang();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const current = SUPPORTED_LANGUAGES.find(l => l.code === lang) || SUPPORTED_LANGUAGES[0];

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener("pointerdown", handler);
    return () => document.removeEventListener("pointerdown", handler);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-[#9CA3AF] hover:text-white transition-colors text-xs px-2 py-1.5 rounded-lg hover:bg-[var(--color-surface)]"
        data-testid="language-selector-btn"
      >
        <Globe className="w-3 h-3" />
        <span>{current.flag}</span>
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 w-40 bg-[var(--color-surface)] border border-[#2A2A2D] rounded-xl shadow-xl overflow-hidden z-50 animate-fade-in" data-testid="language-dropdown">
          {SUPPORTED_LANGUAGES.map((l) => (
            <button
              key={l.code}
              onClick={() => { setLang(l.code); setOpen(false); }}
              className={`w-full flex items-center gap-2.5 px-3 py-2.5 text-left text-sm transition-colors ${
                l.code === lang
                  ? "bg-[var(--color-primary)]/10 text-[var(--color-primary)]"
                  : "text-[#D1D5DB] hover:bg-[var(--color-background)]"
              }`}
              data-testid={`lang-option-${l.code}`}
            >
              <span className="text-base">{l.flag}</span>
              <span>{l.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default LanguageSelector;
