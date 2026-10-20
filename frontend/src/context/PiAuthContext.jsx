import { createContext, useContext, useState, useEffect } from "react";

const PiAuthContext = createContext(null);
export const usePiAuth = () => useContext(PiAuthContext);

// Probni (mock) Pi nalog radi samo na preview/lokalnoj adresi
const isPreviewHost = () => {
  const host = window.location.hostname;
  return host === "localhost" || host === "127.0.0.1" || host.includes("emergentagent.com");
};

const detectPiBrowser = () => /PiBrowser/i.test(navigator.userAgent || "");

export const PiAuthProvider = ({ children }) => {
  const [piUser, setPiUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const isSandbox = isPreviewHost();
  const isPiBrowser = detectPiBrowser();

  useEffect(() => {
    if (isSandbox) {
      const timer = setTimeout(() => {
        setPiUser({ uid: "mock_pi_user_marko_83", username: "MarkoDev" });
        setLoading(false);
      }, 500);
      return () => clearTimeout(timer);
    }

    if (!isPiBrowser || !window.Pi) {
      setLoading(false);
      return;
    }

    (async () => {
      try {
        // Testnet mreža se bira registracijom aplikacije u Pi Developer Portalu
        await window.Pi.init({ version: "2.0", sandbox: false });
        const auth = await window.Pi.authenticate(["username", "payments"], (payment) => {
          console.log("[Pi] Incomplete payment found:", payment);
        });
        setPiUser({ uid: auth.user.uid, username: auth.user.username });
      } catch (err) {
        console.error("[Pi] Auth failed:", err);
      } finally {
        setLoading(false);
      }
    })();
  }, [isSandbox, isPiBrowser]);

  const canBook = isSandbox || isPiBrowser;

  return (
    <PiAuthContext.Provider value={{ piUser, loading, isSandbox, isPiBrowser, canBook }}>
      {children}
    </PiAuthContext.Provider>
  );
};
