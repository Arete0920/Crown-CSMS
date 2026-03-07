/**
 * DonorsPage — list, search, and manage donors.
 * Calls GET /api/v1/advancement/donors/
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

const DONOR_TYPES = ["individual", "business", "church", "alumni"];

export default function DonorsPage() {
  const [donors, setDonors] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", phone: "", organization: "", donor_type: "individual" });
  const [saving, setSaving] = useState(false);

  function load() {
    setLoading(true);
    fetch(`${apiBase()}/api/v1/advancement/donors/`, { headers: authHeaders() })
      .then((r) => r.ok ? r.json() : Promise.reject(`HTTP ${r.status}`))
      .then((d) => { setDonors(d.results ?? d); setLoading(false); })
      .catch((e) => { setError(String(e)); setLoading(false); });
  }

  useEffect(() => { load(); }, []);

  const filtered = donors.filter(
    (d) =>
      d.name?.toLowerCase().includes(search.toLowerCase()) ||
      d.email?.toLowerCase().includes(search.toLowerCase()) ||
      d.organization?.toLowerCase().includes(search.toLowerCase())
  );

  function handleCreate(e) {
    e.preventDefault();
    setSaving(true);
    fetch(`${apiBase()}/api/v1/advancement/donors/`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(form),
    })
      .then((r) => r.ok ? r.json() : Promise.reject(`HTTP ${r.status}`))
      .then(() => { setShowForm(false); setForm({ name: "", email: "", phone: "", organization: "", donor_type: "individual" }); load(); })
      .catch((e) => alert(`Error: ${e}`))
      .finally(() => setSaving(false));
  }

  if (loading) return <p aria-busy="true">Loading donors…</p>;
  if (error)   return <p role="alert" style={{ color: "red" }}>Error: {error}</p>;

  return (
    <div aria-label="Donors">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>Donors ({filtered.length})</h2>
        <button onClick={() => setShowForm(!showForm)}>+ Add Donor</button>
      </div>

      <input
        aria-label="Search donors"
        placeholder="Search by name, email, or organization…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        style={{ width: "100%", padding: "8px 12px", marginBottom: 16, border: "1px solid #e2e8f0", borderRadius: 6 }}
      />

      {showForm && (
        <form onSubmit={handleCreate} aria-label="Add Donor Form" style={{ marginBottom: 20, padding: 16, border: "1px solid #e2e8f0", borderRadius: 8 }}>
          <h3 style={{ margin: "0 0 12px" }}>New Donor</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <Input label="Full Name *" value={form.name} onChange={(v) => setForm({ ...form, name: v })} required />
            <Input label="Email" type="email" value={form.email} onChange={(v) => setForm({ ...form, email: v })} />
            <Input label="Phone" value={form.phone} onChange={(v) => setForm({ ...form, phone: v })} />
            <Input label="Organization" value={form.organization} onChange={(v) => setForm({ ...form, organization: v })} />
            <div>
              <label style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 4 }}>Donor Type</label>
              <select value={form.donor_type} onChange={(e) => setForm({ ...form, donor_type: e.target.value })} style={{ width: "100%", padding: "8px 10px", border: "1px solid #cbd5e1", borderRadius: 6 }}>
                {DONOR_TYPES.map((t) => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
              </select>
            </div>
          </div>
          <div style={{ marginTop: 12 }}>
            <button type="submit" disabled={saving}>{saving ? "Saving…" : "Create Donor"}</button>
            <button type="button" onClick={() => setShowForm(false)} style={{ marginLeft: 8 }}>Cancel</button>
          </div>
        </form>
      )}

      <table aria-label="Donors Table" style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            {["Name", "Email", "Type", "Organization", "Lifetime Giving"].map((h) => (
              <th key={h} scope="col" style={TH}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filtered.length === 0 && (
            <tr><td colSpan={5} style={{ padding: 16, textAlign: "center", color: "#94a3b8" }}>No donors found.</td></tr>
          )}
          {filtered.map((d) => (
            <tr key={d.id}>
              <td style={TD}><strong>{d.name}</strong></td>
              <td style={TD}>{d.email}</td>
              <td style={TD}>{d.donor_type}</td>
              <td style={TD}>{d.organization || "—"}</td>
              <td style={TD}>${Number(d.lifetime_giving || 0).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Input({ label, value, onChange, type = "text", required = false }) {
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
