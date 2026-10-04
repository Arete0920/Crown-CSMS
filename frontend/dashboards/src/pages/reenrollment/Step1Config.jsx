import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { configureSession, createReenrollmentSession } from "../../api/reenrollment.js";
import "../../styles/crown-wizard.css";

export default function Step1Config({ context, setContext, goNext, stepIndex, totalSteps, steps }) {
  const [yearLabel, setYearLabel] = useState(context.targetYearLabel || "");
  const [deadline, setDeadline] = useState(context.deadlineAt || "");
  const [zone, setZone] = useState(context.communicationTimezone || "America/New_York");
  const [fee, setFee] = useState(context.enrollmentFee ?? "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleContinue() {
    if (!yearLabel.trim()) { setError("Academic year label is required."); return; }
    const feeNum = parseFloat(fee);
    if (isNaN(feeNum) || feeNum < 0) { setError("Enrollment fee must be a valid non-negative number."); return; }

    setLoading(true);
    setError(null);
    try {
      // Create session if not yet created
      let sessionId = context.sessionId;
      if (!sessionId) {
        const created = await createReenrollmentSession();
        sessionId = created.session_id;
      }
      const data = await configureSession(sessionId, yearLabel.trim(), String(feeNum.toFixed(2)), deadline ? { deadline_at: deadline, communication_timezone: zone } : {});
      setContext({
        sessionId,
        targetYearLabel: yearLabel.trim(),
        enrollmentFee: feeNum,
        deadlineAt: deadline,
        communicationTimezone: zone,
        configure: data,
        candidates: null,
        selectedExcluded: [],
        commit: null,
        verify: null,
      });
      goNext();
    } catch (e) {
      setError(e.body?.detail || e.message || "Configuration failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Configure Re-enrollment"
        subtitle="Set the target academic year and per-student enrollment fee."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 14 }}>
        <div>
          <div style={{ display: "block", fontSize: 12, color: "var(--crown-muted)", marginBottom: 4 }}>
            Target Academic Year *
          </div>
          <input
            className="crown-input"
            type="text"
            placeholder="e.g. 2026-2027"
            value={yearLabel}
            onChange={(e) => setYearLabel(e.target.value)}
            maxLength={24}
            style={{ width: "100%", boxSizing: "border-box" }}
          />
          <span style={{ fontSize: 11, color: "var(--crown-muted)" }}>Max 24 characters. Used as the billing run term label.</span>
        </div>

        <div>
          <div style={{ display: "block", fontSize: 12, color: "var(--crown-muted)", marginBottom: 4 }}>
            Enrollment Fee (per student, $) *
          </div>
          <input
            className="crown-input"
            type="number"
            min="0"
            step="0.01"
            placeholder="e.g. 500.00"
            value={fee}
            onChange={(e) => setFee(e.target.value)}
            style={{ width: "100%", boxSizing: "border-box" }}
          />
        </div>

        <label>Re-enrollment deadline (ISO date, time and offset)
          <input className="crown-input" placeholder="2027-03-01T17:00:00-05:00" value={deadline} onChange={(e) => setDeadline(e.target.value)} />
        </label>
        <label>School communication timezone
          <input className="crown-input" value={zone} onChange={(e) => setZone(e.target.value)} />
        </label>
        <p>Set a deadline to prepare coordinated family communications.</p>
        {error && <div className="crown-alert">{error}</div>}
      </div>

      <div className="crown-wizard-actions">
        <span className="crown-muted" style={{ fontSize: 12 }}>Step {stepIndex + 1} of {totalSteps}</span>
        <div className="crown-wizard-actions-right">
          <button
            className="crown-btn crown-btn-primary"
            onClick={handleContinue}
            disabled={loading}
          >
            {loading ? "Saving…" : "Continue →"}
          </button>
        </div>
      </div>
    </div>
  );
}
