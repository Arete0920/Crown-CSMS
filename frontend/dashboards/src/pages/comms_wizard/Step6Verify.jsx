import { useEffect, useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { verifyCommsSetup } from "../../api/comms_wizard.js";
import "../../styles/crown-wizard.css";

const STORAGE_KEY = "crown_comms_wizard_ctx_v1";

export default function Step6Verify({ context, stepIndex, totalSteps, steps }) {
  const [result, setResult] = useState(context.verify || null);
  const [loading, setLoading] = useState(!context.verify);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (context.verify) return;
    verifyCommsSetup(context.sessionId)
      .then((data) => { setResult(data); setLoading(false); })
      .catch((e) => { setError(e.body?.error || e.message || "Verification failed."); setLoading(false); });
  }, []);

  function handleReset() {
    try { sessionStorage.removeItem(STORAGE_KEY); } catch { /* ignore */ }
    window.location.reload();
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Verified"
        subtitle="Messages have been queued for delivery. They will be processed by the background worker."
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
              background: "var(--crown-success-bg, #f0faf0)",
              border: "1px solid var(--crown-success-border, #b7dfb7)",
              borderRadius: 6,
              fontSize: 13,
              fontWeight: 600,
              color: "var(--crown-success, #2d7a2d)",
            }}>
              Campaign queued and verified. Status: {result.status}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              {[
                { label: "Messages Queued", value: result.messages_created ?? "—" },
                { label: "Already Queued (Skipped)", value: result.messages_skipped ?? "—" },
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
              Messages are now in the outbox and will be delivered by the background worker.
            </div>

            <button
              className="crown-btn"
              onClick={handleReset}
              style={{ alignSelf: "flex-start" }}
            >
              Start New Campaign
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
