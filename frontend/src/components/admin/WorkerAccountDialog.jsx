import React from "react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { KeyRound, Copy, Check } from "lucide-react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "../ui/dialog";

const WorkerAccountDialog = ({
  open,
  onClose,
  target,
  mode,
  accountEmail,
  setAccountEmail,
  accountLoading,
  onCreateAccount,
  onResetPassword,
  createdAccount,
  copiedField,
  onCopy,
}) => {
  const isCreate = mode === "create";
  const hasResult = !!createdAccount;

  const title = hasResult
    ? (isCreate ? "Nalog kreiran" : "Lozinka resetovana")
    : (isCreate ? "Kreiraj nalog" : "Resetuj lozinku");

  const description = hasResult
    ? "Lozinka je prikazana samo jednom. Sačuvajte je."
    : isCreate
      ? `Kreiraj nalog za prijavu radnika ${target?.name}`
      : `Resetuj lozinku za radnika ${target?.name}`;

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="bg-[var(--color-surface)] border-[#2A2A2D] max-w-sm" data-testid="worker-account-dialog">
        <DialogHeader>
          <DialogTitle className="font-['Cormorant_Garamond'] text-2xl flex items-center gap-2">
            <KeyRound className="w-5 h-5 text-[var(--color-primary)]" />
            {title}
          </DialogTitle>
          <DialogDescription className="text-[#9CA3AF]">{description}</DialogDescription>
        </DialogHeader>

        {!hasResult ? (
          <div className="space-y-4 mt-2">
            {isCreate && (
              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Email za prijavu</label>
                <Input
                  type="email"
                  value={accountEmail}
                  onChange={(e) => setAccountEmail(e.target.value)}
                  placeholder="radnik@email.com"
                  className="bg-[var(--color-background)] border-[#2A2A2D]"
                  data-testid="worker-account-email-input"
                />
              </div>
            )}
            <Button
              onClick={isCreate ? onCreateAccount : onResetPassword}
              disabled={accountLoading}
              className="w-full bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black font-medium"
              data-testid={isCreate ? "worker-account-create-btn" : "worker-reset-password-btn"}
            >
              {accountLoading
                ? (isCreate ? "Kreiranje..." : "Resetovanje...")
                : (isCreate ? "Kreiraj nalog" : "Resetuj lozinku")
              }
            </Button>
          </div>
        ) : (
          <div className="space-y-3 mt-2">
            <div className="bg-[var(--color-background)] rounded-lg p-4 space-y-3">
              <div>
                <label className="text-[10px] text-[#6B7280] uppercase tracking-wider mb-1 block">Email</label>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white font-mono">{createdAccount.email}</span>
                  <button onClick={() => onCopy(createdAccount.email, "email")} className="p-1 hover:bg-[var(--color-surface)] rounded transition-colors" data-testid="copy-email-btn">
                    {copiedField === "email" ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5 text-[#9CA3AF]" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="text-[10px] text-[#6B7280] uppercase tracking-wider mb-1 block">Privremena lozinka</label>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[var(--color-primary)] font-mono font-bold">{createdAccount.temp_password}</span>
                  <button onClick={() => onCopy(createdAccount.temp_password, "password")} className="p-1 hover:bg-[var(--color-surface)] rounded transition-colors" data-testid="copy-password-btn">
                    {copiedField === "password" ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5 text-[#9CA3AF]" />}
                  </button>
                </div>
              </div>
            </div>
            <p className="text-[10px] text-amber-400/70">Ova lozinka se prikazuje samo jednom. Prosledite je radniku lično.</p>
            <Button
              onClick={onClose}
              variant="outline"
              className="w-full border-[#2A2A2D]"
              data-testid="close-account-dialog-btn"
            >
              Zatvori
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default WorkerAccountDialog;
