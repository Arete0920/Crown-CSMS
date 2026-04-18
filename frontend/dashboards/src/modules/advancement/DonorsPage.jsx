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

const DONOR_TYPES = ["individual", "business", "church", "alumni"];
const EMPTY_FORM = { name: "", email: "", phone: "", organization: "", donor_type: "individual" };

export default function DonorsPage() {
  const [donors, setDonors] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api("/api/v1/advancement/donors/");
      setDonors(data.results ?? data);
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
        const data = await api("/api/v1/advancement/donors/");
        if (!cancelled) {
          setDonors(data.results ?? data);
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

  const filtered = donors.filter(
    (donor) =>
      donor.name?.toLowerCase().includes(search.toLowerCase()) ||
      donor.email?.toLowerCase().includes(search.toLowerCase()) ||
      donor.organization?.toLowerCase().includes(search.toLowerCase())
  );

  const handleCreate = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      await api("/api/v1/advancement/donors/", {
        method: "POST",
        body: JSON.stringify(form),
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

  if (loading) return <p aria-busy="true">Loading donors...</p>;
  if (error) return <p role="alert" style={{ color: "red" }}>Error: {error}</p>;

  return (
    <div aria-label="Donors">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>Donors ({filtered.length})</h2>
        <button onClick={() => setShowForm(!showForm)}>+ Add Donor</button>
      </div>

      <input
        aria-label="Search donors"
        placeholder="Search by name, email, or organization..."
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        style={{ width: "100%", padding: "8px 12px", marginBottom: 16, border: "1px solid #e2e8f0", borderRadius: 6 }}
      />

      {showForm && (
        <form onSubmit={handleCreate} aria-label="Add Donor Form" style={{ marginBottom: 20, padding: 16, border: "1px solid #e2e8f0", borderRadius: 8 }}>
          <h3 style={{ margin: "0 0 12px" }}>New Donor</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <label htmlFor="donor-name" style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 4 }}>Full Name *</label>
              <input id="donor-name" type="text" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required style={INPUT_STYLE} />
            </div>
            <div>
              <label htmlFor="donor-email" style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 4 }}>Email</label>
              <input id="donor-email" type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} style={INPUT_STYLE} />
            </div>
            <div>
              <label htmlFor="donor-phone" style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 4 }}>Phone</label>
              <input id="donor-phone" type="text" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} style={INPUT_STYLE} />
            </div>
            <div>
              <label htmlFor="donor-organization" style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 4 }}>Organization</label>
              <input id="donor-organization" type="text" value={form.organization} onChange={(event) => setForm({ ...form, organization: event.target.value })} style={INPUT_STYLE} />
            </div>
            <div>
              <label htmlFor="donor-type" style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 4 }}>Donor Type</label>
              <select id="donor-type" value={form.donor_type} onChange={(event) => setForm({ ...form, donor_type: event.target.value })} style={{ width: "100%", padding: "8px 10px", border: "1px solid #cbd5e1", borderRadius: 6 }}>
                {DONOR_TYPES.map((type) => <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>)}
              </select>
            </div>
          </div>
          <div style={{ marginTop: 12 }}>
            <button type="submit" disabled={saving}>{saving ? "Saving..." : "Create Donor"}</button>
            <button type="button" onClick={() => setShowForm(false)} style={{ marginLeft: 8 }}>Cancel</button>
          </div>
        </form>
      )}

      <table aria-label="Donors Table" style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            {["Name", "Email", "Type", "Organization", "Lifetime Giving"].map((heading) => (
              <th key={heading} scope="col" style={TH}>{heading}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filtered.length === 0 && (
            <tr><td colSpan={5} style={{ padding: 16, textAlign: "center", color: "#94a3b8" }}>No donors found.</td></tr>
          )}
          {filtered.map((donor) => (
            <tr key={donor.id}>
              <td style={TD}><strong>{donor.name}</strong></td>
              <td style={TD}>{donor.email}</td>
              <td style={TD}>{donor.donor_type}</td>
              <td style={TD}>{donor.organization || "-"}</td>
              <td style={TD}>${Number(donor.lifetime_giving || 0).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const INPUT_STYLE = { width: "100%", padding: "8px 10px", border: "1px solid #cbd5e1", borderRadius: 6, boxSizing: "border-box" };
const TH = { padding: "8px 12px", textAlign: "left", borderBottom: "2px solid #e2e8f0", fontSize: 13, color: "#475569" };
const TD = { padding: "8px 12px", borderBottom: "1px solid #f1f5f9", fontSize: 14 };
