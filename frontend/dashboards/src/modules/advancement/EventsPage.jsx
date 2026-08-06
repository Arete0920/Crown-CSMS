import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api.js";

async function api(path, opts = {}) {
  const response = await apiFetch(path, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...opts.headers,
    },
  });
  const text = await response.text();
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

const EMPTY_FORM = { name: "", date: "", location: "", ticket_price: "", capacity: "", description: "" };

export default function EventsPage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api("/api/v1/advancement/events/");
      setEvents(data.results ?? data);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      try {
        const data = await api("/api/v1/advancement/events/");
        if (!cancelled) {
          setEvents(data.results ?? data);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError(String(e.message || e));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void initialize();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleCreate = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      const payload = {
        ...form,
        ticket_price: Number.parseFloat(form.ticket_price) || 0,
        capacity: Number.parseInt(form.capacity, 10) || 0,
      };
      await api("/api/v1/advancement/events/", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setShowForm(false);
      setForm(EMPTY_FORM);
      await load();
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p aria-busy="true">Loading events...</p>;
  if (error) return <p role="alert" style={{ color: "var(--crown-danger)" }}>Error: {error}</p>;

  return (
    <div aria-label="Events">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>Events ({events.length})</h2>
        <button onClick={() => setShowForm(!showForm)}>+ Create Event</button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} aria-label="Create Event Form" style={{ marginBottom: 20, padding: 16, border: "1px solid var(--crown-compat-color-3b313dfb66)", borderRadius: 8 }}>
          <h3 style={{ margin: "0 0 12px" }}>New Event</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <label htmlFor="event-name" style={{ fontSize: 12, color: "var(--crown-compat-color-6b3d6d843d)", display: "block", marginBottom: 4 }}>Event Name *</label>
              <input id="event-name" type="text" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required style={INPUT_STYLE} />
            </div>
            <div>
              <label htmlFor="event-date" style={{ fontSize: 12, color: "var(--crown-compat-color-6b3d6d843d)", display: "block", marginBottom: 4 }}>Date & Time *</label>
              <input id="event-date" type="datetime-local" value={form.date} onChange={(event) => setForm({ ...form, date: event.target.value })} required style={INPUT_STYLE} />
            </div>
            <div>
              <label htmlFor="event-location" style={{ fontSize: 12, color: "var(--crown-compat-color-6b3d6d843d)", display: "block", marginBottom: 4 }}>Location</label>
              <input id="event-location" type="text" value={form.location} onChange={(event) => setForm({ ...form, location: event.target.value })} style={INPUT_STYLE} />
            </div>
            <div>
              <label htmlFor="event-price" style={{ fontSize: 12, color: "var(--crown-compat-color-6b3d6d843d)", display: "block", marginBottom: 4 }}>Ticket Price ($)</label>
              <input id="event-price" type="number" value={form.ticket_price} onChange={(event) => setForm({ ...form, ticket_price: event.target.value })} style={INPUT_STYLE} />
            </div>
            <div>
              <label htmlFor="event-capacity" style={{ fontSize: 12, color: "var(--crown-compat-color-6b3d6d843d)", display: "block", marginBottom: 4 }}>Capacity (0 = unlimited)</label>
              <input id="event-capacity" type="number" value={form.capacity} onChange={(event) => setForm({ ...form, capacity: event.target.value })} style={INPUT_STYLE} />
            </div>
            <div>
              <label htmlFor="event-description" style={{ fontSize: 12, color: "var(--crown-compat-color-6b3d6d843d)", display: "block", marginBottom: 4 }}>Description</label>
              <input id="event-description" type="text" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} style={INPUT_STYLE} />
            </div>
          </div>
          <div style={{ marginTop: 12 }}>
            <button type="submit" disabled={saving}>{saving ? "Saving..." : "Create Event"}</button>
            <button type="button" onClick={() => setShowForm(false)} style={{ marginLeft: 8 }}>Cancel</button>
          </div>
        </form>
      )}

      {events.length === 0 ? (
        <p style={{ color: "var(--crown-compat-color-b5e2bc59ff)", textAlign: "center", padding: 32 }}>No events yet. Create your first event.</p>
      ) : (
        <table aria-label="Events Table" style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              {["Event", "Date", "Location", "Ticket Price", "Tickets Sold", "Capacity", "Attendance %"].map((heading) => (
                <th key={heading} scope="col" style={TH}>{heading}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {events.map((item) => (
              <tr key={item.id}>
                <td style={TD}><strong>{item.name}</strong></td>
                <td style={TD}>{item.date ? new Date(item.date).toLocaleString() : "-"}</td>
                <td style={TD}>{item.location || "-"}</td>
                <td style={TD}>${Number(item.ticket_price || 0).toFixed(2)}</td>
                <td style={TD}>{item.tickets_sold}</td>
                <td style={TD}>{item.capacity || "8"}</td>
                <td style={TD}>
                  <span style={{ fontWeight: 600, color: Number(item.attendance_percent) > 80 ? "var(--crown-compat-color-3c5c1ab6c5)" : "var(--crown-compat-color-0e684e5160)" }}>
                    {item.attendance_percent}%
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

const INPUT_STYLE = { width: "100%", padding: "8px 10px", border: "1px solid var(--crown-compat-color-e2442d83b3)", borderRadius: 6, boxSizing: "border-box" };
const TH = { padding: "8px 12px", textAlign: "left", borderBottom: "2px solid var(--crown-compat-color-3b313dfb66)", fontSize: 13, color: "var(--crown-compat-color-833631aa32)" };
const TD = { padding: "8px 12px", borderBottom: "1px solid var(--crown-compat-color-4702b16c05)", fontSize: 14 };
