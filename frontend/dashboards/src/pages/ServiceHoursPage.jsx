import { useEffect, useState } from "react";
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
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export default function ServiceHoursPage() {
  const [pending, setPending] = useState([]);
  const [err, setErr] = useState("");

  const load = async () => {
    setErr("");
    try {
      const data = await api("/api/service/approvals/");
      setPending(Array.isArray(data) ? data : []);
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      try {
        const data = await api("/api/service/approvals/");
        if (!cancelled) {
          setPending(Array.isArray(data) ? data : []);
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
    <CrownLayout
      title="Service Hours"
      subtitle="Pending approvals and student service activity"
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h2 style={{ margin: 0, fontSize: 18, color: "var(--crown-ink)" }}>Pending Approvals</h2>
        <button className="crown-btn" onClick={load}>Refresh</button>
      </div>

      {err ? <ErrorBanner title="Service hours unavailable" message={err} /> : null}

      <div className="crown-card">
        <div style={{ fontSize: 12, color: "var(--crown-muted)", marginBottom: 10 }}>Pending approvals</div>
        <div style={{ display: "grid", gap: 8 }}>
          {pending.slice(0, 30).map((item) => (
            <div key={item.id} style={{ border: "1px solid var(--crown-border)", borderRadius: 10, padding: 10 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                <div style={{ fontWeight: 700, color: "var(--crown-ink)" }}>{item.student_name} - {item.hours}h</div>
                <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>{item.status}</div>
              </div>
              <div style={{ fontSize: 12, color: "var(--crown-muted)", marginTop: 4 }}>{item.category} - {item.organization}</div>
              <div style={{ fontSize: 11, color: "var(--crown-muted)", marginTop: 2 }}>{item.date}</div>
            </div>
          ))}
          {pending.length === 0 ? <div style={{ fontSize: 12, color: "var(--crown-muted)" }}>No pending items.</div> : null}
        </div>
      </div>
    </CrownLayout>
  );
}
