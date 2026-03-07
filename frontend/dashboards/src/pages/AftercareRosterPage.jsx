import { useEffect, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import DashboardSection from "../components/layout/DashboardSection.jsx";
import { fetchRosterToday, checkinStudent, checkoutStudent } from "../api/aftercareApi.js";

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

const TAG = {
  base: { display: "inline-block", padding: "2px 8px", borderRadius: 12, fontSize: 12, fontWeight: 600 },
  default: { background: "var(--crown-surface-2)", color: "var(--crown-muted)" },
  primary:  { background: "var(--crown-surface-2)", color: "var(--crown-brand)" },
  success:  { background: "var(--crown-ok-bg)", color: "var(--crown-ok)" },
};

function AttendanceChip({ row }) {
  const att = row.attendance;
  if (!att) return <span style={{ ...TAG.base, ...TAG.default }}>Not checked in</span>;
  if (att.checkout_time) return <span style={{ ...TAG.base, ...TAG.success }}>Checked out</span>;
  return <span style={{ ...TAG.base, ...TAG.primary }}>Checked in</span>;
}

const TH = { padding: "8px 12px", textAlign: "left", fontSize: 12, fontWeight: 700, borderBottom: "2px solid var(--crown-border)", whiteSpace: "nowrap" };
const TD = { padding: "8px 12px", fontSize: 13, borderBottom: "1px solid var(--crown-border)" };
const BTN_OUT  = { cursor: "pointer", padding: "4px 10px", fontSize: 12, borderRadius: 4, border: "1px solid var(--crown-border)", background: "transparent" };
const BTN_PRIM = { cursor: "pointer", padding: "4px 10px", fontSize: 12, borderRadius: 4, border: "none", background: "var(--crown-ok)", color: "var(--crown-surface)" };

export default function AftercareRosterPage() {
  const { token, schoolId } = getSession();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [roster, setRoster] = useState(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRosterToday();
      setRoster(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCheckin(studentId) {
    try {
      await checkinStudent({ student_id: studentId });
      await load();
    } catch (e) {
      alert(`Check-in failed: ${e.message}`);
    }
  }

  async function handleCheckout(studentId) {
    try {
      await checkoutStudent({ student_id: studentId, pickup_verified: false });
      await load();
    } catch (e) {
      alert(`Check-out failed: ${e.message}`);
    }
  }

  return (
    <CrownLayout title="Aftercare Roster">
      <DashboardSection title={`Today's Aftercare Roster${roster ? ` — ${roster.date} (${roster.dow})` : ""}`}>
        {loading && <span>Loading…</span>}
        {error && <div style={{ color: "var(--crown-danger)", background: "var(--crown-danger-bg)", padding: "10px 14px", borderRadius: 4, marginBottom: 12 }}>{error}</div>}
        {!loading && !error && roster && (
          <div style={{ border: "1px solid var(--crown-border)", borderRadius: 4, overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={TH}>Student ID</th>
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
                  const hasCheckout = row.attendance?.checkout_time;
                  return (
                    <tr key={row.student_id}>
                      <td style={TD}>{row.student_id}</td>
                      <td style={TD}>{row.enrollment?.billing_model}</td>
                      <td style={TD}><AttendanceChip row={row} /></td>
                      <td style={TD}>{row.attendance?.late_minutes ?? "—"}</td>
                      <td style={TD}>
                        {row.attendance?.late_fee_cents
                          ? `$${(row.attendance.late_fee_cents / 100).toFixed(2)}`
                          : "—"}
                      </td>
                      <td style={TD}>
                        {!hasCheckin && (
                          <button style={BTN_OUT} onClick={() => handleCheckin(row.student_id)}>Check In</button>
                        )}
                        {hasCheckin && !hasCheckout && (
                          <button style={BTN_PRIM} onClick={() => handleCheckout(row.student_id)}>Check Out</button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </DashboardSection>
    </CrownLayout>
  );
}
