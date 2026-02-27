import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import {
  createCommsWizardSession,
  configureCommsSession,
} from "../../api/comms_wizard.js";
import "../../styles/crown-wizard.css";

const CHANNEL_OPTIONS = [
  { value: "email", label: "Email" },
  { value: "sms", label: "SMS" },
  { value: "teams", label: "Teams" },
];

export default function Step1Purpose({ context, setContext, goNext, stepIndex, totalSteps, steps }) {
  const [purpose, setPurpose] = useState(context.purpose || "");
  const [channels, setChannels] = useState(context.channels || ["email"]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function toggleChannel(value) {
    setChannels((prev) =>
      prev.includes(value) ? prev.filter((c) => c !== value) : [...prev, value]
    );
  }

  async function handleContinue() {
    if (!purpose.trim()) { setError("Purpose is required."); return; }
    if (purpose.trim().length > 128) { setError("Purpose must be 128 characters or fewer."); return; }
    if (channels.length === 0) { setError("Select at least one channel."); return; }

    setLoading(true);
    setError(null);
    try {
      let sessionId = context.sessionId;
      if (!sessionId) {
        const created = await createCommsWizardSession();
        sessionId = created.session_id;
      }
      const data = await configureCommsSession(sessionId, purpose.trim(), channels);
      setContext({
        sessionId,
        purpose: purpose.trim(),
        channels,
        configure: data,
        subject: null,
        body: null,
        recipients: null,
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
        title="Purpose & Channels"
        subtitle="Describe the communication purpose and select which channels to use."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 16 }}>
        <div>
          <label style={{ display: "block", fontSize: 12, color: "var(--crown-muted)", marginBottom: 4 }}>
            Campaign Purpose *
          </label>
          <input
            className="crown-input"
            type="text"
            placeholder="e.g. Re-enrollment Reminder"
            value={purpose}
            onChange={(e) => setPurpose(e.target.value)}
            maxLength={128}
            style={{ width: "100%", boxSizing: "border-box" }}
          />
          <span style={{ fontSize: 11, color: "var(--crown-muted)" }}>Max 128 characters.</span>
        </div>

        <div>
          <label style={{ display: "block", fontSize: 12, color: "var(--crown-muted)", marginBottom: 8 }}>
            Channels *
          </label>
          <div style={{ display: "flex", gap: 20 }}>
            {CHANNEL_OPTIONS.map((ch) => (
              <label key={ch.value} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={channels.includes(ch.value)}
                  onChange={() => toggleChannel(ch.value)}
                />
                {ch.label}
              </label>
            ))}
          </div>
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
