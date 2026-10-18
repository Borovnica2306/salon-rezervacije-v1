import React, { useState, useEffect } from "react";
import { toast } from "sonner";
import axios from "axios";
import { API, useTenant, getTenantHeaders, getToken } from "../../App";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Scissors, Clock, Plus, Edit2, Trash2, ChevronDown, ChevronsDown, ChevronsUp } from "lucide-react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription,
} from "../ui/dialog";
import DeleteWorkerDialog from "./DeleteWorkerDialog";

const ServicesPage = () => {
  const tenant = useTenant();
  const [services, setServices] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingService, setEditingService] = useState(null);
  const [openCats, setOpenCats] = useState(null);
  const [serviceToDelete, setServiceToDelete] = useState(null);
  const [form, setForm] = useState({
    name: "",
    category: "hair",
    duration: 30,
    price: 0,
    description: "",
  });

  const token = getToken();
  const headers = { Authorization: `Bearer ${token}`, ...getTenantHeaders(tenant?.tenant_id) };

  useEffect(() => {
    if (tenant?.tenant_id) {
      fetchServices();
      fetchCategories();
    }
  }, [tenant?.tenant_id]);

  const fetchCategories = async () => {
    try {
      const res = await axios.get(`${API}/categories`, { headers });
      setCategories(res.data);
    } catch (error) {
      console.error("Error fetching categories:", error);
    }
  };

  const fetchServices = async () => {
    try {
      const response = await axios.get(`${API}/services?active_only=false`, { headers });
      setServices(response.data);
    } catch (error) {
      toast.error("Greška pri učitavanju");
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setForm({
      name: "",
      category: "hair",
      duration: 30,
      price: 0,
      description: "",
    });
    setEditingService(null);
  };

  const handleEdit = (service) => {
    setEditingService(service);
    setForm({
      name: service.name,
      category: service.category,
      duration: service.duration,
      price: service.price,
      description: service.description || "",
    });
    setDialogOpen(true);
  };

  const handleSubmit = async () => {
    if (!form.name.trim()) {
      toast.error("Unesite naziv usluge");
      return;
    }

    try {
      if (editingService) {
        await axios.put(`${API}/services/${editingService.id}`, form, { headers });
        toast.success("Usluga ažurirana");
      } else {
        await axios.post(`${API}/services`, form, { headers });
        toast.success("Usluga dodata");
      }
      
      setDialogOpen(false);
      resetForm();
      fetchServices();
    } catch (error) {
      toast.error("Greška pri čuvanju");
    }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API}/services/${id}`, { headers });
      toast.success("Usluga je trajno obrisana");
      setServiceToDelete(null);
      fetchServices();
    } catch (error) {
      toast.error("Greška pri brisanju");
    }
  };

  const categoryLabels = Object.fromEntries(
    categories.map(c => [c.key, c.label])
  );
  const usedCats = Object.keys(categoryLabels).filter(k => services.some(s => s.category === k));
  const openSet = openCats ?? new Set(usedCats.slice(0, 1));
  const toggleCat = (key) => {
    const next = new Set(openSet);
    next.has(key) ? next.delete(key) : next.add(key);
    setOpenCats(next);
  };

  return (
    <div className="animate-fade-in">
      <DeleteWorkerDialog worker={serviceToDelete} itemLabel="uslugu" onClose={() => setServiceToDelete(null)} onDelete={handleDelete} />
      <div className="flex items-center justify-between mb-6">
        <h2 className="font-['Cormorant_Garamond'] text-3xl font-light">Usluge</h2>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black" data-testid="add-service-btn">
              <Plus className="w-4 h-4 mr-2" />
              Dodaj Uslugu
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-[var(--color-surface)] border-[#2A2A2D]">
            <DialogHeader>
              <DialogTitle className="font-['Cormorant_Garamond'] text-2xl">
                {editingService ? "Izmeni Uslugu" : "Nova Usluga"}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Naziv</label>
                <Input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Naziv usluge"
                  className="bg-[var(--color-background)] border-[#2A2A2D]"
                  data-testid="service-name-input"
                />
              </div>

              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Kategorija</label>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(categoryLabels).map(([key, label]) => (
                    <button
                      key={key}
                      type="button"
                      onClick={() => setForm({ ...form, category: key })}
                      className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                        form.category === key
                          ? "bg-[var(--color-primary)] text-black"
                          : "bg-[var(--color-background)] border border-[#2A2A2D] text-[#9CA3AF]"
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-[#9CA3AF] mb-2 block">Trajanje (min)</label>
                  <Input
                    type="number"
                    value={form.duration}
                    onChange={(e) => setForm({ ...form, duration: parseInt(e.target.value) || 0 })}
                    className="bg-[var(--color-background)] border-[#2A2A2D]"
                    data-testid="service-duration-input"
                  />
                </div>
                <div>
                  <label className="text-sm text-[#9CA3AF] mb-2 block">Cena (π)</label>
                  <Input
                    type="number"
                    value={form.price}
                    onChange={(e) => setForm({ ...form, price: parseFloat(e.target.value) || 0 })}
                    className="bg-[var(--color-background)] border-[#2A2A2D]"
                    data-testid="service-price-input"
                  />
                </div>
              </div>

              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Opis (opciono)</label>
                <Input
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="Kratak opis usluge"
                  className="bg-[var(--color-background)] border-[#2A2A2D]"
                  data-testid="service-description-input"
                />
              </div>

              <Button
                onClick={handleSubmit}
                className="w-full bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black"
                data-testid="save-service-btn"
              >
                {editingService ? "Sačuvaj Izmene" : "Dodaj Uslugu"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="text-center py-12 text-[#9CA3AF]">Učitavanje...</div>
      ) : services.length === 0 ? (
        <div className="text-center py-12 bg-[var(--color-surface)] rounded-xl border border-[#2A2A2D]">
          <Scissors className="w-12 h-12 mx-auto text-[#9CA3AF] mb-4" />
          <p className="text-[#9CA3AF]">Nema usluga</p>
        </div>
      ) : (
        <>
        <div className="flex justify-end gap-2 mb-4">
          <Button variant="outline" size="sm" onClick={() => setOpenCats(new Set(usedCats))} className="border-[#2A2A2D] bg-transparent text-[#9CA3AF] hover:text-white" data-testid="expand-all-categories-btn">
            <ChevronsDown className="w-4 h-4 mr-1" />Otvori sve
          </Button>
          <Button variant="outline" size="sm" onClick={() => setOpenCats(new Set())} className="border-[#2A2A2D] bg-transparent text-[#9CA3AF] hover:text-white" data-testid="collapse-all-categories-btn">
            <ChevronsUp className="w-4 h-4 mr-1" />Zatvori sve
          </Button>
        </div>
        <div className="space-y-3 stagger-children">
          {Object.entries(categoryLabels).map(([category, label]) => {
            const categoryServices = services.filter(s => s.category === category);
            if (categoryServices.length === 0) return null;
            const isOpen = openSet.has(category);
            
            return (
              <div key={category} className="bg-[var(--color-surface)]/60 rounded-xl border border-[#2A2A2D] overflow-hidden" data-testid={`category-section-${category}`}>
                <button
                  type="button"
                  onClick={() => toggleCat(category)}
                  className="w-full flex items-center justify-between px-4 py-3 hover:bg-[var(--color-background)]/50 transition-colors"
                  aria-expanded={isOpen}
                  data-testid={`category-toggle-${category}`}
                >
                  <span className="flex items-center gap-2">
                    <span className="text-sm text-white uppercase tracking-wider">{label}</span>
                    <span className="text-xs text-[#6B7280]">({categoryServices.length})</span>
                  </span>
                  <ChevronDown className={`w-4 h-4 text-[#9CA3AF] transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`} />
                </button>
                {isOpen && (
                <div className="space-y-2 px-3 pb-3" data-testid={`category-services-${category}`}>
                  {categoryServices.map((service) => (
                    <div
                      key={service.id}
                      className={`bg-[var(--color-surface)] rounded-xl border p-4 ${
                        service.active ? "border-[#2A2A2D]" : "border-red-400/30 opacity-60"
                      }`}
                      data-testid={`service-item-${service.id}`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 flex-1">
                          <h4 className="font-medium truncate">{service.name}</h4>
                          <p className="text-sm text-[#9CA3AF]">
                            <Clock className="w-3 h-3 inline mr-1" />
                            {service.duration} min
                          </p>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <span className="font-semibold text-[var(--color-primary)] text-sm whitespace-nowrap">
                            {service.price} π
                          </span>
                          <div className="flex gap-1">
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => handleEdit(service)}
                              className="h-8 w-8 hover:bg-[var(--color-background)]"
                              data-testid={`edit-service-${service.id}`}
                            >
                              <Edit2 className="w-4 h-4" />
                            </Button>
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => setServiceToDelete(service)}
                              className="h-8 w-8 hover:bg-red-400/10 text-red-400"
                              data-testid={`delete-service-${service.id}`}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                )}
              </div>
            );
          })}
        </div>
        </>
      )}
    </div>
  );
};



export default ServicesPage;
