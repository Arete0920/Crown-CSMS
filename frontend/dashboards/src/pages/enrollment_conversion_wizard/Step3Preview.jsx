import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import "../../styles/crown-wizard.css";

export default function Step3Preview({ context, goNext, goPrev, stepIndex, totalSteps, steps }) {
  return (
    <div>
      <CrownWizardStepHeader title="Preview" subtitle="Confirm conversion before committing." stepIndex={stepIndex} totalSteps={totalSteps} steps={steps} />
      <div className="crown-warning-box" style={{ padding: 16, background: "#fff3cd", borderRadius: 6, marginBottom: 16 }}>
        <p>⚠ This will convert <strong>{context.applicant_count}</strong> applicant(s) from <strong>{context.from_status}</strong> to <strong>ENROLLED</strong>.</p>
        <p>Academic Year: <strong>{context.academic_year_label}</strong></p>
        <p>This action cannot be undone.</p>
      </div>
      <div style={{ marginTop: 16 }}>
        <button className="crown-btn" onClick={goPrev}>Back</button>
        <button className="crown-btn crown-btn-primary" onClick={goNext} style={{ marginLeft: 8 }}>Confirm & Commit</button>
      </div>
    </div>
  );
}
