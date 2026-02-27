import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { commitGradebookSetupSession } from "../../api/gradebook_setup_wizard.js";
import "../../styles/crown-wizard.css";

export default function Step4Commit({ context, setContext, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleCommit() {
    setLoading(true); setError(null);
    try {
      const result = await commitGradebookSetupSession(context.sessionId);
      setContext({ ...context, commitResult: result });
      goNext();
    } catch (e) {
      setError(e.body?.error || e.message || "Commit failed.");
    } finally { setLoading(false); }
  }

  return (
    <div>
      <CrownWizardStepHeader title="Commit" subtitle="Save gradebook categories to the database." stepIndex={stepIndex} totalSteps={totalSteps} steps={steps} />
      <p>Committing <strong>{(context.categories || []).length}</strong> categories for section <code>{context.section_id}</code>.</p>
      {error && <p className="crown-error">{error}</p>}
      <div style={{ marginTop: 16 }}>
        <button className="crown-btn" onClick={goPrev} disabled={loading}>Back</button>
        <button className="crown-btn crown-btn-primary" onClick={handleCommit} disabled={loading} style={{ marginLeft: 8 }}>
          {loading ? "Committing..." : "Commit"}
        </button>
      </div>
    </div>
  );
}
