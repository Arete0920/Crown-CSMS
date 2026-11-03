import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api.js";
import { createSummerCampEnrollment, fetchSummerCampEnrollments } from "../api/summerCampApi.js";
import { getAccessToken, getSelectedSchoolId, AUTH_CONTEXT_CHANGE_EVENT, SCHOOL_CONTEXT_CHANGE_EVENT } from "../utils/authClient.js";

const SCHOOL = "19801b59-8c05-4c84-9312-5d792e4e839d";
const sameContext = (scope) => scope.school === getSelectedSchoolId() && scope.token === getAccessToken();

export default function SummerCampDemoRegistration({ session, rows, disabled, onSaved }) {
  const [scope] = useState(() => ({ school: getSelectedSchoolId(), token: getAccessToken() }));
  const [students, setStudents] = useState([]);
  const [student, setStudent] = useState("");
  const [busy, setBusy] = useState(false);
  const [locked, setLocked] = useState(false);
  const [message, setMessage] = useState("");
  const allowed = import.meta.env.VITE_LOCAL_DEMO === "1" && scope.school === SCHOOL && Boolean(scope.token)
    && session?.status === "PUBLISHED" && Number(session.price_cents) === 0 && Number(session.deposit_cents) === 0;
  useEffect(() => {
    if (!allowed) return;
    let active = true;
    const invalidate = () => {
      if (sameContext(scope)) return;
      setStudents([]); setStudent(""); setLocked(true);
      setMessage("Staff session changed. Refresh this roster before registering.");
    };
    const events = [AUTH_CONTEXT_CHANGE_EVENT, SCHOOL_CONTEXT_CHANGE_EVENT, "focus", "storage"];
    events.forEach((name) => window.addEventListener(name, invalidate));
    apiFetch("/api/v1/students/").then(async (response) => {
      if (!response.ok) throw new Error("Student list unavailable");
      const data = await response.json();
      const list = Array.isArray(data) ? data : data?.results;
      if (!Array.isArray(list)) throw new Error("Invalid student list");
      if (active && sameContext(scope)) setStudents(list.filter((item) => item.is_active && typeof item.id === "string"));
    }).catch(() => {
      if (active) { setLocked(true); setMessage("Authorized student records are unavailable. Refresh before registering."); }
    });
    return () => { active = false; events.forEach((name) => window.removeEventListener(name, invalidate)); };
  }, [allowed, scope]);

  async function register(event) {
    event.preventDefault();
    if (!allowed || !sameContext(scope) || busy || locked || disabled || !students.some((item) => item.id === student)) return;
    setBusy(true); setMessage("");
    try {
      const saved = await createSummerCampEnrollment({ session_id: session.id, student_id: student, registration_source: "EXISTING" });
      if (!sameContext(scope) || !Number.isSafeInteger(saved?.id)) throw new Error("Unconfirmed registration");
      const records = await fetchSummerCampEnrollments({ session_id: session.id });
      const matches = Array.isArray(records) ? records.filter((item) => item.id === saved.id) : [];
      const actual = matches[0];
      if (!sameContext(scope) || matches.length !== 1 || actual.school !== scope.school
          || String(actual.student) !== student || Number(actual.session) !== Number(session.id)
          || actual.readiness_status !== "BLOCKED" || actual.payment_status !== "NOT_BILLED"
          || Number(actual.balance_due_cents) !== 0) throw new Error("Readback did not confirm the fictional registration");
      await onSaved();
      if (!sameContext(scope)) throw new Error("Staff session changed");
      setStudent(""); setMessage("Registration saved and verified. Attendance remains blocked until required reviews pass.");
    } catch {
      setLocked(true);
      setMessage("Registration not confirmed. Refresh this roster and verify current records before another attempt.");
    } finally { setBusy(false); }
  }

  if (!allowed) return null;
  const registered = new Set(rows.filter((row) => ["REGISTERED", "WAITLISTED"].includes(row.status)).map((row) => String(row.student_id)));
  return <section aria-label="Fictional Camp registration">
    <h3>Register a fictional camper</h3>
    <p>Local demonstration, no fees or payments. Registration does not authorize attendance or pickup.</p>
    <form onSubmit={register}>
      <label>Camper <select value={student} disabled={busy || locked || disabled} onChange={(event) => setStudent(event.target.value)}>
        <option value="">Choose an active student</option>
        {students.filter((item) => !registered.has(item.id)).map((item) => <option key={item.id} value={item.id}>{item.first_name} {item.last_name} (Grade {item.grade_level})</option>)}
      </select></label>
      <button type="submit" disabled={busy || locked || disabled || !student}>{busy ? "Registering..." : "Save fictional registration"}</button>
    </form>
    {message && <p role={locked ? "alert" : "status"}>{message}</p>}
  </section>;
}
