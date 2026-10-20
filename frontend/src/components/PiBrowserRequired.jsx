import { toast } from "sonner";
import { Smartphone, Copy } from "lucide-react";
import { useLang } from "../i18n";
import LanguageSelector from "./LanguageSelector";

const PiBrowserRequired = ({ salonName }) => {
  const { t } = useLang();
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      toast.success(t("linkCopied"));
    } catch {
      toast.error(window.location.href);
    }
  };

  return (
    <div className="min-h-screen bg-transparent flex flex-col" data-testid="pi-browser-required">
      <header className="max-w-lg w-full mx-auto px-4 py-3 flex items-center justify-between">
        <span className="text-[#9CA3AF] text-xs">{salonName || "Beauty Studio"}</span>
        <LanguageSelector />
      </header>
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-[var(--color-surface)] rounded-2xl border border-[#2A2A2D] p-8 text-center animate-fade-in">
          <div className="w-16 h-16 rounded-2xl bg-[var(--color-primary)]/15 border border-[var(--color-primary)]/30 flex items-center justify-center mx-auto mb-6">
            <Smartphone className="w-8 h-8 text-[var(--color-primary)]" />
          </div>
          <h1 className="font-['Cormorant_Garamond'] text-3xl font-light mb-3" data-testid="pi-browser-required-title">{t("piBrowserOnlyTitle")}</h1>
          <p className="text-sm text-[#9CA3AF] leading-relaxed mb-6" data-testid="pi-browser-required-text">{t("piBrowserOnlyText")}</p>
          <button
            type="button"
            onClick={copy}
            className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black font-medium text-sm transition-colors"
            data-testid="pi-browser-copy-link-btn"
          >
            <Copy className="w-4 h-4" />
            {t("copyLink")}
          </button>
        </div>
      </div>
    </div>
  );
};

export default PiBrowserRequired;
