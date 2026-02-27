import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { commitSectionAssign } from "../../api/section_assign_wizard.js";
import "../../styles/crown-wizard.css";

export default function Step5Commit({ context, setContext, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const [confirmed, setConfirmed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const changes = context.roster_changes || [];
  const adds = changes.filter((c) => c.action === "add");
  const removes = changes.filter((c) => c.action === "remove");

  async function handleCommit() {
    if (!confirmed) { setError("Please check the confirmation box before committing."); return; }

    setLoading(true);
    setError(null);
    try {
      const data = await commitSectionAssign(context.sessionId);
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
        subtitle="Write enrollment records to the database. This action is idempotent and safe to repeat."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={{ padding: "12px 16px", background: "var(--crown-surface)", border: "1px solid var(--crown-border)", borderRadius: 6, fontSize: 13 }}>
          <div><strong>Section:</strong> {context.section_id || "—"}</div>
          <div style={{ marginTop: 4 }}><strong>Term:</strong> {context.term || "—"}</div>
          <div style={{ marginTop: 8, fontWeight: 600 }}>
            {adds.length} enrollment{adds.length !== 1 ? "s" : ""} to add &nbsp;·&nbsp; {removes.length} to remove
          </div>
        </div>

        <label style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 13, cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
          />
          I confirm these enrollment changes are correct and ready to commit.
        </label>

        {error && <div className="crown-alert">{error}</div>}

        <div style={{ display: "flex", gap: 12 }}>
          <button className="crown-btn" onClick={goPrev} disabled={loading}>← Back</button>
          <button
            className="crown-btn crown-btn-primary"
            onClick={handleCommit}
            disabled={loading || !confirmed}
          >
            {loading ? "Committing…" : "Commit Enrollments"}
          </button>
        </div>
      </div>
    </div>
  );
}
