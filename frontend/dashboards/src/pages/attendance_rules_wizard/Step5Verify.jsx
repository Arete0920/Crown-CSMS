import { useEffect, useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { verifyAttendanceRulesSession } from "../../api/attendance_rules_wizard.js";
import "../../styles/crown-wizard.css";

const STORAGE_KEY = "crown_attendance_rules_wizard_ctx_v1";

export default function Step5Verify({ context, stepIndex, totalSteps, steps }) {
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    verifyAttendanceRulesSession(context.sessionId)
      .then(setResult)
      .catch(e => setError(e.body?.error || e.message || "Verification failed."));
  }, [context.sessionId]);

  function handleReset() { sessionStorage.removeItem(STORAGE_KEY); window.location.reload(); }

  return (
    <div>
      <CrownWizardStepHeader title="Verify" subtitle="Attendance rules committed." stepIndex={stepIndex} totalSteps={totalSteps} steps={steps} />
      {error && <p className="crown-error">{error}</p>}
      {result && (
        <div className="crown-success-box">
          <p>✓ <strong>{result.label}</strong> committed with <strong>{result.code_count}</strong> codes.</p>
          <p>School Year: {result.school_year}</p>
          <p>Status: {result.status}</p>
        </div>
      )}
      <button className="crown-btn" onClick={handleReset} style={{ marginTop: 16 }}>Start New Ruleset</button>
    </div>
  );
}
