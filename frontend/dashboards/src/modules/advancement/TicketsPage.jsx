/**
 * TicketsPage — list tickets, check in attendees, purchase new tickets.
 * Calls GET  /api/v1/advancement/tickets/
 *       POST /api/v1/advancement/purchase/ticket/
 *       POST /api/v1/advancement/tickets/{id}/check-in/
 */
import { useState, useEffect } from "react";

function apiBase() {
  const base = (import.meta?.env?.VITE_API_BASE_URL || "").trim();
  return base.endsWith("/") ? base.slice(0, -1) : base;
}
function getSession() {
  try {
    return { token: sessionStorage.getItem("crown.jwt.access") || "", schoolId: sessionStorage.getItem("crown.school.id") || "" };
  } catch { return { token: "", schoolId: "" }; }
}
function authHeaders() {
  const { token, schoolId } = getSession();
  const h = { Accept: "application/json", "Content-Type": "application/json" };
  if (token)    h["Authorization"] = `Bearer ${token}`;
  if (schoolId) h["X-School-Id"] = schoolId;
  return h;
}

export default function TicketsPage() {
  const [tickets, setTickets]   = useState([]);
  const [events, setEvents]     = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [showPurchase, setShowPurchase] = useState(false);
  const [filterEvent, setFilterEvent]  = useState("");
  const [form, setForm] = useState({ event_id: "", purchaser_name: "", purchaser_email: "" });
  const [purchasing, setPurchasing] = useState(false);
  const [checkingIn, setCheckingIn] = useState(null);

  function loadTickets(eventId = "") {
    let url = `${apiBase()}/api/v1/advancement/tickets/`;
    if (eventId) url += `?event_id=${eventId}`;
    return fetch(url, { headers: authHeaders() })
      .then((r) => r.ok ? r.json() : Promise.reject(`HTTP ${r.status}`))
      .then((d) => setTickets(d.results ?? d));
  }

  function loadEvents() {
    return fetch(`${apiBase()}/api/v1/advancement/events/?active=true`, { headers: authHeaders() })
      .then((r) => r.ok ? r.json() : Promise.reject(`HTTP ${r.status}`))
      .then((d) => setEvents(d.results ?? d));
  }

  useEffect(() => {
    Promise.all([loadTickets(), loadEvents()])
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  function handleFilterChange(eventId) {
    setFilterEvent(eventId);
    loadTickets(eventId).catch((e) => setError(String(e)));
  }

  function handlePurchase(e) {
    e.preventDefault();
    setPurchasing(true);
    fetch(`${apiBase()}/api/v1/advancement/purchase/ticket/`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(form),
    })
      .then((r) => r.ok ? r.json() : r.json().then((d) => Promise.reject(d.detail || `HTTP ${r.status}`)))
      .then(() => {
        setShowPurchase(false);
        setForm({ event_id: "", purchaser_name: "", purchaser_email: "" });
        loadTickets(filterEvent);
      })
      .catch((e) => alert(`Purchase failed: ${e}`))
      .finally(() => setPurchasing(false));
  }

  function handleCheckIn(ticketId) {
    setCheckingIn(ticketId);
    fetch(`${apiBase()}/api/v1/advancement/tickets/${ticketId}/check-in/`, {
      method: "POST",
      headers: authHeaders(),
    })
      .then((r) => r.ok ? r.json() : r.json().then((d) => Promise.reject(d.detail || `HTTP ${r.status}`)))
      .then(() => loadTickets(filterEvent))
      .catch((e) => alert(`Check-in failed: ${e}`))
      .finally(() => setCheckingIn(null));
  }

  if (loading) return <p aria-busy="true">Loading tickets…</p>;
  if (error)   return <p role="alert" style={{ color: "red" }}>Error: {error}</p>;

  return (
    <div aria-label="Tickets">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>Tickets ({tickets.length})</h2>
        <button onClick={() => setShowPurchase(!showPurchase)}>+ Purchase Ticket</button>
      </div>

      {/* Event filter */}
      <div style={{ marginBottom: 16 }}>
        <label htmlFor="event-filter" style={{ fontSize: 13, marginRight: 8 }}>Filter by event:</label>
        <select
          id="event-filter"
          value={filterEvent}
          onChange={(e) => handleFilterChange(e.target.value)}
          style={{ padding: "6px 10px", border: "1px solid #cbd5e1", borderRadius: 6 }}
        >
          <option value="">All Events</option>
          {events.map((ev) => <option key={ev.id} value={ev.id}>{ev.name}</option>)}
        </select>
      </div>

      {/* Purchase form */}
      {showPurchase && (
        <form onSubmit={handlePurchase} aria-label="Purchase Ticket Form" style={{ marginBottom: 20, padding: 16, border: "1px solid #e2e8f0", borderRadius: 8 }}>
          <h3 style={{ margin: "0 0 12px" }}>Purchase Ticket</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
            <div>
              <label style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 4 }}>Event *</label>
              <select required value={form.event_id} onChange={(e) => setForm({ ...form, event_id: e.target.value })}
                style={{ width: "100%", padding: "8px 10px", border: "1px solid #cbd5e1", borderRadius: 6 }}>
                <option value="">Select event…</option>
                {events.map((ev) => <option key={ev.id} value={ev.id}>{ev.name}</option>)}
              </select>
            </div>
            <Field label="Purchaser Name *" value={form.purchaser_name} onChange={(v) => setForm({ ...form, purchaser_name: v })} required />
            <Field label="Purchaser Email *" type="email" value={form.purchaser_email} onChange={(v) => setForm({ ...form, purchaser_email: v })} required />
          </div>
          <div style={{ marginTop: 12 }}>
            <button type="submit" disabled={purchasing}>{purchasing ? "Processing…" : "Purchase"}</button>
            <button type="button" onClick={() => setShowPurchase(false)} style={{ marginLeft: 8 }}>Cancel</button>
          </div>
        </form>
      )}

      <table aria-label="Tickets Table" style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            {["Event", "Purchaser", "Email", "Purchased", "Status", ""].map((h) => (
              <th key={h} scope="col" style={TH}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tickets.length === 0 && (
            <tr><td colSpan={6} style={{ padding: 16, textAlign: "center", color: "#94a3b8" }}>No tickets found.</td></tr>
          )}
          {tickets.map((t) => (
            <tr key={t.id}>
              <td style={TD}>{t.event_name || t.event}</td>
              <td style={TD}>{t.purchaser_name}</td>
              <td style={TD}>{t.purchaser_email}</td>
              <td style={TD}>{t.purchased_at ? new Date(t.purchased_at).toLocaleDateString() : "—"}</td>
              <td style={TD}>
                <span style={{
                  display: "inline-block", padding: "2px 8px", borderRadius: 12, fontSize: 12, fontWeight: 600,
                  background: t.checked_in ? "#dcfce7" : "#fef9c3",
                  color: t.checked_in ? "#16a34a" : "#92400e",
                }}>
                  {t.checked_in ? "Checked In" : "Not Checked In"}
                </span>
              </td>
              <td style={TD}>
                {!t.checked_in && (
                  <button
                    onClick={() => handleCheckIn(t.id)}
                    disabled={checkingIn === t.id}
                    style={{ fontSize: 12, padding: "4px 10px" }}
                    aria-label={`Check in ${t.purchaser_name}`}
                  >
                    {checkingIn === t.id ? "…" : "Check In"}
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Field({ label, value, onChange, type = "text", required = false }) {
  return (
    <div>
      <label style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 4 }}>{label}</label>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} required={required}
        style={{ width: "100%", padding: "8px 10px", border: "1px solid #cbd5e1", borderRadius: 6, boxSizing: "border-box" }} />
    </div>
  );
}

const TH = { padding: "8px 12px", textAlign: "left", borderBottom: "2px solid #e2e8f0", fontSize: 13, color: "#475569" };
const TD = { padding: "8px 12px", borderBottom: "1px solid #f1f5f9", fontSize: 14 };
