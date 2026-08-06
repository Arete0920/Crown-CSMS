import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import "../../styles/crown-wizard.css";

export default function Step3Preview({ context, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const periods = context.periods || [];
  return (
    <div>
      <CrownWizardStepHeader title="Preview" subtitle="Review your bell schedule before committing." stepIndex={stepIndex} totalSteps={totalSteps} steps={steps} />
      <p><strong>Label:</strong> {context.label}</p>
      <p><strong>School Year:</strong> {context.school_year}</p>
      <p><strong>Periods:</strong> {periods.length}</p>
      <ul>
        {periods.map((p, i) => (
          <li key={i}>{p.name} — {p.start_time} to {p.end_time}</li>
        ))}
      </ul>
      <div style={{ marginTop: 16 }}>
        <button className="crown-btn" onClick={goPrev}>Back</button>
        <button className="crown-btn crown-btn-primary" onClick={goNext} style={{ marginLeft: 8 }}>Confirm & Commit</button>
      </div>
    </div>
  );
}
