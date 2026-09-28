import { useEffect, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";

function apiBase() {
  const base = (import.meta?.env?.VITE_API_BASE_URL || "").trim();
  return base.endsWith("/") ? base.slice(0, -1) : base;
}

function getSession() {
  try {
    return {
      token: sessionStorage.getItem("crown.jwt.access") || "",
      schoolId: sessionStorage.getItem("crown.school.id") || "",
    };
  } catch {
    return { token: "", schoolId: "" };
  }
}

function authHeaders() {
  const { token, schoolId } = getSession();
  const headers = { Accept: "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (schoolId) headers["X-School-Id"] = schoolId;
  return headers;
}

export default function CrownPassMyTicketsPage() {
  const [tickets, setTickets] = useState([]);
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");
  const [activeTicket, setActiveTicket] = useState(null);
  const [credential, setCredential] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function loadTickets() {
      try {
        const response = await globalThis.fetch(
          `${apiBase()}/api/v1/crownpass/my-tickets/`,
          { headers: authHeaders() },
        );
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload?.detail || `HTTP ${response.status}`);
        }
        if (!cancelled) {
          setTickets(Array.isArray(payload?.tickets) ? payload.tickets : []);
          setStatus("ready");
        }
      } catch (err) {
        if (!cancelled) {
          setError(String(err?.message || err));
          setStatus("error");
        }
      }
    }

    loadTickets();
    return () => {
      cancelled = true;
    };
  }, []);

  async function showTicket(ticket) {
    setActiveTicket(ticket);
    setCredential(null);
    setError("");
    try {
      const response = await globalThis.fetch(
        `${apiBase()}/api/v1/crownpass/my-tickets/${ticket.ticket_id}/credential/`,
        { headers: authHeaders() },
      );
      const payload = await response.json();
      if (!response.ok) throw new Error(payload?.detail || `HTTP ${response.status}`);
      setCredential(payload);
    } catch (err) {
      setError(String(err?.message || err));
    }
  }

  function closeTicket() {
    setActiveTicket(null);
    setCredential(null);
  }

  return (
    <CrownLayout title="CrownPass — My Tickets" subtitle="Your Crown event tickets in one place">
      <div style={{ maxWidth: 860, margin: "0 auto" }}>

      {status === "loading" && <p>Loading tickets…</p>}

      {status === "error" && (
        <div role="alert">
          Unable to load CrownPass tickets: {error}
        </div>
      )}

      {status === "ready" && tickets.length === 0 && (
        <section aria-label="No CrownPass tickets">
          <h2>No tickets yet</h2>
          <p>Tickets purchased with your Crown account email will appear here.</p>
        </section>
      )}

      {activeTicket && (
        <section
          role="dialog"
          aria-modal="true"
          aria-label="CrownPass admission ticket"
          style={{
            marginBottom: 20,
            border: "2px solid var(--crown-compat-color-e2442d83b3)",
            borderRadius: 14,
            padding: 20,
            textAlign: "center",
          }}
        >
          <h2 style={{ marginTop: 0 }}>{activeTicket.event_name}</h2>
          {credential?.qr_data_url ? (
            <>
              <img
                src={credential.qr_data_url}
                alt="CrownPass admission QR code"
                width="260"
                height="260"
                style={{ maxWidth: "100%", height: "auto" }}
              />
              <p><strong>Present this code at the gate.</strong></p>
              <p style={{ fontSize: 12 }}>Ticket {activeTicket.ticket_id}</p>
            </>
          ) : (
            <p>Preparing secure ticket…</p>
          )}
          <button type="button" onClick={closeTicket}>Close Ticket</button>
        </section>
      )}

      {status === "ready" && tickets.length > 0 && (
        <section aria-label="CrownPass tickets" style={{ display: "grid", gap: 12 }}>
          {tickets.map((ticket) => (
            <article
              key={ticket.ticket_id}
              style={{
                border: "1px solid var(--crown-compat-color-e2442d83b3)",
                borderRadius: 12,
                padding: 16,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: 16 }}>
                <div>
                  <h2 style={{ margin: 0, fontSize: "1.1rem" }}>{ticket.event_name}</h2>
                  <p style={{ margin: "0.35rem 0 0" }}>{ticket.location || "Location to be announced"}</p>
                  {ticket.event_date && (
                    <p style={{ margin: "0.35rem 0 0" }}>
                      {new Date(ticket.event_date).toLocaleString()}
                    </p>
                  )}
                </div>
                <strong>{ticket.checked_in ? "Used" : "Ready"}</strong>
              </div>

              <div style={{ marginTop: 14, fontSize: 13 }}>
                Ticket ID: {ticket.ticket_id}
              </div>

              <div style={{ marginTop: 14 }}>
                <button type="button" onClick={() => showTicket(ticket)}>
                  Show Ticket
                </button>
              </div>
            </article>
          ))}
        </section>
      )}
      </div>
    </CrownLayout>
  );
}
