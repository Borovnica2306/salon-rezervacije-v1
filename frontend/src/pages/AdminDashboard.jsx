import { useState, useEffect } from "react";
import { Routes, Route, Link, useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import axios from "axios";
import { API, useAuth } from "../App";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { 
  Calendar, Users, Scissors, Settings, LogOut, Menu, X,
  Clock, Phone, User, Ban, Check, ChevronLeft, ChevronRight,
  Plus, Edit2, Trash2, DollarSign, Shield
} from "lucide-react";
import { format, addDays, subDays, parseISO } from "date-fns";
import { sr } from "date-fns/locale";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogDescription,
} from "../components/ui/dialog";
import { Switch } from "../components/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";

const AdminDashboard = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { logout, user } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate("/admin/login");
  };

  const navItems = [
    { path: "/admin", label: "Rezervacije", icon: Calendar },
    { path: "/admin/blacklist", label: "Crna Lista", icon: Shield },
    { path: "/admin/employees", label: "Radnici", icon: Users },
    { path: "/admin/services", label: "Usluge", icon: Scissors },
    { path: "/admin/settings", label: "Podešavanja", icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-[#0A0A0B]">
      {/* Mobile Header */}
      <header className="lg:hidden sticky top-0 z-50 glass border-b border-[#2A2A2D]">
        <div className="flex items-center justify-between p-4">
          <h1 className="font-['Cormorant_Garamond'] text-xl font-light">Dashboard</h1>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 hover:bg-[#141416] rounded-lg transition-colors"
            data-testid="mobile-menu-toggle"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
        
        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <nav className="border-t border-[#2A2A2D] p-4 space-y-2 animate-fade-in">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                  location.pathname === item.path
                    ? "bg-[#C5A880]/10 text-[#C5A880]"
                    : "hover:bg-[#141416] text-[#9CA3AF]"
                }`}
              >
                <item.icon className="w-5 h-5" />
                {item.label}
              </Link>
            ))}
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 p-3 rounded-lg text-red-400 hover:bg-red-400/10 w-full"
              data-testid="logout-btn"
            >
              <LogOut className="w-5 h-5" />
              Odjava
            </button>
          </nav>
        )}
      </header>

      <div className="flex">
        {/* Desktop Sidebar */}
        <aside className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 bg-[#141416] border-r border-[#2A2A2D]">
          <div className="p-6 border-b border-[#2A2A2D]">
            <h1 className="font-['Cormorant_Garamond'] text-2xl font-light">Beauty Salon</h1>
            <p className="text-sm text-[#9CA3AF] mt-1">{user?.email}</p>
          </div>

          <nav className="flex-1 p-4 space-y-2">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                  location.pathname === item.path
                    ? "bg-[#C5A880]/10 text-[#C5A880]"
                    : "hover:bg-[#0A0A0B] text-[#9CA3AF]"
                }`}
                data-testid={`nav-${item.label.toLowerCase()}`}
              >
                <item.icon className="w-5 h-5" />
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="p-4 border-t border-[#2A2A2D]">
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 p-3 rounded-lg text-red-400 hover:bg-red-400/10 w-full transition-colors"
              data-testid="desktop-logout-btn"
            >
              <LogOut className="w-5 h-5" />
              Odjava
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 lg:ml-64 p-4 lg:p-8">
          <Routes>
            <Route index element={<ReservationsPage />} />
            <Route path="blacklist" element={<BlacklistPage />} />
            <Route path="employees" element={<EmployeesPage />} />
            <Route path="services" element={<ServicesPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

// Reservations Page
const ReservationsPage = () => {
  const [reservations, setReservations] = useState([]);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [loading, setLoading] = useState(true);
  const [blacklist, setBlacklist] = useState([]);

  const token = localStorage.getItem("access_token");
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchReservations();
    fetchBlacklist();
  }, [selectedDate]);

  const fetchReservations = async () => {
    try {
      const response = await axios.get(`${API}/reservations`, {
        params: { date: format(selectedDate, "yyyy-MM-dd") },
        headers,
      });
      setReservations(response.data);
    } catch (error) {
      toast.error("Greška pri učitavanju rezervacija");
    } finally {
      setLoading(false);
    }
  };

  const fetchBlacklist = async () => {
    try {
      const response = await axios.get(`${API}/blacklist`, { headers });
      setBlacklist(response.data.map(b => b.phone));
    } catch (error) {
      console.error("Error fetching blacklist:", error);
    }
  };

  const handleReleaseAdvance = async (id) => {
    try {
      await axios.put(`${API}/reservations/${id}/release-advance`, {}, { headers });
      toast.success("Avans oslobođen");
      fetchReservations();
    } catch (error) {
      toast.error("Greška pri oslobađanju avansa");
    }
  };

  const handleCancel = async (id) => {
    try {
      await axios.put(`${API}/reservations/${id}/cancel`, {}, { headers });
      toast.success("Rezervacija otkazana");
      fetchReservations();
    } catch (error) {
      toast.error("Greška pri otkazivanju");
    }
  };

  const handleBlacklist = async (phone) => {
    try {
      await axios.post(`${API}/blacklist?phone=${encodeURIComponent(phone)}`, {}, { headers });
      toast.success("Broj dodat na crnu listu");
      fetchBlacklist();
    } catch (error) {
      toast.error("Greška pri dodavanju na crnu listu");
    }
  };

  const handleRemoveFromBlacklist = async (phone) => {
    try {
      await axios.delete(`${API}/blacklist/${encodeURIComponent(phone)}`, { headers });
      toast.success("Broj uklonjen sa crne liste");
      fetchBlacklist();
    } catch (error) {
      toast.error("Greška pri uklanjanju sa crne liste");
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="font-['Cormorant_Garamond'] text-3xl font-light">Rezervacije</h2>
          <p className="text-[#9CA3AF]">
            {format(selectedDate, "EEEE, d. MMMM yyyy", { locale: sr })}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => setSelectedDate(subDays(selectedDate, 1))}
            className="border-[#2A2A2D] hover:bg-[#141416]"
            data-testid="prev-day-btn"
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <Button
            variant="outline"
            onClick={() => setSelectedDate(new Date())}
            className="border-[#2A2A2D] hover:bg-[#141416]"
            data-testid="today-btn"
          >
            Danas
          </Button>
          <Button
            variant="outline"
            size="icon"
            onClick={() => setSelectedDate(addDays(selectedDate, 1))}
            className="border-[#2A2A2D] hover:bg-[#141416]"
            data-testid="next-day-btn"
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Reservations Table */}
      {loading ? (
        <div className="text-center py-12 text-[#9CA3AF]">Učitavanje...</div>
      ) : reservations.length === 0 ? (
        <div className="text-center py-12 bg-[#141416] rounded-xl border border-[#2A2A2D]">
          <Calendar className="w-12 h-12 mx-auto text-[#9CA3AF] mb-4" />
          <p className="text-[#9CA3AF]">Nema rezervacija za ovaj datum</p>
        </div>
      ) : (
        <div className="bg-[#141416] rounded-xl border border-[#2A2A2D] overflow-hidden">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-[#2A2A2D] hover:bg-transparent">
                  <TableHead className="text-[#9CA3AF]">Vreme</TableHead>
                  <TableHead className="text-[#9CA3AF]">Ime</TableHead>
                  <TableHead className="text-[#9CA3AF]">Telefon</TableHead>
                  <TableHead className="text-[#9CA3AF]">Usluge</TableHead>
                  <TableHead className="text-[#9CA3AF]">Radnik</TableHead>
                  <TableHead className="text-[#9CA3AF] text-right">Cena</TableHead>
                  <TableHead className="text-[#9CA3AF]">Avans</TableHead>
                  <TableHead className="text-[#9CA3AF] text-right">Akcije</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reservations.map((res) => {
                  const isBlacklisted = blacklist.includes(res.client_phone);
                  return (
                    <TableRow key={res.id} className="border-[#2A2A2D]" data-testid={`reservation-${res.id}`}>
                      <TableCell>
                        <div className="font-semibold text-[#C5A880]">
                          {res.time} - {res.end_time}
                        </div>
                        <div className="text-xs text-[#9CA3AF]">{res.total_duration} min</div>
                      </TableCell>
                      <TableCell className="font-medium">{res.client_name}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          {res.client_phone}
                          {isBlacklisted && (
                            <Ban className="w-3 h-3 text-red-400" title="Blokiran" />
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="max-w-[150px] truncate" title={res.service_names.join(", ")}>
                          {res.service_names.join(", ")}
                        </div>
                      </TableCell>
                      <TableCell>{res.worker_name}</TableCell>
                      <TableCell className="text-right font-semibold text-[#C5A880]">
                        {res.total_price.toLocaleString()} RSD
                      </TableCell>
                      <TableCell>
                        {res.advance_required && !res.advance_released ? (
                          <Button
                            size="sm"
                            onClick={() => handleReleaseAdvance(res.id)}
                            className="bg-green-600/20 text-green-400 hover:bg-green-600/30 h-8 text-xs"
                            data-testid={`release-advance-${res.id}`}
                          >
                            <DollarSign className="w-3 h-3 mr-1" />
                            Oslobodi
                          </Button>
                        ) : res.advance_released ? (
                          <span className="px-2 py-1 rounded-full text-xs bg-green-600/20 text-green-400">
                            <Check className="w-3 h-3 inline mr-1" />
                            OK
                          </span>
                        ) : (
                          <span className="text-[#9CA3AF] text-xs">-</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          {!isBlacklisted ? (
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => handleBlacklist(res.client_phone)}
                              className="h-8 w-8 text-red-400 hover:bg-red-400/10"
                              title="Blokiraj broj"
                              data-testid={`blacklist-${res.id}`}
                            >
                              <Ban className="w-4 h-4" />
                            </Button>
                          ) : (
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => handleRemoveFromBlacklist(res.client_phone)}
                              className="h-8 w-8 text-green-400 hover:bg-green-400/10"
                              title="Odblokiraj broj"
                              data-testid={`unblock-${res.id}`}
                            >
                              <Check className="w-4 h-4" />
                            </Button>
                          )}
                          <Button
                            size="icon"
                            variant="ghost"
                            onClick={() => handleCancel(res.id)}
                            className="h-8 w-8 text-[#9CA3AF] hover:bg-red-400/10 hover:text-red-400"
                            title="Otkaži rezervaciju"
                            data-testid={`cancel-${res.id}`}
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        </div>
      )}
    </div>
  );
};

// Employees Page
const EmployeesPage = () => {
  const [employees, setEmployees] = useState([]);
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [form, setForm] = useState({
    name: "",
    services: [],
    work_start: "09:00",
    work_end: "21:00",
    break_start: "",
    break_end: "",
    days_off: [],
  });

  const token = localStorage.getItem("access_token");
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [empRes, servRes] = await Promise.all([
        axios.get(`${API}/workers?active_only=false`, { headers }),
        axios.get(`${API}/services?active_only=false`, { headers }),
      ]);
      setEmployees(empRes.data);
      setServices(servRes.data);
    } catch (error) {
      toast.error("Greška pri učitavanju");
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setForm({
      name: "",
      services: [],
      work_start: "09:00",
      work_end: "21:00",
      break_start: "",
      break_end: "",
      days_off: [],
    });
    setEditingEmployee(null);
  };

  const handleEdit = (emp) => {
    setEditingEmployee(emp);
    setForm({
      name: emp.name,
      services: emp.services,
      work_start: emp.work_start,
      work_end: emp.work_end,
      break_start: emp.break_start || "",
      break_end: emp.break_end || "",
      days_off: emp.days_off || [],
    });
    setDialogOpen(true);
  };

  const handleSubmit = async () => {
    if (!form.name.trim()) {
      toast.error("Unesite ime radnika");
      return;
    }

    try {
      const payload = {
        ...form,
        break_start: form.break_start || null,
        break_end: form.break_end || null,
      };

      if (editingEmployee) {
        await axios.put(`${API}/workers/${editingEmployee.id}`, payload, { headers });
        toast.success("Radnik ažuriran");
      } else {
        await axios.post(`${API}/workers`, payload, { headers });
        toast.success("Radnik dodat");
      }
      
      setDialogOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error("Greška pri čuvanju");
    }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API}/workers/${id}`, { headers });
      toast.success("Radnik deaktiviran");
      fetchData();
    } catch (error) {
      toast.error("Greška pri brisanju");
    }
  };

  const toggleService = (serviceId) => {
    setForm(prev => ({
      ...prev,
      services: prev.services.includes(serviceId)
        ? prev.services.filter(s => s !== serviceId)
        : [...prev.services, serviceId],
    }));
  };

  const toggleDayOff = (day) => {
    setForm(prev => ({
      ...prev,
      days_off: prev.days_off.includes(day)
        ? prev.days_off.filter(d => d !== day)
        : [...prev.days_off, day],
    }));
  };

  const dayLabels = ["Ned", "Pon", "Uto", "Sre", "Čet", "Pet", "Sub"];

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <h2 className="font-['Cormorant_Garamond'] text-3xl font-light">Radnici</h2>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="bg-[#C5A880] hover:bg-[#B89970] text-black" data-testid="add-employee-btn">
              <Plus className="w-4 h-4 mr-2" />
              Dodaj Radnika
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-[#141416] border-[#2A2A2D] max-h-[90vh] overflow-y-auto">
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
                  className="bg-[#0A0A0B] border-[#2A2A2D]"
                  data-testid="employee-name-input"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-[#9CA3AF] mb-2 block">Početak rada</label>
                  <Input
                    type="time"
                    value={form.work_start}
                    onChange={(e) => setForm({ ...form, work_start: e.target.value })}
                    className="bg-[#0A0A0B] border-[#2A2A2D]"
                    data-testid="employee-work-start"
                  />
                </div>
                <div>
                  <label className="text-sm text-[#9CA3AF] mb-2 block">Kraj rada</label>
                  <Input
                    type="time"
                    value={form.work_end}
                    onChange={(e) => setForm({ ...form, work_end: e.target.value })}
                    className="bg-[#0A0A0B] border-[#2A2A2D]"
                    data-testid="employee-work-end"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-[#9CA3AF] mb-2 block">Pauza od</label>
                  <Input
                    type="time"
                    value={form.break_start}
                    onChange={(e) => setForm({ ...form, break_start: e.target.value })}
                    className="bg-[#0A0A0B] border-[#2A2A2D]"
                    data-testid="employee-break-start"
                  />
                </div>
                <div>
                  <label className="text-sm text-[#9CA3AF] mb-2 block">Pauza do</label>
                  <Input
                    type="time"
                    value={form.break_end}
                    onChange={(e) => setForm({ ...form, break_end: e.target.value })}
                    className="bg-[#0A0A0B] border-[#2A2A2D]"
                    data-testid="employee-break-end"
                  />
                </div>
              </div>

              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Slobodni dani</label>
                <div className="flex flex-wrap gap-2">
                  {dayLabels.map((label, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => toggleDayOff(idx)}
                      className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                        form.days_off.includes(idx)
                          ? "bg-[#C5A880] text-black"
                          : "bg-[#0A0A0B] border border-[#2A2A2D] text-[#9CA3AF]"
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Usluge</label>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {services.filter(s => s.active).map((service) => (
                    <button
                      key={service.id}
                      type="button"
                      onClick={() => toggleService(service.id)}
                      className={`w-full p-3 rounded-lg text-left text-sm transition-colors ${
                        form.services.includes(service.id)
                          ? "bg-[#C5A880]/10 border border-[#C5A880]"
                          : "bg-[#0A0A0B] border border-[#2A2A2D] hover:border-[#C5A880]/50"
                      }`}
                    >
                      <span className="font-medium">{service.name}</span>
                      <span className="text-[#9CA3AF] ml-2">({service.duration} min)</span>
                    </button>
                  ))}
                </div>
              </div>

              <Button
                onClick={handleSubmit}
                className="w-full bg-[#C5A880] hover:bg-[#B89970] text-black"
                data-testid="save-employee-btn"
              >
                {editingEmployee ? "Sačuvaj Izmene" : "Dodaj Radnika"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="text-center py-12 text-[#9CA3AF]">Učitavanje...</div>
      ) : employees.length === 0 ? (
        <div className="text-center py-12 bg-[#141416] rounded-xl border border-[#2A2A2D]">
          <Users className="w-12 h-12 mx-auto text-[#9CA3AF] mb-4" />
          <p className="text-[#9CA3AF]">Nema radnika</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 stagger-children">
          {employees.map((emp) => (
            <div
              key={emp.id}
              className={`bg-[#141416] rounded-xl border p-5 ${
                emp.active ? "border-[#2A2A2D]" : "border-red-400/30 opacity-60"
              }`}
              data-testid={`employee-${emp.id}`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#C5A880] to-[#8B7355] flex items-center justify-center text-black font-semibold text-lg">
                    {emp.name.charAt(0)}
                  </div>
                  <div>
                    <h3 className="font-medium">{emp.name}</h3>
                    <p className="text-sm text-[#9CA3AF]">
                      {emp.work_start} - {emp.work_end}
                    </p>
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => handleEdit(emp)}
                    className="h-8 w-8 hover:bg-[#0A0A0B]"
                    data-testid={`edit-employee-${emp.id}`}
                  >
                    <Edit2 className="w-4 h-4" />
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => handleDelete(emp.id)}
                    className="h-8 w-8 hover:bg-red-400/10 text-red-400"
                    data-testid={`delete-employee-${emp.id}`}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              
              {emp.break_start && emp.break_end && (
                <p className="text-xs text-[#9CA3AF] mb-2">
                  Pauza: {emp.break_start} - {emp.break_end}
                </p>
              )}
              
              <p className="text-xs text-[#9CA3AF]">
                {emp.services.length} usluga
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Services Page
const ServicesPage = () => {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingService, setEditingService] = useState(null);
  const [form, setForm] = useState({
    name: "",
    category: "hair",
    duration: 30,
    price: 0,
    description: "",
  });

  const token = localStorage.getItem("access_token");
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchServices();
  }, []);

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
      toast.success("Usluga deaktivirana");
      fetchServices();
    } catch (error) {
      toast.error("Greška pri brisanju");
    }
  };

  const categoryLabels = {
    hair: "Frizura",
    massage: "Masaža",
    nails: "Nokti",
  };

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <h2 className="font-['Cormorant_Garamond'] text-3xl font-light">Usluge</h2>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="bg-[#C5A880] hover:bg-[#B89970] text-black" data-testid="add-service-btn">
              <Plus className="w-4 h-4 mr-2" />
              Dodaj Uslugu
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-[#141416] border-[#2A2A2D]">
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
                  className="bg-[#0A0A0B] border-[#2A2A2D]"
                  data-testid="service-name-input"
                />
              </div>

              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Kategorija</label>
                <div className="flex gap-2">
                  {Object.entries(categoryLabels).map(([key, label]) => (
                    <button
                      key={key}
                      type="button"
                      onClick={() => setForm({ ...form, category: key })}
                      className={`flex-1 py-2 rounded-lg text-sm transition-colors ${
                        form.category === key
                          ? "bg-[#C5A880] text-black"
                          : "bg-[#0A0A0B] border border-[#2A2A2D] text-[#9CA3AF]"
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
                    className="bg-[#0A0A0B] border-[#2A2A2D]"
                    data-testid="service-duration-input"
                  />
                </div>
                <div>
                  <label className="text-sm text-[#9CA3AF] mb-2 block">Cena (RSD)</label>
                  <Input
                    type="number"
                    value={form.price}
                    onChange={(e) => setForm({ ...form, price: parseFloat(e.target.value) || 0 })}
                    className="bg-[#0A0A0B] border-[#2A2A2D]"
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
                  className="bg-[#0A0A0B] border-[#2A2A2D]"
                  data-testid="service-description-input"
                />
              </div>

              <Button
                onClick={handleSubmit}
                className="w-full bg-[#C5A880] hover:bg-[#B89970] text-black"
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
        <div className="text-center py-12 bg-[#141416] rounded-xl border border-[#2A2A2D]">
          <Scissors className="w-12 h-12 mx-auto text-[#9CA3AF] mb-4" />
          <p className="text-[#9CA3AF]">Nema usluga</p>
        </div>
      ) : (
        <div className="space-y-4 stagger-children">
          {Object.entries(categoryLabels).map(([category, label]) => {
            const categoryServices = services.filter(s => s.category === category);
            if (categoryServices.length === 0) return null;
            
            return (
              <div key={category}>
                <h3 className="text-sm text-[#9CA3AF] uppercase tracking-wider mb-3">{label}</h3>
                <div className="space-y-2">
                  {categoryServices.map((service) => (
                    <div
                      key={service.id}
                      className={`bg-[#141416] rounded-xl border p-4 flex items-center justify-between ${
                        service.active ? "border-[#2A2A2D]" : "border-red-400/30 opacity-60"
                      }`}
                      data-testid={`service-item-${service.id}`}
                    >
                      <div>
                        <h4 className="font-medium">{service.name}</h4>
                        <p className="text-sm text-[#9CA3AF]">
                          <Clock className="w-3 h-3 inline mr-1" />
                          {service.duration} min
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="font-semibold text-[#C5A880]">
                          {service.price.toLocaleString()} RSD
                        </span>
                        <div className="flex gap-1">
                          <Button
                            size="icon"
                            variant="ghost"
                            onClick={() => handleEdit(service)}
                            className="h-8 w-8 hover:bg-[#0A0A0B]"
                            data-testid={`edit-service-${service.id}`}
                          >
                            <Edit2 className="w-4 h-4" />
                          </Button>
                          <Button
                            size="icon"
                            variant="ghost"
                            onClick={() => handleDelete(service.id)}
                            className="h-8 w-8 hover:bg-red-400/10 text-red-400"
                            data-testid={`delete-service-${service.id}`}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

// Settings Page
const SettingsPage = () => {
  const [settings, setSettings] = useState({
    salon_name: "",
    work_start: "09:00",
    work_end: "21:00",
    advance_instructions: "",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const token = localStorage.getItem("access_token");
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`, { headers });
      setSettings(response.data);
    } catch (error) {
      toast.error("Greška pri učitavanju");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/settings`, settings, { headers });
      toast.success("Podešavanja sačuvana");
    } catch (error) {
      toast.error("Greška pri čuvanju");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12 text-[#9CA3AF]">Učitavanje...</div>;
  }

  return (
    <div className="animate-fade-in max-w-2xl">
      <h2 className="font-['Cormorant_Garamond'] text-3xl font-light mb-6">Podešavanja</h2>

      <div className="bg-[#141416] rounded-xl border border-[#2A2A2D] p-6 space-y-6">
        <div>
          <label className="text-sm text-[#9CA3AF] mb-2 block">Naziv Salona</label>
          <Input
            value={settings.salon_name}
            onChange={(e) => setSettings({ ...settings, salon_name: e.target.value })}
            placeholder="Beauty Salon"
            className="bg-[#0A0A0B] border-[#2A2A2D]"
            data-testid="settings-salon-name"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-[#9CA3AF] mb-2 block">Radno vreme od</label>
            <Input
              type="time"
              value={settings.work_start}
              onChange={(e) => setSettings({ ...settings, work_start: e.target.value })}
              className="bg-[#0A0A0B] border-[#2A2A2D]"
              data-testid="settings-work-start"
            />
          </div>
          <div>
            <label className="text-sm text-[#9CA3AF] mb-2 block">Radno vreme do</label>
            <Input
              type="time"
              value={settings.work_end}
              onChange={(e) => setSettings({ ...settings, work_end: e.target.value })}
              className="bg-[#0A0A0B] border-[#2A2A2D]"
              data-testid="settings-work-end"
            />
          </div>
        </div>

        <div>
          <label className="text-sm text-[#9CA3AF] mb-2 block">Instrukcije za Avans</label>
          <textarea
            value={settings.advance_instructions}
            onChange={(e) => setSettings({ ...settings, advance_instructions: e.target.value })}
            placeholder="Unesite instrukcije za uplatu avansa..."
            rows={4}
            className="w-full bg-[#0A0A0B] border border-[#2A2A2D] rounded-lg p-3 text-white resize-none focus:border-[#C5A880] focus:outline-none"
            data-testid="settings-advance-instructions"
          />
        </div>

        <Button
          onClick={handleSave}
          disabled={saving}
          className="w-full bg-[#C5A880] hover:bg-[#B89970] text-black"
          data-testid="save-settings-btn"
        >
          {saving ? "Čuvanje..." : "Sačuvaj Podešavanja"}
        </Button>
      </div>
    </div>
  );
};

// Blacklist Page
const BlacklistPage = () => {
  const [blacklist, setBlacklist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newPhone, setNewPhone] = useState("");
  const [isAdding, setIsAdding] = useState(false);

  const token = localStorage.getItem("access_token");
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchBlacklist();
  }, []);

  const fetchBlacklist = async () => {
    try {
      const response = await axios.get(`${API}/blacklist`, { headers });
      setBlacklist(response.data);
    } catch (error) {
      toast.error("Greška pri učitavanju crne liste");
    } finally {
      setLoading(false);
    }
  };

  const handleAddToBlacklist = async () => {
    if (!newPhone.trim()) {
      toast.error("Unesite broj telefona");
      return;
    }

    setIsAdding(true);
    try {
      await axios.post(`${API}/blacklist?phone=${encodeURIComponent(newPhone)}`, {}, { headers });
      toast.success("Broj dodat na crnu listu");
      setNewPhone("");
      fetchBlacklist();
    } catch (error) {
      toast.error("Greška pri dodavanju na crnu listu");
    } finally {
      setIsAdding(false);
    }
  };

  const handleRemoveFromBlacklist = async (phone) => {
    try {
      await axios.delete(`${API}/blacklist/${encodeURIComponent(phone)}`, { headers });
      toast.success("Broj uklonjen sa crne liste");
      fetchBlacklist();
    } catch (error) {
      toast.error("Greška pri uklanjanju sa crne liste");
    }
  };

  return (
    <div className="animate-fade-in">
      <h2 className="font-['Cormorant_Garamond'] text-3xl font-light mb-6">Crna Lista</h2>
      
      <p className="text-[#9CA3AF] mb-6">
        Blokirani brojevi telefona ne mogu praviti nove rezervacije u salonu.
      </p>

      {/* Add new phone */}
      <div className="bg-[#141416] rounded-xl border border-[#2A2A2D] p-6 mb-6">
        <h3 className="font-medium mb-4">Dodaj broj na crnu listu</h3>
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#9CA3AF]" />
            <Input
              value={newPhone}
              onChange={(e) => setNewPhone(e.target.value)}
              placeholder="+381 6X XXX XXXX"
              className="pl-12 bg-[#0A0A0B] border-[#2A2A2D] focus:border-[#C5A880]"
              data-testid="blacklist-phone-input"
              onKeyDown={(e) => e.key === "Enter" && handleAddToBlacklist()}
            />
          </div>
          <Button
            onClick={handleAddToBlacklist}
            disabled={isAdding}
            className="bg-red-500 hover:bg-red-600 text-white"
            data-testid="add-to-blacklist-btn"
          >
            <Ban className="w-4 h-4 mr-2" />
            Blokiraj
          </Button>
        </div>
      </div>

      {/* Blacklist table */}
      {loading ? (
        <div className="text-center py-12 text-[#9CA3AF]">Učitavanje...</div>
      ) : blacklist.length === 0 ? (
        <div className="text-center py-12 bg-[#141416] rounded-xl border border-[#2A2A2D]">
          <Shield className="w-12 h-12 mx-auto text-[#9CA3AF] mb-4" />
          <p className="text-[#9CA3AF]">Nema blokiranih brojeva</p>
        </div>
      ) : (
        <div className="bg-[#141416] rounded-xl border border-[#2A2A2D] overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="border-[#2A2A2D] hover:bg-transparent">
                <TableHead className="text-[#9CA3AF]">Broj telefona</TableHead>
                <TableHead className="text-[#9CA3AF]">Datum blokiranja</TableHead>
                <TableHead className="text-[#9CA3AF] text-right">Akcija</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {blacklist.map((item, index) => (
                <TableRow key={index} className="border-[#2A2A2D]" data-testid={`blacklist-row-${index}`}>
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      <Ban className="w-4 h-4 text-red-400" />
                      {item.phone}
                    </div>
                  </TableCell>
                  <TableCell className="text-[#9CA3AF]">
                    {item.created_at ? format(new Date(item.created_at), "d. MMM yyyy HH:mm", { locale: sr }) : "-"}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleRemoveFromBlacklist(item.phone)}
                      className="border-green-400/30 text-green-400 hover:bg-green-400/10"
                      data-testid={`unblock-${index}`}
                    >
                      <Check className="w-4 h-4 mr-1" />
                      Odblokiraj
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
