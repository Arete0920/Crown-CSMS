import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { createBillingWizardSession, configureWizardSession } from "../../api/billing_wizard.js";
import "../../styles/crown-wizard.css";

const BILLING_MODES = [
  { value: "simple", label: "Simple", desc: "One tuition plan + basic fees. Best for most schools." },
  { value: "advanced", label: "Advanced", desc: "Multiple plans, grade-level fees, custom schedules." },
];

export default function Step1Mode({ context, setContext, goNext, stepIndex, totalSteps, steps }) {
  const [term, setTerm] = useState(context.term || "");
  const [mode, setMode] = useState(context.billingMode || "simple");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleContinue() {
    if (!term.trim()) { setError("Term is required (e.g. 2026-FALL)."); return; }
    if (term.trim().length > 24) { setError("Term must be 24 characters or fewer."); return; }

    setLoading(true);
    setError(null);
    try {
      let sessionId = context.sessionId;
      if (!sessionId) {
        const created = await createBillingWizardSession();
        sessionId = created.session_id;
      }
      const data = await configureWizardSession(sessionId, term.trim(), mode);
      setContext({
        sessionId,
        term: term.trim(),
        billingMode: mode,
        configure: data,
        plans: null,
        fees: null,
        commit: null,
        verify: null,
      });
      goNext();
    } catch (e) {
      setError(e.body?.error || e.message || "Configuration failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Mode & Term"
        subtitle="Select the billing mode and set the term label for this billing setup."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 18 }}>
        <div>
          <label htmlFor="billing-term" style={{ display: "block", fontSize: 12, color: "var(--crown-muted)", marginBottom: 4 }}>
            Billing Term *
          </label>
          <input
            id="billing-term"
            className="crown-input"
            type="text"
            placeholder="e.g. 2026-FALL"
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            maxLength={24}
            style={{ width: "100%", boxSizing: "border-box" }}
          />
          <span style={{ fontSize: 11, color: "var(--crown-muted)" }}>Max 24 characters. Used as the term key on billing records.</span>
        </div>

        <fieldset style={{ border: 0, margin: 0, padding: 0 }}>
          <legend style={{ fontSize: 12, color: "var(--crown-muted)", marginBottom: 8 }}>
            Billing Mode *
          </legend>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {BILLING_MODES.map((billingModeOption) => (
              <div
                key={billingModeOption.value}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: 10,
                  padding: "10px 12px",
                  border: `1px solid ${mode === billingModeOption.value ? "var(--crown-primary)" : "var(--crown-border)"}`,
                  borderRadius: 6,
                  background: mode === billingModeOption.value ? "var(--crown-surface-2)" : "transparent",
                }}
              >
                <input
                  id={`billing-mode-${billingModeOption.value}`}
                  type="radio"
                  name="billing_mode"
                  value={billingModeOption.value}
                  checked={mode === billingModeOption.value}
                  onChange={() => setMode(billingModeOption.value)}
                  style={{ marginTop: 2 }}
                />
                <label htmlFor={`billing-mode-${billingModeOption.value}`} style={{ cursor: "pointer" }}>
                  <div style={{ fontWeight: 600, fontSize: 13 }}>{billingModeOption.label}</div>
                  <div style={{ fontSize: 12, color: "var(--crown-muted)", marginTop: 2 }}>{billingModeOption.desc}</div>
                </label>
              </div>
            ))}
          </div>
        </fieldset>

        {error && <div className="crown-alert">{error}</div>}
      </div>

      <div className="crown-wizard-actions">
        <span className="crown-muted" style={{ fontSize: 12 }}>Step {stepIndex + 1} of {totalSteps}</span>
        <div className="crown-wizard-actions-right">
          <button className="crown-btn crown-btn-primary" onClick={handleContinue} disabled={loading}>
            {loading ? "Saving..." : "Continue"}
          </button>
        </div>
      </div>
    </div>
  );
}