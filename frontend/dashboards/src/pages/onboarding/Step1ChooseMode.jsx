import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import "../../styles/crown-wizard.css";

const MODES = [
  { value: "students_guardians", label: "Students + Guardians", description: "Import students and linked guardian/household records from a single CSV." },
  { value: "staff", label: "Staff", description: "Import staff accounts (teachers, counselors, administrators)." },
  { value: "contacts", label: "Contacts Only", description: "Import additional contacts not tied to enrollment." },
];

export default function Step1ChooseMode({ context, setContext, goNext, stepIndex, totalSteps, steps }) {
  const [mode, setMode] = useState(context.mode || "students_guardians");

  function handleContinue() {
    setContext({ mode, importId: null, upload: null, validate: null, preview: null, commit: null, verify: null });
    goNext();
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Choose Import Type"
        subtitle="Select what kind of records you are importing."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 10 }}>
        {MODES.map((m) => (
          <div
            key={m.value}
            className="crown-card"
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: 10,
              cursor: "pointer",
              padding: "14px 16px",
              border: mode === m.value ? "1.5px solid var(--crown-gold)" : undefined,
            }}
          >
            <input
              type="radio"
              name="mode"
              value={m.value}
              checked={mode === m.value}
              onChange={() => setMode(m.value)}
              style={{ marginTop: 3 }}
            />
            <span>
              <span style={{ fontWeight: 600, color: "var(--crown-text)" }}>{m.label}</span>
              <span style={{ display: "block", fontSize: 12, color: "var(--crown-muted)", marginTop: 4 }}>{m.description}</span>
            </span>
          </div>
        ))}
      </div>

      <div className="crown-wizard-actions">
        <span className="crown-muted" style={{ fontSize: 12 }}>Step {stepIndex + 1} of {totalSteps}</span>
        <div className="crown-wizard-actions-right">
          <button className="crown-btn crown-btn-primary" onClick={handleContinue}>
            Continue →
          </button>
        </div>
      </div>
    </div>
  );
}
