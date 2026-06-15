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
        const ROLE_KEY = "crown.role";

        const did = await ensureDemoAutoLogin({
          apiBase,
          username: import.meta.env.VITE_DEMO_USER,
          password: import.meta.env.VITE_DEMO_PASS,
          schoolId: import.meta.env.VITE_DEMO_SCHOOL_ID,
          tokenKey: TOKEN_KEY,
          schoolKey: SCHOOL_KEY,
          role: import.meta.env.VITE_DEMO_ROLE || "school_admin",
          roleKey: ROLE_KEY,
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

