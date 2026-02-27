import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { createEnrollmentConversionSession, configureEnrollmentConversionSession } from "../../api/enrollment_conversion_wizard.js";
import "../../styles/crown-wizard.css";

const FROM_STATUS_OPTIONS = ["ACCEPTED", "WAITLISTED"];

export default function Step1Configure({ context, setContext, goNext, stepIndex, totalSteps, steps }) {
  const [academicYearLabel, setAcademicYearLabel] = useState(context.academic_year_label || "");
  const [fromStatus, setFromStatus] = useState(context.from_status || "ACCEPTED");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleNext() {
    if (!academicYearLabel.trim()) { setError("Academic year label is required."); return; }
    setLoading(true); setError(null);
    try {
      let sessionId = context.sessionId;
      if (!sessionId) {
        const created = await createEnrollmentConversionSession();
        sessionId = created.session_id;
      }
      await configureEnrollmentConversionSession(sessionId, academicYearLabel.trim(), fromStatus);
      setContext({ ...context, sessionId, academic_year_label: academicYearLabel.trim(), from_status: fromStatus });
      goNext();
    } catch (e) {
      setError(e.body?.error || e.message || "Failed to configure session.");
    } finally { setLoading(false); }
  }

  return (
    <div>
      <CrownWizardStepHeader title="Configure" subtitle="Set the academic year and source application status." stepIndex={stepIndex} totalSteps={totalSteps} steps={steps} />
      <div className="crown-wizard-field">
        <label>Academic Year</label>
        <input className="crown-input" value={academicYearLabel} onChange={e => setAcademicYearLabel(e.target.value)} placeholder="e.g. 2026-2027" />
      </div>
      <div className="crown-wizard-field">
        <label>Convert From Status</label>
        <select className="crown-input" value={fromStatus} onChange={e => setFromStatus(e.target.value)}>
          {FROM_STATUS_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
      {error && <p className="crown-error">{error}</p>}
      <button className="crown-btn crown-btn-primary" onClick={handleNext} disabled={loading}>
        {loading ? "Saving..." : "Next"}
      </button>
    </div>
  );
}
