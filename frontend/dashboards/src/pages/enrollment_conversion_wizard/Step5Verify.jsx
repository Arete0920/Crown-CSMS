import { useEffect, useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { verifyEnrollmentConversionSession, finalizeEnrollmentConversionVerification } from "../../api/enrollment_conversion_wizard.js";
import "../../styles/crown-wizard.css";

const STORAGE_KEY = "crown_enrollment_conversion_wizard_ctx_v1";

export default function Step5Verify({ context, stepIndex, totalSteps, steps }) {
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    verifyEnrollmentConversionSession(context.sessionId)
      .then(setResult)
      .catch(e => setError(e.body?.error || e.message || "Verification failed."));
  }, [context.sessionId]);

  async function recordVerification() {
    setSaving(true);
    setError(null);
    try {
      setResult(await finalizeEnrollmentConversionVerification(context.sessionId));
    } catch (e) {
      setError(e.body?.error || e.message || "Verification failed.");
    } finally {
      setSaving(false);
    }
  }

  function handleReset() { sessionStorage.removeItem(STORAGE_KEY); window.location.reload(); }

  return (
    <div>
      <CrownWizardStepHeader title="Verify" subtitle="Enrollment conversion complete." stepIndex={stepIndex} totalSteps={totalSteps} steps={steps} />
      {error && <p className="crown-error">{error}</p>}
      {result && (
        <div className="crown-success-box">
          <p>✓ <strong>{result.enrolled_count}</strong> applicant(s) enrolled.</p>
          <p>Academic Year: {result.academic_year_label}</p>
          <p>Status: {result.status}</p>
        </div>
      )}
      {result?.all_enrolled && result.status !== "verified" && (
        <button className="crown-btn" onClick={recordVerification} disabled={saving} type="button">
          {saving ? "Recording..." : "Record Verified Status"}
        </button>
      )}
      <button className="crown-btn" onClick={handleReset} style={{ marginTop: 16 }}>Start New Conversion</button>
    </div>
  );
}
