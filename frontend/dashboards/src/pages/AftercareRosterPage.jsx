import { useEffect, useRef, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import DashboardSection from "../components/layout/DashboardSection.jsx";
import { CareHandoffDialog, CarePickupDialog } from "../components/care/CareCustodyDialogs.jsx";
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
  const [checkinBusyId, setCheckinBusyId] = useState(null);
  const checkinInFlightRef = useRef(false);
  const sessionRef = useRef(careSession);

  async function load() {
    if (sessionRef.current !== careSession) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRosterToday(careSession);
      if (sessionRef.current !== careSession) return;
      if (data?.care_session !== careSession || !Array.isArray(data?.rows)) {
        throw new Error("Roster API returned an invalid care session.");
      }
      setRoster(data);
    } catch (e) {
      if (sessionRef.current === careSession) setError(e.message);
    } finally {
      if (sessionRef.current === careSession) setLoading(false);
    }
  }

  useEffect(() => {
    sessionRef.current = careSession;
    setLoading(true);
    setRoster(null);
    setError(null);
    setPickup(null);
    setHandoff(null);
    setPickupBusy(false);
    setHandoffBusy(false);
    setCheckinBusyId(null);
    checkinInFlightRef.current = false;
    let cancelled = false;

    async function initialize() {
      try {
        const data = await fetchRosterToday(careSession);
        if (data?.care_session !== careSession || !Array.isArray(data?.rows)) {
          throw new Error("Roster API returned an invalid care session.");
        }
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
    if (checkinInFlightRef.current || sessionRef.current !== careSession) return;
    checkinInFlightRef.current = true;
    setCheckinBusyId(studentId);
    setError(null);
    try {
      await checkinStudent({ student_id: studentId, care_session: careSession });
      await load();
    } catch (e) {
      if (sessionRef.current === careSession) setError(`Check-in failed: ${e.message}`);
    } finally {
      if (sessionRef.current === careSession) {
        checkinInFlightRef.current = false;
        setCheckinBusyId(null);
      }
    }
  }

  async function beginCheckout(studentId) {
    if (sessionRef.current !== careSession || isMorning) return;
    setPickupBusy(true);
    setError(null);
    try {
      const contacts = await fetchPickupContacts(studentId);
      if (sessionRef.current !== careSession) return;
      setPickup({ studentId, careSession, contacts: Array.isArray(contacts) ? contacts.filter((c) => c.is_active) : [],
                  contactId: "", verified: false });
    } catch (e) {
      if (sessionRef.current === careSession) setError(`Cannot load authorized pickup contacts: ${e.message}`);
    } finally {
      if (sessionRef.current === careSession) setPickupBusy(false);
    }
  }

  async function handleCheckout() {
    if (isMorning || pickup?.careSession !== careSession || !pickup?.contactId || !pickup.verified) return;
    setPickupBusy(true);
    try {
      await checkoutStudent({
        student_id: pickup.studentId,
        pickup_contact_id: pickup.contactId,
        pickup_verified: true,
        care_session: careSession,
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
    if (!isMorning || handoff?.careSession !== careSession || !handoff?.acknowledged) return;
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

  // A care-session switch must never temporarily display the previous session's children.
  const currentRoster = roster?.care_session === careSession ? roster : null;
  const rosterTitle = currentRoster
    ? "Today's " + sessionLabel + " Roster - " + currentRoster.date + " (" + currentRoster.dow + ")"
    : "Today's " + sessionLabel + " Roster";
  const childName = (studentId) => currentRoster?.rows.find((row) => row.student_id === studentId)?.student_name || studentId || "";

  return (
    <CrownLayout title={sessionLabel + " Roster"}>
      <DashboardSection title={rosterTitle}>
        {(loading || (!currentRoster && !error)) && <span>Loading...</span>}
        {error && <div role="alert" style={{ color: "var(--crown-danger)", background: "var(--crown-danger-bg)", padding: "10px 14px", borderRadius: 4, marginBottom: 12 }}>{error}</div>}
        {!loading && !error && currentRoster && (
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
                {currentRoster.rows.length === 0 && (
                  <tr>
                    <td colSpan={6} style={{ ...TD, color: "var(--crown-muted)" }}>No students scheduled today.</td>
                  </tr>
                )}
                {currentRoster.rows.map((row) => {
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
                      <td style={TD}>
                        {row.student_name || row.student_id}
                        {row.unscheduled && <div role="alert">Not on an active care schedule; review this custody record.</div>}
                      </td>
                      <td style={TD}>{row.enrollment?.billing_model}</td>
                      <td style={TD}>{statusChip}</td>
                      <td style={TD}>{row.attendance?.late_minutes ?? "-"}</td>
                      <td style={TD}>
                        {row.attendance?.late_fee_cents
                          ? `$${(row.attendance.late_fee_cents / 100).toFixed(2)}`
                          : "-"}
                      </td>
                      <td style={TD}>
                        {!hasCheckin && !row.unscheduled && (
                          <button type="button" style={BTN_OUT} disabled={Boolean(checkinBusyId) || loading} onClick={() => handleCheckin(row.student_id)}>{checkinBusyId === row.student_id ? "Checking In..." : "Check In"}</button>
                        )}
                        {hasCheckin && !hasCheckout && !isMorning && (
                          <button style={BTN_PRIM} onClick={() => beginCheckout(row.student_id)} disabled={pickupBusy}>Verify Pickup</button>
                        )}
                        {hasCheckin && !hasCheckout && isMorning && (
                          <button style={BTN_PRIM} onClick={() => setHandoff({ studentId: row.student_id, careSession, acknowledged: false })} disabled={handoffBusy}>Acknowledge School Handoff</button>
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
        {currentRoster?.unlinked_attendance_count > 0 && (
          <p role="alert">{currentRoster.unlinked_attendance_count} attendance record(s) cannot be linked to a verified student in this school. Escalate for manual custody reconciliation; identities from other schools are not displayed.</p>
        )}
        <CareHandoffDialog
          open={Boolean(handoff && isMorning && currentRoster && handoff.careSession === careSession)}
          studentName={childName(handoff?.studentId)}
          acknowledged={Boolean(handoff?.acknowledged)}
          busy={handoffBusy}
          onAcknowledge={(acknowledged) => setHandoff((previous) => previous ? { ...previous, acknowledged } : null)}
          onConfirm={handleHandoff}
          onCancel={() => setHandoff(null)}
        />
        <CarePickupDialog
          open={Boolean(pickup && !isMorning && currentRoster && pickup.careSession === careSession)}
          studentName={childName(pickup?.studentId)}
          contacts={pickup?.contacts || []}
          selectedContactId={pickup?.contactId || ""}
          verified={Boolean(pickup?.verified)}
          busy={pickupBusy}
          onSelectContact={(contactId) => setPickup((previous) => previous ? { ...previous, contactId, verified: false } : null)}
          onVerify={(verified) => setPickup((previous) => previous ? { ...previous, verified } : null)}
          onConfirm={handleCheckout}
          onCancel={() => setPickup(null)}
        />
      </DashboardSection>
    </CrownLayout>
  );
}
