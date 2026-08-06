import { useEffect, useRef, useState } from "react";

import {
  PAYMENT_DISABLED_MESSAGE,
  PAYMENT_PROCESSING_ENABLED,
} from "./paymentAvailability.js";

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
  const headers = { Accept: "application/json", "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (schoolId) headers["X-School-Id"] = schoolId;
  return headers;
}

function getOrderIdFromUrl() {
  try {
    return new URLSearchParams(globalThis.location.search).get("order_id") || "";
  } catch {
    return "";
  }
}

const POLL_INTERVAL_MS = 3000;
const MAX_POLLS = 20;

export default function TicketSuccessPage() {
  const orderId = getOrderIdFromUrl();
  const [status, setStatus] = useState(
    PAYMENT_PROCESSING_ENABLED ? "polling" : "disabled"
  );
  const [orderData, setOrderData] = useState(null);
  const [error, setError] = useState("");
  const pollCount = useRef(0);

  useEffect(() => {
    if (!PAYMENT_PROCESSING_ENABLED) return undefined;

    if (!orderId) {
      setStatus("error");
      setError("No order_id in URL.");
      return undefined;
    }

    let intervalId;
    const poll = async () => {
      pollCount.current += 1;
      try {
        const response = await globalThis.fetch(
          `${apiBase()}/api/v1/advancement/orders/${orderId}/status/`,
          { headers: authHeaders() }
        );
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        setOrderData(data);
        if (data.status === "fulfilled" || data.status === "failed") {
          setStatus(data.status);
          clearInterval(intervalId);
        } else if (pollCount.current >= MAX_POLLS) {
          setStatus("error");
          setError("Timed out waiting for payment confirmation.");
          clearInterval(intervalId);
        }
      } catch (caught) {
        setStatus("error");
        setError(caught.message);
        clearInterval(intervalId);
      }
    };

    intervalId = setInterval(poll, POLL_INTERVAL_MS);
    poll();
    return () => clearInterval(intervalId);
  }, [orderId]);

  if (status === "disabled") {
    return (
      <main style={styles.container}>
        <section style={styles.card}>
          <h2 style={styles.warningHeading}>Online payment unavailable</h2>
          <p style={styles.subtext}>{PAYMENT_DISABLED_MESSAGE}</p>
        </section>
      </main>
    );
  }

  if (status === "polling") {
    return (
      <main style={styles.container}>
        <section style={styles.card}>
          <h2 style={styles.heading}>Confirming your payment</h2>
          <p style={styles.subtext}>Please keep this page open.</p>
        </section>
      </main>
    );
  }

  if (status === "fulfilled" && orderData) {
    return (
      <main style={styles.container}>
        <section style={styles.card}>
          <h2 style={styles.successHeading}>Order confirmed</h2>
          <p style={styles.subtext}>Your tickets have been emailed to you.</p>
        </section>
      </main>
    );
  }

  if (status === "failed") {
    return (
      <main style={styles.container}>
        <section style={styles.card}>
          <h2 style={styles.errorHeading}>Payment not completed</h2>
          <p style={styles.subtext}>Contact the school office for assistance.</p>
        </section>
      </main>
    );
  }

  return (
    <main style={styles.container}>
      <section style={styles.card}>
        <h2 style={styles.warningHeading}>Unable to confirm payment</h2>
        <p style={styles.subtext}>{error}</p>
      </section>
    </main>
  );
}

const styles = {
  container: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "var(--crown-compat-color-ad8260e36d)",
    fontFamily: "var(--crown-font-family)",
  },
  card: {
    background: "var(--crown-compat-color-e08de71387)",
    borderRadius: 12,
    padding: "40px 48px",
    textAlign: "center",
    maxWidth: 480,
    width: "100%",
    boxShadow: "0 4px 24px var(--crown-compat-color-a70919eca5)",
  },
  heading: { fontSize: 24, fontWeight: 700, color: "var(--crown-compat-color-dd15e6f7d4)" },
  warningHeading: { fontSize: 24, fontWeight: 700, color: "var(--crown-compat-color-90b141cff8)" },
  successHeading: { fontSize: 24, fontWeight: 700, color: "var(--crown-compat-color-e21c21ccc2)" },
  errorHeading: { fontSize: 24, fontWeight: 700, color: "var(--crown-compat-color-59dbd12595)" },
  subtext: { fontSize: 15, color: "var(--crown-compat-color-a95c525e33)", lineHeight: 1.5 },
};
