import { useEffect, useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { verifyBellScheduleSession } from "../../api/bell_schedule_wizard.js";
import "../../styles/crown-wizard.css";

const STORAGE_KEY = "crown_bell_schedule_wizard_ctx_v1";

export default function Step5Verify({ context, stepIndex, totalSteps, steps }) {
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    verifyBellScheduleSession(context.sessionId)
      .then(setResult)
      .catch(e => setError(e.body?.error || e.message || "Verification failed."));
  }, [context.sessionId]);

  function handleReset() { sessionStorage.removeItem(STORAGE_KEY); window.location.reload(); }

  return (
    <div>
      <CrownWizardStepHeader title="Verify" subtitle="Bell schedule confirmed." stepIndex={stepIndex} totalSteps={totalSteps} steps={steps} />
      {error && <p className="crown-error">{error}</p>}
      {result && (
        <div className="crown-success-box">
          <p>✓ <strong>{result.label}</strong> committed with <strong>{result.period_count}</strong> periods.</p>
          <p>School Year: {result.school_year}</p>
          <p>Status: {result.status}</p>
        </div>
      )}
      <button className="crown-btn" onClick={handleReset} style={{ marginTop: 16 }}>Start New Schedule</button>
    </div>
  );
}
