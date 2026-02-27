import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { definePeriods } from "../../api/bell_schedule_wizard.js";
import "../../styles/crown-wizard.css";

const EMPTY_PERIOD = { name: "", start_time: "", end_time: "" };

export default function Step2Periods({ context, setContext, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const [periods, setPeriods] = useState(context.periods || [{ ...EMPTY_PERIOD }]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function addPeriod() { setPeriods([...periods, { ...EMPTY_PERIOD }]); }
  function removePeriod(i) { setPeriods(periods.filter((_, idx) => idx !== i)); }
  function updatePeriod(i, field, val) {
    const updated = [...periods];
    updated[i] = { ...updated[i], [field]: val };
    setPeriods(updated);
  }

  async function handleNext() {
    if (periods.length === 0) { setError("At least one period is required."); return; }
    setLoading(true); setError(null);
    try {
      await definePeriods(context.sessionId, periods);
      setContext({ ...context, periods });
      goNext();
    } catch (e) {
      setError(e.body?.errors?.join(", ") || e.body?.error || e.message || "Failed to save periods.");
    } finally { setLoading(false); }
  }

  return (
    <div>
      <CrownWizardStepHeader title="Define Periods" subtitle="Add bell schedule periods with start/end times." stepIndex={stepIndex} totalSteps={totalSteps} steps={steps} />
      {periods.map((p, i) => (
        <div key={i} className="crown-wizard-field" style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
          <input className="crown-input" placeholder="Name" value={p.name} onChange={e => updatePeriod(i, "name", e.target.value)} style={{ flex: 2 }} />
          <input className="crown-input" placeholder="08:00" value={p.start_time} onChange={e => updatePeriod(i, "start_time", e.target.value)} style={{ flex: 1 }} />
          <input className="crown-input" placeholder="08:55" value={p.end_time} onChange={e => updatePeriod(i, "end_time", e.target.value)} style={{ flex: 1 }} />
          <button className="crown-btn" onClick={() => removePeriod(i)} style={{ color: "red" }}>✕</button>
        </div>
      ))}
      <button className="crown-btn" onClick={addPeriod}>+ Add Period</button>
      {error && <p className="crown-error">{error}</p>}
      <div style={{ marginTop: 16 }}>
        <button className="crown-btn" onClick={goPrev}>Back</button>
        <button className="crown-btn crown-btn-primary" onClick={handleNext} disabled={loading} style={{ marginLeft: 8 }}>
          {loading ? "Saving..." : "Next"}
        </button>
      </div>
    </div>
  );
}
