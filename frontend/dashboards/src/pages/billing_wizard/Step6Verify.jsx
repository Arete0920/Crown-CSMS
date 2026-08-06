import { useEffect, useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { verifyBillingSetup } from "../../api/billing_wizard.js";
import "../../styles/crown-wizard.css";

export default function Step6Verify({ context, stepIndex, totalSteps, steps }) {
  const existingVerify = context.verify || null;
  const sessionId = context.sessionId;
  const term = context.term;
  const [result, setResult] = useState(existingVerify);
  const [loading, setLoading] = useState(!existingVerify);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (existingVerify || !sessionId) return;
    verifyBillingSetup(sessionId)
      .then((data) => { setResult(data); setLoading(false); })
      .catch((e) => { setError(e.body?.error || e.message || "Verification failed."); setLoading(false); });
  }, [existingVerify, sessionId]);

  const plans = result?.result?.plans || [];
  const feesCount = result?.result?.fees_count ?? 0;
  const fees = result?.result?.fees_config || [];

  return (
    <div>
      <CrownWizardStepHeader
        title="Verified"
        subtitle="Billing setup has been committed and verified. Plans are now active in the system."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16 }}>
        {loading && <div style={{ color: "var(--crown-muted)", fontSize: 13 }}>Verifying...</div>}
        {error && <div className="crown-alert">{error}</div>}

        {result && !loading && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ padding: "12px 16px", background: "var(--crown-ok-bg)", border: "1px solid var(--crown-ok)", borderRadius: 6, fontSize: 13, fontWeight: 600, color: "var(--crown-ok)" }}>
              Billing setup verified. Status: {result.status}
            </div>

            {plans.length > 0 && (
              <div>
                <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>Installment Plans Created ({plans.length})</div>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, border: "1px solid var(--crown-border)" }}>
                  <thead>
                    <tr style={{ background: "var(--crown-surface)", borderBottom: "1px solid var(--crown-border)" }}>
                      <th style={{ padding: "6px 14px", textAlign: "left" }}>Plan Name</th>
                      <th style={{ padding: "6px 14px", textAlign: "left" }}>Plan ID</th>
                    </tr>
                  </thead>
                  <tbody>
                    {plans.map((plan) => (
                      <tr key={plan.plan_id} style={{ borderBottom: "1px solid var(--crown-border)" }}>
                        <td style={{ padding: "6px 14px" }}>{plan.name}</td>
                        <td style={{ padding: "6px 14px", fontFamily: "var(--crown-font-mono)", fontSize: 11 }}>{plan.plan_id}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {feesCount > 0 && (
              <div>
                <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>Fees Recorded ({feesCount})</div>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, border: "1px solid var(--crown-border)" }}>
                  <thead>
                    <tr style={{ background: "var(--crown-surface)", borderBottom: "1px solid var(--crown-border)" }}>
                      <th style={{ padding: "6px 14px", textAlign: "left" }}>Name</th>
                      <th style={{ padding: "6px 14px", textAlign: "left" }}>Type</th>
                      <th style={{ padding: "6px 14px", textAlign: "right" }}>Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fees.map((fee) => (
                      <tr key={[fee.name, fee.fee_type, fee.amount].join("-")} style={{ borderBottom: "1px solid var(--crown-border)" }}>
                        <td style={{ padding: "6px 14px" }}>{fee.name}</td>
                        <td style={{ padding: "6px 14px" }}>{fee.fee_type}</td>
                        <td style={{ padding: "6px 14px", textAlign: "right" }}>${Number.parseFloat(fee.amount).toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div style={{ fontSize: 12, color: "var(--crown-muted)" }}>
              Setup complete for term <strong>{result.result?.term || term}</strong>. Return to the dashboard to begin billing runs.
            </div>
          </div>
        )}
      </div>

      <div className="crown-wizard-actions">
        <span />
        <div className="crown-wizard-actions-right">
          <span className="crown-muted" style={{ fontSize: 12 }}>Step {stepIndex + 1} of {totalSteps} - Complete</span>
        </div>
      </div>
    </div>
  );
}