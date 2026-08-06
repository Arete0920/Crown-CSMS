import { useMemo, useState } from "react";
import {
  clearAccessToken,
  getAccessToken,
  getSelectedSchoolId,
} from "../utils/authClient";

/**
 * DevJwtPanel
 * - Dev-only login helper for fast local testing.
 * - Uses /api/dev/token/ endpoint (no password typing).
 * - Deterministic auth: single-button login.
 */
export default function DevJwtPanel() {
  const isDev = import.meta.env.DEV;
  const isDemoMode = import.meta.env.VITE_DEMO_MODE === "1";
  const apiBase = useMemo(() => {
    return import.meta.env.VITE_API_BASE_URL || "";
  }, []);
  const demoKey = useMemo(() => {
    return import.meta.env.VITE_DEMO_KEY || "";
  }, []);

  const [status, setStatus] = useState(() => (getAccessToken() ? "token loaded" : "no token"));
  const [err, setErr] = useState("");
  const [schoolId, setSchoolId] = useState(() => getSelectedSchoolId());

  // Hide in production builds AND during demo mode
  if (!isDev || isDemoMode) return null;

  const onDemoLogin = async () => {
    setErr("");
    setStatus("requesting...");
    try {
      const res = await globalThis.fetch(`${apiBase}/api/dev/token/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Demo-Key": demoKey,
        },
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Demo token failed: ${res.status} ${text.slice(0, 200)}`);
      }

      const data = await res.json();
      
      // Store token and school ID in sessionStorage (same keys as authenticatedFetch uses)
      sessionStorage.setItem("crown.jwt.access", data.access);
      sessionStorage.setItem("crown.school.id", data.school_id);
      
      setStatus("token set");
      setSchoolId(data.school_id);
      
      // Auto-reload page to refresh all authenticated data
      setTimeout(() => globalThis.location.reload(), 500);
    } catch (e) {
      setErr(String(e?.message || e));
      setStatus("login failed");
    }
  };

  const onClear = () => {
    clearAccessToken();
    sessionStorage.removeItem("crown.school.id");
    setStatus("token cleared");
    setErr("");
  };

  return (
    <div
      style={{
        position: "fixed",
        right: 12,
        bottom: 12,
        width: 320,
        padding: 12,
        borderRadius: 12,
        background: "var(--crown-compat-color-de9b5a6dd3)",
        color: "var(--crown-surface)",
        zIndex: 9999,
        fontFamily: "var(--crown-font-family)",
        boxShadow: "0 10px 30px var(--crown-compat-color-2d55e9cc1b)",
      }}
    >
      <div style={{ fontWeight: 700, marginBottom: 6 }}>Dev JWT Login</div>
      <div style={{ fontSize: 12, opacity: 0.8, marginBottom: 10 }}>Status: {status}</div>

      {schoolId && (
        <div style={{ fontSize: 11, opacity: 0.6, marginBottom: 10, wordBreak: "break-all" }}>
          School: {schoolId.slice(0, 8)}...
        </div>
      )}

      <div style={{ display: "flex", gap: 8 }}>
        <button
          onClick={onDemoLogin}
          style={{
            flex: 1,
            padding: 10,
            borderRadius: 10,
            border: 0,
            cursor: "pointer",
            background: "var(--crown-brand)",
            color: "var(--crown-surface)",
            fontWeight: 600,
          }}
        >
          Demo Login
        </button>
        <button
          onClick={onClear}
          style={{
            flex: 1,
            padding: 10,
            borderRadius: 10,
            border: 0,
            cursor: "pointer",
            background: "var(--crown-compat-color-fd3259d37c)",
            color: "var(--crown-surface)",
          }}
        >
          Clear
        </button>
      </div>

      {err ? (
        <div style={{ marginTop: 10, fontSize: 12, color: "var(--crown-danger-bg)", whiteSpace: "pre-wrap" }}>{err}</div>
      ) : null}
    </div>
  );
}

