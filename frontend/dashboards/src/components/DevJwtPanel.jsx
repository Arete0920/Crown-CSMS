import { useMemo, useState } from "react";
import {
  jwtLogin,
  clearAccessToken,
  getAccessToken,
  getSelectedSchoolId,
  setSelectedSchoolId,
} from "../utils/authClient";

/**
 * DevJwtPanel
 * - Dev-only login helper for fast local testing.
 * - Does NOT ship as a real login UX (we'll build real auth later).
 */
export default function DevJwtPanel() {
  const isDev = import.meta.env.DEV;
  const apiBase = useMemo(() => {
    return import.meta.env.VITE_API_BASE_URL;
  }, []);

  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [schoolId, setSchoolId] = useState(() => getSelectedSchoolId());
  const [status, setStatus] = useState(() => (getAccessToken() ? "token loaded" : "no token"));
  const [err, setErr] = useState("");

  if (!isDev) return null;

  const onLogin = async () => {
    setErr("");
    try {
      await jwtLogin({ username, password, apiBase });
      setStatus("token set");
    } catch (e) {
      setErr(String(e?.message || e));
      setStatus("login failed");
    }
  };

  const onClear = () => {
    clearAccessToken();
    setStatus("token cleared");
    setErr("");
  };

  const onSchoolChange = (v) => {
    setSchoolId(v);
    setSelectedSchoolId(v);
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
        background: "rgba(20,20,30,.92)",
        color: "#fff",
        zIndex: 9999,
        fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Arial",
        boxShadow: "0 10px 30px rgba(0,0,0,.35)",
      }}
    >
      <div style={{ fontWeight: 700, marginBottom: 6 }}>Dev JWT Login</div>
      <div style={{ fontSize: 12, opacity: 0.8, marginBottom: 10 }}>Status: {status}</div>

      <label style={{ fontSize: 12, display: "block", marginBottom: 4 }}>Username</label>
      <input
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        style={{
          width: "100%",
          padding: 8,
          borderRadius: 8,
          border: "1px solid rgba(255,255,255,.15)",
          marginBottom: 8,
        }}
      />

      <label style={{ fontSize: 12, display: "block", marginBottom: 4 }}>Password</label>
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        style={{
          width: "100%",
          padding: 8,
          borderRadius: 8,
          border: "1px solid rgba(255,255,255,.15)",
          marginBottom: 10,
        }}
      />

      <label style={{ fontSize: 12, display: "block", marginBottom: 4 }}>
        School ID (optional)
      </label>
      <input
        value={schoolId}
        onChange={(e) => onSchoolChange(e.target.value)}
        placeholder="UUID (X-Crown-School-Id)"
        style={{
          width: "100%",
          padding: 8,
          borderRadius: 8,
          border: "1px solid rgba(255,255,255,.15)",
          marginBottom: 10,
        }}
      />

      <div style={{ display: "flex", gap: 8 }}>
        <button
          onClick={onLogin}
          style={{ flex: 1, padding: 10, borderRadius: 10, border: 0, cursor: "pointer" }}
        >
          Login
        </button>
        <button
          onClick={onClear}
          style={{ flex: 1, padding: 10, borderRadius: 10, border: 0, cursor: "pointer" }}
        >
          Clear
        </button>
      </div>

      {err ? (
        <div style={{ marginTop: 10, fontSize: 12, color: "#ffb3b3", whiteSpace: "pre-wrap" }}>{err}</div>
      ) : null}
    </div>
  );
}
