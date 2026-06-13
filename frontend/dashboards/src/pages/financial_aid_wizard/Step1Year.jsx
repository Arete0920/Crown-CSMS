import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { createAidWizardSession, configureAidWizardSession } from "../../api/aid_wizard.js";
import "../../styles/crown-wizard.css";

export default function Step1Year({ context, setContext, goNext, stepIndex, totalSteps, steps }) {
  const [aidYear, setAidYear] = useState(context.aidYear || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleContinue() {
    if (!aidYear.trim()) { setError("Aid year is required (e.g. 2026-2027)."); return; }
    if (aidYear.trim().length > 24) { setError("Aid year must be 24 characters or fewer."); return; }

    setLoading(true);
    setError(null);
    try {
      let sessionId = context.sessionId;
      if (!sessionId) {
        const created = await createAidWizardSession();
        sessionId = created.session_id;
      }
      const data = await configureAidWizardSession(sessionId, aidYear.trim());
      setContext({
        sessionId,
        aidYear: aidYear.trim(),
        configure: data,
        buckets: null,
        awards: null,
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
        title="Aid Year"
        subtitle="Set the academic year for this financial aid cycle."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 18 }}>
        <div>
          <div style={{ display: "block", fontSize: 12, color: "var(--crown-muted)", marginBottom: 4 }}>
            Aid Year *
          </div>
          <input
            className="crown-input"
            type="text"
            placeholder="e.g. 2026-2027"
            value={aidYear}
            onChange={(e) => setAidYear(e.target.value)}
            maxLength={24}
            style={{ width: "100%", boxSizing: "border-box" }}
          />
          <span style={{ fontSize: 11, color: "var(--crown-muted)" }}>
            Max 24 characters. Used as the key for this aid cycle.
          </span>
        </div>

        {error && (
          <div className="crown-alert crown-alert--error">{error}</div>
        )}

        <button
          className="crown-btn crown-btn--primary"
          onClick={handleContinue}
          disabled={loading}
        >
          {loading ? "Saving…" : "Continue"}
        </button>
      </div>
    </div>
  );
}
