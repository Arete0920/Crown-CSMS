import { useEffect, useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { verifySectionAssign } from "../../api/section_assign_wizard.js";
import "../../styles/crown-wizard.css";

const STORAGE_KEY = "crown_section_assign_wizard_ctx_v1";

export default function Step6Verify({ context, stepIndex, totalSteps, steps }) {
  const [result, setResult] = useState(context.verify || null);
  const [loading, setLoading] = useState(!context.verify);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (context.verify) return;
    verifySectionAssign(context.sessionId)
      .then((data) => { setResult(data); setLoading(false); })
      .catch((e) => { setError(e.body?.error || e.message || "Verification failed."); setLoading(false); });
  }, [context.verify, context.sessionId]);

  function handleReset() {
    try { sessionStorage.removeItem(STORAGE_KEY); } catch { /* ignore */ }
    window.location.reload();
  }

  const commit = context.commit || {};

  return (
    <div>
      <CrownWizardStepHeader
        title="Verified"
        subtitle="Enrollment records have been committed. The section roster is now live."
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
              Section roster committed and verified. Status: {result.status}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
              {[
                { label: "Total Enrollments", value: result.enrollment_count ?? "—" },
                { label: "Added This Run", value: commit.enrolled ?? "—" },
                { label: "Removed This Run", value: commit.removed ?? "—" },
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

            <div style={{ fontSize: 12, color: "var(--crown-muted)", padding: "8px 0" }}>
              Section: {result.section_id || context.section_id || "—"} &nbsp;·&nbsp; Term: {result.term || context.term || "—"}
            </div>

            <button
              className="crown-btn"
              onClick={handleReset}
              style={{ alignSelf: "flex-start" }}
            >
              Start New Assignment
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
