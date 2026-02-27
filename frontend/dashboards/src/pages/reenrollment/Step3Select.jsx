import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { selectStudents } from "../../api/reenrollment.js";
import "../../styles/crown-wizard.css";

export default function Step3Select({ context, setContext, goNext, goBack, stepIndex, totalSteps, steps }) {
  const candidates = context.candidates?.candidates || [];
  const [excluded, setExcluded] = useState(new Set(context.selectedExcluded || []));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function toggleExclude(id) {
    setExcluded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function handleContinue() {
    setLoading(true);
    setError(null);
    try {
      const excludedList = [...excluded];
      await selectStudents(context.sessionId, excludedList);
      setContext((c) => ({ ...c, selectedExcluded: excludedList }));
      goNext();
    } catch (e) {
      setError(e.body?.detail || e.message || "Failed to save selection.");
    } finally {
      setLoading(false);
    }
  }

  const selected = candidates.length - excluded.size;

  return (
    <div>
      <CrownWizardStepHeader
        title="Select Students"
        subtitle="Uncheck any students you do not want to re-enroll. All are selected by default."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div className="crown-card" style={{ padding: "10px 16px", marginTop: 14 }}>
        <span style={{ fontSize: 13, color: "var(--crown-muted)" }}>
          <strong style={{ color: selected > 0 ? "var(--crown-gold)" : "var(--crown-danger)" }}>{selected}</strong> of{" "}
          <strong style={{ color: "var(--crown-text)" }}>{candidates.length}</strong> students selected
          {excluded.size > 0 && (
            <span style={{ marginLeft: 8 }}>
              — <strong style={{ color: "var(--crown-danger)" }}>{excluded.size}</strong> excluded
            </span>
          )}
        </span>
      </div>

      <div style={{ marginTop: 12, maxHeight: 320, overflowY: "auto", border: "1px solid var(--crown-border)", borderRadius: 6 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ background: "var(--crown-surface)" }}>
              <th style={{ width: 40, padding: "8px 12px" }} />
              <th style={{ textAlign: "left", padding: "8px 12px", color: "var(--crown-muted)", fontWeight: 600 }}>Name</th>
              <th style={{ textAlign: "left", padding: "8px 12px", color: "var(--crown-muted)", fontWeight: 600 }}>Grade</th>
            </tr>
          </thead>
          <tbody>
            {candidates.map((c) => (
              <tr
                key={c.id}
                style={{
                  borderTop: "1px solid var(--crown-border)",
                  opacity: excluded.has(c.id) ? 0.45 : 1,
                }}
              >
                <td style={{ padding: "7px 12px", textAlign: "center" }}>
                  <input
                    type="checkbox"
                    checked={!excluded.has(c.id)}
                    onChange={() => toggleExclude(c.id)}
                  />
                </td>
                <td style={{ padding: "7px 12px", color: "var(--crown-text)" }}>{c.last_name}, {c.first_name}</td>
                <td style={{ padding: "7px 12px", color: "var(--crown-muted)" }}>{c.grade_level || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {error && <div className="crown-alert" style={{ marginTop: 12 }}>{error}</div>}

      <div className="crown-wizard-actions">
        <button className="crown-btn" onClick={goBack}>← Back</button>
        <div className="crown-wizard-actions-right">
          <button
            className="crown-btn crown-btn-primary"
            onClick={handleContinue}
            disabled={loading || selected === 0}
          >
            {loading ? "Saving…" : `Continue with ${selected} students →`}
          </button>
        </div>
      </div>
    </div>
  );
}
