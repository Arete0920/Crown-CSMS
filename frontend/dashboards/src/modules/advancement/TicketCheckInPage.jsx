/**
 * TicketCheckInPage  QR code-based event check-in scanner.
 * Calls POST /api/v1/advancement/qr-checkin/
 * Body:  { qr_code: string }
 * Returns TicketScan audit record with result: "accepted" | "duplicate" | "invalid"
 */
import { useState } from "react";

function apiBase() {
  const base = (import.meta?.env?.VITE_API_BASE_URL || "").trim();
  return base.endsWith("/") ? base.slice(0, -1) : base;
}
function getSession() {
  try {
    return {
      token: sessionStorage.getItem("crown.jwt.access") || "",
      schoolId: sessionStorage.getItem("crown.school.id") || "",
    };
  } catch {
    return { token: "", schoolId: "" };
  }
}
function authHeaders() {
  const { token, schoolId } = getSession();
  const h = { Accept: "application/json", "Content-Type": "application/json" };
  if (token) h["Authorization"] = `Bearer ${token}`;
  if (schoolId) h["X-School-Id"] = schoolId;
  return h;
}

const RESULT_STYLE = {
  accepted: { color: "var(--crown-compat-color-7d4ff8ff7b)", bg: "var(--crown-compat-color-64033be9a6)", label: " Accepted" },
  duplicate: { color: "var(--crown-compat-color-13b406d84d)", bg: "var(--crown-compat-color-5106142d0d)", label: " Duplicate  already checked in" },
  invalid: { color: "var(--crown-compat-color-59dbd12595)", bg: "var(--crown-compat-color-4b54505300)", label: " Invalid QR code" },
};

export default function TicketCheckInPage() {
  const [qrInput, setQrInput] = useState("");
  const [scanning, setScanning] = useState(false);
  const [lastScan, setLastScan] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const code = qrInput.trim();
    if (!code) return;
    setScanning(true);
    setError(null);
    try {
      const res = await globalThis.fetch(`${apiBase()}/api/v1/advancement/qr-checkin/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ qr_code: code }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data?.detail || `HTTP ${res.status}`);
        return;
      }
      setLastScan(data);
      setHistory((prev) => [data, ...prev].slice(0, 50));
      setQrInput("");
    } catch (err) {
      setError(String(err));
    } finally {
      setScanning(false);
    }
  }

  const resultStyle = lastScan ? RESULT_STYLE[lastScan.result] ?? RESULT_STYLE.invalid : null;

  return (
    <div style={{ maxWidth: 560, margin: "0 auto", padding: "2rem 1rem", fontFamily: "var(--crown-font-family)" }}>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "1.5rem" }}>
        QR Ticket Check-In
      </h1>

      {resultStyle && (
        <div
          style={{
            background: resultStyle.bg,
            color: resultStyle.color,
            border: `1px solid ${resultStyle.color}`,
            borderRadius: 8,
            padding: "1rem 1.25rem",
            marginBottom: "1.5rem",
            fontWeight: 600,
            fontSize: "1.1rem",
          }}
        >
          {resultStyle.label}
          {lastScan.ticket && (
            <div style={{ fontWeight: 400, fontSize: "0.85rem", marginTop: 4 }}>
              Ticket ID: {lastScan.ticket}
            </div>
          )}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: "flex", gap: 8, marginBottom: "2rem" }}>
        <input
          type="text"
          placeholder="Scan or paste QR code"
          value={qrInput}
          onChange={(e) => setQrInput(e.target.value)}
          disabled={scanning}
          style={{
            flex: 1,
            padding: "0.65rem 1rem",
            border: "1px solid var(--crown-compat-color-9643a6d44f)",
            borderRadius: 6,
            fontSize: "1rem",
          }}
        />
        <button
          type="submit"
          disabled={scanning || !qrInput.trim()}
          style={{
            padding: "0.65rem 1.25rem",
            background: "var(--crown-compat-color-1d4a6b66ff)",
            color: "var(--crown-compat-color-e08de71387)",
            border: "none",
            borderRadius: 6,
            cursor: scanning ? "wait" : "pointer",
            fontWeight: 600,
          }}
        >
          {scanning ? "Checking" : "Check In"}
        </button>
      </form>

      {error && (
        <div style={{ color: "var(--crown-compat-color-59dbd12595)", marginBottom: "1rem", fontSize: "0.9rem" }}>
          Error: {error}
        </div>
      )}

      {history.length > 0 && (
        <>
          <h2 style={{ fontSize: "1rem", fontWeight: 600, marginBottom: "0.75rem", color: "var(--crown-compat-color-a95c525e33)" }}>
            Recent scans ({history.length})
          </h2>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
            <thead>
              <tr style={{ borderBottom: "2px solid var(--crown-compat-color-bfd4f8ffca)", textAlign: "left" }}>
                <th style={{ padding: "0.4rem 0.5rem" }}>Result</th>
                <th style={{ padding: "0.4rem 0.5rem" }}>QR Attempted</th>
                <th style={{ padding: "0.4rem 0.5rem" }}>Scanned At</th>
              </tr>
            </thead>
            <tbody>
              {history.map((s) => {
                const rs = RESULT_STYLE[s.result] ?? RESULT_STYLE.invalid;
                return (
                  <tr key={s.id} style={{ borderBottom: "1px solid var(--crown-compat-color-8c857e7d93)" }}>
                    <td style={{ padding: "0.4rem 0.5rem", color: rs.color, fontWeight: 600 }}>
                      {rs.label}
                    </td>
                    <td style={{ padding: "0.4rem 0.5rem", fontFamily: "var(--crown-font-mono)" }}>
                      {s.qr_attempted}
                    </td>
                    <td style={{ padding: "0.4rem 0.5rem", color: "var(--crown-compat-color-66341b70b3)" }}>
                      {s.scanned_at ? new Date(s.scanned_at).toLocaleTimeString() : ""}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
