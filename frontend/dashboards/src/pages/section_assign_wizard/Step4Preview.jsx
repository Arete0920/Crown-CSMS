import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import "../../styles/crown-wizard.css";

export default function Step4Preview({ context, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const changes = context.roster_changes || [];
  const adds = changes.filter((c) => c.action === "add");
  const removes = changes.filter((c) => c.action === "remove");

  return (
    <div>
      <CrownWizardStepHeader
        title="Preview"
        subtitle="Review staged changes before committing to the enrollment database."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 16, maxWidth: 600 }}>
        <div style={{ padding: "12px 16px", background: "var(--crown-surface)", border: "1px solid var(--crown-border)", borderRadius: 6, fontSize: 13 }}>
          <div><strong>Section:</strong> {context.section_id || "—"}</div>
          <div style={{ marginTop: 4 }}><strong>Term:</strong> {context.term || "—"}</div>
          <div style={{ marginTop: 8, fontWeight: 600 }}>
            {adds.length} to add &nbsp;·&nbsp; {removes.length} to remove
          </div>
        </div>

        {adds.length > 0 && (
          <div>
            <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 6, color: "var(--crown-ok)" }}>Adding ({adds.length})</div>
            <ul style={{ margin: 0, padding: "0 0 0 18px", fontSize: 12, fontFamily: "var(--crown-font-mono)" }}>
              {adds.map((c) => <li key={c.student_id}>{c.student_id}</li>)}
            </ul>
          </div>
        )}

        {removes.length > 0 && (
          <div>
            <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 6, color: "var(--crown-danger)" }}>Removing ({removes.length})</div>
            <ul style={{ margin: 0, padding: "0 0 0 18px", fontSize: 12, fontFamily: "var(--crown-font-mono)" }}>
              {removes.map((c) => <li key={c.student_id}>{c.student_id}</li>)}
            </ul>
          </div>
        )}

        <div style={{ display: "flex", gap: 12 }}>
          <button className="crown-btn" onClick={goPrev}>← Back</button>
          <button className="crown-btn crown-btn-primary" onClick={goNext}>Commit →</button>
        </div>
      </div>
    </div>
  );
}
