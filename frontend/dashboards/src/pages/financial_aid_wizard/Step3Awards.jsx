import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { stageAidAwards } from "../../api/financial_aid_wizard.js";
import "../../styles/crown-wizard.css";

function emptyRow(buckets) {
  return { application_id: "", bucket: buckets[0] || "need", amount: "", rationale: "" };
}

export default function Step3Awards({ context, setContext, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const activeBuckets = context.buckets || [];
  const [rows, setRows] = useState(
    context.awards?.length > 0
      ? context.awards
      : [emptyRow(activeBuckets)]
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function updateRow(index, field, value) {
    setRows((prev) => prev.map((r, i) => (i === index ? { ...r, [field]: value } : r)));
  }

  function addRow() {
    setRows((prev) => [...prev, emptyRow(activeBuckets)]);
  }

  function removeRow(index) {
    setRows((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSkip() {
    setLoading(true);
    setError(null);
    try {
      const data = await stageAidAwards(context.sessionId, []);
      setContext((prev) => ({ ...prev, awards: [], awardsData: data }));
      goNext();
    } catch (e) {
      setError(e.body?.error || e.message || "Failed to stage awards.");
    } finally {
      setLoading(false);
    }
  }

  async function handleContinue() {
    const awards = rows
      .filter((r) => r.application_id.trim())
      .map((r) => ({
        application_id: r.application_id.trim(),
        bucket: r.bucket,
        amount: r.amount,
        rationale: r.rationale.trim(),
      }));

    if (awards.length === 0) {
      setError("Add at least one award, or use 'No Awards — Skip'.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await stageAidAwards(context.sessionId, awards);
      setContext((prev) => ({ ...prev, awards, awardsData: data }));
      goNext();
    } catch (e) {
      setError(e.body?.error || e.message || "Failed to stage awards.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Stage Awards"
        subtitle="Enter the aid awards for this cycle. Each row is one award for one application."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 12 }}>
        {rows.map((row, i) => (
          <div
            key={i}
            style={{
              border: "1px solid var(--crown-border)",
              borderRadius: 6,
              padding: "12px",
              display: "flex",
              flexDirection: "column",
              gap: 8,
            }}
          >
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <span style={{ fontSize: 12, color: "var(--crown-muted)", fontWeight: 600 }}>
                Award #{i + 1}
              </span>
              {rows.length > 1 && (
                <button
                  type="button"
                  className="crown-btn crown-btn--ghost"
                  style={{ fontSize: 11, padding: "2px 8px", marginLeft: "auto" }}
                  onClick={() => removeRow(i)}
                >
                  Remove
                </button>
              )}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              <div>
                <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>Application ID *</div>
                <input
                  className="crown-input"
                  type="text"
                  placeholder="UUID of the FinancialAidApplication"
                  value={row.application_id}
                  onChange={(e) => updateRow(i, "application_id", e.target.value)}
                  style={{ width: "100%", boxSizing: "border-box" }}
                />
              </div>
              <div>
                <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>Bucket *</div>
                <select
                  className="crown-input"
                  value={row.bucket}
                  onChange={(e) => updateRow(i, "bucket", e.target.value)}
                  style={{ width: "100%", boxSizing: "border-box" }}
                >
                  {activeBuckets.map((b) => (
                    <option key={b} value={b}>{b.charAt(0).toUpperCase() + b.slice(1)}</option>
                  ))}
                </select>
              </div>
              <div>
                <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>Amount ($) *</div>
                <input
                  className="crown-input"
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="0.00"
                  value={row.amount}
                  onChange={(e) => updateRow(i, "amount", e.target.value)}
                  style={{ width: "100%", boxSizing: "border-box" }}
                />
              </div>
              <div>
                <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>Rationale</div>
                <input
                  className="crown-input"
                  type="text"
                  placeholder="Optional notes"
                  value={row.rationale}
                  onChange={(e) => updateRow(i, "rationale", e.target.value)}
                  style={{ width: "100%", boxSizing: "border-box" }}
                />
              </div>
            </div>
          </div>
        ))}

        <button type="button" className="crown-btn crown-btn--ghost" onClick={addRow}>
          + Add Award
        </button>

        {error && <div className="crown-alert crown-alert--error">{error}</div>}

        <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
          <button className="crown-btn crown-btn--ghost" onClick={goPrev} disabled={loading}>Back</button>
          <button className="crown-btn crown-btn--ghost" onClick={handleSkip} disabled={loading}>
            No Awards — Skip
          </button>
          <button className="crown-btn crown-btn--primary" onClick={handleContinue} disabled={loading}>
            {loading ? "Saving…" : "Continue"}
          </button>
        </div>
      </div>
    </div>
  );
}
