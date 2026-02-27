import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import "../../styles/crown-wizard.css";

export default function Step3Preview({ context, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const categories = context.categories || [];
  const totalWeight = categories.reduce((sum, c) => sum + (c.weight_percent || 0), 0);
  return (
    <div>
      <CrownWizardStepHeader title="Preview" subtitle="Review gradebook categories before committing." stepIndex={stepIndex} totalSteps={totalSteps} steps={steps} />
      <p><strong>Section ID:</strong> {context.section_id}</p>
      <p><strong>Categories:</strong> {categories.length}</p>
      <table className="crown-table">
        <thead><tr><th>#</th><th>Name</th><th>Weight %</th><th>Sort</th></tr></thead>
        <tbody>
          {categories.map((c, i) => (
            <tr key={i}><td>{i + 1}</td><td>{c.name}</td><td>{c.weight_percent}</td><td>{c.sort_order}</td></tr>
          ))}
        </tbody>
        <tfoot><tr><td colSpan={2}><strong>Total</strong></td><td>{totalWeight}%</td><td></td></tr></tfoot>
      </table>
      <div style={{ marginTop: 16 }}>
        <button className="crown-btn" onClick={goPrev}>Back</button>
        <button className="crown-btn crown-btn-primary" onClick={goNext} style={{ marginLeft: 8 }}>Confirm & Commit</button>
      </div>
    </div>
  );
}
