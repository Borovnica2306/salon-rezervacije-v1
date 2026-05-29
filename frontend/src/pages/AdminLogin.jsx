import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { useAuth, useTenant } from "../App";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Mail, Lock, Scissors } from "lucide-react";

const AdminLogin = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { slug } = useParams();
  const { login, user } = useAuth();
  const tenant = useTenant();

  if (user) {
    navigate(`/${slug}/admin`, { replace: true });
    return null;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error("Unesite email i lozinku");
      return;
    }

    setIsLoading(true);
    try {
      await login(email, password);
      toast.success("Uspešna prijava!");
      navigate(`/${slug}/admin`);
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
    <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8 animate-fade-in">
          <div className="w-16 h-16 rounded-2xl bg-[#C5A880]/20 flex items-center justify-center mx-auto mb-4">
            <Scissors className="w-8 h-8 text-[#C5A880]" />
          </div>
          <h1 className="font-['Cormorant_Garamond'] text-3xl font-light mb-2">Admin Panel</h1>
          <p className="text-[#9CA3AF]">Prijavite se za pristup dashboardu</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 animate-slide-up">
          <div className="bg-[#141416] rounded-2xl border border-[#2A2A2D] p-6 space-y-4">
            <div>
              <label className="text-sm text-[#9CA3AF] mb-2 block">Email</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#9CA3AF]" />
                <Input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@salon.com"
                  className="pl-12 bg-[#0A0A0B] border-[#2A2A2D] focus:border-[#C5A880] h-14"
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
                  placeholder="••••••••"
                  className="pl-12 bg-[#0A0A0B] border-[#2A2A2D] focus:border-[#C5A880] h-14"
                  data-testid="login-password-input"
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full h-14 bg-[#C5A880] hover:bg-[#B89970] text-black font-medium"
              data-testid="login-submit-btn"
            >
              {isLoading ? "Prijava..." : "Prijavite se"}
            </Button>
          </div>
        </form>

        <p className="text-center mt-6 text-sm text-[#9CA3AF]">
          <a href="/" className="hover:text-[#C5A880] transition-colors" data-testid="back-to-booking-link">
            ← Nazad na rezervacije
          </a>
        </p>
      </div>
    </div>
  );
};

export default AdminLogin;
