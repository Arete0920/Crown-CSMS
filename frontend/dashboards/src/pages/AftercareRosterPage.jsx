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


const CUSTODY_BARRIER_KEY = "crown.extended-care.unconfirmed-custody";
const CUSTODY_BARRIER_EVENT = "crown:extended-care-custody-changed";
// Fallback retains the barrier within this tab when browser storage is blocked.
// Never persist a staff bearer token or child identity in this marker.
let memoryCustodyBarrier = null;
let custodyMarkerSequence = 0;
const custodyMessage = "A prior custody operation has an unconfirmed outcome. Return to its originating school and care session for explicit reconciliation; do not retry automatically.";

function readCustodyBarrier() {
  try {
    const raw = sessionStorage.getItem(CUSTODY_BARRIER_KEY);
    if (!raw) return null;
    const value = JSON.parse(raw);
    if (value && typeof value.school === "string" && ["AM", "PM"].includes(value.careSession)
      && ["pending", "unconfirmed"].includes(value.status) && typeof value.id === "string") return value;
    // A malformed marker must not silently enable a new custody write.
    return { school: "", careSession: "", status: "pending", id: "invalid" };
  } catch {
    return memoryCustodyBarrier;
  }
}

function updateCustodyBarrier(next) {
  memoryCustodyBarrier = next;
  try {
    if (next) sessionStorage.setItem(CUSTODY_BARRIER_KEY, JSON.stringify(next));
    else sessionStorage.removeItem(CUSTODY_BARRIER_KEY);
  } catch {
    // Preserve the in-memory barrier across same-tab React route unmounts.
  }
  window.dispatchEvent(new Event(CUSTODY_BARRIER_EVENT));
}

function beginCustodyBarrier(identity, careSession) {
  if (readCustodyBarrier()) return null;
  const marker = {
    id: String(++custodyMarkerSequence) + "-" + String(Date.now()),
    school: identity.school,
    careSession,
    status: "pending",
  };
  updateCustodyBarrier(marker);
  return marker;
}

function finalizeCustodyBarrier(marker, confirmed) {
  const current = readCustodyBarrier();
  if (!current || current.id !== marker?.id) return;
  updateCustodyBarrier(confirmed ? null : { ...current, status: "unconfirmed" });
}

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
  // Monotonic scope generation rejects responses from school/token/session ABA switches.
  const scopeEpochRef = useRef(0);
  const sameIdentity = (scope = identity) => Boolean(scope.school && scope.token)
    && scope.school === getSelectedSchoolId() && scope.token === getAccessToken();
  const [pickup, setPickup] = useState(null);
  const [pickupBusy, setPickupBusy] = useState(false);
  const [checkinBusyId, setCheckinBusyId] = useState(null);
  const [custodyWarning, setCustodyWarning] = useState(() => readCustodyBarrier() ? custodyMessage : "");
  const [unconfirmedScope, setUnconfirmedScope] = useState(() => {
    const marker = readCustodyBarrier();
    return marker ? { school: marker.school, careSession: marker.careSession } : null;
  });
  // A manual custody readback must not outrun an unresolved prior staff write.
  const [custodyWritePending, setCustodyWritePending] = useState(() => readCustodyBarrier()?.status === "pending");
  // Keep the request marker outside render state: a remote custody write may
  // finish even if its originating staff session changes before response.
  const operationInFlightRef = useRef(null);
  const checkinInFlightRef = useRef(false);
  const sessionRef = useRef(careSession);
  const mountedRef = useRef(false);

  useEffect(() => {
    mountedRef.current = true;
    const syncBarrier = () => {
      const marker = readCustodyBarrier();
      setUnconfirmedScope(marker ? { school: marker.school, careSession: marker.careSession } : null);
      setCustodyWritePending(marker?.status === "pending");
      // The originating component keeps its own in-flight status. A newly
      // mounted route must immediately display the persisted custody warning.
      if (!operationInFlightRef.current) setCustodyWarning(marker ? custodyMessage : "");
    };
    window.addEventListener(CUSTODY_BARRIER_EVENT, syncBarrier);
    syncBarrier();
    return () => {
      mountedRef.current = false;
      window.removeEventListener(CUSTODY_BARRIER_EVENT, syncBarrier);
    };
  }, []);

  // Existing authentication transport notifies on school changes; the
  // auth-token change event is also supported once its producer is installed.
  // Focus/storage catch external identity changes without granting access.
  useEffect(() => {
    const reconcileIdentity = () => {
      const next = { school: getSelectedSchoolId(), token: getAccessToken() };
      const current = identityRef.current;
      if (current.school === next.school && current.token === next.token) return;
      scopeEpochRef.current += 1;
      if (operationInFlightRef.current) {
        const pending = operationInFlightRef.current;
        setUnconfirmedScope({ school: pending.identity.school, careSession: pending.careSession });
        setCustodyWarning(
          "A care operation was in flight when the staff session changed. Its outcome is unconfirmed. Return to the originating school and care session for explicit custody reconciliation; do not retry automatically."
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
    const epoch = scopeEpochRef.current;
    if (!mountedRef.current || scopeEpochRef.current !== epoch || sessionRef.current !== careSession || !sameIdentity(scope)) return false;
    setLoading(true);
    setError(null);
    setRoster(null);
    setRosterScope(null);
    try {
      const data = await fetchRosterToday(careSession);
      if (!mountedRef.current || scopeEpochRef.current !== epoch || sessionRef.current !== careSession || !sameIdentity(scope)) return false;
      if (data?.care_session !== careSession || !Array.isArray(data?.rows)) {
        throw new Error("Roster API returned an invalid care session.");
      }
      setRosterScope(scope);
      setRoster(data);
      return true;
    } catch (e) {
      if (mountedRef.current && scopeEpochRef.current === epoch && sessionRef.current === careSession && sameIdentity(scope)) setError(e.message);
      return false;
    } finally {
      if (mountedRef.current && scopeEpochRef.current === epoch && sessionRef.current === careSession && sameIdentity(scope)) setLoading(false);
    }
  }

  useEffect(() => {
    const switchedCareSession = sessionRef.current !== careSession;
    if (switchedCareSession) scopeEpochRef.current += 1;
    if (switchedCareSession && operationInFlightRef.current) {
      const pending = operationInFlightRef.current;
      setUnconfirmedScope({ school: pending.identity.school, careSession: pending.careSession });
      setCustodyWarning(
        "A custody operation remained in flight when the care session changed. Its outcome is unconfirmed. Return to the originating school and care session for reconciliation."
      );
    }
    sessionRef.current = careSession;
    const scope = identity;
    const epoch = scopeEpochRef.current;
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
        if (!cancelled && scopeEpochRef.current === epoch && sameIdentity(scope)) {
          setRosterScope(scope);
          setRoster(data);
          setError(null);
        }
      } catch (e) {
        if (!cancelled && scopeEpochRef.current === epoch && sameIdentity(scope)) {
          setError(e.message);
        }
      } finally {
        if (!cancelled && scopeEpochRef.current === epoch && sameIdentity(scope)) {
          setLoading(false);
        }
      }
    }

    void initialize();
    return () => {
      cancelled = true;
    };
  }, [careSession, identity]);

  // Rejected writes may have committed remotely before a timeout or connection loss.
  // Never expose a retry until a new, explicitly requested authorized roster read.
  function requireCustodyReadback(attempt) {
    setUnconfirmedScope({ school: attempt.identity.school, careSession: attempt.careSession });
    setCustodyWarning(
      "A custody write did not return a confirmed result. Its outcome is unconfirmed. " +
      "Return to the originating school and care session for explicit custody reconciliation; do not retry automatically."
    );
    setPickup(null);
    setHandoff(null);
    finalizeCustodyBarrier(attempt.marker, false);
  }

  async function handleCheckin(studentId) {
    if (custodyWarning || readCustodyBarrier() || operationInFlightRef.current || checkinInFlightRef.current || sessionRef.current !== careSession || !sameIdentity() || rosterScope !== identity) return;
    const marker = beginCustodyBarrier(identity, careSession);
    if (!marker) return;
    const attempt = { operation: "checkin", identity, careSession, epoch: scopeEpochRef.current, marker };
    operationInFlightRef.current = attempt;
    setCustodyWritePending(true);
    checkinInFlightRef.current = true;
    setCheckinBusyId(studentId);
    setError(null);
    try {
      await checkinStudent({ student_id: studentId, care_session: careSession });
      const confirmed = mountedRef.current && scopeEpochRef.current === attempt.epoch && await load();
      if (confirmed) finalizeCustodyBarrier(marker, true);
      else requireCustodyReadback(attempt);
    } catch (e) {
      requireCustodyReadback(attempt);
      if (sessionRef.current === careSession && sameIdentity()) setError(`Check-in failed: ${e.message}`);
    } finally {
      if (operationInFlightRef.current === attempt) {
        operationInFlightRef.current = null;
        checkinInFlightRef.current = false;
        setCustodyWritePending(false);
      }
      if (sessionRef.current === careSession && sameIdentity()) {
        setCheckinBusyId(null);
      }
    }
  }

  async function beginCheckout(studentId) {
    if (custodyWarning || readCustodyBarrier() || operationInFlightRef.current || sessionRef.current !== careSession || isMorning || !sameIdentity() || rosterScope !== identity) return;
    const epoch = scopeEpochRef.current;
    setPickupBusy(true);
    setError(null);
    try {
      const contacts = await fetchPickupContacts(studentId);
      if (scopeEpochRef.current !== epoch || sessionRef.current !== careSession || !sameIdentity()) return;
      setPickup({ studentId, careSession, contacts: Array.isArray(contacts) ? contacts.filter((c) => c.is_active) : [],
                  contactId: "", verified: false });
    } catch (e) {
      if (scopeEpochRef.current === epoch && sessionRef.current === careSession && sameIdentity()) setError(`Cannot load authorized pickup contacts: ${e.message}`);
    } finally {
      if (scopeEpochRef.current === epoch && sessionRef.current === careSession && sameIdentity()) setPickupBusy(false);
    }
  }

  async function handleCheckout() {
    if (custodyWarning || readCustodyBarrier() || operationInFlightRef.current || isMorning || pickup?.careSession !== careSession || !pickup?.contactId || !pickup.verified
        || !sameIdentity() || rosterScope !== identity) return;
    const marker = beginCustodyBarrier(identity, careSession);
    if (!marker) return;
    const attempt = { operation: "checkout", identity, careSession, epoch: scopeEpochRef.current, marker };
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
      if (scopeEpochRef.current === attempt.epoch && sessionRef.current === careSession && sameIdentity()) {
        setPickup(null);
        if (mountedRef.current && await load()) finalizeCustodyBarrier(marker, true);
        else requireCustodyReadback(attempt);
      } else requireCustodyReadback(attempt);
    } catch (e) {
      requireCustodyReadback(attempt);
      if (scopeEpochRef.current === attempt.epoch && sessionRef.current === careSession && sameIdentity()) setError(`Check-out failed: ${e.message}`);
    } finally {
      if (operationInFlightRef.current === attempt) {
        operationInFlightRef.current = null;
        setCustodyWritePending(false);
      }
      if (scopeEpochRef.current === attempt.epoch && sessionRef.current === careSession && sameIdentity()) setPickupBusy(false);
    }
  }

  async function handleHandoff() {
    if (custodyWarning || readCustodyBarrier() || operationInFlightRef.current || !isMorning || handoff?.careSession !== careSession || !handoff?.acknowledged
        || !sameIdentity() || rosterScope !== identity) return;
    const marker = beginCustodyBarrier(identity, careSession);
    if (!marker) return;
    const attempt = { operation: "school_handoff", identity, careSession, epoch: scopeEpochRef.current, marker };
    operationInFlightRef.current = attempt;
    setCustodyWritePending(true);
    setHandoffBusy(true);
    setError(null);
    try {
      await handoffToSchool({ student_id: handoff.studentId });
      if (scopeEpochRef.current === attempt.epoch && sessionRef.current === careSession && sameIdentity()) {
        setHandoff(null);
        if (mountedRef.current && await load()) finalizeCustodyBarrier(marker, true);
        else requireCustodyReadback(attempt);
      } else requireCustodyReadback(attempt);
    } catch (e) {
      requireCustodyReadback(attempt);
      if (scopeEpochRef.current === attempt.epoch && sessionRef.current === careSession && sameIdentity()) setError("School handoff failed: " + e.message);
    } finally {
      if (operationInFlightRef.current === attempt) {
        operationInFlightRef.current = null;
        setCustodyWritePending(false);
      }
      if (scopeEpochRef.current === attempt.epoch && sessionRef.current === careSession && sameIdentity()) setHandoffBusy(false);
    }
  }

  // Only the originating school's matching care-session read can resolve a write.
  const affectedScopeMatches = !unconfirmedScope || (
    unconfirmedScope.school === identity.school && unconfirmedScope.careSession === careSession
  );
  // This is an explicit human-triggered reconcile, not an automatic retry.
  // Reading the current roster cannot itself certify who received the child.
  async function reconcileAfterIdentityChange() {
    const scope = identity;
    const epoch = scopeEpochRef.current;
    if (!custodyWarning || !affectedScopeMatches || operationInFlightRef.current || readCustodyBarrier()?.status === "pending" || !sameIdentity(scope) || loading) return;
    setLoading(true);
    try {
      const fresh = await fetchRosterToday(careSession);
      if (scopeEpochRef.current !== epoch || !sameIdentity(scope) || sessionRef.current !== careSession) return;
      if (fresh?.care_session !== careSession || !Array.isArray(fresh.rows)) {
        throw new Error("Invalid care roster from the server.");
      }
      setRosterScope(scope);
      setRoster(fresh);
      setError(null);
      const marker = readCustodyBarrier();
      if (marker && marker.status === "unconfirmed"
        && marker.school === scope.school && marker.careSession === careSession) {
        finalizeCustodyBarrier(marker, true);
      }
      setCustodyWarning("");
      setUnconfirmedScope(null);
    } catch (error) {
      if (scopeEpochRef.current === epoch && sameIdentity(scope)) {
        setError("Custody reconciliation failed: " + error.message);
      }
    } finally {
      if (scopeEpochRef.current === epoch && sameIdentity(scope)) setLoading(false);
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
          {!affectedScopeMatches && <p role="status">Return to the originating school and care session before resolving the unconfirmed custody operation.</p>}
          <button type="button" disabled={loading || custodyWritePending || readCustodyBarrier()?.status === "pending" || !affectedScopeMatches || !sameIdentity()}
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
                          <button type="button" style={BTN_OUT} disabled={Boolean(checkinBusyId) || custodyWritePending || Boolean(readCustodyBarrier()) || loading || Boolean(custodyWarning)} onClick={() => handleCheckin(row.student_id)}>{checkinBusyId === row.student_id ? "Checking In..." : "Check In"}</button>
                        )}
                        {hasCheckin && !hasCheckout && !isMorning && (
                          <button style={BTN_PRIM} onClick={() => beginCheckout(row.student_id)} disabled={pickupBusy || custodyWritePending || Boolean(readCustodyBarrier()) || Boolean(custodyWarning)}>Verify Pickup</button>
                        )}
                        {hasCheckin && !hasCheckout && isMorning && (
                          <button style={BTN_PRIM} onClick={() => setHandoff({ studentId: row.student_id, careSession, acknowledged: false })} disabled={handoffBusy || custodyWritePending || Boolean(readCustodyBarrier()) || Boolean(custodyWarning)}>Acknowledge School Handoff</button>
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
