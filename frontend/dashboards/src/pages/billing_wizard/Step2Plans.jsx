import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { savePlans } from "../../api/billing_wizard.js";
import "../../styles/crown-wizard.css";

const EMPTY_PLAN = () => ({
  name: "",
  installment_count: 1,
  first_due_on: "",
  cadence_days: 30,
  total_amount: "",
});

export default function Step2Plans({ context, setContext, goNext, goBack, stepIndex, totalSteps, steps }) {
  const [plans, setPlans] = useState(
    context.plans && context.plans.length > 0 ? context.plans : [EMPTY_PLAN()]
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function updatePlan(idx, field, val) {
    setPlans((prev) => prev.map((plan, planIndex) => (planIndex === idx ? { ...plan, [field]: val } : plan)));
  }

  function addPlan() {
    setPlans((prev) => [...prev, EMPTY_PLAN()]);
  }

  function removePlan(idx) {
    setPlans((prev) => prev.filter((_, planIndex) => planIndex !== idx));
  }

  async function handleContinue() {
    if (plans.length === 0) { setError("At least one tuition plan is required."); return; }
    for (let i = 0; i < plans.length; i += 1) {
      if (!plans[i].name.trim()) { setError(`Plan ${i + 1}: name is required.`); return; }
      if (!plans[i].first_due_on) { setError(`Plan ${i + 1}: first due date is required.`); return; }
      const amount = Number.parseFloat(plans[i].total_amount);
      if (Number.isNaN(amount) || amount < 0) { setError(`Plan ${i + 1}: total amount must be a valid non-negative number.`); return; }
      const count = Number.parseInt(plans[i].installment_count, 10);
      if (!count || count < 1) { setError(`Plan ${i + 1}: installment count must be at least 1.`); return; }
    }

    setLoading(true);
    setError(null);
    try {
      const normalised = plans.map((plan) => ({
        name: plan.name.trim(),
        installment_count: Number.parseInt(plan.installment_count, 10),
        first_due_on: plan.first_due_on,
        cadence_days: Number.parseInt(plan.cadence_days || 30, 10),
        total_amount: Number.parseFloat(plan.total_amount).toFixed(2),
      }));
      const data = await savePlans(context.sessionId, normalised);
      setContext({ ...context, plans: normalised, plansResult: data });
      goNext();
    } catch (e) {
      const errs = e.body?.errors;
      setError(errs ? errs.join("; ") : (e.body?.error || e.message || "Failed to save plans."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Define Tuition Plans"
        subtitle={`Term: ${context.term || "-"} - Mode: ${context.billingMode || "-"}`}
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 16 }}>
        {plans.map((plan, idx) => (
          <div key={[plan.name, plan.first_due_on, plan.total_amount, plan.installment_count, idx].join("-")} style={{ border: "1px solid var(--crown-border)", borderRadius: 6, padding: "12px 14px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <span style={{ fontWeight: 600, fontSize: 13 }}>Plan {idx + 1}</span>
              {plans.length > 1 && (
                <button className="crown-btn" style={{ fontSize: 11, padding: "2px 8px" }} onClick={() => removePlan(idx)}>
                  Remove
                </button>
              )}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <div style={{ gridColumn: "1 / -1" }}>
                <label htmlFor={`billing-plan-name-${idx}`} style={{ display: "block", fontSize: 11, color: "var(--crown-muted)", marginBottom: 3 }}>Plan Name *</label>
                <input id={`billing-plan-name-${idx}`} className="crown-input" type="text" placeholder="e.g. Annual Pay" value={plan.name}
                  onChange={(e) => updatePlan(idx, "name", e.target.value)} style={{ width: "100%", boxSizing: "border-box" }} />
              </div>
              <div>
                <label htmlFor={`billing-plan-amount-${idx}`} style={{ display: "block", fontSize: 11, color: "var(--crown-muted)", marginBottom: 3 }}>Total Amount ($) *</label>
                <input id={`billing-plan-amount-${idx}`} className="crown-input" type="number" min="0" step="0.01" placeholder="10500.00" value={plan.total_amount}
                  onChange={(e) => updatePlan(idx, "total_amount", e.target.value)} style={{ width: "100%", boxSizing: "border-box" }} />
              </div>
              <div>
                <label htmlFor={`billing-plan-installments-${idx}`} style={{ display: "block", fontSize: 11, color: "var(--crown-muted)", marginBottom: 3 }}>Installments *</label>
                <input id={`billing-plan-installments-${idx}`} className="crown-input" type="number" min="1" step="1" placeholder="1" value={plan.installment_count}
                  onChange={(e) => updatePlan(idx, "installment_count", e.target.value)} style={{ width: "100%", boxSizing: "border-box" }} />
              </div>
              <div>
                <label htmlFor={`billing-plan-first-due-${idx}`} style={{ display: "block", fontSize: 11, color: "var(--crown-muted)", marginBottom: 3 }}>First Due Date *</label>
                <input id={`billing-plan-first-due-${idx}`} className="crown-input" type="date" value={plan.first_due_on}
                  onChange={(e) => updatePlan(idx, "first_due_on", e.target.value)} style={{ width: "100%", boxSizing: "border-box" }} />
              </div>
              <div>
                <label htmlFor={`billing-plan-cadence-${idx}`} style={{ display: "block", fontSize: 11, color: "var(--crown-muted)", marginBottom: 3 }}>Days Between Payments</label>
                <input id={`billing-plan-cadence-${idx}`} className="crown-input" type="number" min="0" step="1" placeholder="30" value={plan.cadence_days}
                  onChange={(e) => updatePlan(idx, "cadence_days", e.target.value)} style={{ width: "100%", boxSizing: "border-box" }} />
              </div>
            </div>
          </div>
        ))}

        <button className="crown-btn" onClick={addPlan} style={{ alignSelf: "flex-start" }}>
          + Add Plan
        </button>

        {error && <div className="crown-alert">{error}</div>}
      </div>

      <div className="crown-wizard-actions">
        <button className="crown-btn" onClick={goBack} disabled={loading}>Back</button>
        <div className="crown-wizard-actions-right">
          <span className="crown-muted" style={{ fontSize: 12 }}>Step {stepIndex + 1} of {totalSteps}</span>
          <button className="crown-btn crown-btn-primary" onClick={handleContinue} disabled={loading}>
            {loading ? "Saving..." : "Continue"}
          </button>
        </div>
      </div>
    </div>
  );
}