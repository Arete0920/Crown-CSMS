import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../lib/api.js";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import ErrorBanner from "../components/ui/ErrorBanner.jsx";

async function api(path, opts = {}) {
  const response = await apiFetch(path, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...opts.headers,
    },
  });
  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;
  if (!response.ok) {
    throw new Error(payload?.detail || `Request failed (${response.status})`);
  }
  return payload;
}

export default function StudentServiceHoursPage() {
  const [studentId, setStudentId] = useState("");
  const [entries, setEntries] = useState([]);
  const [err, setErr] = useState("");
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    date: new Date().toISOString().slice(0, 10),
    hours: "",
    category: "Community Service",
    organization: "",
    supervisor_name: "",
    supervisor_contact: "",
    notes: "",
  });

  const totals = useMemo(() => {
    return entries.reduce(
      (acc, entry) => {
        const hours = Number(entry.hours || 0);
        acc.total += hours;
        if (entry.status === "approved") acc.approved += hours;
        if (entry.status === "pending") acc.pending += hours;
        return acc;
      },
      { total: 0, approved: 0, pending: 0 },
    );
  }, [entries]);

  async function load() {
    setErr("");
    const overview = await api("/api/v1/360/me/overview/");
    const canonicalStudentId = overview?.student?.id;
    if (!canonicalStudentId) {
      throw new Error("A verified student identity is required before service hours can be submitted.");
    }
    setStudentId(canonicalStudentId);
    const rows = await api("/api/service/entries/");
    setEntries(Array.isArray(rows) ? rows : []);
  }

  useEffect(() => {
    load().catch((error) => setErr(String(error.message || error)));
  }, []);

  async function submit(event) {
    event.preventDefault();
    if (!studentId) {
      setErr("A verified student identity is required before service hours can be submitted.");
      return;
    }
    setSaving(true);
    setErr("");
    try {
      await api("/api/service/entries/", {
        method: "POST",
        body: JSON.stringify({ student: studentId, ...form }),
      });
      setForm((current) => ({ ...current, hours: "", organization: "", supervisor_name: "", supervisor_contact: "", notes: "" }));
      await load();
    } catch (error) {
      setErr(String(error.message || error));
    } finally {
      setSaving(false);
    }
  }

  return (
    <CrownLayout
      title="My Service Hours"
      subtitle="Log service activity and review your own approval history."
    >
      {err ? <ErrorBanner title="Service hours unavailable" message={err} /> : null}

      <div className="crown-card" style={{ marginBottom: 16 }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 12 }}>
          <div><strong>{totals.approved.toFixed(1)}</strong><div>Approved hours</div></div>
          <div><strong>{totals.pending.toFixed(1)}</strong><div>Pending hours</div></div>
          <div><strong>{totals.total.toFixed(1)}</strong><div>Total submitted</div></div>
        </div>
      </div>

      <form className="crown-card" onSubmit={submit} style={{ marginBottom: 16 }}>
        <h2 style={{ marginTop: 0 }}>Log service hours</h2>
        <div style={{ display: "grid", gap: 10, gridTemplateColumns: "repeat(2, minmax(0, 1fr))" }}>
          <label>Date<input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} required /></label>
          <label>Hours<input type="number" min="0.25" step="0.25" value={form.hours} onChange={(e) => setForm({ ...form, hours: e.target.value })} required /></label>
          <label>Category<input value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} /></label>
          <label>Organization<input value={form.organization} onChange={(e) => setForm({ ...form, organization: e.target.value })} /></label>
          <label>Supervisor name<input value={form.supervisor_name} onChange={(e) => setForm({ ...form, supervisor_name: e.target.value })} /></label>
          <label>Supervisor contact<input value={form.supervisor_contact} onChange={(e) => setForm({ ...form, supervisor_contact: e.target.value })} /></label>
        </div>
        <label style={{ display: "block", marginTop: 10 }}>Notes<textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} /></label>
        <button className="crown-btn" type="submit" disabled={saving || !studentId} style={{ marginTop: 12 }}>
          {saving ? "Submitting..." : "Submit hours"}
        </button>
      </form>

      <div className="crown-card">
        <h2 style={{ marginTop: 0 }}>My service history</h2>
        <div style={{ display: "grid", gap: 8 }}>
          {entries.map((entry) => (
            <div key={entry.id} style={{ border: "1px solid var(--crown-border)", borderRadius: 10, padding: 10 }}>
              <strong>{entry.hours}h — {entry.category || "Service"}</strong>
              <div>{entry.organization || "Organization not provided"}</div>
              <div style={{ fontSize: 12, color: "var(--crown-muted)" }}>{entry.date} · {entry.status}</div>
            </div>
          ))}
          {entries.length === 0 ? <div>No service hours submitted yet.</div> : null}
        </div>
      </div>
    </CrownLayout>
  );
}
