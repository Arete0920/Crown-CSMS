import { useEffect, useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { verifyInvoiceRunSession } from "../../api/invoice_run_wizard.js";
import "../../styles/crown-wizard.css";

const STORAGE_KEY = "crown_invoice_run_wizard_ctx_v1";

export default function Step5Verify({ context, stepIndex, totalSteps, steps }) {
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    verifyInvoiceRunSession(context.sessionId)
      .then(setResult)
      .catch(e => setError(e.body?.error || e.message || "Verification failed."));
  }, [context.sessionId]);

  function handleReset() { sessionStorage.removeItem(STORAGE_KEY); window.location.reload(); }

  return (
    <div>
      <CrownWizardStepHeader title="Verify" subtitle="Invoice run complete." stepIndex={stepIndex} totalSteps={totalSteps} steps={steps} />
      {error && <p className="crown-error">{error}</p>}
      {result && (
        <div className="crown-success-box">
          <p>✓ <strong>{result.invoice_count}</strong> invoice(s) generated.</p>
          <p>Period: {result.period_start} → {result.period_end}</p>
          <p>Status: {result.status}</p>
        </div>
      )}
      <button className="crown-btn" onClick={handleReset} style={{ marginTop: 16 }}>Start New Invoice Run</button>
    </div>
  );
}
