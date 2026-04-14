import PropTypes from "prop-types";
import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { loadStudents } from "../../api/section_assign_wizard.js";
import "../../styles/crown-wizard.css";

function parseIds(text) {
  return text
    .split(/[\s,]+/)
    .map((s) => s.trim())
    .filter(Boolean);
}

export default function Step2LoadStudents({ context, setContext, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const [raw, setRaw] = useState((context.student_ids || []).join("\n"));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleNext() {
    const ids = parseIds(raw);
    if (ids.length === 0) { setError("Enter at least one student UUID."); return; }

    setLoading(true);
    setError(null);
    try {
      const data = await loadStudents(context.sessionId, ids);
      setContext({ ...context, student_ids: data.student_ids || ids });
      goNext();
    } catch (e) {
      setError(e.body?.error || e.message || "Failed to load students.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Load Students"
        subtitle="Paste student UUIDs (one per line, or comma-separated). Duplicates are deduplicated automatically."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 14, maxWidth: 540 }}>
        <div>
          <div style={{ display: "block", fontSize: 13, marginBottom: 4 }}>Student IDs</div>
          <textarea
            className="crown-input"
            rows={8}
            placeholder={"00000000-0000-0000-0000-000000000000\n11111111-1111-1111-1111-111111111111"}
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
            style={{ width: "100%", fontFamily: "monospace", fontSize: 12 }}
          />
          <div style={{ fontSize: 11, color: "var(--crown-muted)", marginTop: 4 }}>
            Detected: {parseIds(raw).length} IDs
          </div>
        </div>

        {error && <div className="crown-alert">{error}</div>}

        <div style={{ display: "flex", gap: 12 }}>
          <button className="crown-btn" onClick={goPrev} disabled={loading}>Back</button>
          <button className="crown-btn crown-btn-primary" onClick={handleNext} disabled={loading}>
            {loading ? "Loading..." : "Next ->"}
          </button>
        </div>
      </div>
    </div>
  );
}

Step2LoadStudents.propTypes = {
  context: PropTypes.shape({
    sessionId: PropTypes.string,
    student_ids: PropTypes.arrayOf(PropTypes.string),
  }).isRequired,
  setContext: PropTypes.func.isRequired,
  goNext: PropTypes.func.isRequired,
  goPrev: PropTypes.func.isRequired,
  stepIndex: PropTypes.number.isRequired,
  totalSteps: PropTypes.number.isRequired,
  steps: PropTypes.arrayOf(PropTypes.object).isRequired,
};
