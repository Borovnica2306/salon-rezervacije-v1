import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import axios from "axios";
import { API, useAuth, getToken } from "../App";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Mail, Lock, Scissors, ChevronRight, ShieldCheck } from "lucide-react";

const AdminLogin = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { slug } = useParams();
  const { login, user, updateUser } = useAuth();

  // Password change form state
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [changingPassword, setChangingPassword] = useState(false);

  const mustChangePassword = user?.must_change_password === true;

  // Smart redirect if already logged in AND password is OK
  useEffect(() => {
    if (user && !mustChangePassword) {
      redirectUser(user);
    }
  }, [user, mustChangePassword]);

  const redirectUser = (userData) => {
    if (userData.role === "super_admin") {
      navigate("/super-admin", { replace: true });
    } else if (userData.slug || slug) {
      navigate(`/${userData.slug || slug}/admin`, { replace: true });
    } else {
      navigate("/", { replace: true });
    }
  };

  // Already logged in and password OK → hide page
  if (user && !mustChangePassword) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error("Unesite email i lozinku");
      return;
    }

    setIsLoading(true);
    try {
      const data = await login(email, password);
      if (data.must_change_password) {
        // Stay on this page — password change form will render
        toast.info("Morate promeniti privremenu lozinku pre pristupa.");
      } else {
        toast.success("Uspešna prijava!");
        redirectUser(data);
      }
    } catch (error) {
      const detail = error.response?.data?.detail;
      let message = "Greška pri prijavi";
      if (typeof detail === "string") {
        message = detail;
      } else if (Array.isArray(detail)) {
        message = detail.map(e => e.msg || JSON.stringify(e)).join(" ");
      }
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();

    if (newPassword.length < 6) {
      toast.error("Lozinka mora imati najmanje 6 karaktera");
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error("Lozinke se ne poklapaju");
      return;
    }

    setChangingPassword(true);
    try {
      const token = getToken();
      await axios.put(
        `${API}/auth/change-password`,
        { new_password: newPassword },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Lozinka uspešno postavljena!");
      updateUser({ must_change_password: false });
      // redirectUser will fire from useEffect when must_change_password becomes false
    } catch (error) {
      const msg = error.response?.data?.detail || "Greška pri promeni lozinke";
      toast.error(msg);
    } finally {
      setChangingPassword(false);
    }
  };

  // ===== FORCED PASSWORD CHANGE SCREEN =====
  if (mustChangePassword) {
    return (
      <div className="min-h-screen bg-transparent flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8 animate-fade-in">
            <div className="w-16 h-16 rounded-2xl bg-amber-500/20 flex items-center justify-center mx-auto mb-4">
              <ShieldCheck className="w-8 h-8 text-amber-400" />
            </div>
            <h1 className="font-['Cormorant_Garamond'] text-3xl font-light mb-2">
              Postavite novu lozinku
            </h1>
            <p className="text-[#9CA3AF] text-sm">
              Vaš nalog koristi privremenu lozinku. Postavite novu lozinku da biste nastavili.
            </p>
          </div>

          <form onSubmit={handleChangePassword} className="space-y-4 animate-slide-up">
            <div className="bg-[var(--color-surface)] rounded-2xl border border-[#2A2A2D] p-6 space-y-4">
              {/* Who is logged in */}
              <div className="flex items-center gap-3 pb-3 border-b border-[#2A2A2D]">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#C5A880] to-[#8B7355] flex items-center justify-center text-black font-semibold">
                  {user?.name?.charAt(0) || "?"}
                </div>
                <div>
                  <p className="text-sm font-medium text-white">{user?.name}</p>
                  <p className="text-xs text-[#6B7280]">{user?.email}</p>
                </div>
              </div>

              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Nova lozinka</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#9CA3AF]" />
                  <Input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Minimum 6 karaktera"
                    className="pl-12 bg-[var(--color-background)] border-[#2A2A2D] focus:border-[var(--color-primary)] h-14"
                    data-testid="new-password-input"
                    autoFocus
                  />
                </div>
              </div>

              <div>
                <label className="text-sm text-[#9CA3AF] mb-2 block">Potvrdite lozinku</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#9CA3AF]" />
                  <Input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Ponovite novu lozinku"
                    className="pl-12 bg-[var(--color-background)] border-[#2A2A2D] focus:border-[var(--color-primary)] h-14"
                    data-testid="confirm-password-input"
                  />
                </div>
                {confirmPassword && newPassword !== confirmPassword && (
                  <p className="text-xs text-red-400 mt-1">Lozinke se ne poklapaju</p>
                )}
              </div>

              <Button
                type="submit"
                disabled={changingPassword || newPassword.length < 6 || newPassword !== confirmPassword}
                className="w-full h-14 bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black font-medium disabled:opacity-40"
                data-testid="set-password-btn"
              >
                {changingPassword ? "Postavljanje..." : "Postavi lozinku"}
              </Button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  // ===== NORMAL LOGIN SCREEN =====
  return (
    <div className="min-h-screen bg-transparent flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8 animate-fade-in">
          <div className="w-16 h-16 rounded-2xl bg-[var(--color-primary)]/20 flex items-center justify-center mx-auto mb-4">
            <Scissors className="w-8 h-8 text-[var(--color-primary)]" />
          </div>
          <h1 className="font-['Cormorant_Garamond'] text-3xl font-light mb-2">Prijava</h1>
          <p className="text-[#9CA3AF]">{"Unesite kredencijale za pristup vašem panelu"}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 animate-slide-up">
          <div className="bg-[var(--color-surface)] rounded-2xl border border-[#2A2A2D] p-6 space-y-4">
            <div>
              <label className="text-sm text-[#9CA3AF] mb-2 block">Email</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#9CA3AF]" />
                <Input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="vas@email.com"
                  className="pl-12 bg-[var(--color-background)] border-[#2A2A2D] focus:border-[var(--color-primary)] h-14"
                  data-testid="login-email-input"
                />
              </div>
            </div>

            <div>
              <label className="text-sm text-[#9CA3AF] mb-2 block">Lozinka</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#9CA3AF]" />
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="********"
                  className="pl-12 bg-[var(--color-background)] border-[#2A2A2D] focus:border-[var(--color-primary)] h-14"
                  data-testid="login-password-input"
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full h-14 bg-[var(--color-primary)] hover:bg-[var(--color-secondary)] text-black font-medium"
              data-testid="login-submit-btn"
            >
              {isLoading ? "Prijava..." : "Prijavite se"}
            </Button>
          </div>
        </form>

        <p className="text-center mt-6 text-sm text-[#9CA3AF]">
          <a href="/" className="hover:text-[var(--color-primary)] transition-colors flex items-center justify-center gap-1" data-testid="back-to-home-link">
            <ChevronRight className="w-4 h-4 rotate-180" />
            {"Nazad na početnu"}
          </a>
        </p>
      </div>
    </div>
  );
};

export default AdminLogin;
