import { useState, useEffect } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { verifyImport } from "../../api/onboarding.js";
import "../../styles/crown-wizard.css";

export default function Step6Verify({ context, setContext, stepIndex, totalSteps, steps }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(context.verify || null);

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
      const data = await verifyImport(context.importId);
      setResult(data);
      setContext((c) => ({ ...c, verify: data }));
    } catch (e) {
      setError(e.body?.error || e.message || "Verification failed");
    } finally {
      setLoading(false);
    }
  }

  function handleStartNew() {
    // Reset context, keeping only the mode
    setContext({ mode: context.mode });
    // Navigate back to step 0 via page reload trick — wizard owns step state
    // Parent will re-mount CrownWizard when importId is cleared
    window.location.reload();
  }

  function statusColor(status) {
    if (status === "ok" || status === "pass") return "rgba(78,225,138,0.9)";
    if (status === "warning") return "var(--crown-gold)";
    return "rgb(255,120,120)";
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Verify Results"
        subtitle="Post-commit integrity checks."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      {loading && <p style={{ color: "var(--crown-muted)", fontSize: 13, marginTop: 14 }}>Running verification…</p>}
      {error && <div className="crown-alert" style={{ marginTop: 14 }}>{error}</div>}

      {result && (
        <div style={{ marginTop: 14 }}>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 16 }}>
            {[
              ["Students imported", result.students_imported],
              ["Guardians imported", result.guardians_imported],
              ["Households imported", result.households_imported],
              ["Exceptions", result.exceptions_count],
            ].map(([label, val]) => (
              <div key={label} className="crown-card" style={{ padding: "10px 16px", minWidth: 110 }}>
                <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>{label}</div>
                <div style={{ fontSize: 22, fontWeight: 700, color: "var(--crown-text)" }}>{val}</div>
              </div>
            ))}
          </div>

          {result.checks && result.checks.length > 0 && (
            <table className="crown-table">
              <thead>
                <tr><th>Check</th><th>Status</th><th>Detail</th></tr>
              </thead>
              <tbody>
                {result.checks.map((chk, i) => (
                  <tr key={i}>
                    <td>{chk.name}</td>
                    <td style={{ color: statusColor(chk.status), fontWeight: 600 }}>{chk.status}</td>
                    <td style={{ color: "var(--crown-muted)", fontSize: 12 }}>{chk.detail || ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      <div className="crown-wizard-actions">
        <span />
        <div className="crown-wizard-actions-right">
          {result && (
            <button className="crown-btn" onClick={load} disabled={loading}>Re-check</button>
          )}
          <button className="crown-btn crown-btn-primary" onClick={handleStartNew}>
            Start New Import
          </button>
        </div>
      </div>
    </div>
  );
}
