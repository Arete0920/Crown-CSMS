import { useEffect, useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { verifySchedulingSetup } from "../../api/scheduling_wizard.js";
import "../../styles/crown-wizard.css";

const STORAGE_KEY = "crown_scheduling_wizard_ctx_v1";

export default function Step6Verify({ context, stepIndex, totalSteps, steps }) {
  const [result, setResult] = useState(context.verify || null);
  const [loading, setLoading] = useState(!context.verify);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (context.verify) return;
    verifySchedulingSetup(context.sessionId)
      .then((data) => { setResult(data); setLoading(false); })
      .catch((e) => { setError(e.body?.error || e.message || "Verification failed."); setLoading(false); });
  }, [context.verify, context.sessionId]);

  function handleReset() {
    try { sessionStorage.removeItem(STORAGE_KEY); } catch { /* ignore */ }
    window.location.reload();
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Verified"
        subtitle="Scheduling setup has been committed and verified. Courses and sections are now active."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16 }}>
        {loading && <div style={{ color: "var(--crown-muted)", fontSize: 13 }}>Verifying…</div>}
        {error && <div className="crown-alert">{error}</div>}

        {result && !loading && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{
              padding: "12px 16px",
              background: "var(--crown-ok-bg)",
              border: "1px solid var(--crown-ok)",
              borderRadius: 6,
              fontSize: 13,
              fontWeight: 600,
              color: "var(--crown-ok)",
            }}>
              Scheduling setup verified. Status: {result.status}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              {[
                { label: "Courses Created", value: result.courses_created ?? "—" },
                { label: "Courses Skipped", value: result.courses_skipped ?? "—" },
                { label: "Sections Created", value: result.sections_created ?? "—" },
                { label: "Sections Skipped", value: result.sections_skipped ?? "—" },
              ].map(({ label, value }) => (
                <div key={label} style={{
                  padding: "10px 14px",
                  background: "var(--crown-surface)",
                  border: "1px solid var(--crown-border)",
                  borderRadius: 6,
                  fontSize: 12,
                }}>
                  <div style={{ color: "var(--crown-muted)", marginBottom: 4 }}>{label}</div>
                  <div style={{ fontWeight: 700, fontSize: 20 }}>{value}</div>
                </div>
              ))}
            </div>

            <button
              className="crown-btn"
              onClick={handleReset}
              style={{ alignSelf: "flex-start", marginTop: 8 }}
            >
              Start New Schedule
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
