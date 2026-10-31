import { useEffect, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import DashboardSection from "../components/layout/DashboardSection.jsx";
import { fetchRosterToday, checkinStudent, checkoutStudent, fetchPickupContacts, handoffToSchool } from "../api/aftercareApi.js";

const TAG = {
  base: { display: "inline-block", padding: "2px 8px", borderRadius: 12, fontSize: 12, fontWeight: 600 },
  default: { background: "var(--crown-surface-2)", color: "var(--crown-muted)" },
  primary: { background: "var(--crown-surface-2)", color: "var(--crown-brand)" },
  success: { background: "var(--crown-ok-bg)", color: "var(--crown-ok)" },
};

const TH = { padding: "8px 12px", textAlign: "left", fontSize: 12, fontWeight: 700, borderBottom: "2px solid var(--crown-border)", whiteSpace: "nowrap" };
const TD = { padding: "8px 12px", fontSize: 13, borderBottom: "1px solid var(--crown-border)" };
const BTN_OUT = { cursor: "pointer", padding: "4px 10px", fontSize: 12, borderRadius: 4, border: "1px solid var(--crown-border)", background: "transparent" };
const BTN_PRIM = { cursor: "pointer", padding: "4px 10px", fontSize: 12, borderRadius: 4, border: "none", background: "var(--crown-ok)", color: "var(--crown-surface)" };

export default function AftercareRosterPage({ careSession = "PM" }) {
  const isMorning = careSession === "AM";
  const sessionLabel = isMorning ? "Before Care" : "After Care";
  const [handoff, setHandoff] = useState(null);
  const [handoffBusy, setHandoffBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [roster, setRoster] = useState(null);
  const [pickup, setPickup] = useState(null);
  const [pickupBusy, setPickupBusy] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRosterToday(careSession);
      setRoster(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      try {
        const data = await fetchRosterToday(careSession);
        if (!cancelled) {
          setRoster(data);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void initialize();
    return () => {
      cancelled = true;
    };
  }, [careSession]);

  async function handleCheckin(studentId) {
    try {
      await checkinStudent({ student_id: studentId, care_session: careSession });
      await load();
    } catch (e) {
      alert(`Check-in failed: ${e.message}`);
    }
  }

  async function beginCheckout(studentId) {
    setPickupBusy(true);
    setError(null);
    try {
      const contacts = await fetchPickupContacts(studentId);
      setPickup({ studentId, contacts: Array.isArray(contacts) ? contacts.filter((c) => c.is_active) : [],
                  contactId: "", verified: false });
    } catch (e) {
      setError(`Cannot load authorized pickup contacts: ${e.message}`);
    } finally {
      setPickupBusy(false);
    }
  }

  async function handleCheckout() {
    if (!pickup?.contactId || !pickup.verified) return;
    setPickupBusy(true);
    try {
      await checkoutStudent({
        student_id: pickup.studentId,
        pickup_contact_id: pickup.contactId,
        pickup_verified: true,
      });
      setPickup(null);
      await load();
    } catch (e) {
      setError(`Check-out failed: ${e.message}`);
    } finally {
      setPickupBusy(false);
    }
  }

  async function handleHandoff() {
    if (!handoff?.acknowledged) return;
    setHandoffBusy(true);
    setError(null);
    try {
      await handoffToSchool({ student_id: handoff.studentId });
      setHandoff(null);
      await load();
    } catch (e) {
      setError("School handoff failed: " + e.message);
    } finally {
      setHandoffBusy(false);
    }
  }

  const rosterTitle = roster
    ? "Today's " + sessionLabel + " Roster - " + roster.date + " (" + roster.dow + ")"
    : "Today's " + sessionLabel + " Roster";

  return (
    <CrownLayout title={sessionLabel + " Roster"}>
      <DashboardSection title={rosterTitle}>
        {loading && <span>Loading...</span>}
        {error && <div style={{ color: "var(--crown-danger)", background: "var(--crown-danger-bg)", padding: "10px 14px", borderRadius: 4, marginBottom: 12 }}>{error}</div>}
        {!loading && !error && roster && (
          <div style={{ border: "1px solid var(--crown-border)", borderRadius: 4, overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={TH}>Child</th>
                  <th style={TH}>Billing</th>
                  <th style={TH}>Status</th>
                  <th style={TH}>Late Min</th>
                  <th style={TH}>Late Fee</th>
                  <th style={TH}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {roster.rows.length === 0 && (
                  <tr>
                    <td colSpan={6} style={{ ...TD, color: "var(--crown-muted)" }}>No students scheduled today.</td>
                  </tr>
                )}
                {roster.rows.map((row) => {
                  const hasCheckin = !!row.attendance;
                  const hasCheckout = Boolean(row.attendance?.checkout_time);
                  const verifiedClosure = hasCheckout && (isMorning
                    ? Boolean(row.attendance?.handoff_verified && row.attendance?.handoff_time)
                    : Boolean(row.attendance?.pickup_verified));
                  const statusChip = !row.attendance
                    ? <span style={{ ...TAG.base, ...TAG.default }}>Not checked in</span>
                    : hasCheckout
                      ? verifiedClosure
                        ? <span style={{ ...TAG.base, ...TAG.success }}>{isMorning ? "Handed off" : "Checked out"}</span>
                        : <span role="alert" style={{ ...TAG.base, ...TAG.default }}>Unverified {isMorning ? "handoff" : "checkout"} — review</span>
                      : <span style={{ ...TAG.base, ...TAG.primary }}>Checked in</span>;

                  return (
                    <tr key={row.student_id}>
                      <td style={TD}>{row.student_name || row.student_id}</td>
                      <td style={TD}>{row.enrollment?.billing_model}</td>
                      <td style={TD}>{statusChip}</td>
                      <td style={TD}>{row.attendance?.late_minutes ?? "-"}</td>
                      <td style={TD}>
                        {row.attendance?.late_fee_cents
                          ? `$${(row.attendance.late_fee_cents / 100).toFixed(2)}`
                          : "-"}
                      </td>
                      <td style={TD}>
                        {!hasCheckin && (
                          <button style={BTN_OUT} onClick={() => handleCheckin(row.student_id)}>Check In</button>
                        )}
                        {hasCheckin && !hasCheckout && !isMorning && (
                          <button style={BTN_PRIM} onClick={() => beginCheckout(row.student_id)} disabled={pickupBusy}>Verify Pickup</button>
                        )}
                        {hasCheckin && !hasCheckout && isMorning && (
                          <button style={BTN_PRIM} onClick={() => setHandoff({ studentId: row.student_id, acknowledged: false })} disabled={handoffBusy}>Acknowledge School Handoff</button>
                        )}
                        {hasCheckin && hasCheckout && !verifiedClosure && (
                          <span>Supervisor review required; custody status is unverified.</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        {handoff && (
          <div role="dialog" aria-modal="true" aria-label="Confirm receiving staff handoff" style={{ border: "1px solid var(--crown-border)", padding: 16, marginTop: 16 }}>
            <h3>School handoff for {handoff.studentId}</h3>
            <p>The authenticated receiving staff member must personally confirm the child is physically in their care. This is a recorded staff attestation, not automated identity proof.</p>
            <label style={{ display: "block", marginTop: 12 }}>
              <input type="checkbox" checked={handoff.acknowledged} onChange={(e) => setHandoff((old) => ({ ...old, acknowledged: e.target.checked }))} />
              I am the receiving staff member and acknowledge custody of this child.
            </label>
            <button type="button" onClick={handleHandoff} disabled={handoffBusy || !handoff.acknowledged}>Record School Handoff</button>
            <button type="button" style={{ marginLeft: 12 }} disabled={handoffBusy} onClick={() => setHandoff(null)}>Cancel</button>
          </div>
        )}
        {pickup && (
          <div role="dialog" aria-modal="true" aria-label="Verify authorized pickup" style={{ border: "1px solid var(--crown-border)", padding: 16, marginTop: 16 }}>
            <h3>Verify pickup for {pickup.studentId}</h3>
            <p>Confirm the person's identity against the school's authorized pickup record before releasing a student.</p>
            {pickup.contacts.length === 0 ? (
              <p>No active authorized pickup contacts are on file. Checkout is blocked; contact school administration.</p>
            ) : (
              <>
                <label htmlFor="pickup-contact">Authorized pickup contact</label>
                <select id="pickup-contact" value={pickup.contactId}
                  onChange={(e) => setPickup((old) => ({ ...old, contactId: e.target.value, verified: false }))}>
                  <option value="">Select a contact</option>
                  {pickup.contacts.map((contact) => (
                    <option key={contact.id} value={contact.id}>{contact.name} — {contact.relationship || "Authorized contact"}</option>
                  ))}
                </select>
                <label style={{ display: "block", marginTop: 12 }}>
                  <input type="checkbox" checked={pickup.verified}
                    disabled={!pickup.contactId}
                    onChange={(e) => setPickup((old) => ({ ...old, verified: e.target.checked }))} />
                  I have checked this person's identity against the selected authorized pickup record.
                </label>
                <button type="button" onClick={handleCheckout}
                  disabled={pickupBusy || !pickup.contactId || !pickup.verified}>Confirm Checkout</button>
              </>
            )}
            <button type="button" style={{ marginLeft: 12 }} disabled={pickupBusy} onClick={() => setPickup(null)}>Cancel</button>
          </div>
        )}
      </DashboardSection>
    </CrownLayout>
  );
}
