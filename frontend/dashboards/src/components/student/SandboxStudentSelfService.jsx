import { useEffect, useState } from "react";
import { authenticatedJson } from "../../utils/authClient";

const sandboxEnabled = String(import.meta.env.VITE_SANDBOX_MODE || "") === "1";

function hasStudentSelfServicePayload(payload) {
  return Boolean(
    payload
    && payload.student
    && typeof payload.student.name === "string"
    && Array.isArray(payload.schedule)
    && Array.isArray(payload.learning_tasks)
    && Array.isArray(payload.attendance)
    && Array.isArray(payload.communications)
    && payload.privileged_actions
  );
}

export default function SandboxStudentSelfService() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!sandboxEnabled) return;
    let active = true;
    authenticatedJson("/api/v1/sandbox/student/self-service/")
      .then((payload) => {
        if (!active) return;
        if (!hasStudentSelfServicePayload(payload)) {
          setError("Unable to load student self-service data.");
          setData(null);
          return;
        }
        setData(payload);
      })
      .catch((err) => { if (active) setError(err?.response?.data?.detail || err?.message || "Unable to load student self-service data."); });
    return () => { active = false; };
  }, []);

  if (!sandboxEnabled) return null;

  return (
    <section data-testid="sandbox-student-self-service" style={{ margin: "16px 24px", padding: 16, border: "1px solid var(--crown-border)", borderRadius: 10, background: "var(--crown-surface)" }}>
      <h2 style={{ marginTop: 0 }}>Student Self-Service</h2>
      {error ? <div role="alert">{error}</div> : null}
      {!data ? <p>Loading student schedule and progress...</p> : (
        <div style={{ display: "grid", gap: 16 }}>
          <div><strong data-testid="student-self-service-name">{data.student.name}</strong> · Grade {data.student.grade}</div>
          <div>
            <h3>Schedule</h3>
            <ul data-testid="student-schedule">{data.schedule.map((row) => <li key={`${row.course}-${row.time}`}>{row.course} · {row.days} {row.time} · Room {row.room} · {row.teacher}</li>)}</ul>
          </div>
          <div>
            <h3>Assignments & Progress</h3>
            <ul data-testid="student-learning-tasks">{data.learning_tasks.map((row) => <li key={row.assignment}><strong>{row.assignment}</strong> · {row.letter_grade} · {row.score}/{row.score_max} · {row.feedback}</li>)}</ul>
          </div>
          <div>
            <h3>Attendance</h3>
            <ul data-testid="student-attendance">{data.attendance.map((row) => <li key={`${row.date}-${row.course}`}>{row.date} · {row.course} · {row.status}</li>)}</ul>
          </div>
          <div>
            <h3>Communications</h3>
            <ul data-testid="student-communications">{data.communications.map((thread) => <li key={thread.subject}><strong>{thread.subject}</strong>: {thread.messages.join(" ")}</li>)}</ul>
          </div>
          <div data-testid="student-privilege-boundary">
            Administrative privileges: grading={String(data.privileged_actions.grading)}, admissions={String(data.privileged_actions.admissions)}, finance={String(data.privileged_actions.finance_admin)}, tenant-admin={String(data.privileged_actions.tenant_admin)}
          </div>
        </div>
      )}
    </section>
  );
}
