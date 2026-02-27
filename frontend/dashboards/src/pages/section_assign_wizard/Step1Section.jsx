import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { createSectionAssignSession, configureSectionAssignSession } from "../../api/section_assign_wizard.js";
import "../../styles/crown-wizard.css";

export default function Step1Section({ context, setContext, goNext, stepIndex, totalSteps, steps }) {
  const [sectionId, setSectionId] = useState(context.section_id || "");
  const [term, setTerm] = useState(context.term || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleNext() {
    if (!sectionId.trim()) { setError("Section ID is required."); return; }

    setLoading(true);
    setError(null);
    try {
      let sessionId = context.sessionId;
      if (!sessionId) {
        const created = await createSectionAssignSession();
        sessionId = created.session_id;
      }
      const data = await configureSectionAssignSession(sessionId, sectionId.trim(), term.trim() || undefined);
      setContext({ ...context, sessionId, section_id: sectionId.trim(), term: data.term || term.trim() });
      goNext();
    } catch (e) {
      setError(e.body?.error || e.message || "Failed to configure session.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Section & Term"
        subtitle="Select the section you want to assign students to."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 14, maxWidth: 480 }}>
        <div>
          <label style={{ display: "block", fontSize: 13, marginBottom: 4 }}>Section ID (UUID)</label>
          <input
            className="crown-input"
            type="text"
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            value={sectionId}
            onChange={(e) => setSectionId(e.target.value)}
            style={{ width: "100%" }}
          />
        </div>
        <div>
          <label style={{ display: "block", fontSize: 13, marginBottom: 4 }}>Term (optional — inherited from section if blank)</label>
          <input
            className="crown-input"
            type="text"
            placeholder="e.g. 2026-spring"
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            style={{ width: "100%" }}
          />
        </div>

        {error && <div className="crown-alert">{error}</div>}

        <div>
          <button
            className="crown-btn crown-btn-primary"
            onClick={handleNext}
            disabled={loading}
          >
            {loading ? "Configuring…" : "Next →"}
          </button>
        </div>
      </div>
    </div>
  );
}
