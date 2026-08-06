import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { saveFees } from "../../api/billing_wizard.js";
import "../../styles/crown-wizard.css";

const FEE_TYPES = ["REGISTRATION", "TECH", "BOOKS", "ATHLETICS", "OTHER"];

const EMPTY_FEE = () => ({
  name: "",
  fee_type: "REGISTRATION",
  amount: "",
  is_recurring: false,
  grade_level: "",
});

export default function Step3Fees({ context, setContext, goNext, goBack, stepIndex, totalSteps, steps }) {
  const [fees, setFees] = useState(
    context.fees !== null && context.fees !== undefined ? context.fees : [EMPTY_FEE()]
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function updateFee(idx, field, val) {
    setFees((prev) => prev.map((fee, feeIndex) => feeIndex === idx ? { ...fee, [field]: val } : fee));
  }

  function addFee() {
    setFees((prev) => [...prev, EMPTY_FEE()]);
  }

  function removeFee(idx) {
    setFees((prev) => prev.filter((_, feeIndex) => feeIndex !== idx));
  }

  async function handleContinue() {
    for (let i = 0; i < fees.length; i++) {
      if (!fees[i].name.trim()) { setError(`Fee ${i + 1}: name is required.`); return; }
      const amt = Number.parseFloat(fees[i].amount);
      if (Number.isNaN(amt) || amt < 0) { setError(`Fee ${i + 1}: amount must be a valid non-negative number.`); return; }
    }

    setLoading(true);
    setError(null);
    try {
      const normalised = fees.map((fee) => ({
        name: fee.name.trim(),
        fee_type: fee.fee_type,
        amount: Number.parseFloat(fee.amount || 0).toFixed(2),
        is_recurring: !!fee.is_recurring,
        grade_level: fee.grade_level?.trim() || null,
      }));
      const data = await saveFees(context.sessionId, normalised);
      setContext({ ...context, fees: normalised, feesResult: data });
      goNext();
    } catch (e) {
      const errs = e.body?.errors;
      setError(errs ? errs.join("; ") : (e.body?.error || e.message || "Failed to save fees."));
    } finally {
      setLoading(false);
    }
  }

  function handleSkip() {
    // No fees - proceed with empty array
    setFees([]);
    saveFees(context.sessionId, [])
      .then((data) => {
        setContext({ ...context, fees: [], feesResult: data });
        goNext();
      })
      .catch((e) => setError(e.message));
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Define Fees"
        subtitle="Add one-time or recurring fees (registration, tech, books, etc.). Skip if none."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 14 }}>
        {fees.map((fee, idx) => (
          <div key={[fee.name, fee.fee_type, fee.amount, fee.grade_level].join("-")} style={{ border: "1px solid var(--crown-border)", borderRadius: 6, padding: "12px 14px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <span style={{ fontWeight: 600, fontSize: 13 }}>Fee {idx + 1}</span>
              <button className="crown-btn" style={{ fontSize: 11, padding: "2px 8px" }} onClick={() => removeFee(idx)}>
                Remove
              </button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <div style={{ gridColumn: "1 / -1" }}>
                <label htmlFor={`billing-fee-name-${idx}`} style={{ display: "block", fontSize: 11, color: "var(--crown-muted)", marginBottom: 3 }}>Fee Name *</label>
                <input id={`billing-fee-name-${idx}`} className="crown-input" type="text" placeholder="e.g. Registration Fee" value={fee.name}
                  onChange={(e) => updateFee(idx, "name", e.target.value)} style={{ width: "100%", boxSizing: "border-box" }} />
              </div>
              <div>
                <label htmlFor={`billing-fee-type-${idx}`} style={{ display: "block", fontSize: 11, color: "var(--crown-muted)", marginBottom: 3 }}>Type *</label>
                <select id={`billing-fee-type-${idx}`} className="crown-input" value={fee.fee_type} onChange={(e) => updateFee(idx, "fee_type", e.target.value)}
                  style={{ width: "100%", boxSizing: "border-box" }}>
                  {FEE_TYPES.map((feeType) => <option key={feeType} value={feeType}>{feeType}</option>)}
                </select>
              </div>
              <div>
                <label htmlFor={`billing-fee-amount-${idx}`} style={{ display: "block", fontSize: 11, color: "var(--crown-muted)", marginBottom: 3 }}>Amount ($) *</label>
                <input id={`billing-fee-amount-${idx}`} className="crown-input" type="number" min="0" step="0.01" placeholder="250.00" value={fee.amount}
                  onChange={(e) => updateFee(idx, "amount", e.target.value)} style={{ width: "100%", boxSizing: "border-box" }} />
              </div>
              <div>
                <label htmlFor={`billing-fee-grade-level-${idx}`} style={{ display: "block", fontSize: 11, color: "var(--crown-muted)", marginBottom: 3 }}>Grade Level (optional)</label>
                <input id={`billing-fee-grade-level-${idx}`} className="crown-input" type="text" placeholder="e.g. 9, 10, all" value={fee.grade_level}
                  onChange={(e) => updateFee(idx, "grade_level", e.target.value)} style={{ width: "100%", boxSizing: "border-box" }} />
              </div>
              <div style={{ gridColumn: "1 / -1" }}>
                <label htmlFor={`billing-fee-recurring-${idx}`} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, cursor: "pointer" }}>
                  <input id={`billing-fee-recurring-${idx}`} type="checkbox" checked={fee.is_recurring} onChange={(e) => updateFee(idx, "is_recurring", e.target.checked)} />
                  <span>Recurring fee (charged each installment period)</span>
                </label>
              </div>
            </div>
          </div>
        ))}

        <div style={{ display: "flex", gap: 8 }}>
          <button className="crown-btn" onClick={addFee}>+ Add Fee</button>
          <button className="crown-btn" onClick={handleSkip} disabled={loading} style={{ color: "var(--crown-muted)" }}>
            No fees, skip
          </button>
        </div>

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
