import { useState, useEffect } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { previewImport } from "../../api/onboarding.js";
import "../../styles/crown-wizard.css";

export default function Step4Preview({ context, setContext, goBack, goNext, stepIndex, totalSteps, steps }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(context.preview || null);

  useEffect(() => {
    if (!result) {
      load();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await previewImport(context.importId);
      setResult(data);
      setContext((c) => ({ ...c, preview: data }));
    } catch (e) {
      setError(e.body?.error || e.message || "Preview failed");
    } finally {
      setLoading(false);
    }
  }

  const s = result?.summary;

  return (
    <div>
      <CrownWizardStepHeader
        title="Preview"
        subtitle="Review the import summary before committing."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      {loading && <p style={{ color: "var(--crown-muted)", fontSize: 13, marginTop: 14 }}>Loading preview…</p>}
      {error && <div className="crown-alert" style={{ marginTop: 14 }}>{error}</div>}

      {result && (
        <div style={{ marginTop: 14 }}>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 16 }}>
            {[
              ["Rows", s.rows_total],
              ["Students", s.students_to_create],
              ["Guardians", s.guardians_to_create],
              ["Households", s.households_to_create],
              ["Duplicates detected", s.duplicates_detected],
              ["Errors detected", s.errors_detected],
            ].map(([label, val]) => (
              <div key={label} className="crown-card" style={{ padding: "10px 16px", minWidth: 110 }}>
                <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>{label}</div>
                <div style={{ fontSize: 22, fontWeight: 700, color: "var(--crown-text)" }}>{val}</div>
              </div>
            ))}
          </div>

          {result.sample_rows && result.sample_rows.length > 0 && (
            <>
              <p style={{ fontSize: 12, color: "var(--crown-muted)", margin: "0 0 6px" }}>
                First {result.sample_rows.length} row(s):
              </p>
              <div style={{ overflowX: "auto" }}>
                <table className="crown-table">
                  <thead>
                    <tr>
                      {Object.keys(result.sample_rows[0]).map((k) => <th key={k}>{k}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {result.sample_rows.map((row, i) => (
                      <tr key={i}>
                        {Object.values(row).map((v, j) => <td key={j}>{String(v ?? "")}</td>)}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}

      <div className="crown-wizard-actions">
        <button className="crown-btn" onClick={goBack}>← Back</button>
        <div className="crown-wizard-actions-right">
          {result && <button className="crown-btn" onClick={load} disabled={loading}>Refresh</button>}
          {result && (
            <button className="crown-btn crown-btn-primary" onClick={goNext} disabled={!result || (s?.errors_detected > 0)}>
              Continue →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
