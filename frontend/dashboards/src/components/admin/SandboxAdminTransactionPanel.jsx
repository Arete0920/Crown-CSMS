import { useCallback, useEffect, useState } from "react";
import { authenticatedJson } from "../../utils/authClient";

const sandboxEnabled = String(import.meta.env.VITE_SANDBOX_MODE || "") === "1";

function dollars(cents) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(Number(cents || 0) / 100);
}

export default function SandboxAdminTransactionPanel() {
  const [state, setState] = useState(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    if (!sandboxEnabled) return;
    setError("");
    try {
      setState(await authenticatedJson("/api/v1/sandbox/admin/state/"));
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to load administrator transaction state.");
    }
  }, []);

  useEffect(() => { void load(); }, [load]);
  if (!sandboxEnabled) return null;

  async function resolveException() {
    setSaving(true);
    setError("");
    try {
      setState(await authenticatedJson("/api/v1/sandbox/admin/resolve-operational-exception/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      }));
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Unable to complete administrator workflow.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section data-testid="sandbox-admin-transaction" style={{ margin: "0 0 20px", padding: 16, border: "1px solid var(--crown-border)", borderRadius: 10, background: "var(--crown-surface)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, flexWrap: "wrap" }}>
        <div>
          <h2 style={{ margin: 0, fontSize: "1.1rem" }}>Administrator Operational Workflow</h2>
          <p style={{ margin: "6px 0 0", fontSize: "0.875rem" }}>Review student, enrollment, academic, tuition and school finance context; verify the household; resolve an attendance exception; and send the follow-up.</p>
        </div>
        <button type="button" onClick={resolveException} disabled={saving || state?.exception_status === "resolved"} className="crown-btn crown-btn-primary">
          {saving ? "Resolving..." : state?.exception_status === "resolved" ? "Workflow Completed" : "Verify + Resolve + Send Follow-up"}
        </button>
      </div>
      {error ? <div role="alert" style={{ marginTop: 12, color: "var(--crown-danger)" }}>{error}</div> : null}
      {state ? (
        <dl style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12, marginTop: 16 }}>
          <div><dt>Student</dt><dd>{state.student_name} ({state.student_number})</dd></div>
          <div><dt>Family</dt><dd>{state.family_name}</dd></div>
          <div><dt>Enrollment / roster</dt><dd data-testid="admin-enrollment-context">{state.enrollment_status} · Grade {state.roster_grade}</dd></div>
          <div><dt>Academic context</dt><dd data-testid="admin-academic-context">{state.academic_context}</dd></div>
          <div><dt>Student tuition context</dt><dd data-testid="admin-tuition-context">{dollars(state.tuition_context_cents)}</dd></div>
          <div><dt>School finance risk summary</dt><dd data-testid="admin-finance-summary">{state.finance_open_obligation_count} open · {dollars(state.finance_open_obligation_cents)}</dd></div>
          <div><dt>Attendance</dt><dd data-testid="admin-attendance-status">{state.attendance_status}</dd></div>
          <div><dt>Exception</dt><dd data-testid="admin-exception-status">{state.exception_status}</dd></div>
          <div><dt>Household verification</dt><dd data-testid="admin-household-note">{state.household_note || "Pending"}</dd></div>
          <div><dt>Follow-up communication</dt><dd data-testid="admin-communication-status">{state.communication_status}</dd></div>
          <div><dt>Platform authority</dt><dd data-testid="admin-platform-authority">{state.is_platform_superuser ? "Platform superuser" : "School-scoped administrator"}</dd></div>
        </dl>
      ) : null}
    </section>
  );
}
