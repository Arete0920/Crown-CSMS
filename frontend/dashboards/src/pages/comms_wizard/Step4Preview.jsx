import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import "../../styles/crown-wizard.css";

export default function Step4Preview({ context, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const channels = context.channels || [];
  const recipients = context.recipients || [];
  const totalMessages = channels.length * recipients.length;

  return (
    <div>
      <CrownWizardStepHeader
        title="Preview"
        subtitle="Review your campaign before committing."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 20 }}>
        {/* Campaign summary */}
        <div style={{ padding: "12px 16px", background: "var(--crown-surface)", border: "1px solid var(--crown-border)", borderRadius: 6, fontSize: 13 }}>
          <div><strong>Purpose:</strong> {context.purpose || "—"}</div>
          <div style={{ marginTop: 6 }}>
            <strong>Channels:</strong>{" "}
            {channels.length > 0
              ? channels.map((c) => <span key={c} style={{ display: "inline-block", marginRight: 8, padding: "2px 8px", background: "var(--crown-surface-2)", borderRadius: 10, fontSize: 11, fontWeight: 600, color: "var(--crown-brand)" }}>{c.toUpperCase()}</span>)
              : "—"}
          </div>
        </div>

        {/* Message preview */}
        <div style={{ border: "1px solid var(--crown-border)", borderRadius: 6, overflow: "hidden" }}>
          <div style={{ padding: "8px 14px", background: "var(--crown-surface)", borderBottom: "1px solid var(--crown-border)", fontSize: 12, fontWeight: 600, color: "var(--crown-muted)" }}>
            Message Preview
          </div>
          <div style={{ padding: "12px 14px" }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>{context.subject || "—"}</div>
            <div style={{ fontSize: 12, color: "var(--crown-text)", whiteSpace: "pre-wrap", lineHeight: 1.6 }}>
              {context.body || "—"}
            </div>
          </div>
        </div>

        {/* Recipients summary */}
        <div>
          <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>
            Recipients ({recipients.length}) × {channels.length} channel{channels.length !== 1 ? "s" : ""} = {totalMessages} message{totalMessages !== 1 ? "s" : ""}
          </div>
          {recipients.length > 0 && (
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, border: "1px solid var(--crown-border)" }}>
              <thead>
                <tr style={{ background: "var(--crown-surface)", borderBottom: "1px solid var(--crown-border)" }}>
                  <th style={{ padding: "6px 12px", textAlign: "left" }}>Address</th>
                  <th style={{ padding: "6px 12px", textAlign: "left" }}>Name</th>
                </tr>
              </thead>
              <tbody>
                {recipients.map((r, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid var(--crown-border)" }}>
                    <td style={{ padding: "6px 12px", fontFamily: "var(--crown-font-mono)", fontSize: 11 }}>{r.to}</td>
                    <td style={{ padding: "6px 12px" }}>{r.name || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div style={{ display: "flex", gap: 12 }}>
          <button className="crown-btn" onClick={goPrev}>← Back</button>
          <button className="crown-btn crown-btn-primary" onClick={goNext}>Looks Good — Commit →</button>
        </div>
      </div>
    </div>
  );
}
