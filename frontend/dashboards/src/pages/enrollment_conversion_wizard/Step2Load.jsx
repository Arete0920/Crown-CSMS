import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { loadApplicants } from "../../api/enrollment_conversion_wizard.js";
import "../../styles/crown-wizard.css";

export default function Step2Load({ context, setContext, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const [loaded, setLoaded] = useState(context.applicant_count != null);
  const [applicantCount, setApplicantCount] = useState(context.applicant_count || 0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleLoad() {
    setLoading(true); setError(null);
    try {
      const result = await loadApplicants(context.sessionId);
      setApplicantCount(result.applicant_count);
      setContext({ ...context, applicant_count: result.applicant_count });
      setLoaded(true);
    } catch (e) {
      setError(e.body?.error || e.message || "Failed to load applicants.");
    } finally { setLoading(false); }
  }

  return (
    <div>
      <CrownWizardStepHeader title="Load Applicants" subtitle="Load applicants matching your configuration." stepIndex={stepIndex} totalSteps={totalSteps} steps={steps} />
      <p>Year: <strong>{context.academic_year_label}</strong> | Status: <strong>{context.from_status}</strong></p>
      <button className="crown-btn" onClick={handleLoad} disabled={loading}>
        {loading ? "Loading..." : "Load Applicants"}
      </button>
      {loaded && <p style={{ marginTop: 8 }}>Found <strong>{applicantCount}</strong> applicant(s) to convert.</p>}
      {error && <p className="crown-error">{error}</p>}
      <div style={{ marginTop: 16 }}>
        <button className="crown-btn" onClick={goPrev}>Back</button>
        <button className="crown-btn crown-btn-primary" onClick={goNext} disabled={!loaded} style={{ marginLeft: 8 }}>Next</button>
      </div>
    </div>
  );
}
