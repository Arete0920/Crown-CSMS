import { useState } from "react";
import { authenticatedFetch } from "../utils/authClient.js";
import CrownLayout from "../components/crown/CrownLayout.jsx";

async function api(path, opts = {}) {
  const base = import.meta.env.VITE_API_BASE_URL || "";
  const res = await authenticatedFetch(`${base}${path}`, opts);
  return res.json();
}

export default function TeamsPreviewPage() {
  const [resp, setResp] = useState(null);
  const [err, setErr] = useState("");

  const send = async () => {
    setErr(""); setResp(null);
    try {
      const data = await api("/api/integrations/teams/preview/", {
        method: "POST",
        body: JSON.stringify({
          event_type: "discipline_incident",
          channel: "staff-general",
          title: "Discipline Incident Alert (Demo)",
          text: "A student has been assigned to in-school suspension.",
        }),
      });
      setResp(data);
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  return (
    <CrownLayout title="Teams Integration Preview" right={<button className="crown-btn crown-btn-primary" onClick={send}>Send Preview</button>}>

      {err ? <div style={{ color: "var(--crown-danger)", fontSize: "0.875rem", marginBottom: "1rem" }}>{err}</div> : null}
      {resp ? (
        <div style={{ border: "1px solid var(--crown-border)", borderRadius: "12px", padding: "1rem" }}>
          <div style={{ fontSize: "0.875rem", color: "var(--crown-muted)", marginBottom: "0.75rem" }}>Response (demo mode, no outbound calls)</div>
          <pre style={{ fontSize: "0.75rem", backgroundColor: "var(--crown-surface-2)", padding: "0.75rem", borderRadius: "6px", overflow: "auto" }}>{JSON.stringify(resp, null, 2)}</pre>
        </div>
      ) : null}
    </CrownLayout>
  );
}
