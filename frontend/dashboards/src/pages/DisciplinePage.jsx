import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api.js";
import CrownLayout from "../components/crown/CrownLayout.jsx";

async function api(path, opts = {}) {
  const response = await apiFetch(path, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(opts.headers || {}),
    },
  });
  const text = await response.text();
  let data = null;
  try {
    data = JSON.parse(text);
  } catch {
    data = text;
  }
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

  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      try {
        const data = await api("/api/discipline/incidents/");
        if (!cancelled) {
          setItems(Array.isArray(data) ? data : []);
          setErr("");
        }
      } catch (e) {
        if (!cancelled) {
          setErr(String(e.message || e));
        }
      }
    }

    void initialize();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <CrownLayout title="Discipline" subtitle="Incidents" right={<button className="crown-btn" onClick={load}>Refresh</button>}>

      {err ? <div style={{ color: "var(--crown-danger)", fontSize: "0.875rem", marginBottom: "1rem" }}>{err}</div> : null}

      <div style={{ border: "1px solid var(--crown-border)", borderRadius: "12px", padding: "1rem" }}>
        <div style={{ fontSize: "0.875rem", color: "var(--crown-muted)", marginBottom: "0.75rem" }}>Latest incidents (school-scoped)</div>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {items.slice(0, 30).map((x) => (
            <div key={x.id} style={{ border: "1px solid var(--crown-border)", borderRadius: "8px", padding: "0.75rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ fontWeight: "500" }}>{x.summary}</div>
                <div style={{ fontSize: "0.75rem", opacity: 0.7 }}>{x.status} / {x.severity}</div>
              </div>
              <div style={{ fontSize: "0.875rem", opacity: 0.8 }}>{x.student_name}</div>
              <div style={{ fontSize: "0.75rem", opacity: 0.6 }}>{x.category} | {x.occurred_at}</div>
            </div>
          ))}
          {items.length === 0 ? <div style={{ fontSize: "0.875rem", opacity: 0.7 }}>No incidents found.</div> : null}
        </div>
      </div>
    </CrownLayout>
  );
}