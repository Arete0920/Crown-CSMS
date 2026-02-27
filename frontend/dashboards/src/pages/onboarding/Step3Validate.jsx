import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { validateImport } from "../../api/onboarding.js";
import "../../styles/crown-wizard.css";

export default function Step3Validate({ context, setContext, goBack, goNext, stepIndex, totalSteps, steps }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(context.validate || null);

  async function handleValidate() {
    setLoading(true);
    setError(null);
    try {
      const data = await validateImport(context.importId);
      setResult(data);
      setContext((c) => ({ ...c, validate: data }));
    } catch (e) {
      setError(e.body?.error || e.message || "Validation failed");
    } finally {
      setLoading(false);
    }
  }

  const hasErrors = result && result.errors && result.errors.length > 0;
  const hasWarnings = result && result.warnings && result.warnings.length > 0;

  return (
    <div>
      <CrownWizardStepHeader
        title="Validate Data"
        subtitle="Check for row errors and warnings before committing."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      {!result && (
        <div style={{ marginTop: 14 }}>
          <p style={{ color: "var(--crown-muted)", fontSize: 13 }}>
            Click Validate to check the uploaded CSV for errors.
          </p>
          {error && <div className="crown-alert">{error}</div>}
        </div>
      )}

      {result && (
        <div style={{ marginTop: 14 }}>
          <p style={{ color: "var(--crown-muted)", fontSize: 13 }}>
            {result.rows_total} rows — {result.students_detected} students, {result.guardians_detected} guardians, {result.households_detected} households.
          </p>

          {hasErrors && (
            <>
              <div className="crown-alert">
                <strong>{result.errors.length} error(s)</strong> found — fix your CSV and re-upload before continuing.
              </div>
              <table className="crown-table" style={{ marginTop: 8 }}>
                <thead>
                  <tr><th>Row</th><th>Field</th><th>Message</th></tr>
                </thead>
                <tbody>
                  {result.errors.map((e, i) => (
                    <tr key={i}>
                      <td>{e.row}</td>
                      <td>{e.field}</td>
                      <td style={{ color: "rgb(255,120,120)" }}>{e.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}

          {hasWarnings && (
            <div style={{ marginTop: 10 }}>
              <p style={{ fontSize: 13, color: "var(--crown-muted)" }}>{result.warnings.length} warning(s):</p>
              <table className="crown-table">
                <thead>
                  <tr><th>Row</th><th>Field</th><th>Message</th></tr>
                </thead>
                <tbody>
                  {result.warnings.map((w, i) => (
                    <tr key={i}>
                      <td>{w.row}</td>
                      <td>{w.field}</td>
                      <td style={{ color: "var(--crown-gold-2, #f1d88a)" }}>{w.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {!hasErrors && (
            <div className="crown-alert success">All rows valid — no errors detected.</div>
          )}
        </div>
      )}

      <div className="crown-wizard-actions">
        <button className="crown-btn" onClick={goBack}>← Back</button>
        <div className="crown-wizard-actions-right">
          <button className="crown-btn" onClick={handleValidate} disabled={loading}>
            {loading ? "Validating…" : result ? "Re-validate" : "Validate"}
          </button>
          {result && !hasErrors && (
            <button className="crown-btn crown-btn-primary" onClick={goNext}>
              Continue →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
