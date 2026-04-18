/**
 * SponsorshipsPage - list and manage sponsorship packages.
 * Calls GET /api/v1/advancement/sponsorships/
 */
import { useEffect, useId, useState } from "react";
import { authenticatedFetch } from "../../utils/authClient.js";

function apiBase() {
  const base = (import.meta?.env?.VITE_API_BASE_URL || "").trim();
  return base.endsWith("/") ? base.slice(0, -1) : base;
}

async function apiJson(path, opts = {}) {
  const response = await authenticatedFetch(`${apiBase()}${path}`, {
    ...opts,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(opts.headers || {}),
    },
  });
  return response.json();
}

export default function SponsorshipsPage() {
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", price: "", description: "", placement_type: "", duration: "" });
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiJson("/api/v1/advancement/sponsorships/");
      setPackages(data.results ?? data);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      try {
        const data = await apiJson("/api/v1/advancement/sponsorships/");
        if (!cancelled) {
          setPackages(data.results ?? data);
          setError(null);
          setLoading(false);
        }
      } catch (e) {
        if (!cancelled) {
          setError(String(e.message || e));
          setLoading(false);
        }
      }
    }

    void initialize();
    return () => {
      cancelled = true;
    };
  }, []);

  function handleCreate(e) {
    e.preventDefault();
    setSaving(true);
    const payload = { ...form, price: parseFloat(form.price) || 0 };
    apiJson("/api/v1/advancement/sponsorships/", {
      method: "POST",
      body: JSON.stringify(payload),
    })
      .then(() => {
        setShowForm(false);
        setForm({ name: "", price: "", description: "", placement_type: "", duration: "" });
        void load();
      })
      .catch((e) => alert(`Error: ${e.message || e}`))
      .finally(() => setSaving(false));
  }

  if (loading) return <p aria-busy="true">Loading sponsorship packages...</p>;
  if (error) return <p role="alert" style={{ color: "red" }}>Error: {error}</p>;

  return (
    <div aria-label="Sponsorship Packages">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>Sponsorship Packages ({packages.length})</h2>
        <button onClick={() => setShowForm(!showForm)}>+ Add Package</button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} aria-label="Create Sponsorship Package" style={{ marginBottom: 20, padding: 16, border: "1px solid #e2e8f0", borderRadius: 8 }}>
          <h3 style={{ margin: "0 0 12px" }}>New Sponsorship Package</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <Field label="Package Name *" value={form.name} onChange={(v) => setForm({ ...form, name: v })} required />
            <Field label="Price ($) *" type="number" value={form.price} onChange={(v) => setForm({ ...form, price: v })} required />
            <Field label="Placement Type" value={form.placement_type} onChange={(v) => setForm({ ...form, placement_type: v })} />
            <Field label="Duration" value={form.duration} onChange={(v) => setForm({ ...form, duration: v })} />
            <div style={{ gridColumn: "1 / -1" }}>
              <label htmlFor="sponsorship-description" style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 4 }}>Description</label>
              <textarea
                id="sponsorship-description"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                rows={3}
                style={{ width: "100%", padding: "8px 10px", border: "1px solid #cbd5e1", borderRadius: 6, boxSizing: "border-box", resize: "vertical" }}
              />
            </div>
          </div>
          <div style={{ marginTop: 12 }}>
            <button type="submit" disabled={saving}>{saving ? "Saving..." : "Create Package"}</button>
            <button type="button" onClick={() => setShowForm(false)} style={{ marginLeft: 8 }}>Cancel</button>
          </div>
        </form>
      )}

      {packages.length === 0 ? (
        <p style={{ color: "#94a3b8", textAlign: "center", padding: 32 }}>No sponsorship packages yet.</p>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16 }}>
          {packages.map((pkg) => (
            <article key={pkg.id} aria-label={pkg.name} style={{ border: "1px solid #e2e8f0", borderRadius: 8, padding: 20, background: "#fff" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <h3 style={{ margin: 0, fontSize: 16 }}>{pkg.name}</h3>
                <span style={{ fontWeight: 700, fontSize: 20, color: "#6366f1" }}>${Number(pkg.price).toLocaleString()}</span>
              </div>
              {pkg.description && <p style={{ margin: "8px 0 4px", fontSize: 13, color: "#475569" }}>{pkg.description}</p>}
              <div style={{ marginTop: 8, fontSize: 12, color: "#64748b" }}>
                {pkg.placement_type && <div>Placement: <strong>{pkg.placement_type}</strong></div>}
                {pkg.duration && <div>Duration: <strong>{pkg.duration}</strong></div>}
              </div>
              <div style={{ marginTop: 12 }}>
                <span style={{
                  display: "inline-block", padding: "2px 8px", borderRadius: 12, fontSize: 11, fontWeight: 600,
                  background: pkg.active ? "#dcfce7" : "#f1f5f9",
                  color: pkg.active ? "#16a34a" : "#94a3b8",
                }}>
                  {pkg.active ? "Active" : "Inactive"}
                </span>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

function Field({ label, value, onChange, type = "text", required = false }) {
  const inputId = useId();

  return (
    <div>
      <label htmlFor={inputId} style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 4 }}>{label}</label>
      <input
        id={inputId}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        style={{ width: "100%", padding: "8px 10px", border: "1px solid #cbd5e1", borderRadius: 6, boxSizing: "border-box" }}
      />
    </div>
  );
}