import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { stageCommsRecipients } from "../../api/comms_wizard.js";
import "../../styles/crown-wizard.css";

function emptyRow() {
  return { to: "", name: "" };
}

export default function Step3Recipients({ context, setContext, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const [rows, setRows] = useState(
    context.recipients && context.recipients.length > 0
      ? context.recipients.map((r) => ({ to: r.to || "", name: r.name || "" }))
      : [emptyRow()]
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function updateRow(i, field, value) {
    setRows((prev) => prev.map((r, idx) => idx === i ? { ...r, [field]: value } : r));
  }

  function addRow() {
    setRows((prev) => [...prev, emptyRow()]);
  }

  function removeRow(i) {
    setRows((prev) => prev.filter((_, idx) => idx !== i));
  }

  async function handleContinue() {
    const filled = rows.filter((r) => r.to.trim());
    if (filled.length === 0) { setError("At least one recipient is required."); return; }

    const tos = filled.map((r) => r.to.trim().toLowerCase());
    const dupes = tos.filter((t, i) => tos.indexOf(t) !== i);
    if (dupes.length > 0) { setError(`Duplicate recipients: ${[...new Set(dupes)].join(", ")}`); return; }

    const payload = filled.map((r) => ({ to: r.to.trim(), name: r.name.trim() }));

    setLoading(true);
    setError(null);
    try {
      const data = await stageCommsRecipients(context.sessionId, payload);
      setContext({ ...context, recipients: payload, recipientsData: data });
      goNext();
    } catch (e) {
      const msgs = e.body?.errors || e.body?.error;
      setError(Array.isArray(msgs) ? msgs.join("; ") : msgs || e.message || "Failed to stage recipients.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Recipients"
        subtitle="Add the recipients for this communication."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 12 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr style={{ background: "var(--crown-surface)", borderBottom: "1px solid var(--crown-border)" }}>
              <th style={{ padding: "6px 10px", textAlign: "left", width: "50%" }}>Email / Address *</th>
              <th style={{ padding: "6px 10px", textAlign: "left", width: "38%" }}>Name</th>
              <th style={{ padding: "6px 10px", width: "12%" }}></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} style={{ borderBottom: "1px solid var(--crown-border)" }}>
                <td style={{ padding: "4px 8px" }}>
                  <input
                    className="crown-input"
                    type="email"
                    value={row.to}
                    onChange={(e) => updateRow(i, "to", e.target.value)}
                    placeholder="parent@example.com"
                    style={{ width: "100%", boxSizing: "border-box" }}
                  />
                </td>
                <td style={{ padding: "4px 8px" }}>
                  <input
                    className="crown-input"
                    value={row.name}
                    onChange={(e) => updateRow(i, "name", e.target.value)}
                    placeholder="John Smith"
                    style={{ width: "100%", boxSizing: "border-box" }}
                  />
                </td>
                <td style={{ padding: "4px 8px", textAlign: "center" }}>
                  {rows.length > 1 && (
                    <button
                      onClick={() => removeRow(i)}
                      style={{ background: "none", border: "none", color: "var(--crown-danger)", cursor: "pointer", fontSize: 16 }}
                      title="Remove row"
                    >✕</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <button
          className="crown-btn"
          onClick={addRow}
          style={{ alignSelf: "flex-start", fontSize: 12 }}
        >
          + Add Recipient
        </button>

        {error && <div className="crown-alert">{error}</div>}

        <div style={{ display: "flex", gap: 12 }}>
          <button className="crown-btn" onClick={goPrev}>← Back</button>
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
