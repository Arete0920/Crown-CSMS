import { useEffect, useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { verifyAidSetup } from "../../api/financial_aid_wizard.js";
import "../../styles/crown-wizard.css";

export default function Step6Verify({ context, setContext, stepIndex, totalSteps, steps }) {
  const [result, setResult] = useState(context.verify || null);
  const [loading, setLoading] = useState(!context.verify);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (context.verify) return;
    let cancelled = false;
    verifyAidSetup(context.sessionId)
      .then((data) => {
        if (cancelled) return;
        setResult(data);
        setContext((prev) => ({ ...prev, verify: data }));
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e.body?.error || e.message || "Verification failed.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  function handleReset() {
    try { sessionStorage.removeItem("crown_aid_wizard_ctx_v1"); } catch { /* ignore */ }
    setContext({});
    window.location.reload();
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Verify"
        subtitle="Confirming the aid cycle setup is complete."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16 }}>
        {loading && (
          <div style={{ color: "var(--crown-muted)", fontSize: 14 }}>Verifying setup…</div>
        )}

        {error && (
          <div className="crown-alert crown-alert--error">{error}</div>
        )}

        {result && !loading && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div
              style={{
                background: "var(--crown-ok-bg)",
                border: "1px solid var(--crown-ok)",
                borderRadius: 6,
                padding: "16px",
                color: "var(--crown-ok)",
                fontWeight: 600,
              }}
            >
              Financial aid setup complete! Status: {result.status}
            </div>

            {/* Commit summary */}
            <div style={{ border: "1px solid var(--crown-border)", borderRadius: 6, padding: "16px" }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: "var(--crown-muted)", marginBottom: 10 }}>
                Commit Summary
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
                <div>
                  <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>Awards Created</div>
                  <div style={{ fontWeight: 700, fontSize: 18 }}>{result.awards_created ?? "—"}</div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>Already Existed</div>
                  <div style={{ fontWeight: 700, fontSize: 18 }}>{result.awards_skipped ?? "—"}</div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>Errors</div>
                  <div style={{ fontWeight: 700, fontSize: 18 }}>
                    {(result.errors?.length ?? 0) > 0 ? (
                      <span style={{ color: "var(--crown-danger)" }}>{result.errors.length}</span>
                    ) : 0}
                  </div>
                </div>
              </div>

              {result.errors?.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "var(--crown-danger)", marginBottom: 6 }}>
                    Errors during commit:
                  </div>
                  {result.errors.map((e, i) => (
                    <div key={i} style={{ fontSize: 12, color: "var(--crown-danger)" }}>{e}</div>
                  ))}
                </div>
              )}
            </div>

            <div style={{ display: "flex", gap: 8 }}>
              <button className="crown-btn crown-btn--ghost" onClick={handleReset}>
                Start New Aid Cycle
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
