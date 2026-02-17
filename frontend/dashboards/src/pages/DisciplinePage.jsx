import { useEffect, useState } from "react";

async function api(path, opts = {}) {
  const base = import.meta.env.VITE_API_BASE_URL || "";
  const res = await fetch(`${base}${path}`, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(opts.headers || {}),
    },
  });
  const text = await res.text();
  let data = null;
  try { data = JSON.parse(text); } catch { data = text; }
  if (!res.ok) throw new Error(typeof data === "string" ? data : (data.detail || "Request failed"));
  return data;
}

export default function DisciplinePage() {
  const [items, setItems] = useState([]);
  const [err, setErr] = useState("");

  const load = async () => {
    setErr("");
    try {
      const data = await api("/api/discipline/incidents/");
      setItems(Array.isArray(data) ? data : []);
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div style={{ padding: "1.5rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: "600" }}>Discipline</h1>
        <button onClick={load} style={{ padding: "0.5rem 1rem", border: "1px solid #ccc", borderRadius: "6px", cursor: "pointer" }}>Refresh</button>
      </div>

      {err ? <div style={{ color: "#dc2626", fontSize: "0.875rem", marginBottom: "1rem" }}>{err}</div> : null}

      <div style={{ border: "1px solid #e5e7eb", borderRadius: "12px", padding: "1rem" }}>
        <div style={{ fontSize: "0.875rem", color: "#6b7280", marginBottom: "0.75rem" }}>Latest incidents (school-scoped)</div>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {items.slice(0, 30).map((x) => (
            <div key={x.id} style={{ border: "1px solid #e5e7eb", borderRadius: "8px", padding: "0.75rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ fontWeight: "500" }}>{x.summary}</div>
                <div style={{ fontSize: "0.75rem", opacity: 0.7 }}>{x.status} / {x.severity}</div>
              </div>
              <div style={{ fontSize: "0.875rem", opacity: 0.8 }}>{x.student_name}</div>
              <div style={{ fontSize: "0.75rem", opacity: 0.6 }}>{x.category} • {x.occurred_at}</div>
            </div>
          ))}
          {items.length === 0 ? <div style={{ fontSize: "0.875rem", opacity: 0.7 }}>No incidents found.</div> : null}
        </div>
      </div>
    </div>
  );
}
