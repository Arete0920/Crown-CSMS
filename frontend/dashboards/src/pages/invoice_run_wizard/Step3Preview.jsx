import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import "../../styles/crown-wizard.css";

export default function Step3Preview({ context, goNext, goPrev, stepIndex, totalSteps, steps }) {
  return (
    <div>
      <CrownWizardStepHeader title="Preview" subtitle="Review invoice run before committing." stepIndex={stepIndex} totalSteps={totalSteps} steps={steps} />
      <p><strong>Period:</strong> {context.period_start} → {context.period_end}</p>
      <p><strong>Due Date:</strong> {context.due_date}</p>
      <p><strong>Open Obligations:</strong> {context.obligation_count}</p>
      <p style={{ color: "#856404", background: "#fff3cd", padding: 8, borderRadius: 4 }}>
        Invoices will be grouped by payer. One invoice per payer will be created or updated.
      </p>
      <div style={{ marginTop: 16 }}>
        <button className="crown-btn" onClick={goPrev}>Back</button>
        <button className="crown-btn crown-btn-primary" onClick={goNext} style={{ marginLeft: 8 }}>Confirm & Commit</button>
      </div>
    </div>
  );
}
