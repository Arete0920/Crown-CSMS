import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { createGradebookSetupSession, configureGradebookSetupSession } from "../../api/gradebook_setup_wizard.js";
import "../../styles/crown-wizard.css";

export default function Step1Configure({ context, setContext, goNext, stepIndex, totalSteps, steps }) {
  const [sectionId, setSectionId] = useState(context.section_id || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleNext() {
    if (!sectionId.trim()) { setError("Section ID is required."); return; }
    setLoading(true); setError(null);
    try {
      let sessionId = context.sessionId;
      if (!sessionId) {
        const created = await createGradebookSetupSession();
        sessionId = created.session_id;
      }
      await configureGradebookSetupSession(sessionId, sectionId.trim());
      setContext({ ...context, sessionId, section_id: sectionId.trim() });
      goNext();
    } catch (e) {
      setError(e.body?.error || e.message || "Failed to configure session.");
    } finally { setLoading(false); }
  }

  return (
    <div>
      <CrownWizardStepHeader title="Select Section" subtitle="Enter the section UUID for gradebook category setup." stepIndex={stepIndex} totalSteps={totalSteps} steps={steps} />
      <div className="crown-wizard-field">
        <label>Section ID (UUID)</label>
        <input className="crown-input" value={sectionId} onChange={e => setSectionId(e.target.value)} placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
      </div>
      {error && <p className="crown-error">{error}</p>}
      <button className="crown-btn crown-btn-primary" onClick={handleNext} disabled={loading}>
        {loading ? "Saving..." : "Next"}
      </button>
    </div>
  );
}
