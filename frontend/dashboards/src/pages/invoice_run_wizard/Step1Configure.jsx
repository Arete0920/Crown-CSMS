import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { createInvoiceRunSession, configureInvoiceRunSession } from "../../api/invoice_run_wizard.js";
import "../../styles/crown-wizard.css";

export default function Step1Configure({ context, setContext, goNext, stepIndex, totalSteps, steps }) {
  const [periodStart, setPeriodStart] = useState(context.period_start || "");
  const [periodEnd, setPeriodEnd] = useState(context.period_end || "");
  const [dueDate, setDueDate] = useState(context.due_date || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleNext() {
    if (!periodStart) { setError("Period start date is required."); return; }
    if (!periodEnd) { setError("Period end date is required."); return; }
    if (!dueDate) { setError("Due date is required."); return; }
    setLoading(true); setError(null);
    try {
      let sessionId = context.sessionId;
      if (!sessionId) {
        const created = await createInvoiceRunSession();
        sessionId = created.session_id;
      }
      await configureInvoiceRunSession(sessionId, periodStart, periodEnd, dueDate);
      setContext({ ...context, sessionId, period_start: periodStart, period_end: periodEnd, due_date: dueDate });
      goNext();
    } catch (e) {
      setError(e.body?.error || e.message || "Failed to configure session.");
    } finally { setLoading(false); }
  }

  return (
    <div>
      <CrownWizardStepHeader title="Configure Period" subtitle="Set billing period dates and invoice due date." stepIndex={stepIndex} totalSteps={totalSteps} steps={steps} />
      <div className="crown-wizard-field">
        <div>Period Start</div>
        <input className="crown-input" type="date" value={periodStart} onChange={e => setPeriodStart(e.target.value)} />
      </div>
      <div className="crown-wizard-field">
        <div>Period End</div>
        <input className="crown-input" type="date" value={periodEnd} onChange={e => setPeriodEnd(e.target.value)} />
      </div>
      <div className="crown-wizard-field">
        <div>Due Date</div>
        <input className="crown-input" type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} />
      </div>
      {error && <p className="crown-error">{error}</p>}
      <button className="crown-btn crown-btn-primary" onClick={handleNext} disabled={loading}>
        {loading ? "Saving..." : "Next"}
      </button>
    </div>
  );
}
