/**
 * SeatSelectionPage – buyer-facing ticket seat picker.
 *
 * Flow:
 *   1. Load availability grid (GET /api/v1/advancement/seating/availability/?event_id=…)
 *   2. Buyer clicks seats to toggle selection
 *   3. "Reserve Seats" → POST /api/v1/advancement/seating/hold-strict/  (10-min hold)
 *   4. "Pay Now"       → POST /api/v1/advancement/seating/checkout/     → redirect to Stripe
 *
 * Auto-refreshes grid every 30 s to show real-time availability.
 * Displays a countdown timer once seats are held.
 *
 * Usage:
 *   <SeatSelectionPage eventId="<uuid>" />
 */
import { useState, useEffect, useCallback, useRef } from "react";

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

const HOLD_MINUTES = 10;
const STATUS_COLOR = {
  available: "#22c55e",
  held: "#f59e0b",
  sold: "#ef4444",
};

function SeatButton({ seat, selected, onToggle }) {
  const bg = selected
    ? "#2563eb"
    : STATUS_COLOR[seat.status] || "#6b7280";
  const cursor = seat.status === "available" || selected ? "pointer" : "not-allowed";
  return (
    <button
      title={`${seat.label} – ${seat.status}`}
      onClick={() => seat.status === "available" || selected ? onToggle(seat.seat_id) : null}
      style={{
        width: 36, height: 36, margin: 2, borderRadius: 4,
        background: bg, color: "#fff", fontSize: 10, fontWeight: 600,
        border: selected ? "2px solid #1e40af" : "1px solid rgba(0,0,0,0.15)",
        cursor, transition: "background 0.15s",
      }}
    >
      {seat.label.split("-").pop()}
    </button>
  );
}

function CountdownTimer({ expiresAt, onExpired }) {
  const [remaining, setRemaining] = useState("");

  useEffect(() => {
    const tick = () => {
      const diff = Math.floor((new Date(expiresAt) - Date.now()) / 1000);
      if (diff <= 0) {
        setRemaining("Expired");
        onExpired && onExpired();
      } else {
        const m = Math.floor(diff / 60).toString().padStart(2, "0");
        const s = (diff % 60).toString().padStart(2, "0");
        setRemaining(`${m}:${s}`);
      }
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [expiresAt, onExpired]);

  return (
    <span style={{ fontVariantNumeric: "tabular-nums", fontFamily: "monospace" }}>
      {remaining}
    </span>
  );
}

export default function SeatSelectionPage({ eventId }) {
  const [grid, setGrid] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [selected, setSelected] = useState(new Set()); // Set of seat_id strings
  const [holdResult, setHoldResult] = useState(null);  // ok + hold_expires_at
  const [holdError, setHoldError] = useState("");
  const [holdLoading, setHoldLoading] = useState(false);

  const [buyerName, setBuyerName] = useState("");
  const [buyerEmail, setBuyerEmail] = useState("");
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [checkoutError, setCheckoutError] = useState("");

  // Stage 3.4 – sponsor tiles
  const [sponsors, setSponsors] = useState([]);

  const timerRef = useRef(null);

  // ---------------------------------------------------------------------------
  // Load / refresh grid
  // ---------------------------------------------------------------------------
  const loadGrid = useCallback(async () => {
    if (!eventId) return;
    try {
      const r = await fetch(
        `${apiBase()}/api/v1/advancement/seating/availability/?event_id=${eventId}`,
        { headers: authHeaders() }
      );
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      setGrid(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [eventId]);

  useEffect(() => {
    loadGrid();
    const id = setInterval(loadGrid, 30_000);
    return () => clearInterval(id);
  }, [loadGrid]);

  // Stage 3.4 – load sponsors for this event
  useEffect(() => {
    if (!eventId) return;
    fetch(
      `${apiBase()}/api/v1/advancement/events/${eventId}/sponsors/`,
      { headers: authHeaders() }
    )
      .then((r) => r.ok ? r.json() : [])
      .then((data) => setSponsors(Array.isArray(data) ? data : []))
      .catch(() => setSponsors([]));
  }, [eventId]);

  // ---------------------------------------------------------------------------
  // Seat toggle
  // ---------------------------------------------------------------------------
  const toggleSeat = (seatId) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(seatId)) next.delete(seatId);
      else next.add(seatId);
      return next;
    });
    setHoldResult(null);
    setHoldError("");
  };

  // ---------------------------------------------------------------------------
  // Hold seats
  // ---------------------------------------------------------------------------
  const holdSeats = async () => {
    if (!buyerEmail) { setHoldError("Enter your email before reserving."); return; }
    if (selected.size === 0) { setHoldError("Select at least one seat."); return; }
    setHoldLoading(true);
    setHoldError("");
    try {
      const r = await fetch(`${apiBase()}/api/v1/advancement/seating/hold-strict/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          event_id: eventId,
          seat_ids: Array.from(selected),
          email: buyerEmail,
          hold_minutes: HOLD_MINUTES,
        }),
      });
      const data = await r.json();
      if (!r.ok || !data.ok) {
        const conflict = data.conflict?.length
          ? ` Conflict seats: ${data.conflict.length}`
          : "";
        setHoldError(`Could not reserve seats.${conflict}`);
        return;
      }
      setHoldResult(data);
    } catch (e) {
      setHoldError(e.message);
    } finally {
      setHoldLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Stripe checkout
  // ---------------------------------------------------------------------------
  const checkout = async () => {
    if (!holdResult?.ok) { setCheckoutError("Reserve seats first."); return; }
    if (!buyerName || !buyerEmail) { setCheckoutError("Enter your name and email."); return; }
    setCheckoutLoading(true);
    setCheckoutError("");
    try {
      const r = await fetch(`${apiBase()}/api/v1/advancement/seating/checkout/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          event_id: eventId,
          purchaser_name: buyerName,
          purchaser_email: buyerEmail,
          seat_ids: Array.from(selected),
          amount_cents: 0, // Server calculates from section prices; 0 = placeholder
        }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || "Checkout failed");
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    } catch (e) {
      setCheckoutError(e.message);
    } finally {
      setCheckoutLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  if (loading) return <div style={{ padding: 24 }}>Loading seat map…</div>;
  if (error) return <div style={{ padding: 24, color: "#ef4444" }}>Error: {error}</div>;
  if (!grid || !grid.sections) return <div style={{ padding: 24 }}>No seating configured for this event.</div>;

  const sections = grid.sections;

  return (
    <div style={{ padding: 24, maxWidth: 900, margin: "0 auto", fontFamily: "system-ui, sans-serif" }}>
      <h2 style={{ marginBottom: 8 }}>Select Your Seats</h2>

      {/* Stats bar */}
      <div style={{ display: "flex", gap: 16, marginBottom: 16, fontSize: 13, color: "#555" }}>
        <span>Total: <strong>{grid.capacity}</strong></span>
        <span style={{ color: STATUS_COLOR.available }}>Available: <strong>{grid.available}</strong></span>
        <span style={{ color: STATUS_COLOR.held }}>Held: <strong>{grid.held}</strong></span>
        <span style={{ color: STATUS_COLOR.sold }}>Sold: <strong>{grid.sold}</strong></span>
      </div>

      {/* Legend */}
      <div style={{ display: "flex", gap: 12, marginBottom: 20, fontSize: 12 }}>
        {[["#22c55e", "Available"], ["#f59e0b", "Held"], ["#ef4444", "Sold"], ["#2563eb", "Selected"]].map(([c, l]) => (
          <div key={l} style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <div style={{ width: 14, height: 14, borderRadius: 3, background: c }} />
            <span>{l}</span>
          </div>
        ))}
      </div>

      {/* Seat map */}
      {/* Stage 3.4 – Sponsor tiles */}
      {sponsors.length > 0 && (
        <div style={{ marginBottom: 20, padding: "12px 16px", background: "#f8fafc",
                      border: "1px solid #e2e8f0", borderRadius: 8 }}>
          <p style={{ fontSize: 12, color: "#6b7280", margin: "0 0 10px" }}>
            <strong>Event Sponsors</strong>
          </p>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            {sponsors.map((s, i) => (
              <div key={i} style={{ border: "1px solid #dde1e7", borderRadius: 8,
                                    padding: "8px 14px", background: "#fff",
                                    display: "flex", flexDirection: "column",
                                    alignItems: "center", minWidth: 100 }}>
                {s.logo_url && (
                  <img src={s.logo_url} alt={s.sponsor_name}
                       style={{ maxWidth: 80, maxHeight: 40, objectFit: "contain", marginBottom: 4 }} />
                )}
                <span style={{ fontSize: 11, color: "#374151", textAlign: "center" }}>
                  {s.sponsor_name}
                </span>
                {s.tier && s.tier !== "standard" && (
                  <span style={{ fontSize: 10, color: "#9ca3af", textTransform: "capitalize" }}>
                    {s.tier}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Seat map */}
      {Object.entries(sections).map(([sectionName, section]) => (
        <div key={sectionName} style={{ marginBottom: 20 }}>
          <h4 style={{ marginBottom: 8, color: "#374151" }}>Section {sectionName}</h4>
          {Object.entries(section.rows).map(([rowName, seats]) => (
            <div key={rowName} style={{ display: "flex", alignItems: "center", marginBottom: 4 }}>
              <span style={{ width: 28, fontSize: 12, color: "#666", textAlign: "right", marginRight: 8 }}>
                {rowName}
              </span>
              <div style={{ display: "flex", flexWrap: "wrap" }}>
                {seats.map((seat) => (
                  <SeatButton
                    key={seat.seat_id}
                    seat={seat}
                    selected={selected.has(seat.seat_id)}
                    onToggle={toggleSeat}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      ))}

      {/* Buyer info */}
      <div style={{ display: "flex", gap: 12, marginTop: 20, flexWrap: "wrap" }}>
        <input
          type="text"
          placeholder="Your full name"
          value={buyerName}
          onChange={(e) => setBuyerName(e.target.value)}
          style={{ flex: 1, minWidth: 180, padding: "8px 12px", border: "1px solid #d1d5db", borderRadius: 6 }}
        />
        <input
          type="email"
          placeholder="Your email"
          value={buyerEmail}
          onChange={(e) => setBuyerEmail(e.target.value)}
          style={{ flex: 1, minWidth: 180, padding: "8px 12px", border: "1px solid #d1d5db", borderRadius: 6 }}
        />
      </div>

      {/* Selection summary */}
      {selected.size > 0 && (
        <p style={{ marginTop: 8, fontSize: 14, color: "#374151" }}>
          {selected.size} seat{selected.size !== 1 ? "s" : ""} selected
        </p>
      )}

      {/* Hold timer */}
      {holdResult?.ok && holdResult.hold_expires_at && (
        <div style={{ marginTop: 12, padding: "8px 14px", background: "#fef3c7", borderRadius: 8, fontSize: 14 }}>
          Seats reserved! Time remaining: <strong>
            <CountdownTimer
              expiresAt={holdResult.hold_expires_at}
              onExpired={() => { setHoldResult(null); setSelected(new Set()); loadGrid(); }}
            />
          </strong>
        </div>
      )}

      {/* Actions */}
      <div style={{ display: "flex", gap: 12, marginTop: 16, flexWrap: "wrap" }}>
        {!holdResult?.ok ? (
          <button
            onClick={holdSeats}
            disabled={holdLoading || selected.size === 0}
            style={{
              padding: "10px 20px", background: "#2563eb", color: "#fff",
              border: "none", borderRadius: 6, fontWeight: 600, cursor: "pointer",
              opacity: holdLoading || selected.size === 0 ? 0.5 : 1,
            }}
          >
            {holdLoading ? "Reserving…" : `Reserve ${selected.size} Seat${selected.size !== 1 ? "s" : ""}`}
          </button>
        ) : (
          <button
            onClick={checkout}
            disabled={checkoutLoading}
            style={{
              padding: "10px 20px", background: "#16a34a", color: "#fff",
              border: "none", borderRadius: 6, fontWeight: 600, cursor: "pointer",
              opacity: checkoutLoading ? 0.5 : 1,
            }}
          >
            {checkoutLoading ? "Redirecting…" : "Pay Now →"}
          </button>
        )}

        <button
          onClick={loadGrid}
          style={{
            padding: "10px 16px", background: "#f3f4f6", color: "#374151",
            border: "1px solid #d1d5db", borderRadius: 6, cursor: "pointer",
          }}
        >
          Refresh Map
        </button>
      </div>

      {holdError && <p style={{ marginTop: 8, color: "#ef4444", fontSize: 14 }}>{holdError}</p>}
      {checkoutError && <p style={{ marginTop: 8, color: "#ef4444", fontSize: 14 }}>{checkoutError}</p>}
    </div>
  );
}
