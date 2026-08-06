import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { commitInvoiceRunSession } from "../../api/invoice_run_wizard.js";
import "../../styles/crown-wizard.css";

export default function Step4Commit({ context, setContext, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleCommit() {
    setLoading(true); setError(null);
    try {
      const result = await commitInvoiceRunSession(context.sessionId);
      setContext({ ...context, commitResult: result });
      goNext();
    } catch (e) {
      setError(e.body?.error || e.message || "Commit failed.");
    } finally { setLoading(false); }
  }

  return (
    <div>
      <CrownWizardStepHeader title="Commit" subtitle="Generate invoices. This action cannot be undone." stepIndex={stepIndex} totalSteps={totalSteps} steps={steps} />
      <p>Processing <strong>{context.obligation_count}</strong> obligation(s) into invoices.</p>
      <p>Due date: <strong>{context.due_date}</strong></p>
      {error && <p className="crown-error">{error}</p>}
      <div style={{ marginTop: 16 }}>
        <button className="crown-btn" onClick={goPrev} disabled={loading}>Back</button>
        <button className="crown-btn crown-btn-primary" onClick={handleCommit} disabled={loading} style={{ marginLeft: 8 }}>
          {loading ? "Generating Invoices..." : "Generate Invoices"}
        </button>
      </div>
    </div>
  );
}
