import React from "react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger,
} from "../ui/dialog";
import { Plus } from "lucide-react";

const WorkerFormDialog = ({
  open,
  onOpenChange,
  editingEmployee,
  form,
  setForm,
  categories,
  servicesByCategory,
  salonClosedDays,
  startOptions,
  endOptions,
  dayLabels,
  toggleCategory,
  toggleDayOff,
  onSubmit,
  resetForm,
}) => {
  return (
    <Dialog open={open} onOpenChange={(o) => { onOpenChange(o); if (!o) resetForm(); }}>
      <DialogTrigger asChild>
        <Button className="bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black" data-testid="add-employee-btn">
          <Plus className="w-4 h-4 mr-2" />
          Dodaj Radnika
        </Button>
      </DialogTrigger>
      <DialogContent className="bg-[var(--color-surface)] border-[#2A2A2D] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="font-['Cormorant_Garamond'] text-2xl">
            {editingEmployee ? "Izmeni Radnika" : "Novi Radnik"}
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 mt-4">
          <div>
            <label className="text-sm text-[#9CA3AF] mb-2 block">Ime</label>
            <Input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Ime radnika"
              className="bg-[var(--color-background)] border-[#2A2A2D]"
              data-testid="employee-name-input"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-[#9CA3AF] mb-2 block">{"Početak rada"}</label>
              <select
                value={form.work_start}
                onChange={(e) => {
                  const val = e.target.value;
                  setForm(prev => ({
                    ...prev,
                    work_start: val,
                    work_end: prev.work_end < val ? val : prev.work_end,
                  }));
                }}
                className="w-full bg-[var(--color-background)] border border-[#2A2A2D] rounded-lg px-3 h-10 text-white text-sm focus:border-[var(--color-primary)] focus:outline-none"
                data-testid="employee-work-start"
              >
                {startOptions.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm text-[#9CA3AF] mb-2 block">{"Kraj rada"}</label>
              <select
                value={form.work_end}
                onChange={(e) => setForm({ ...form, work_end: e.target.value })}
                className="w-full bg-[var(--color-background)] border border-[#2A2A2D] rounded-lg px-3 h-10 text-white text-sm focus:border-[var(--color-primary)] focus:outline-none"
                data-testid="employee-work-end"
              >
                {endOptions.filter(t => t >= form.work_start).map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-[#9CA3AF] mb-2 block">Pauza od</label>
              <select
                value={form.break_start}
                onChange={(e) => setForm({ ...form, break_start: e.target.value })}
                className="w-full bg-[var(--color-background)] border border-[#2A2A2D] rounded-lg px-3 h-10 text-white text-sm focus:border-[var(--color-primary)] focus:outline-none"
                data-testid="employee-break-start"
              >
                <option value="">Bez pauze</option>
                {startOptions.filter(t => t >= form.work_start && t < form.work_end).map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm text-[#9CA3AF] mb-2 block">Pauza do</label>
              <select
                value={form.break_end}
                onChange={(e) => setForm({ ...form, break_end: e.target.value })}
                className="w-full bg-[var(--color-background)] border border-[#2A2A2D] rounded-lg px-3 h-10 text-white text-sm focus:border-[var(--color-primary)] focus:outline-none"
                data-testid="employee-break-end"
              >
                <option value="">Bez pauze</option>
                {endOptions.filter(t => t > (form.break_start || form.work_start) && t <= form.work_end).map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="text-sm text-[#9CA3AF] mb-2 block">Neradni dani</label>
            <div className="flex gap-2 flex-wrap">
              {dayLabels.map((label, idx) => {
                const isOff = form.days_off.includes(idx);
                const salonClosed = salonClosedDays.includes(idx);
                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => !salonClosed && toggleDayOff(idx)}
                    disabled={salonClosed}
                    className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                      salonClosed
                        ? "bg-[var(--color-background)] border border-[#2A2A2D] text-[#3A3A3D] cursor-not-allowed line-through"
                        : isOff
                          ? "bg-[var(--color-primary)] text-black"
                          : "bg-[var(--color-background)] border border-[#2A2A2D] text-[#9CA3AF]"
                    }`}
                    title={salonClosed ? "Salon je zatvoren ovog dana" : ""}
                  >
                    {label}
                  </button>
                );
              })}
            </div>
            {salonClosedDays.length > 0 && (
              <p className="text-[10px] text-[#6B7280] mt-1">{"Precrtani dani: salon je zatvoren."}</p>
            )}
          </div>

          <div>
            <label className="text-sm text-[#9CA3AF] mb-2 block">Kategorije usluga</label>
            <div className="space-y-2">
              {categories.map((cat) => {
                const catServices = servicesByCategory[cat.key] || [];
                const isSelected = form.categories.includes(cat.key);
                return (
                  <button
                    key={cat.key}
                    type="button"
                    onClick={() => toggleCategory(cat.key)}
                    className={`w-full p-3 rounded-lg text-left text-sm transition-colors ${
                      isSelected
                        ? "bg-[var(--color-primary)]/10 border border-[var(--color-primary)]"
                        : "bg-[var(--color-background)] border border-[#2A2A2D] hover:border-[var(--color-primary)]/50"
                    }`}
                    data-testid={`category-toggle-${cat.key}`}
                  >
                    <span className="font-medium">{cat.label}</span>
                    <span className="text-[#6B7280] ml-2 text-xs">({catServices.length} usluga)</span>
                  </button>
                );
              })}
            </div>
          </div>

          <Button
            onClick={onSubmit}
            className="w-full bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black"
            data-testid="save-employee-btn"
          >
            {editingEmployee ? "Sačuvaj Izmene" : "Dodaj Radnika"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default WorkerFormDialog;
