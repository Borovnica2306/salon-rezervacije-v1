import { createContext, useContext, useState, useEffect } from "react";

const PiAuthContext = createContext(null);
export const usePiAuth = () => useContext(PiAuthContext);

const SANDBOX_HOSTS = ["localhost", "127.0.0.1"];

function isSandboxEnv() {
  const host = window.location.hostname;
  if (SANDBOX_HOSTS.includes(host)) return true;
  if (host.includes("emergentagent.com")) return true;
  if (!window.Pi) return true;
  return false;
}

export const PiAuthProvider = ({ children }) => {
  const [piUser, setPiUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isSandbox, setIsSandbox] = useState(false);

  useEffect(() => {
    if (isSandboxEnv()) {
      setIsSandbox(true);
      const timer = setTimeout(() => {
        setPiUser({ uid: "mock_pi_user_marko_83", username: "MarkoDev" });
        setLoading(false);
      }, 500);
      return () => clearTimeout(timer);
    }

    // Production: load Pi SDK
    const script = document.createElement("script");
    script.src = "https://sdk.minepi.com/pi-sdk.js";
    script.async = true;
    script.onload = async () => {
      try {
        window.Pi.init({ version: "2.0", sandbox: false });
        const auth = await window.Pi.authenticate(
          ["username", "payments"],
          (payment) => {
            console.log("[Pi] Incomplete payment found:", payment);
          }
        );
        setPiUser({ uid: auth.user.uid, username: auth.user.username });
      } catch (err) {
        console.error("[Pi] Auth failed:", err);
      } finally {
        setLoading(false);
      }
    };
    script.onerror = () => {
      console.error("[Pi] SDK failed to load");
      setLoading(false);
    };
    document.head.appendChild(script);

    return () => {
      if (script.parentNode) script.parentNode.removeChild(script);
    };
  }, []);

  return (
    <PiAuthContext.Provider value={{ piUser, loading, isSandbox }}>
      {children}
    </PiAuthContext.Provider>
  );
};
