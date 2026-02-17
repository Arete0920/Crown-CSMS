import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { authenticatedFetch } from "../utils/authClient.js";

async function api(path, opts = {}) {
  const base = import.meta.env.VITE_API_BASE_URL || "";
  const res = await authenticatedFetch(`${base}${path}`, opts);
  return res.json();
}

export default function CommsThreadPage() {
  const { id } = useParams();
  const [thread, setThread] = useState(null);
  const [body, setBody] = useState("");
  const [err, setErr] = useState("");
  const [info, setInfo] = useState("");

  const load = async () => {
    setErr(""); setInfo("");
    try {
      const data = await api(`/api/comms/threads/${id}/`);
      setThread(data);
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  useEffect(() => { load(); }, [id]);

  const send = async () => {
    setErr(""); setInfo("");
    try {
      await api(`/api/comms/threads/${id}/messages/`, {
        method: "POST",
        body: JSON.stringify({ body }),
      });
      setBody("");
      setInfo("Message sent.");
      await load();
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  const teamsPreview = async () => {
    setErr(""); setInfo("");
    try {
      const resp = await api("/api/integrations/teams/preview/", {
        method: "POST",
        body: JSON.stringify({
          event_type: "comms_message",
          channel: "staff-general",
          title: "Message thread (Demo)",
          text: `Thread: ${thread?.subject || ""}`,
        }),
      });
      setInfo(`Queued Teams preview (demo): ${resp?.queued ? "yes" : "no"}`);
    } catch (e) {
      setErr(String(e.message || e));
    }
  };

  return (
    <div style={{ padding: "1.5rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <div>
          <div style={{ fontSize: "0.75rem", opacity: 0.7 }}><Link to="/comms">← Back to Inbox</Link></div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: "600" }}>{thread?.subject || "Thread"}</h1>
        </div>
        <button onClick={teamsPreview} style={{ padding: "0.5rem 1rem", border: "1px solid #ccc", borderRadius: "6px", cursor: "pointer" }}>Send to Teams (Preview)</button>
      </div>

      {err ? <div style={{ color: "#dc2626", fontSize: "0.875rem", marginBottom: "1rem" }}>{err}</div> : null}
      {info ? <div style={{ color: "#15803d", fontSize: "0.875rem", marginBottom: "1rem" }}>{info}</div> : null}

      <div style={{ border: "1px solid #e5e7eb", borderRadius: "12px", padding: "1rem" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1rem" }}>
          {(thread?.messages || []).map((m) => (
            <div key={m.id} style={{ border: "1px solid #e5e7eb", borderRadius: "8px", padding: "0.75rem" }}>
              <div style={{ fontSize: "0.75rem", opacity: 0.6 }}>{m.sender_name || "User"} • {m.created_at}</div>
              <div style={{ fontSize: "0.875rem" }}>{m.body}</div>
            </div>
          ))}
          {!thread?.messages?.length ? <div style={{ fontSize: "0.875rem", opacity: 0.7 }}>No messages.</div> : null}
        </div>

        <div style={{ borderTop: "1px solid #e5e7eb", paddingTop: "1rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          <textarea
            style={{ width: "100%", border: "1px solid #e5e7eb", borderRadius: "8px", padding: "0.5rem", fontSize: "0.875rem" }}
            rows={3}
            placeholder="Type a message…"
            value={body}
            onChange={(e) => setBody(e.target.value)}
          />
          <div style={{ display: "flex", justifyContent: "flex-end" }}>
            <button onClick={send} disabled={!body.trim()} style={{ padding: "0.5rem 1rem", border: "1px solid #ccc", borderRadius: "6px", cursor: body.trim() ? "pointer" : "not-allowed", opacity: body.trim() ? 1 : 0.5 }}>Send</button>
          </div>
        </div>
      </div>
    </div>
  );
}
