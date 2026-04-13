import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { createBellScheduleSession, configureBellScheduleSession } from "../../api/bell_schedule_wizard.js";
import "../../styles/crown-wizard.css";

export default function Step1Configure({ context, setContext, goNext, stepIndex, totalSteps, steps }) {
  const [label, setLabel] = useState(context.label || "");
  const [schoolYear, setSchoolYear] = useState(context.school_year || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleNext() {
    if (!label.trim()) { setError("Label is required."); return; }
    if (!schoolYear.trim()) { setError("School year is required."); return; }
    setLoading(true); setError(null);
    try {
      let sessionId = context.sessionId;
      if (!sessionId) {
        const created = await createBellScheduleSession();
        sessionId = created.session_id;
      }
      await configureBellScheduleSession(sessionId, label.trim(), schoolYear.trim());
      setContext({ ...context, sessionId, label: label.trim(), school_year: schoolYear.trim() });
      goNext();
    } catch (e) {
      setError(e.body?.error || e.message || "Failed to configure session.");
    } finally { setLoading(false); }
  }

  return (
    <div>
      <CrownWizardStepHeader title="Label & Year" subtitle="Name this bell schedule and enter the school year." stepIndex={stepIndex} totalSteps={totalSteps} steps={steps} />
      <div className="crown-wizard-field">
        <label htmlFor="bell-schedule-label">Schedule Label</label>
        <input id="bell-schedule-label" className="crown-input" value={label} onChange={e => setLabel(e.target.value)} placeholder="e.g. Standard Day Schedule" />
      </div>
      <div className="crown-wizard-field">
        <label htmlFor="bell-schedule-school-year">School Year</label>
        <input id="bell-schedule-school-year" className="crown-input" value={schoolYear} onChange={e => setSchoolYear(e.target.value)} placeholder="e.g. 2026-2027" />
      </div>
      {error && <p className="crown-error">{error}</p>}
      <button className="crown-btn crown-btn-primary" onClick={handleNext} disabled={loading}>
        {loading ? "Saving..." : "Next"}
      </button>
    </div>
  );
}