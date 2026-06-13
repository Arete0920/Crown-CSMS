import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { saveAidBuckets } from "../../api/aid_wizard.js";
import "../../styles/crown-wizard.css";

const ALL_BUCKETS = [
  { value: "need", label: "Need-Based", desc: "Awarded based on demonstrated financial need." },
  { value: "merit", label: "Merit-Based", desc: "Awarded based on academic or extracurricular achievement." },
  { value: "mission", label: "Mission-Driven", desc: "Awarded to support the school's mission priorities." },
  { value: "marketing", label: "Marketing / Enrollment", desc: "Incentive awards to attract new students." },
  { value: "hardship", label: "Hardship / Crisis", desc: "Emergency aid for families facing unexpected difficulties." },
];

export default function Step2Buckets({ context, setContext, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const [selected, setSelected] = useState(context.buckets || []);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function toggleBucket(value) {
    setSelected((prev) =>
      prev.includes(value) ? prev.filter((b) => b !== value) : [...prev, value]
    );
  }

  async function handleContinue() {
    if (selected.length === 0) { setError("Select at least one aid bucket."); return; }
    setLoading(true);
    setError(null);
    try {
      const data = await saveAidBuckets(context.sessionId, selected);
      setContext((prev) => ({ ...prev, buckets: selected, bucketsData: data }));
      goNext();
    } catch (e) {
      setError(e.body?.error || e.message || "Failed to save buckets.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Aid Buckets"
        subtitle="Select the award categories active for this aid cycle."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 8 }}>
        {ALL_BUCKETS.map((b) => (
          <div
            key={b.value}
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: 10,
              padding: "10px 12px",
              border: `1px solid ${selected.includes(b.value) ? "var(--crown-primary)" : "var(--crown-border)"}`,
              borderRadius: 6,
              cursor: "pointer",
              background: selected.includes(b.value) ? "var(--crown-surface-2)" : "transparent",
            }}
          >
            <input
              type="checkbox"
              value={b.value}
              checked={selected.includes(b.value)}
              onChange={() => toggleBucket(b.value)}
              style={{ marginTop: 3 }}
            />
            <div>
              <div style={{ fontWeight: 600, fontSize: 13 }}>{b.label}</div>
              <div style={{ fontSize: 12, color: "var(--crown-muted)" }}>{b.desc}</div>
            </div>
          </div>
        ))}

        {error && <div className="crown-alert crown-alert--error">{error}</div>}

        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <button className="crown-btn crown-btn--ghost" onClick={goPrev} disabled={loading}>
            Back
          </button>
          <button className="crown-btn crown-btn--primary" onClick={handleContinue} disabled={loading}>
            {loading ? "Saving…" : "Continue"}
          </button>
        </div>
      </div>
    </div>
  );
}
