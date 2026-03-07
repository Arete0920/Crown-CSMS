/**
 * BestAvailableCheckout – "Ticketmaster-style" quantity + section picker.
 *
 * Screen A (selection):
 *   - Quantity selector (1–8)
 *   - Optional preferred section picker (loads from GET /events/<id>/section-prices/)
 *   - "Find Best Seats" button → POST /seating/best-available/checkout/
 *   - Shows computed amount + checkout_url
 *
 * Screen B (after redirect back from Stripe → via TicketSuccessPage):
 *   - User lands on TicketSuccessPage with ?order_id=…
 *
 * Props:
 *   eventId  – UUID of the event
 *   maxQty   – max tickets per order (default: 8)
 *
 * Usage:
 *   <BestAvailableCheckout eventId="<uuid>" />
 */
import { useState, useEffect } from "react";

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

export default function BestAvailableCheckout({ eventId, maxQty = 8 }) {
  const [sectionPrices, setSectionPrices] = useState([]); // [{ section, price_cents }]
  const [loadingPrices, setLoadingPrices] = useState(true);

  const [qty, setQty] = useState(2);
  const [preferredSections, setPreferredSections] = useState(new Set());

  const [buyerName, setBuyerName] = useState("");
  const [buyerEmail, setBuyerEmail] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null); // checkout ok response

  // ---------------------------------------------------------------------------
  // Load section prices
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (!eventId) return;
    (async () => {
      try {
        const r = await fetch(
          `${apiBase()}/api/v1/advancement/events/${eventId}/section-prices/`,
          { headers: authHeaders() }
        );
        if (r.ok) {
          const data = await r.json();
          setSectionPrices(data.prices || []);
        }
      } catch {
        // non-fatal; prices just won't display
      } finally {
        setLoadingPrices(false);
      }
    })();
  }, [eventId]);

  // ---------------------------------------------------------------------------
  // Toggle preferred section
  // ---------------------------------------------------------------------------
  const toggleSection = (section) => {
    setPreferredSections((prev) => {
      const next = new Set(prev);
      if (next.has(section)) next.delete(section);
      else next.add(section);
      return next;
    });
  };

  // ---------------------------------------------------------------------------
  // Find best seats + create checkout
  // ---------------------------------------------------------------------------
  const findAndCheckout = async () => {
    if (!buyerName || !buyerEmail) {
      setError("Enter your name and email.");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const body = {
        event_id: eventId,
        purchaser_name: buyerName,
        purchaser_email: buyerEmail,
        count: qty,
      };
      if (preferredSections.size > 0) {
        body.preferred_sections = Array.from(preferredSections);
      }

      const r = await fetch(
        `${apiBase()}/api/v1/advancement/seating/best-available/checkout/`,
        {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify(body),
        }
      );
      const data = await r.json();

      if (!r.ok || !data.ok) {
        const msg = data.error === "not_enough_seats"
          ? `Only ${data.available} seat${data.available !== 1 ? "s" : ""} available for your request of ${data.requested}.`
          : (data.detail || "Could not find seats. Try fewer seats or different sections.");
        setError(msg);
        return;
      }

      setResult(data);

      // Redirect to Stripe
      if (data.checkout_url) {
        setTimeout(() => { window.location.href = data.checkout_url; }, 800);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------
  const estimatedTotal = () => {
    if (sectionPrices.length === 0) return null;
    // Use lowest price as floor estimate
    const minPrice = Math.min(...sectionPrices.map((p) => p.price_cents));
    const preferred = sectionPrices.filter((p) => preferredSections.has(p.section));
    const avgPrice = preferred.length > 0
      ? preferred.reduce((s, p) => s + p.price_cents, 0) / preferred.length
      : minPrice;
    return (avgPrice * qty / 100).toFixed(2);
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  if (result?.ok) {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>✅</div>
          <h2 style={{ ...styles.heading, color: "#16a34a" }}>Seats Found!</h2>
          <p style={styles.subtext}>
            {result.seat_ids?.length} seat{result.seat_ids?.length !== 1 ? "s" : ""} reserved for you.
            Redirecting to checkout…
          </p>
          <div style={styles.infoBox}>
            <div style={styles.infoRow}>
              <span style={styles.label}>Total</span>
              <span style={styles.value}>
                {result.currency?.toUpperCase()} ${(result.amount_cents / 100).toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: 24, maxWidth: 560, margin: "0 auto", fontFamily: "system-ui, sans-serif" }}>
      <h2 style={{ marginBottom: 4 }}>Get Tickets</h2>
      <p style={{ color: "#6b7280", fontSize: 14, marginBottom: 24 }}>
        We'll find the best available seats for you automatically.
      </p>

      {/* Quantity */}
      <label style={styles.fieldLabel}>How many tickets?</label>
      <div style={{ display: "flex", gap: 8, marginBottom: 20, flexWrap: "wrap" }}>
        {Array.from({ length: maxQty }, (_, i) => i + 1).map((n) => (
          <button
            key={n}
            onClick={() => setQty(n)}
            style={{
              width: 40, height: 40, borderRadius: 8, border: "1px solid",
              borderColor: qty === n ? "#2563eb" : "#d1d5db",
              background: qty === n ? "#2563eb" : "#fff",
              color: qty === n ? "#fff" : "#374151",
              fontWeight: qty === n ? 700 : 400,
              cursor: "pointer", fontSize: 15,
            }}
          >
            {n}
          </button>
        ))}
      </div>

      {/* Section preference */}
      {!loadingPrices && sectionPrices.length > 0 && (
        <>
          <label style={styles.fieldLabel}>Preferred section (optional)</label>
          <div style={{ display: "flex", gap: 10, marginBottom: 20, flexWrap: "wrap" }}>
            {sectionPrices.map(({ section, price_cents }) => {
              const selected = preferredSections.has(section);
              return (
                <button
                  key={section}
                  onClick={() => toggleSection(section)}
                  style={{
                    padding: "8px 16px", borderRadius: 8, border: "1px solid",
                    borderColor: selected ? "#2563eb" : "#d1d5db",
                    background: selected ? "#eff6ff" : "#fff",
                    color: selected ? "#1d4ed8" : "#374151",
                    fontWeight: selected ? 600 : 400,
                    cursor: "pointer", fontSize: 13,
                  }}
                >
                  {section}
                  {price_cents > 0 && (
                    <span style={{ marginLeft: 6, color: "#6b7280" }}>
                      ${(price_cents / 100).toFixed(0)}/seat
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </>
      )}

      {/* Estimated total */}
      {estimatedTotal() !== null && (
        <p style={{ fontSize: 13, color: "#6b7280", marginBottom: 16 }}>
          Estimated total: ~<strong>${estimatedTotal()}</strong>
          {preferredSections.size === 0 ? " (varies by section)" : ""}
        </p>
      )}

      {/* Buyer info */}
      <label style={styles.fieldLabel}>Your details</label>
      <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 20 }}>
        <input
          type="text"
          placeholder="Full name"
          value={buyerName}
          onChange={(e) => setBuyerName(e.target.value)}
          style={styles.input}
        />
        <input
          type="email"
          placeholder="Email address"
          value={buyerEmail}
          onChange={(e) => setBuyerEmail(e.target.value)}
          style={styles.input}
        />
      </div>

      {error && (
        <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8,
                      padding: "10px 14px", color: "#dc2626", fontSize: 14, marginBottom: 16 }}>
          {error}
        </div>
      )}

      <button
        onClick={findAndCheckout}
        disabled={loading}
        style={{
          width: "100%", padding: "12px 0", background: "#2563eb", color: "#fff",
          border: "none", borderRadius: 8, fontWeight: 700, fontSize: 16,
          cursor: loading ? "wait" : "pointer",
          opacity: loading ? 0.7 : 1,
        }}
      >
        {loading ? "Finding your seats…" : `Get ${qty} Best Seat${qty !== 1 ? "s" : ""} →`}
      </button>

      <p style={{ fontSize: 12, color: "#9ca3af", marginTop: 12, textAlign: "center" }}>
        Seats will be held for 10 minutes while you complete checkout.
        Tickets delivered by email as PDF.
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------
const styles = {
  container: {
    minHeight: "70vh", display: "flex", alignItems: "center",
    justifyContent: "center", fontFamily: "system-ui, sans-serif",
  },
  card: {
    background: "#fff", borderRadius: 12, padding: "40px 48px",
    textAlign: "center", maxWidth: 480, width: "100%",
    boxShadow: "0 4px 24px rgba(0,0,0,0.08)",
  },
  heading: { fontSize: 24, fontWeight: 700, marginBottom: 8, color: "#111827" },
  subtext: { fontSize: 15, color: "#374151", marginBottom: 16, lineHeight: 1.5 },
  infoBox: { background: "#f3f4f6", borderRadius: 8, padding: 16, textAlign: "left", marginTop: 16 },
  infoRow: { display: "flex", justifyContent: "space-between", marginBottom: 8, fontSize: 14 },
  label: { color: "#6b7280" },
  value: { fontWeight: 600, color: "#111827" },
  fieldLabel: { display: "block", fontSize: 13, fontWeight: 600, color: "#374151", marginBottom: 8 },
  input: {
    padding: "10px 14px", border: "1px solid #d1d5db",
    borderRadius: 8, fontSize: 15, outline: "none", width: "100%",
    boxSizing: "border-box",
  },
};
