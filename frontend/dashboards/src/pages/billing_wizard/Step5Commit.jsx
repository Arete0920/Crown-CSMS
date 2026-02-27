import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { commitBillingSetup } from "../../api/billing_wizard.js";
import "../../styles/crown-wizard.css";

export default function Step5Commit({ context, setContext, goNext, goBack, stepIndex, totalSteps, steps }) {
  const [confirmed, setConfirmed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const plans = context.plans || [];
  const fees = context.fees || [];

  async function handleCommit() {
    if (!confirmed) { setError("Please check the confirmation box before committing."); return; }
    setLoading(true);
    setError(null);
    try {
      const data = await commitBillingSetup(context.sessionId);
      setContext({ ...context, commit: data });
      goNext();
    } catch (e) {
      setError(e.body?.error || e.message || "Commit failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Commit Billing Setup"
        subtitle="This will create the tuition plans in the system. This action is final."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={{ border: "1px solid var(--crown-border)", borderRadius: 6, padding: "14px 16px", fontSize: 13 }}>
          <div style={{ fontWeight: 600, marginBottom: 10 }}>Summary</div>
          <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "4px 16px", color: "var(--crown-muted)", fontSize: 12 }}>
            <span>Term</span><span style={{ color: "inherit", fontWeight: 500 }}>{context.term || "—"}</span>
            <span>Mode</span><span style={{ color: "inherit", fontWeight: 500 }}>{context.billingMode || "—"}</span>
            <span>Plans</span><span style={{ color: "inherit", fontWeight: 500 }}>{plans.length}</span>
            <span>Fees</span><span style={{ color: "inherit", fontWeight: 500 }}>{fees.length}</span>
          </div>
          {plans.length > 0 && (
            <div style={{ marginTop: 10 }}>
              <div style={{ fontSize: 11, color: "var(--crown-muted)", marginBottom: 4 }}>Plans to create:</div>
              <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12 }}>
                {plans.map((p, i) => (
                  <li key={i}>{p.name} — ${parseFloat(p.total_amount || 0).toFixed(2)} · {p.installment_count} installment{p.installment_count !== 1 ? "s" : ""}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <label style={{ display: "flex", alignItems: "flex-start", gap: 10, fontSize: 13, cursor: "pointer" }}>
          <input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} style={{ marginTop: 2 }} />
          <span>I confirm this billing setup is correct and ready to be committed to the system.</span>
        </label>

        {error && <div className="crown-alert">{error}</div>}
      </div>

      <div className="crown-wizard-actions">
        <button className="crown-btn" onClick={goBack} disabled={loading}>← Back</button>
        <div className="crown-wizard-actions-right">
          <span className="crown-muted" style={{ fontSize: 12 }}>Step {stepIndex + 1} of {totalSteps}</span>
          <button className="crown-btn crown-btn-primary" onClick={handleCommit} disabled={loading || !confirmed}>
            {loading ? "Committing…" : "Commit Billing Setup"}
          </button>
        </div>
      </div>
    </div>
  );
}
