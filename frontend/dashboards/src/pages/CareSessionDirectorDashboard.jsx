import { useEffect, useState } from "react";
import { Link } from "react-router";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import DashboardSection from "../components/layout/DashboardSection.jsx";
import { fetchRosterToday, getAftercareBoardSummary } from "../api/aftercareApi.js";
import { PATHS } from "../routes/paths.js";

const PANEL = { border: "1px solid var(--crown-border)", borderRadius: 8, padding: 16 };
const GRID = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12 };
const MONEY = (cents) => "$" + (cents / 100).toFixed(2);

export function deriveSessionTotals(rows, careSession) {
  const scheduled = Array.isArray(rows) ? rows : [];
  const checkedIn = scheduled.filter((r) => Boolean(r.attendance?.checkin_time));
  const expected = scheduled.filter((r) => !r.unscheduled);
  const unscheduledAttendance = checkedIn.filter((r) => r.unscheduled).length;
  const present = checkedIn.filter((r) => !r.attendance?.checkout_time);
  const verifiedClosure = (r) => careSession === "AM"
    ? Boolean(r.attendance?.checkout_time && r.attendance?.handoff_verified && r.attendance?.handoff_time)
    : Boolean(r.attendance?.checkout_time && r.attendance?.pickup_verified);
  const completed = checkedIn.filter(verifiedClosure);
  // A recorded checkout without proof of transfer is neither supervised nor released.
  const unverifiedClosures = checkedIn.filter((r) => r.attendance?.checkout_time && !verifiedClosure(r));
  const late = careSession === "PM"
    ? checkedIn.filter((r) => Number(r.attendance?.late_minutes || 0) > 0) : [];
  const lateFeeCents = careSession === "PM"
    ? checkedIn.reduce((sum, r) => sum + Number(r.attendance?.late_fee_cents || 0), 0) : 0;
  return {
    expected: expected.length, checkedIn: checkedIn.length,
    present: present.length, completed: completed.length,
    unverifiedClosures: unverifiedClosures.length, unscheduledAttendance,
    awaitingArrival: expected.filter((r) => !r.attendance?.checkin_time).length,
    latePickups: late.length, lateFeeCents,
  };
}

export default function CareSessionDirectorDashboard({ careSession = "PM" }) {
  const morning = careSession === "AM";
  const title = morning ? "Before Care" : "After Care";
  const rosterPath = morning ? PATHS.BEFORECARE_ROSTER : PATHS.AFTERCARE_ROSTER;
  const otherPath = morning ? PATHS.AFTERCARE_DIRECTOR : PATHS.BEFORECARE_DIRECTOR;
  const [roster, setRoster] = useState(null);
  const [summary, setSummary] = useState(null);
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [observedAt, setObservedAt] = useState(null);
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setRoster(null);
      setSummary(null);
      setErrors([]);
      setObservedAt(null);
      const [rosterResult, summaryResult] = await Promise.allSettled([
        fetchRosterToday(careSession),
        getAftercareBoardSummary({ careSession }),
      ]);
      if (!active) return;
      const problems = [];
      if (rosterResult.status === "fulfilled" && rosterResult.value?.care_session === careSession
          && Array.isArray(rosterResult.value?.rows)) {
        setRoster(rosterResult.value);
      } else {
        problems.push("Daily roster unavailable: " + (
          rosterResult.status === "rejected" ? rosterResult.reason.message : "invalid API response"
        ));
      }
      if (summaryResult.status === "fulfilled" && summaryResult.value?.care_session === careSession) {
        setSummary(summaryResult.value);
      } else {
        problems.push("Monthly summary unavailable: " + (
          summaryResult.status === "rejected" ? summaryResult.reason.message : "invalid API response or session mismatch"
        ));
      }
      setErrors(problems);
      setObservedAt(new Date().toISOString());
      setLoading(false);
    }
    void load();
    return () => { active = false; };
  }, [careSession, refresh]);

  const totals = roster ? deriveSessionTotals(roster.rows, careSession) : null;
  const today = totals ? [
    ["Expected Children", totals.expected],
    ["Checked In Today", totals.checkedIn],
    ["Currently Supervised", totals.present],
    [morning ? "School Handoffs" : "Authorized Checkouts", totals.completed],
    ["Unverified Custody Closures", totals.unverifiedClosures],
    ["Attendance Without Active Schedule", totals.unscheduledAttendance],
    ["Attendance Without Verified Student Link", roster?.unlinked_attendance_count ?? 0],
    ["Awaiting Arrival", totals.awaitingArrival],
    ...(morning ? [] : [
      ["Late Pickup Events", totals.latePickups],
      ["Late Fees Assessed Today", MONEY(totals.lateFeeCents)],
    ]),
  ] : [];
  const mtd = summary ? [
    ["Active Enrollment", summary.active_enrollment],
    ["Attendance Sessions MTD", summary.sessions_mtd],
    ["Incidents MTD", summary.incidents_mtd],
    ...(morning ? [] : [
      ["Late Pickups MTD", summary.late_pickups_mtd],
      ["Late Fees Assessed MTD", typeof summary.late_fee_assessed_mtd === "number"
        ? "$" + summary.late_fee_assessed_mtd.toFixed(2) : "Unavailable"],
    ]),
  ] : [];

  return (
    <CrownLayout title={title + " Director"} subtitle="Live tenant-scoped operational records">
      <p>Session: {careSession}. Source: authenticated care roster and board summary APIs. Request observed at: {observedAt || "Unavailable"}.</p>
      <p>Roster date: {roster?.date || "Unavailable"}. Summary as of: {summary?.as_of || "Unavailable"}.</p>
      <nav aria-label={title + " actions"} style={{ display: "flex", flexWrap: "wrap", gap: 16, marginBottom: 18 }}>
        <Link to={rosterPath}>Open {title} roster and actions</Link>
        <Link to={PATHS.WIZARD_AFTERCARE_SETUP}>Open care configuration</Link>
        <Link to={otherPath}>Switch to {morning ? "After Care" : "Before Care"}</Link>
        <button type="button" disabled={loading} onClick={() => setRefresh((n) => n + 1)}>Refresh live data</button>
      </nav>
      {loading && <p role="status">Loading live care records...</p>}
      {errors.length > 0 && <div role="alert">{errors.map((e) => <p key={e}>{e}</p>)}</div>}
      {!loading && <>
        <DashboardSection title="Today">
          {totals?.unverifiedClosures > 0 && (
            <p role="alert">Custody transfer is unverified for {totals.unverifiedClosures} care session(s). Review the roster and investigate; do not assume the children were handed off or released.</p>
          )}
          {totals?.unscheduledAttendance > 0 && (
            <p role="alert">{totals.unscheduledAttendance} attendance record(s) remain open to review despite missing active schedules. These records must not disappear from the custody roster.</p>
          )}
          {roster?.unlinked_attendance_count > 0 && (
            <p role="alert">{roster.unlinked_attendance_count} historical attendance record(s) lack a verified same-school student link. Escalate for manual identity reconciliation.</p>
          )}
          {totals
            ? <div style={GRID}>{today.map(([label, value]) => <div key={label} style={PANEL}>
                <div>{label}</div><strong style={{ fontSize: 24 }}>{value}</strong>
                <div><Link to={rosterPath}>Inspect underlying roster</Link></div>
              </div>)}</div>
            : <p>Daily metrics unavailable; no sample figures are substituted.</p>}
        </DashboardSection>
        <DashboardSection title="Month-to-date">
          {summary
            ? <div style={GRID}>{mtd.map(([label, value]) => <div key={label} style={PANEL}>
                <div>{label}</div><strong style={{ fontSize: 24 }}>{value ?? "Unavailable"}</strong>
              </div>)}</div>
            : <p>Month-to-date metrics unavailable; no sample figures are substituted.</p>}
        </DashboardSection>
        <DashboardSection title="Not yet supported by a verified live API">
          <p>{morning
            ? "Handoff exceptions, absence classification, staff coverage, supervision ratios, location, capacity, waitlist, health alerts, activities and AM charges."
            : "Missing at school intake, unauthorized pickup exceptions, staff coverage, ratios, location, capacity, waitlist, health alerts, clubs and settled receipts."}</p>
          <p>Scheduled enrollment is not actual attendance. Fees assessed are not payments collected. No childcare compliance certification is implied.</p>
        </DashboardSection>
      </>}
    </CrownLayout>
  );
}
