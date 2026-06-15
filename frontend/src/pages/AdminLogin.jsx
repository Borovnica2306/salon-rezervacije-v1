import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "../App";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Mail, Lock, Scissors, ChevronRight } from "lucide-react";

const AdminLogin = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { slug } = useParams();
  const { login, user } = useAuth();

  // Smart redirect if already logged in
  useEffect(() => {
    if (user) {
      redirectUser(user);
    }
  }, [user]);

  const redirectUser = (userData) => {
    if (userData.role === "super_admin") {
      navigate("/super-admin", { replace: true });
    } else if (userData.slug || slug) {
      navigate(`/${userData.slug || slug}/admin`, { replace: true });
    } else {
      navigate("/", { replace: true });
    }
  };

  if (user) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error("Unesite email i lozinku");
      return;
    }

    setIsLoading(true);
    try {
      const data = await login(email, password);
      toast.success("Uspešna prijava!");
      redirectUser(data);
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

  return (
    <div className="min-h-screen bg-[var(--color-background)] flex items-center justify-center p-4">
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
