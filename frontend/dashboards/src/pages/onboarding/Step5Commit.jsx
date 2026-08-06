import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { commitImport } from "../../api/onboarding.js";
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
      const data = await commitImport(context.importId);
      setResult(data);
      setContext((c) => ({ ...c, commit: data }));
    } catch (e) {
      setError(e.body?.error || e.message || "Commit failed");
    } finally {
      setLoading(false);
    }
  }

  const s = context.preview?.summary;

  return (
    <div>
      <CrownWizardStepHeader
        title="Commit Import"
        subtitle="This action writes records to the database. It cannot be undone."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      {!result && (
        <div style={{ marginTop: 14 }}>
          {s && (
            <div className="crown-card" style={{ padding: "12px 16px", marginBottom: 14 }}>
              <p style={{ margin: 0, fontSize: 13, color: "var(--crown-muted)" }}>
                About to create <strong style={{ color: "var(--crown-text)" }}>{s.students_to_create}</strong> students,{" "}
                <strong style={{ color: "var(--crown-text)" }}>{s.guardians_to_create}</strong> guardians, and{" "}
                <strong style={{ color: "var(--crown-text)" }}>{s.households_to_create}</strong> households.
              </p>
            </div>
          )}

          <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
            />
            <span style={{ fontSize: 13, color: "var(--crown-text)" }}>
              I have reviewed the preview and confirm this import.
            </span>
          </label>

          {error && <div className="crown-alert" style={{ marginTop: 12 }}>{error}</div>}
        </div>
      )}

      {result && (
        <div className="crown-alert success" style={{ marginTop: 14 }}>
          <strong>Committed!</strong> Students: {result.students_imported ?? "—"}, Guardians: {result.guardians_imported ?? "—"}, Households: {result.households_imported ?? "—"}
        </div>
      )}

      <div className="crown-wizard-actions">
        <button className="crown-btn" onClick={goBack} disabled={!!result}>← Back</button>
        <div className="crown-wizard-actions-right">
          {!result && (
            <button className="crown-btn crown-btn-primary" onClick={handleCommit} disabled={loading || !confirmed}>
              {loading ? "Committing…" : "Commit Import"}
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
