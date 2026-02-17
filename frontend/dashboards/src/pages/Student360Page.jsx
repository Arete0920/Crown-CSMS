import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { authenticatedFetch } from "../utils/authClient.js";

async function api(path) {
  const base = import.meta.env.VITE_API_BASE_URL || "";
  const res = await authenticatedFetch(`${base}${path}`);
  return res.json();
}

function Tile({ title, children }) {
  return (
    <div style={{ border: "1px solid #e5e7eb", borderRadius: "12px", padding: "1rem" }}>
      <div style={{ fontSize: "0.85rem", color: "#6b7280", marginBottom: "0.5rem" }}>{title}</div>
      {children}
    </div>
  );
}

export default function Student360Page() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");

  const load = async () => {
    setErr("");
    try {
      const d = await api(`/api/360/students/${id}/overview/`);
      setData(d);
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  useEffect(() => { load(); }, [id]);

  const s = data?.student || {};
  const attendance = data?.attendance || {};
  const finance = data?.finance || {};
  const discipline = data?.discipline || {};
  const service = data?.service_hours || {};
  const comms = data?.comms || {};

  return (
    <div style={{ padding: "1.5rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "1rem" }}>
        <div>
          <div style={{ fontSize: "0.75rem", opacity: 0.7 }}>Student 360</div>
          <h1 style={{ fontSize: "1.6rem", fontWeight: 650, margin: 0 }}>
            {s.name || "Student"} {s.grade ? <span style={{ fontSize: "1rem", opacity: 0.6 }}>• Grade {s.grade}</span> : null}
          </h1>
        </div>
        <button onClick={load} style={{ padding: "0.5rem 1rem", border: "1px solid #ccc", borderRadius: "6px", cursor: "pointer" }}>
          Refresh
        </button>
      </div>

      {err ? <div style={{ color: "#dc2626", fontSize: "0.875rem", marginBottom: "1rem" }}>{err}</div> : null}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "1rem" }}>
        <Tile title="Attendance">
          <div style={{ fontSize: "1.25rem", fontWeight: 600 }}>
            {attendance.available ? (attendance.ytd_pct ?? "—") : "—"}{attendance.available && attendance.ytd_pct != null ? "%" : ""}
          </div>
          <div style={{ fontSize: "0.85rem", opacity: 0.75 }}>
            Last 30: {attendance.available ? (attendance.last30_pct ?? "—") : "—"}{attendance.available && attendance.last30_pct != null ? "%" : ""}
          </div>
          <div style={{ marginTop: "0.5rem", fontSize: "0.85rem" }}>
            <Link to="/attendance">View Attendance</Link>
          </div>
        </Tile>

        <Tile title="Finance">
          <div style={{ fontSize: "1.25rem", fontWeight: 600 }}>
            {finance.available ? `$${(finance.open_balance_estimate ?? 0).toFixed(2)}` : "—"}
          </div>
          <div style={{ fontSize: "0.85rem", opacity: 0.75 }}>
            Open invoices: {finance.available ? (finance.open_invoices ?? 0) : "—"}
          </div>
          <div style={{ marginTop: "0.5rem", fontSize: "0.85rem" }}>
            <Link to="/billing">Go to Billing</Link>
          </div>
        </Tile>

        <Tile title="Discipline">
          <div style={{ fontSize: "1.25rem", fontWeight: 600 }}>
            {discipline.available ? (discipline.incidents_total ?? 0) : "—"}
          </div>
          <div style={{ fontSize: "0.85rem", opacity: 0.75 }}>
            Open: {discipline.available ? (discipline.incidents_open ?? 0) : "—"}
          </div>
          <div style={{ marginTop: "0.5rem", fontSize: "0.85rem" }}>
            <Link to="/discipline">Open Discipline</Link>
          </div>
        </Tile>

        <Tile title="Service Hours">
          <div style={{ fontSize: "1.25rem", fontWeight: 600 }}>
            {service.available ? (service.approved_hours ?? 0) : "—"}{service.available ? " hrs" : ""}
          </div>
          <div style={{ fontSize: "0.85rem", opacity: 0.75 }}>
            Pending approvals: {service.available ? (service.pending_count ?? 0) : "—"}
          </div>
          <div style={{ marginTop: "0.5rem", fontSize: "0.85rem" }}>
            <Link to="/service-hours">Open Service Hours</Link>
          </div>
        </Tile>

        <Tile title="Comms">
          <div style={{ fontSize: "0.95rem", fontWeight: 600, marginBottom: "0.25rem" }}>
            Latest Threads
          </div>
          {comms.available ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {(comms.latest_threads || []).map((t) => (
                <Link key={t.id} to={`/comms/thread/${t.id}`} style={{ textDecoration: "none" }}>
                  <div style={{ border: "1px solid #e5e7eb", borderRadius: "8px", padding: "0.5rem" }}>
                    <div style={{ fontSize: "0.9rem", fontWeight: 500, color: "#111827" }}>{t.subject}</div>
                    <div style={{ fontSize: "0.75rem", opacity: 0.6 }}>{t.created_at || ""}</div>
                  </div>
                </Link>
              ))}
              <div style={{ fontSize: "0.85rem" }}>
                <Link to="/comms">Open Inbox</Link>
              </div>
            </div>
          ) : (
            <div style={{ fontSize: "0.85rem", opacity: 0.7 }}>Comms not available.</div>
          )}
        </Tile>
      </div>

      <div style={{ marginTop: "1.25rem", fontSize: "0.85rem", opacity: 0.75 }}>
        Tip: Use any seeded student UUID for the route: <code>/student-360/&lt;student_id&gt;</code>
      </div>
    </div>
  );
}
