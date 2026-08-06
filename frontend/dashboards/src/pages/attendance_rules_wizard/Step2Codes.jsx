import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { defineCodes } from "../../api/attendance_rules_wizard.js";
import "../../styles/crown-wizard.css";

const EMPTY_CODE = { code: "", label: "", excused: false, counts_absent: true };

export default function Step2Codes({ context, setContext, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const [codes, setCodes] = useState(context.codes || [{ ...EMPTY_CODE }]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function addCode() { setCodes([...codes, { ...EMPTY_CODE }]); }
  function removeCode(i) { setCodes(codes.filter((_, idx) => idx !== i)); }
  function updateCode(i, field, val) {
    const updated = [...codes];
    updated[i] = { ...updated[i], [field]: val };
    if (field === "code") updated[i].code = val.toUpperCase().slice(0, 8);
    setCodes(updated);
  }

  async function handleNext() {
    if (codes.length === 0) { setError("At least one code is required."); return; }
    setLoading(true); setError(null);
    try {
      await defineCodes(context.sessionId, codes);
      setContext({ ...context, codes });
      goNext();
    } catch (e) {
      setError(e.body?.error || e.message || "Failed to save codes.");
    } finally { setLoading(false); }
  }

  return (
    <div>
      <CrownWizardStepHeader title="Define Codes" subtitle="Add attendance codes. Max 8 chars, codes auto-uppercased." stepIndex={stepIndex} totalSteps={totalSteps} steps={steps} />
      {codes.map((c, i) => (
        <div key={i} style={{ display: "flex", gap: 8, marginBottom: 8, alignItems: "center" }}>
          <input className="crown-input" placeholder="CODE" maxLength={8} value={c.code} onChange={e => updateCode(i, "code", e.target.value)} style={{ flex: 1, textTransform: "uppercase" }} />
          <input className="crown-input" placeholder="Label" value={c.label} onChange={e => updateCode(i, "label", e.target.value)} style={{ flex: 2 }} />
          <label style={{ display: "flex", gap: 4, alignItems: "center", whiteSpace: "nowrap" }}>
            <input type="checkbox" checked={c.excused} onChange={e => updateCode(i, "excused", e.target.checked)} /> Excused
          </label>
          <label style={{ display: "flex", gap: 4, alignItems: "center", whiteSpace: "nowrap" }}>
            <input type="checkbox" checked={c.counts_absent} onChange={e => updateCode(i, "counts_absent", e.target.checked)} /> Absent
          </label>
          <button className="crown-btn" onClick={() => removeCode(i)} style={{ color: "var(--crown-danger)" }}>✕</button>
        </div>
      ))}
      <button className="crown-btn" onClick={addCode}>+ Add Code</button>
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
