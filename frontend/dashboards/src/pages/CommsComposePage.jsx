import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { authenticatedFetch } from "../utils/authClient.js";
import CrownLayout from "../components/crown/CrownLayout.jsx";

async function api(path, opts = {}) {
  const base = import.meta.env.VITE_API_BASE_URL || "";
  const res = await authenticatedFetch(`${base}${path}`, opts);
  return res.json();
}

export default function CommsComposePage() {
  const nav = useNavigate();
  const [subject, setSubject] = useState("Quick Note");
  const [body, setBody] = useState("Hello�following up with a quick note.");
  const [err, setErr] = useState("");

  const send = async () => {
    setErr("");
    try {
      const resp = await api("/api/comms/compose/", {
        method: "POST",
        body: JSON.stringify({ subject, body }),
      });
      const id = resp?.thread_id;
      if (id) nav(`/comms/thread/${id}`);
      else nav("/comms");
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  return (
    <CrownLayout
      title="Compose"
      subtitle={<Link to="/comms">? Back to Inbox</Link>}
      right={<button className="crown-btn crown-btn-primary" onClick={send}>Send</button>}
    >

      {err ? <div style={{ color: "var(--crown-danger)", fontSize: "0.875rem", marginBottom: "1rem" }}>{err}</div> : null}

      <div style={{ border: "1px solid var(--crown-border)", borderRadius: "12px", padding: "1rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
          <div style={{ fontSize: "0.875rem", opacity: 0.7 }}>Subject</div>
          <input style={{ width: "100%", border: "1px solid var(--crown-border)", borderRadius: "8px", padding: "0.5rem", fontSize: "0.875rem" }} value={subject} onChange={(e) => setSubject(e.target.value)} />
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
          <div style={{ fontSize: "0.875rem", opacity: 0.7 }}>Message</div>
          <textarea style={{ width: "100%", border: "1px solid var(--crown-border)", borderRadius: "8px", padding: "0.5rem", fontSize: "0.875rem" }} rows={6} value={body} onChange={(e) => setBody(e.target.value)} />
        </div>
      </div>
    </CrownLayout>
  );
}
