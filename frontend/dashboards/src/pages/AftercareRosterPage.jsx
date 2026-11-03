import { useEffect, useRef, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import DashboardSection from "../components/layout/DashboardSection.jsx";
import { CareHandoffDialog, CarePickupDialog } from "../components/care/CareCustodyDialogs.jsx";
import { fetchRosterToday, checkinStudent, checkoutStudent, fetchPickupContacts, handoffToSchool } from "../api/aftercareApi.js";
import {
  getAccessToken, getSelectedSchoolId, SCHOOL_CONTEXT_CHANGE_EVENT,
} from "../utils/authClient.js";

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
  const [rosterScope, setRosterScope] = useState(null);
  const [identity, setIdentity] = useState(() => ({
    school: getSelectedSchoolId(), token: getAccessToken(),
  }));
  const identityRef = useRef(identity);
  const sameIdentity = (scope = identity) => Boolean(scope.school && scope.token)
    && scope.school === getSelectedSchoolId() && scope.token === getAccessToken();
  const [pickup, setPickup] = useState(null);
  const [pickupBusy, setPickupBusy] = useState(false);
  const [checkinBusyId, setCheckinBusyId] = useState(null);
  const [custodyWarning, setCustodyWarning] = useState("");
  // A manual custody readback must not outrun an unresolved prior staff write.
  const [custodyWritePending, setCustodyWritePending] = useState(false);
  // Keep the request marker outside render state: a remote custody write may
  // finish even if its originating staff session changes before response.
  const operationInFlightRef = useRef(null);
  const checkinInFlightRef = useRef(false);
  const sessionRef = useRef(careSession);

  // Existing authentication transport notifies on school changes; the
  // auth-token change event is also supported once its producer is installed.
  // Focus/storage catch external identity changes without granting access.
  useEffect(() => {
    const reconcileIdentity = () => {
      const next = { school: getSelectedSchoolId(), token: getAccessToken() };
      const current = identityRef.current;
      if (current.school === next.school && current.token === next.token) return;
      if (operationInFlightRef.current) {
        setCustodyWarning(
          "A care operation was in flight when the staff session changed. Its outcome is unconfirmed. Review the refreshed live custody roster before any further handoff or check-in; do not retry automatically."
        );
      }
      identityRef.current = next;
      setIdentity(next);
      setRoster(null);
      setRosterScope(null);
      setPickup(null);
      setHandoff(null);
      setError(null);
      setCheckinBusyId(null);
    };
    for (const name of [SCHOOL_CONTEXT_CHANGE_EVENT, "crown:auth-context-changed", "focus", "storage"]) {
      window.addEventListener(name, reconcileIdentity);
    }
    return () => {
      for (const name of [SCHOOL_CONTEXT_CHANGE_EVENT, "crown:auth-context-changed", "focus", "storage"]) {
        window.removeEventListener(name, reconcileIdentity);
      }
    };
  }, []);

  async function load() {
    const scope = identity;
    if (sessionRef.current !== careSession || !sameIdentity(scope)) return;
    setLoading(true);
    setError(null);
    setRoster(null);
    setRosterScope(null);
    try {
      const data = await fetchRosterToday(careSession);
      if (sessionRef.current !== careSession || !sameIdentity(scope)) return;
      if (data?.care_session !== careSession || !Array.isArray(data?.rows)) {
        throw new Error("Roster API returned an invalid care session.");
      }
      setRosterScope(scope);
      setRoster(data);
    } catch (e) {
      if (sessionRef.current === careSession && sameIdentity(scope)) setError(e.message);
    } finally {
      if (sessionRef.current === careSession && sameIdentity(scope)) setLoading(false);
    }
  }

  useEffect(() => {
    sessionRef.current = careSession;
    const scope = identity;
    setLoading(true);
    setRoster(null);
    setRosterScope(null);
    setError(null);
    setPickup(null);
    setHandoff(null);
    setPickupBusy(false);
    setHandoffBusy(false);
    setCheckinBusyId(null);
    checkinInFlightRef.current = false;
    let cancelled = false;
    if (!sameIdentity(scope)) {
      setError("Authenticated school and staff session required before opening care records.");
      setLoading(false);
      return () => { cancelled = true; };
    }

    async function initialize() {
      try {
        const data = await fetchRosterToday(careSession);
        if (data?.care_session !== careSession || !Array.isArray(data?.rows)) {
          throw new Error("Roster API returned an invalid care session.");
        }
        if (!cancelled && sameIdentity(scope)) {
          setRosterScope(scope);
          setRoster(data);
          setError(null);
        }
      } catch (e) {
        if (!cancelled && sameIdentity(scope)) {
          setError(e.message);
        }
      } finally {
        if (!cancelled && sameIdentity(scope)) {
          setLoading(false);
        }
      }
    }

    void initialize();
    return () => {
      cancelled = true;
    };
  }, [careSession, identity]);

  async function handleCheckin(studentId) {
    if (custodyWarning || operationInFlightRef.current || checkinInFlightRef.current || sessionRef.current !== careSession || !sameIdentity() || rosterScope !== identity) return;
    const attempt = { operation: "checkin", identity };
    operationInFlightRef.current = attempt;
    setCustodyWritePending(true);
    checkinInFlightRef.current = true;
    setCheckinBusyId(studentId);
    setError(null);
    try {
      await checkinStudent({ student_id: studentId, care_session: careSession });
      await load();
    } catch (e) {
      if (sessionRef.current === careSession && sameIdentity()) setError(`Check-in failed: ${e.message}`);
    } finally {
      if (operationInFlightRef.current === attempt) {
        operationInFlightRef.current = null;
        setCustodyWritePending(false);
      }
      if (sessionRef.current === careSession && sameIdentity()) {
        checkinInFlightRef.current = false;
        setCheckinBusyId(null);
      }
    }
  }

  async function beginCheckout(studentId) {
    if (custodyWarning || operationInFlightRef.current || sessionRef.current !== careSession || isMorning || !sameIdentity() || rosterScope !== identity) return;
    setPickupBusy(true);
    setError(null);
    try {
      const contacts = await fetchPickupContacts(studentId);
      if (sessionRef.current !== careSession || !sameIdentity()) return;
      setPickup({ studentId, careSession, contacts: Array.isArray(contacts) ? contacts.filter((c) => c.is_active) : [],
                  contactId: "", verified: false });
    } catch (e) {
      if (sessionRef.current === careSession && sameIdentity()) setError(`Cannot load authorized pickup contacts: ${e.message}`);
    } finally {
      if (sessionRef.current === careSession && sameIdentity()) setPickupBusy(false);
    }
  }

  async function handleCheckout() {
    if (custodyWarning || operationInFlightRef.current || isMorning || pickup?.careSession !== careSession || !pickup?.contactId || !pickup.verified
        || !sameIdentity() || rosterScope !== identity) return;
    const attempt = { operation: "checkout", identity };
    operationInFlightRef.current = attempt;
    setCustodyWritePending(true);
    setPickupBusy(true);
    try {
      await checkoutStudent({
        student_id: pickup.studentId,
        pickup_contact_id: pickup.contactId,
        pickup_verified: true,
        care_session: careSession,
      });
      if (sameIdentity()) {
        setPickup(null);
        await load();
      }
    } catch (e) {
      if (sameIdentity()) setError(`Check-out failed: ${e.message}`);
    } finally {
      if (operationInFlightRef.current === attempt) {
        operationInFlightRef.current = null;
        setCustodyWritePending(false);
      }
      if (sameIdentity()) setPickupBusy(false);
    }
  }

  async function handleHandoff() {
    if (custodyWarning || operationInFlightRef.current || !isMorning || handoff?.careSession !== careSession || !handoff?.acknowledged
        || !sameIdentity() || rosterScope !== identity) return;
    const attempt = { operation: "school_handoff", identity };
    operationInFlightRef.current = attempt;
    setCustodyWritePending(true);
    setHandoffBusy(true);
    setError(null);
    try {
      await handoffToSchool({ student_id: handoff.studentId });
      if (sameIdentity()) {
        setHandoff(null);
        await load();
      }
    } catch (e) {
      if (sameIdentity()) setError("School handoff failed: " + e.message);
    } finally {
      if (operationInFlightRef.current === attempt) {
        operationInFlightRef.current = null;
        setCustodyWritePending(false);
      }
      if (sameIdentity()) setHandoffBusy(false);
    }
  }

  // This is an explicit human-triggered reconcile, not an automatic retry.
  // Reading the current roster cannot itself certify who received the child.
  async function reconcileAfterIdentityChange() {
    const scope = identity;
    if (!custodyWarning || operationInFlightRef.current || !sameIdentity(scope) || loading) return;
    setLoading(true);
    try {
      const fresh = await fetchRosterToday(careSession);
      if (!sameIdentity(scope) || sessionRef.current !== careSession) return;
      if (fresh?.care_session !== careSession || !Array.isArray(fresh.rows)) {
        throw new Error("Invalid care roster from the server.");
      }
      setRosterScope(scope);
      setRoster(fresh);
      setError(null);
      setCustodyWarning("");
    } catch (error) {
      if (sameIdentity(scope)) {
        setError("Custody reconciliation failed: " + error.message);
      }
    } finally {
      if (sameIdentity(scope)) setLoading(false);
    }
  }

  // A care-session switch must never temporarily display the previous session's children.
  const currentRoster = sameIdentity() && rosterScope === identity && roster?.care_session === careSession
    ? roster : null;
  const rosterTitle = currentRoster
    ? "Today's " + sessionLabel + " Roster - " + currentRoster.date + " (" + currentRoster.dow + ")"
    : "Today's " + sessionLabel + " Roster";
  const childName = (studentId) => currentRoster?.rows.find((row) => row.student_id === studentId)?.student_name || studentId || "";

  return (
    <CrownLayout title={sessionLabel + " Roster"}>
      <DashboardSection title={rosterTitle}>
        {custodyWarning && <div role="alert">
          <p>{custodyWarning}</p>
          {custodyWritePending && <p role="status">The previous custody write is still pending; do not reconcile from an earlier roster snapshot.</p>}
          <button type="button" disabled={loading || custodyWritePending || !sameIdentity()}
            onClick={reconcileAfterIdentityChange}>Review current custody before continuing</button>
        </div>}
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
                          <button type="button" style={BTN_OUT} disabled={Boolean(checkinBusyId) || custodyWritePending || loading || Boolean(custodyWarning)} onClick={() => handleCheckin(row.student_id)}>{checkinBusyId === row.student_id ? "Checking In..." : "Check In"}</button>
                        )}
                        {hasCheckin && !hasCheckout && !isMorning && (
                          <button style={BTN_PRIM} onClick={() => beginCheckout(row.student_id)} disabled={pickupBusy || custodyWritePending || Boolean(custodyWarning)}>Verify Pickup</button>
                        )}
                        {hasCheckin && !hasCheckout && isMorning && (
                          <button style={BTN_PRIM} onClick={() => setHandoff({ studentId: row.student_id, careSession, acknowledged: false })} disabled={handoffBusy || custodyWritePending || Boolean(custodyWarning)}>Acknowledge School Handoff</button>
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
