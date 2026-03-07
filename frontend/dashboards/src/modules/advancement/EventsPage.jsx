/**
 * EventsPage — list events and attendance.
 * Calls GET /api/v1/advancement/events/
 */
import { useState, useEffect } from "react";

function apiBase() {
  const base = (import.meta?.env?.VITE_API_BASE_URL || "").trim();
  return base.endsWith("/") ? base.slice(0, -1) : base;
}
function getSession() {
  try {
    return {
      token:    sessionStorage.getItem("crown.jwt.access") || "",
      schoolId: sessionStorage.getItem("crown.school.id")  || "",
    };
  } catch { return { token: "", schoolId: "" }; }
}
function authHeaders() {
  const { token, schoolId } = getSession();
  const h = { Accept: "application/json", "Content-Type": "application/json" };
  if (token)    h["Authorization"] = `Bearer ${token}`;
  if (schoolId) h["X-School-Id"] = schoolId;
  return h;
}

export default function EventsPage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", date: "", location: "", ticket_price: "", capacity: "", description: "" });
  const [saving, setSaving] = useState(false);

  function load() {
    setLoading(true);
    fetch(`${apiBase()}/api/v1/advancement/events/`, { headers: authHeaders() })
      .then((r) => r.ok ? r.json() : Promise.reject(`HTTP ${r.status}`))
      .then((d) => { setEvents(d.results ?? d); setLoading(false); })
      .catch((e) => { setError(String(e)); setLoading(false); });
  }

  useEffect(() => { load(); }, []);

  function handleCreate(e) {
    e.preventDefault();
    setSaving(true);
    const payload = {
      ...form,
      ticket_price: parseFloat(form.ticket_price) || 0,
      capacity: parseInt(form.capacity) || 0,
    };
    fetch(`${apiBase()}/api/v1/advancement/events/`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload),
    })
      .then((r) => r.ok ? r.json() : Promise.reject(`HTTP ${r.status}`))
      .then(() => { setShowForm(false); setForm({ name: "", date: "", location: "", ticket_price: "", capacity: "", description: "" }); load(); })
      .catch((e) => alert(`Error: ${e}`))
      .finally(() => setSaving(false));
  }

  if (loading) return <p aria-busy="true">Loading events…</p>;
  if (error)   return <p role="alert" style={{ color: "red" }}>Error: {error}</p>;

  return (
    <div aria-label="Events">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>Events ({events.length})</h2>
        <button onClick={() => setShowForm(!showForm)}>+ Create Event</button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} aria-label="Create Event Form" style={{ marginBottom: 20, padding: 16, border: "1px solid #e2e8f0", borderRadius: 8 }}>
          <h3 style={{ margin: "0 0 12px" }}>New Event</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <Field label="Event Name *" value={form.name} onChange={(v) => setForm({ ...form, name: v })} required />
            <Field label="Date & Time *" type="datetime-local" value={form.date} onChange={(v) => setForm({ ...form, date: v })} required />
            <Field label="Location" value={form.location} onChange={(v) => setForm({ ...form, location: v })} />
            <Field label="Ticket Price ($)" type="number" value={form.ticket_price} onChange={(v) => setForm({ ...form, ticket_price: v })} />
            <Field label="Capacity (0 = unlimited)" type="number" value={form.capacity} onChange={(v) => setForm({ ...form, capacity: v })} />
            <Field label="Description" value={form.description} onChange={(v) => setForm({ ...form, description: v })} />
          </div>
          <div style={{ marginTop: 12 }}>
            <button type="submit" disabled={saving}>{saving ? "Saving…" : "Create Event"}</button>
            <button type="button" onClick={() => setShowForm(false)} style={{ marginLeft: 8 }}>Cancel</button>
          </div>
        </form>
      )}

      {events.length === 0 ? (
        <p style={{ color: "#94a3b8", textAlign: "center", padding: 32 }}>No events yet. Create your first event.</p>
      ) : (
        <table aria-label="Events Table" style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              {["Event", "Date", "Location", "Ticket Price", "Tickets Sold", "Capacity", "Attendance %"].map((h) => (
                <th key={h} scope="col" style={TH}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {events.map((e) => (
              <tr key={e.id}>
                <td style={TD}><strong>{e.name}</strong></td>
                <td style={TD}>{e.date ? new Date(e.date).toLocaleString() : "—"}</td>
                <td style={TD}>{e.location || "—"}</td>
                <td style={TD}>${Number(e.ticket_price || 0).toFixed(2)}</td>
                <td style={TD}>{e.tickets_sold}</td>
                <td style={TD}>{e.capacity || "∞"}</td>
                <td style={TD}>
                  <span style={{ fontWeight: 600, color: Number(e.attendance_percent) > 80 ? "#16a34a" : "#0f172a" }}>
                    {e.attendance_percent}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function Field({ label, value, onChange, type = "text", required = false }) {
  return (
    <div>
      <label style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 4 }}>{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        style={{ width: "100%", padding: "8px 10px", border: "1px solid #cbd5e1", borderRadius: 6, boxSizing: "border-box" }}
      />
    </div>
  );
}

const TH = { padding: "8px 12px", textAlign: "left", borderBottom: "2px solid #e2e8f0", fontSize: 13, color: "#475569" };
const TD = { padding: "8px 12px", borderBottom: "1px solid #f1f5f9", fontSize: 14 };
