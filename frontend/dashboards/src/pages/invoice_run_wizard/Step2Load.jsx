import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { loadObligations } from "../../api/invoice_run_wizard.js";
import "../../styles/crown-wizard.css";

export default function Step2Load({ context, setContext, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const [loaded, setLoaded] = useState(context.obligation_count != null);
  const [obligationCount, setObligationCount] = useState(context.obligation_count || 0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleLoad() {
    setLoading(true); setError(null);
    try {
      const result = await loadObligations(context.sessionId);
      setObligationCount(result.obligation_count);
      setContext({ ...context, obligation_count: result.obligation_count });
      setLoaded(true);
    } catch (e) {
      setError(e.body?.error || e.message || "Failed to load obligations.");
    } finally { setLoading(false); }
  }

  return (
    <div>
      <CrownWizardStepHeader title="Load Obligations" subtitle="Load open billing obligations for this period." stepIndex={stepIndex} totalSteps={totalSteps} steps={steps} />
      <p>Period: <strong>{context.period_start}</strong> → <strong>{context.period_end}</strong></p>
      <button className="crown-btn" onClick={handleLoad} disabled={loading}>
        {loading ? "Loading..." : "Load Open Obligations"}
      </button>
      {loaded && <p style={{ marginTop: 8 }}>Found <strong>{obligationCount}</strong> open obligation(s).</p>}
      {error && <p className="crown-error">{error}</p>}
      <div style={{ marginTop: 16 }}>
        <button className="crown-btn" onClick={goPrev}>Back</button>
        <button className="crown-btn crown-btn-primary" onClick={goNext} disabled={!loaded} style={{ marginLeft: 8 }}>Next</button>
      </div>
    </div>
  );
}
