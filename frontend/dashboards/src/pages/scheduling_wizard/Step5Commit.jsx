import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { commitSchedulingSetup } from "../../api/scheduling_wizard.js";
import "../../styles/crown-wizard.css";

export default function Step5Commit({ context, setContext, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const [confirmed, setConfirmed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const courses = context.courses || [];
  const sections = context.sections || [];

  async function handleCommit() {
    if (!confirmed) { setError("Please check the confirmation box before committing."); return; }

    setLoading(true);
    setError(null);
    try {
      const data = await commitSchedulingSetup(context.sessionId);
      setContext({ ...context, commit: data });
      goNext();
    } catch (e) {
      setError(e.body?.error || e.message || "Commit failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Commit"
        subtitle="Write courses and sections to the database. This action is idempotent and safe to repeat."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 16 }}>
        {/* Summary */}
        <div style={{ padding: "12px 16px", background: "var(--crown-surface)", border: "1px solid var(--crown-border)", borderRadius: 6, fontSize: 13 }}>
          <div><strong>Term:</strong> {context.term || "—"}</div>
          <div style={{ marginTop: 4 }}><strong>School Year:</strong> {context.schoolYear || "—"}</div>
          <div style={{ marginTop: 4 }}><strong>Courses:</strong> {courses.length}</div>
          <div style={{ marginTop: 4 }}><strong>Sections:</strong> {sections.length}</div>
        </div>

        {/* Confirmation */}
        <label style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 13, cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
          />
          I confirm this scheduling setup is correct and ready to commit.
        </label>

        {error && <div className="crown-alert">{error}</div>}

        <div style={{ display: "flex", gap: 12 }}>
          <button className="crown-btn" onClick={goPrev} disabled={loading}>← Back</button>
          <button
            className="crown-btn crown-btn-primary"
            onClick={handleCommit}
            disabled={loading || !confirmed}
          >
            {loading ? "Committing…" : "Commit Schedule"}
          </button>
        </div>
      </div>
    </div>
  );
}
