import { useEffect, useState } from "react";
import { ensureDemoAutoLogin } from "../utils/demoAutoLogin";

/**
 * AutoLoginGate
 * Handles demo-only auto-login on app start.
 * Runs once when VITE_DEMO_MODE=1 && VITE_DEMO_AUTO_LOGIN=1.
 */
export function AutoLoginGate({ children }) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const apiBase = import.meta.env.VITE_API_BASE_URL || "";

        const TOKEN_KEY = "crown.jwt.access";
        const SCHOOL_KEY = "crown.school.id";

        const did = await ensureDemoAutoLogin({
          apiBase,
          username: import.meta.env.VITE_DEMO_USER || "head@crown-demo.local",
          password: import.meta.env.VITE_DEMO_PASS || "demo1234",
          schoolId: import.meta.env.VITE_DEMO_SCHOOL_ID || "b45b8c5a-6708-4597-aad9-a226627b2962",
          tokenKey: TOKEN_KEY,
          schoolKey: SCHOOL_KEY,
        });

        // If we just logged in, reload once so all hooks see token + school immediately
        if (did) {
          window.location.reload();
          return; // Don't set ready, reload handles it
        }
      } catch (e) {
        // Don't crash the app; leave it in manual login state
        console.error("Demo auto-login failed:", e);
      }
      setReady(true);
    })();
  }, []);

  // Show nothing until auto-login attempt completes
  // (or reload happens, in which case this component remounts)
  if (!ready) return null;

  return children;
}

