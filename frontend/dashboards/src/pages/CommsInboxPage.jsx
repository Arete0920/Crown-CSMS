import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { authenticatedFetch } from "../utils/authClient.js";
import CrownLayout from "../components/crown/CrownLayout.jsx";

async function api(path, opts = {}) {
  const base = import.meta.env.VITE_API_BASE_URL || "";
  const res = await authenticatedFetch(`${base}${path}`, opts);
  return res.json();
}

export default function CommsInboxPage() {
  const [threads, setThreads] = useState([]);
  const [err, setErr] = useState("");

  const load = async () => {
    setErr("");
    try {
      const data = await api("/api/comms/threads/");
      setThreads(Array.isArray(data) ? data : []);
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <CrownLayout
      title="Inbox"
      right={<div style={{ display: "flex", gap: "0.5rem" }}><Link to="/comms/compose"><button className="crown-btn">Compose</button></Link><button className="crown-btn" onClick={load}>Refresh</button></div>}
    >

      {err ? <div style={{ color: "#dc2626", fontSize: "0.875rem", marginBottom: "1rem" }}>{err}</div> : null}

      <div style={{ border: "1px solid #e5e7eb", borderRadius: "12px", padding: "1rem" }}>
        <div style={{ fontSize: "0.875rem", color: "#6b7280", marginBottom: "0.75rem" }}>Threads (school-scoped)</div>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {threads.slice(0, 40).map((t) => (
            <Link key={t.id} to={`/comms/thread/${t.id}`} style={{ textDecoration: "none", color: "inherit" }}>
              <div style={{ border: "1px solid #e5e7eb", borderRadius: "8px", padding: "0.75rem", cursor: "pointer" }}>
                <div style={{ fontWeight: "500" }}>{t.subject}</div>
                <div style={{ fontSize: "0.75rem", opacity: 0.6 }}>{t.last_message_at || t.created_at}</div>
                <div style={{ fontSize: "0.875rem", opacity: 0.8 }}>{t.last_message_preview}</div>
              </div>
            </Link>
          ))}
          {threads.length === 0 ? <div style={{ fontSize: "0.875rem", opacity: 0.7 }}>No threads found.</div> : null}
        </div>
      </div>
    </CrownLayout>
  );
}
