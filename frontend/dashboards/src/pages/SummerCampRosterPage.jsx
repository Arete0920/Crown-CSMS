import { useEffect, useMemo, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import DashboardSection from "../components/layout/DashboardSection.jsx";
import {
  checkoutSummerCamper,
  checkinSummerCamper,
  fetchSummerCampRosterToday,
  fetchSummerCampSessions,
  fetchSummerCampSessionRoster,
} from "../api/summerCampApi.js";

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

export default function SummerCampRosterPage() {
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState("");
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function loadInitial() {
      try {
        const sessionData = await fetchSummerCampSessions();
        if (cancelled) return;
        setSessions(sessionData.results || []);
        if ((sessionData.results || []).length > 0) {
          setSelectedSession(String(sessionData.results[0].id));
        } else {
          const today = await fetchSummerCampRosterToday();
          if (!cancelled) setRows(today.results || []);
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
    if (!selectedSession) return;
    let cancelled = false;

    async function loadSessionRoster() {
      setLoading(true);
      try {
        const roster = await fetchSummerCampSessionRoster(selectedSession);
        if (!cancelled) {
          setRows(roster.results || []);
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

  async function onCheckin(studentId) {
    await checkinSummerCamper({
      session_id: selectedSessionId,
      student_id: studentId,
      method: "STAFF",
    });
    const roster = await fetchSummerCampSessionRoster(selectedSessionId);
    setRows(roster.results || []);
  }

  async function onCheckout(studentId) {
    await checkoutSummerCamper({
      session_id: selectedSessionId,
      student_id: studentId,
      method: "STAFF",
    });
    const roster = await fetchSummerCampSessionRoster(selectedSessionId);
    setRows(roster.results || []);
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
                <th style={thtdStyle}>Status</th>
                <th style={thtdStyle}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.student_id}>
                  <td style={thtdStyle}>{row.student_name}</td>
                  <td style={thtdStyle}>{row.readiness_state}</td>
                  <td style={thtdStyle}>{row.attendance_status}</td>
                  <td style={thtdStyle}>
                    <button type="button" onClick={() => onCheckin(row.student_id)} style={{ marginRight: 8 }}>
                      Check in
                    </button>
                    <button type="button" onClick={() => onCheckout(row.student_id)}>
                      Check out
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </DashboardSection>
    </CrownLayout>
  );
}
