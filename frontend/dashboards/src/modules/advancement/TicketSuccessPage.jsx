/**
 * TicketSuccessPage  polls order status after Stripe redirect and shows confirmation.
 *
 * Stripe redirects buyer to: /advancement/tickets/success?order_id=<uuid>
 * This page polls GET /api/v1/advancement/orders/<orderId>/status/ every 3 s
 * until status === "fulfilled" (or failed), then shows confirmation.
 *
 * Usage:
 *   <TicketSuccessPage />
 * (Reads ?order_id from URL via globalThis.location.search)
 */
import { useState, useEffect, useRef } from "react";

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
  const h = { Accept: "application/json", "Content-Type": "application/json" };
  if (token) h["Authorization"] = `Bearer ${token}`;
  if (schoolId) h["X-School-Id"] = schoolId;
  return h;
}

const POLL_INTERVAL_MS = 3000;
const MAX_POLLS = 20; // ~60 s before giving up

function getOrderIdFromUrl() {
  try {
    const params = new URLSearchParams(globalThis.location.search);
    return params.get("order_id") || "";
  } catch {
    return "";
  }
}

export default function TicketSuccessPage() {
  const orderId = getOrderIdFromUrl();
  const [status, setStatus] = useState("polling"); // "polling" | "fulfilled" | "failed" | "error"
  const [orderData, setOrderData] = useState(null);
  const [error, setError] = useState("");
  const pollCount = useRef(0);

  useEffect(() => {
    if (!orderId) {
      setStatus("error");
      setError("No order_id in URL.");
      return;
    }

    const poll = async () => {
      pollCount.current += 1;
      try {
        const r = await globalThis.fetch(
          `${apiBase()}/api/v1/advancement/orders/${orderId}/status/`,
          { headers: authHeaders() }
        );
        if (!r.ok) {
          if (r.status === 404) throw new Error("Order not found.");
          throw new Error(`HTTP ${r.status}`);
        }
        const data = await r.json();
        setOrderData(data);

        if (data.status === "fulfilled") {
          setStatus("fulfilled");
          clearInterval(intervalId);
        } else if (data.status === "failed") {
          setStatus("failed");
          clearInterval(intervalId);
        } else if (pollCount.current >= MAX_POLLS) {
          clearInterval(intervalId);
          setStatus("error");
          setError("Timed out waiting for payment confirmation. Check your email for updates.");
        }
      } catch (e) {
        clearInterval(intervalId);
        setStatus("error");
        setError(e.message);
      }
    };

    const intervalId = setInterval(poll, POLL_INTERVAL_MS);
    poll(); // immediate first poll

    return () => clearInterval(intervalId);
  }, [orderId]);

  // ---------------------------------------------------------------------------
  // Render states
  // ---------------------------------------------------------------------------

  if (status === "polling") {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <div style={styles.spinner} />
          <h2 style={styles.heading}>Confirming your payment</h2>
          <p style={styles.subtext}>This usually takes just a few seconds. Please don't close this page.</p>
        </div>
      </div>
    );
  }

  if (status === "fulfilled" && orderData) {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <div style={{ fontSize: 56, marginBottom: 12 }}></div>
          <h2 style={{ ...styles.heading, color: "#16a34a" }}>You're in!</h2>
          <p style={styles.subtext}>
            Order confirmed for <strong>{orderData.purchaser_email}</strong>.
            Your tickets have been emailed to you.
          </p>

          <div style={styles.infoBox}>
            <div style={styles.infoRow}>
              <span style={styles.label}>Order ID</span>
              <span style={styles.value}>{orderData.order_id}</span>
            </div>
            <div style={styles.infoRow}>
              <span style={styles.label}>Seats</span>
              <span style={styles.value}>{orderData.seat_ids?.length || 0}</span>
            </div>
            <div style={styles.infoRow}>
              <span style={styles.label}>Total</span>
              <span style={styles.value}>
                {orderData.currency?.toUpperCase()} ${(orderData.amount_cents / 100).toFixed(2)}
              </span>
            </div>
          </div>

          <p style={{ fontSize: 13, color: "#6b7280", marginTop: 16 }}>
            Check your email for your PDF tickets. Add them to your digital wallet or print and bring to the event.
          </p>

          {/* Stage 3.4  Wallet buttons (shown once we have ticket IDs) */}
          {orderData.ticket_ids?.length > 0 && (
            <div style={{ marginTop: 20, display: "flex", gap: 10, flexWrap: "wrap", justifyContent: "center" }}>
              <a
                href={`/api/v1/advancement/wallet/apple/tickets/${orderData.ticket_ids[0]}.pkpass`}
                style={{
                  display: "inline-block", padding: "10px 18px",
                  background: "#000", color: "#fff", borderRadius: 8,
                  fontWeight: 600, fontSize: 13, textDecoration: "none",
                }}
              >
                 Add to Apple Wallet
              </a>
              <button
                onClick={async () => {
                  try {
                    const r = await globalThis.fetch(
                      `/api/v1/advancement/wallet/google/tickets/${orderData.ticket_ids[0]}/link/`,
                      { headers: { Authorization: `Bearer ${sessionStorage.getItem("crown.jwt.access") || ""}` } }
                    );
                    const d = await r.json();
                    if (d.save_url) globalThis.open(d.save_url, "_blank");
                  } catch { /* non-fatal */ }
                }}
                style={{
                  display: "inline-block", padding: "10px 18px",
                  background: "#1a73e8", color: "#fff", borderRadius: 8,
                  fontWeight: 600, fontSize: 13, border: "none", cursor: "pointer",
                }}
              >
                 Add to Google Wallet
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  if (status === "failed") {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <div style={{ fontSize: 48, marginBottom: 12 }}></div>
          <h2 style={{ ...styles.heading, color: "#ef4444" }}>Payment not completed</h2>
          <p style={styles.subtext}>
            Your payment could not be processed. Your seats have been released.
            Please try again or contact support.
          </p>
          <button
            onClick={() => globalThis.history.back()}
            style={styles.button}
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // error state
  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={{ fontSize: 48, marginBottom: 12 }}></div>
        <h2 style={{ ...styles.heading, color: "#f59e0b" }}>Something went wrong</h2>
        <p style={styles.subtext}>{error}</p>
        <p style={{ fontSize: 13, color: "#6b7280" }}>
          If you completed payment, your tickets will appear in your email. Order ID: <strong>{orderId}</strong>
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------
const styles = {
  container: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "#f9fafb",
    fontFamily: "system-ui, sans-serif",
  },
  card: {
    background: "#fff",
    borderRadius: 12,
    padding: "40px 48px",
    textAlign: "center",
    maxWidth: 480,
    width: "100%",
    boxShadow: "0 4px 24px rgba(0,0,0,0.08)",
  },
  heading: {
    fontSize: 24,
    fontWeight: 700,
    marginBottom: 8,
    color: "#111827",
  },
  subtext: {
    fontSize: 15,
    color: "#374151",
    marginBottom: 16,
    lineHeight: 1.5,
  },
  infoBox: {
    background: "#f3f4f6",
    borderRadius: 8,
    padding: 16,
    textAlign: "left",
    marginTop: 16,
  },
  infoRow: {
    display: "flex",
    justifyContent: "space-between",
    marginBottom: 8,
    fontSize: 14,
  },
  label: { color: "#6b7280" },
  value: { fontWeight: 600, color: "#111827" },
  button: {
    marginTop: 16,
    padding: "10px 24px",
    background: "#2563eb",
    color: "#fff",
    border: "none",
    borderRadius: 6,
    fontWeight: 600,
    cursor: "pointer",
    fontSize: 15,
  },
  spinner: {
    width: 40,
    height: 40,
    border: "4px solid #e5e7eb",
    borderTop: "4px solid #2563eb",
    borderRadius: "50%",
    margin: "0 auto 20px",
    animation: "spin 0.8s linear infinite",
  },
};
