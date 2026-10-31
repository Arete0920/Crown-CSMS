import { useEffect, useMemo, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import DashboardSection from "../components/layout/DashboardSection.jsx";
import {
  checkinSummerCamper,
  checkoutSummerCamper,
  fetchCampPickupChoices,
  fetchSummerCampRosterToday,
  fetchSummerCampSessions,
  fetchSummerCampSessionRoster,
} from "../api/summerCampApi.js";

import { campSessions, campRoster, campToday, currentCampCustody, campCanCheckIn, campCanVerifyPickup, campCustodyLabel, campPickupContacts, duplicateCampRegistration } from "./summerCampRosterState.js";

const tableStyle = {
  width: "100%",
  borderCollapse: "collapse",
  border: "1px solid var(--crown-border)",
};

const thtdStyle = {
  borderBottom: "1px solid var(--crown-border)",
  padding: "8px 10px",
  textAlign: "left",
};


function requireCampRows(payload) {
  if (!payload || !Array.isArray(payload.rows)) {
    throw new Error("Unexpected Camp roster response");
  }
  return payload.rows;
}

export default function SummerCampRosterPage() {
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState("");
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [today, setToday] = useState(null);
  const [pickup, setPickup] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadInitial() {
      try {
        const sessionData = await fetchSummerCampSessions();
        if (cancelled) return;
        setSessions(campSessions(sessionData));
        if (sessionData.length > 0) {
          setSelectedSession(String(sessionData[0].id));
        } else {
          const today = await fetchSummerCampRosterToday();
          if (!cancelled) setRows(requireCampRows(today));
        }
      } catch (e) {
        if (!cancelled) setError(e.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadInitial();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    setPickup(null);
    setToday(null);
    if (!selectedSession) return;
    let cancelled = false;

    async function loadSessionRoster() {
      setLoading(true);
      try {
        const [roster, custody] = await Promise.all([fetchSummerCampSessionRoster(selectedSession), fetchSummerCampRosterToday()]);
        if (!cancelled) {
          setRows(campRoster(roster, selectedSession));
          setToday(campToday(custody));
          setError(null);
        }
      } catch (e) {
        if (!cancelled) setError(e.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadSessionRoster();
    return () => {
      cancelled = true;
    };
  }, [selectedSession]);

  const selectedSessionId = useMemo(() => Number(selectedSession), [selectedSession]);

  const selected = sessions.find((session) => String(session.id) === selectedSession);
  async function refresh() {
    const [roster, custody] = await Promise.all([
      fetchSummerCampSessionRoster(selectedSession), fetchSummerCampRosterToday(),
    ]);
    setRows(campRoster(roster, selectedSession));
    setToday(campToday(custody));
  }
  async function checkin(row) {
    if (busy) return;
    setBusy(true);
    try {
      await checkinSummerCamper({ session_id: Number(selectedSession), student_id: row.student_id });
      await refresh();
      setError(null);
    } catch (e) { setError("Check-in outcome must be verified before retrying: " + e.message); }
    finally { setBusy(false); }
  }
  async function beginPickup(row) {
    if (busy) return;
    setBusy(true);
    try {
      const result = await fetchCampPickupChoices(row.enrollment_id);
      setPickup({ sessionId: selectedSession, studentId: row.student_id,
        contacts: campPickupContacts(result, row.enrollment_id), contactId: "", verified: false });
      setError(null);
    } catch (e) { setError("Pickup authorization unavailable: " + e.message); }
    finally { setBusy(false); }
  }
  async function release() {
    if (!pickup || !pickup.verified || busy || pickup.sessionId !== selectedSession) return;
    const id = Number(pickup.contactId);
    if (!Number.isSafeInteger(id) || !pickup.contacts.some((contact) => contact.id === id)) return;
    setBusy(true);
    try {
      await checkoutSummerCamper({ session_id: Number(selectedSession),
        student_id: pickup.studentId, pickup_contact_id: id, pickup_verified: true });
      setPickup(null);
      await refresh();
      setError(null);
    } catch (e) {
      setPickup(null);
      setError("Checkout outcome requires manual reconciliation before retry: " + e.message);
    } finally { setBusy(false); }
  }

  return (
    <CrownLayout title="Summer Camp Roster">
      <DashboardSection title="Session Roster">
        <div style={{ marginBottom: 12 }}>
          <label htmlFor="summer-camp-session-select" style={{ marginRight: 8 }}>Session:</label>
          <select
            id="summer-camp-session-select"
            value={selectedSession}
            onChange={(event) => setSelectedSession(event.target.value)}
          >
            {sessions.map((session) => (
              <option key={session.id} value={session.id}>
                {session.name}
              </option>
            ))}
          </select>
        </div>

        {loading && <span>Loading roster...</span>}
        {error && (
          <div style={{ color: "var(--crown-danger)", background: "var(--crown-danger-bg)", padding: "10px 14px", borderRadius: 4 }}>
            {error}
          </div>
        )}

        {!loading && !error && (
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thtdStyle}>Student</th>
                <th style={thtdStyle}>Readiness</th>
                <th style={thtdStyle}>Registration</th>
                <th style={thtdStyle}>Custody</th>
                <th style={thtdStyle}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => { const custody = currentCampCustody(row, today, selectedSession);
                const duplicate = duplicateCampRegistration(row, rows);
                return (
                <tr key={row.enrollment_id}>
                  <td style={thtdStyle}>{row.student_name}</td>
                  <td style={thtdStyle}>{row.readiness_status || "Not available"}</td>
                  <td style={thtdStyle}>{row.status || "Not available"}</td>
                  <td style={thtdStyle}>{campCustodyLabel(custody)}</td>
                  <td style={thtdStyle}>
                    <button type="button" disabled={busy || !campCanCheckIn(row, custody, selected, today?.date, duplicate)} onClick={() => checkin(row)} style={{ marginRight: 8 }}>
                      Check in
                    </button>
                    <button type="button" disabled={busy || !campCanVerifyPickup(row, custody, duplicate)} onClick={() => beginPickup(row)}>Verify pickup</button>
                  </td>
                </tr>
              ); })}
            </tbody>
          </table>
        )}
        {pickup && pickup.sessionId === selectedSession && (
          <div role="dialog" aria-modal="true" aria-label="Verify Camp pickup">
            <p>Match the person to the current authorized pickup record before releasing the child.</p>
            {pickup.contacts.length === 0 && <p role="alert">No active authorized pickup contact; release blocked.</p>}
            <label htmlFor="camp-authorized-contact">Authorized person</label>
            <select id="camp-authorized-contact" disabled={busy} value={pickup.contactId} onChange={(event) => setPickup((old) => ({ ...old, contactId: event.target.value, verified: false }))}>
              <option value="">Select a person</option>
              {pickup.contacts.map((contact) => <option key={contact.id} value={contact.id}>{contact.name} ({contact.relationship})</option>)}
            </select>
            <label><input type="checkbox" disabled={busy || !pickup.contactId} checked={pickup.verified} onChange={(event) => setPickup((old) => ({ ...old, verified: event.target.checked }))} /> I personally verified this pickup identity.</label>
            <button type="button" disabled={busy || !pickup.verified || !pickup.contactId} onClick={release}>Record verified release</button>
            <button type="button" disabled={busy} onClick={() => setPickup(null)}>Cancel</button>
          </div>
        )}
      </DashboardSection>
    </CrownLayout>
  );
}
