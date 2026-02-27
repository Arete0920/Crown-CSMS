import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { commitReenrollment } from "../../api/reenrollment.js";
import "../../styles/crown-wizard.css";

export default function Step5Commit({ context, setContext, goBack, goNext, stepIndex, totalSteps, steps }) {
  const [confirmed, setConfirmed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(context.commit || null);

  async function handleCommit() {
    if (!confirmed) return;
    setLoading(true);
    setError(null);
    try {
      const data = await commitReenrollment(context.sessionId);
      setResult(data);
      setContext((c) => ({ ...c, commit: data }));
    } catch (e) {
      setError(e.body?.detail || e.message || "Commit failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Commit Re-enrollment"
        subtitle="This creates billing records for all selected students. It cannot be undone."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      {!result && (
        <div style={{ marginTop: 14 }}>
          <div className="crown-card" style={{ padding: "12px 16px", marginBottom: 14 }}>
            <p style={{ margin: 0, fontSize: 13, color: "var(--crown-muted)" }}>
              Year: <strong style={{ color: "var(--crown-text)" }}>{context.targetYearLabel}</strong> &nbsp;·&nbsp;
              Fee: <strong style={{ color: "var(--crown-text)" }}>${context.enrollmentFee?.toFixed(2)}</strong>
            </p>
          </div>

          <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
            />
            <span style={{ fontSize: 13, color: "var(--crown-text)" }}>
              I have reviewed the preview and confirm this re-enrollment run.
            </span>
          </label>

          {error && <div className="crown-alert" style={{ marginTop: 12 }}>{error}</div>}
        </div>
      )}

      {result && (
        <div className="crown-alert success" style={{ marginTop: 14 }}>
          <strong>Committed!</strong>{" "}
          {result.students_reenrolled} students re-enrolled &nbsp;·&nbsp;
          {result.households_invoiced} households invoiced &nbsp;·&nbsp;
          Total: ${result.total_amount}
        </div>
      )}

      <div className="crown-wizard-actions">
        <button className="crown-btn" onClick={goBack} disabled={!!result}>← Back</button>
        <div className="crown-wizard-actions-right">
          {!result && (
            <button
              className="crown-btn crown-btn-primary"
              onClick={handleCommit}
              disabled={loading || !confirmed}
            >
              {loading ? "Committing…" : "Commit Re-enrollment"}
            </button>
          )}
          {result && (
            <button className="crown-btn crown-btn-primary" onClick={goNext}>
              Verify Results →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
