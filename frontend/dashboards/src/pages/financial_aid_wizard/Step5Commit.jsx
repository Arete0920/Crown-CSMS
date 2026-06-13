import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { commitAidSetup } from "../../api/aid_wizard.js";
import "../../styles/crown-wizard.css";

export default function Step5Commit({ context, setContext, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const [confirmed, setConfirmed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const awards = context.awards || [];
  const totalAmount = awards.reduce((s, a) => s + (parseFloat(a.amount) || 0), 0);

  async function handleCommit() {
    if (!confirmed) { setError("Please confirm before committing."); return; }
    setLoading(true);
    setError(null);
    try {
      const data = await commitAidSetup(context.sessionId);
      setContext((prev) => ({ ...prev, commit: data }));
      goNext();
    } catch (e) {
      setError(e.body?.error || e.message || "Commit failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Commit Aid Setup"
        subtitle="Review and confirm. This will create AidAward records in the database."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 16 }}>
        {/* Summary */}
        <div style={{ border: "1px solid var(--crown-border)", borderRadius: 6, padding: "16px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>Aid Year</div>
              <div style={{ fontWeight: 600 }}>{context.aidYear || "—"}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>Active Buckets</div>
              <div style={{ fontWeight: 600 }}>{(context.buckets || []).join(", ") || "None"}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>Awards to Create</div>
              <div style={{ fontWeight: 600 }}>{awards.length}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>Total Aid</div>
              <div style={{ fontWeight: 600 }}>
                ${totalAmount.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>
          </div>
        </div>

        {/* Confirmation */}
        <label style={{ display: "flex", alignItems: "flex-start", gap: 10, cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
            style={{ marginTop: 2 }}
          />
          <span style={{ fontSize: 13 }}>
            I confirm this setup is correct. AidAward records will be created for all
            staged awards. This action is idempotent — re-running will not create duplicates.
          </span>
        </label>

        {error && <div className="crown-alert crown-alert--error">{error}</div>}

        <div style={{ display: "flex", gap: 8 }}>
          <button className="crown-btn crown-btn--ghost" onClick={goPrev} disabled={loading}>Back</button>
          <button
            className="crown-btn crown-btn--primary"
            onClick={handleCommit}
            disabled={loading || !confirmed}
          >
            {loading ? "Committing…" : "Commit Aid Setup"}
          </button>
        </div>
      </div>
    </div>
  );
}
