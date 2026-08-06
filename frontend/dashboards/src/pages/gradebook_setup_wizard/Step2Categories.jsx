import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { defineCategories } from "../../api/gradebook_setup_wizard.js";
import "../../styles/crown-wizard.css";

const EMPTY_CAT = { name: "", weight_percent: 0, sort_order: 0 };

export default function Step2Categories({ context, setContext, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const [categories, setCategories] = useState(context.categories || [{ ...EMPTY_CAT }]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function addCategory() { setCategories([...categories, { ...EMPTY_CAT, sort_order: categories.length }]); }
  function removeCategory(i) { setCategories(categories.filter((_, idx) => idx !== i)); }
  function updateCategory(i, field, val) {
    const updated = [...categories];
    updated[i] = { ...updated[i], [field]: field === "name" ? val : Number(val) };
    setCategories(updated);
  }
  const totalWeight = categories.reduce((sum, c) => sum + (c.weight_percent || 0), 0);

  async function handleNext() {
    if (categories.length === 0) { setError("At least one category is required."); return; }
    setLoading(true); setError(null);
    try {
      await defineCategories(context.sessionId, categories);
      setContext({ ...context, categories });
      goNext();
    } catch (e) {
      setError(e.body?.error || e.message || "Failed to save categories.");
    } finally { setLoading(false); }
  }

  return (
    <div>
      <CrownWizardStepHeader title="Define Categories" subtitle="Define assignment categories. Weights must sum to 0 or 100." stepIndex={stepIndex} totalSteps={totalSteps} steps={steps} />
      {categories.map((c, i) => (
        <div key={i} style={{ display: "flex", gap: 8, marginBottom: 8, alignItems: "center" }}>
          <input className="crown-input" placeholder="Name" value={c.name} onChange={e => updateCategory(i, "name", e.target.value)} style={{ flex: 2 }} />
          <input className="crown-input" type="number" min={0} max={100} placeholder="Weight %" value={c.weight_percent} onChange={e => updateCategory(i, "weight_percent", e.target.value)} style={{ flex: 1 }} />
          <input className="crown-input" type="number" min={0} placeholder="Sort" value={c.sort_order} onChange={e => updateCategory(i, "sort_order", e.target.value)} style={{ flex: 1 }} />
          <button className="crown-btn" onClick={() => removeCategory(i)} style={{ color: "var(--crown-danger)" }}>✕</button>
        </div>
      ))}
      <p style={{ fontWeight: "bold", color: totalWeight !== 0 && totalWeight !== 100 ? "red" : "inherit" }}>
        Total Weight: {totalWeight}%
      </p>
      <button className="crown-btn" onClick={addCategory}>+ Add Category</button>
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
