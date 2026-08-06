import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { draftCommsMessage } from "../../api/comms_wizard.js";
import "../../styles/crown-wizard.css";

export default function Step2Message({ context, setContext, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const [subject, setSubject] = useState(context.subject || "");
  const [body, setBody] = useState(context.body || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleContinue() {
    if (!subject.trim()) { setError("Subject is required."); return; }
    if (subject.trim().length > 255) { setError("Subject must be 255 characters or fewer."); return; }
    if (!body.trim()) { setError("Message body is required."); return; }

    setLoading(true);
    setError(null);
    try {
      const data = await draftCommsMessage(context.sessionId, subject.trim(), body.trim());
      setContext({ ...context, subject: subject.trim(), body: body.trim(), message: data });
      goNext();
    } catch (e) {
      setError(e.body?.error || e.message || "Failed to save message.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Message"
        subtitle="Write the subject and body for this communication."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 16 }}>
        <div>
          <label htmlFor="comms-subject" style={{ display: "block", fontSize: 12, color: "var(--crown-muted)", marginBottom: 4 }}>
            Subject *
          </label>
          <input
            id="comms-subject"
            className="crown-input"
            type="text"
            placeholder="e.g. Action Required: Please Re-enroll by March 1"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            maxLength={255}
            style={{ width: "100%", boxSizing: "border-box" }}
          />
        </div>

        <div>
          <label htmlFor="comms-message-body" style={{ display: "block", fontSize: 12, color: "var(--crown-muted)", marginBottom: 4 }}>
            Message Body *
          </label>
          <textarea
            id="comms-message-body"
            className="crown-input"
            placeholder="Write your message here..."
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={8}
            style={{ width: "100%", boxSizing: "border-box", resize: "vertical", fontFamily: "inherit" }}
          />
        </div>

        {error && <div className="crown-alert">{error}</div>}

        <div style={{ display: "flex", gap: 12 }}>
          <button className="crown-btn" onClick={goPrev}>Back</button>
          <button
            className="crown-btn crown-btn-primary"
            onClick={handleContinue}
            disabled={loading}
          >
            {loading ? "Saving..." : "Continue"}
          </button>
        </div>
      </div>
    </div>
  );
}
