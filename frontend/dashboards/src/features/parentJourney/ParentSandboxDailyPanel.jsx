import { useEffect, useState } from "react";
import { authenticatedJson } from "../../utils/authClient";

const sandboxEnabled = String(import.meta.env.VITE_SANDBOX_MODE || "") === "1";

function dollars(cents) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(Number(cents || 0) / 100);
}

export default function ParentSandboxDailyPanel() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!sandboxEnabled) return;
    let active = true;
    authenticatedJson("/api/v1/sandbox/parent/daily/")
      .then((payload) => { if (active) setData(payload); })
      .catch((err) => { if (active) setError(err?.response?.data?.detail || err?.message || "Unable to load family daily-work data."); });
    return () => { active = false; };
  }, []);

  if (!sandboxEnabled) return null;

  return (
    <section data-testid="sandbox-parent-daily" style={{ margin: "16px 24px", padding: 16, border: "1px solid var(--crown-border)", borderRadius: 10, background: "var(--crown-surface)" }}>
      <h2 style={{ marginTop: 0 }}>Family Daily Work</h2>
      {error ? <div role="alert">{error}</div> : null}
      {!data ? <p>Loading child, school and billing context...</p> : (
        <div style={{ display: "grid", gap: 16 }}>
          <div><strong data-testid="parent-daily-child">{data.child.name}</strong> · Grade {data.child.grade}</div>
          <div>
            <h3>Attendance</h3>
            <ul data-testid="parent-daily-attendance">{data.attendance.map((row) => <li key={`${row.date}-${row.course}`}>{row.date} · {row.course} · {row.status}</li>)}</ul>
          </div>
          <div>
            <h3>Learning & Progress</h3>
            <ul data-testid="parent-daily-progress">{data.progress.map((row) => <li key={row.assignment}><strong>{row.assignment}</strong> · {row.letter_grade} · {row.score}/{row.score_max} · {row.feedback}</li>)}</ul>
          </div>
          <div>
            <h3>Communications</h3>
            <ul data-testid="parent-daily-communications">{data.communications.map((thread) => <li key={thread.subject}><strong>{thread.subject}</strong>: {thread.messages.join(" ")}</li>)}</ul>
          </div>
          <div data-testid="parent-daily-billing"><strong>Family balance:</strong> {dollars(data.billing.balance_cents)} · External provider enabled: {String(data.billing.external_payment_provider_enabled)}</div>
          <div data-testid="parent-daily-staff-controls">Staff controls: grade-write={String(data.staff_controls.grade_write)}, attendance-write={String(data.staff_controls.attendance_write)}, admissions-decision={String(data.staff_controls.admissions_decision)}, finance-admin={String(data.staff_controls.finance_admin)}, tenant-admin={String(data.staff_controls.tenant_admin)}</div>
        </div>
      )}
    </section>
  );
}
