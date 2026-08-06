import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import "../../styles/crown-wizard.css";

export default function Step3Preview({ context, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const codes = context.codes || [];
  return (
    <div>
      <CrownWizardStepHeader title="Preview" subtitle="Review attendance codes before committing." stepIndex={stepIndex} totalSteps={totalSteps} steps={steps} />
      <p><strong>Label:</strong> {context.label}</p>
      <p><strong>School Year:</strong> {context.school_year}</p>
      <table className="crown-table">
        <thead><tr><th>Code</th><th>Label</th><th>Excused</th><th>Counts Absent</th></tr></thead>
        <tbody>
          {codes.map((c, i) => (
            <tr key={i}>
              <td><code>{c.code}</code></td>
              <td>{c.label}</td>
              <td>{c.excused ? "Yes" : "No"}</td>
              <td>{c.counts_absent ? "Yes" : "No"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ marginTop: 16 }}>
        <button className="crown-btn" onClick={goPrev}>Back</button>
        <button className="crown-btn crown-btn-primary" onClick={goNext} style={{ marginLeft: 8 }}>Confirm & Commit</button>
      </div>
    </div>
  );
}
