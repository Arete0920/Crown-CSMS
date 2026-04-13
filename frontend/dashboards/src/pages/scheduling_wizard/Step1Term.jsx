import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import {
  createSchedulingWizardSession,
  configureSchedulingSession,
} from "../../api/scheduling_wizard.js";
import "../../styles/crown-wizard.css";

export default function Step1Term({ context, setContext, goNext, stepIndex, totalSteps, steps }) {
  const [term, setTerm] = useState(context.term || "");
  const [schoolYear, setSchoolYear] = useState(context.schoolYear || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleContinue() {
    if (!term.trim()) { setError("Term is required (e.g. 2026-FALL)."); return; }
    if (term.trim().length > 24) { setError("Term must be 24 characters or fewer."); return; }
    if (!schoolYear.trim()) { setError("School year is required (e.g. 2026-2027)."); return; }
    if (schoolYear.trim().length > 16) { setError("School year must be 16 characters or fewer."); return; }

    setLoading(true);
    setError(null);
    try {
      let sessionId = context.sessionId;
      if (!sessionId) {
        const created = await createSchedulingWizardSession();
        sessionId = created.session_id;
      }
      const data = await configureSchedulingSession(sessionId, term.trim(), schoolYear.trim());
      setContext({
        sessionId,
        term: term.trim(),
        schoolYear: schoolYear.trim(),
        configure: data,
        courses: null,
        sections: null,
        commit: null,
        verify: null,
      });
      goNext();
    } catch (e) {
      setError(e.body?.error || e.message || "Configuration failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Term Setup"
        subtitle="Set the term label and school year for this scheduling run."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 16 }}>
        <div>
          <div style={{ display: "block", fontSize: 12, color: "var(--crown-muted)", marginBottom: 4 }}>
            Term Label *
          </div>
          <input
            className="crown-input"
            type="text"
            placeholder="e.g. 2026-FALL"
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            maxLength={24}
            style={{ width: "100%", boxSizing: "border-box" }}
          />
          <span style={{ fontSize: 11, color: "var(--crown-muted)" }}>Max 24 characters. Used as the term key on course sections.</span>
        </div>

        <div>
          <div style={{ display: "block", fontSize: 12, color: "var(--crown-muted)", marginBottom: 4 }}>
            School Year *
          </div>
          <input
            className="crown-input"
            type="text"
            placeholder="e.g. 2026-2027"
            value={schoolYear}
            onChange={(e) => setSchoolYear(e.target.value)}
            maxLength={16}
            style={{ width: "100%", boxSizing: "border-box" }}
          />
          <span style={{ fontSize: 11, color: "var(--crown-muted)" }}>Max 16 characters. e.g. 2026-2027.</span>
        </div>

        {error && <div className="crown-alert">{error}</div>}

        <button
          className="crown-btn crown-btn-primary"
          onClick={handleContinue}
          disabled={loading}
          style={{ alignSelf: "flex-start" }}
        >
          {loading ? "Saving…" : "Continue →"}
        </button>
      </div>
    </div>
  );
}
