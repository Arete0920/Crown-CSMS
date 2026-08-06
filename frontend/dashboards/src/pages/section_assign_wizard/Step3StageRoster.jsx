import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { stageRoster } from "../../api/section_assign_wizard.js";
import "../../styles/crown-wizard.css";

export default function Step3StageRoster({ context, setContext, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const studentIds = context.student_ids || [];

  const [actions, setActions] = useState(() => {
    const saved = context.roster_changes || [];
    const map = {};
    saved.forEach(({ student_id, action }) => { map[student_id] = action; });
    studentIds.forEach((id) => { if (!map[id]) map[id] = "add"; });
    return map;
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function setAction(id, action) {
    setActions((prev) => ({ ...prev, [id]: action }));
  }

  async function handleNext() {
    const changes = studentIds.map((id) => ({ student_id: id, action: actions[id] || "add" }));

    setLoading(true);
    setError(null);
    try {
      const data = await stageRoster(context.sessionId, changes);
      setContext({ ...context, roster_changes: data.roster_changes || changes });
      goNext();
    } catch (e) {
      setError(e.body?.error || e.message || "Failed to stage roster.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Stage Roster"
        subtitle="Choose add or remove for each student. Last action wins on duplicate entries."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 14, maxWidth: 600 }}>
        {studentIds.length === 0 && (
          <div style={{ fontSize: 13, color: "var(--crown-muted)" }}>No students loaded. Go back and load students first.</div>
        )}

        {studentIds.length > 0 && (
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--crown-border)" }}>
                <th style={{ textAlign: "left", padding: "6px 8px" }}>Student ID</th>
                <th style={{ textAlign: "left", padding: "6px 8px" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {studentIds.map((id) => (
                <tr key={id} style={{ borderBottom: "1px solid var(--crown-border)" }}>
                  <td style={{ padding: "6px 8px", fontFamily: "var(--crown-font-mono)", fontSize: 11 }}>{id}</td>
                  <td style={{ padding: "6px 8px" }}>
                    <select
                      className="crown-input"
                      value={actions[id] || "add"}
                      onChange={(e) => setAction(id, e.target.value)}
                      style={{ padding: "3px 6px", fontSize: 12 }}
                    >
                      <option value="add">Add</option>
                      <option value="remove">Remove</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {error && <div className="crown-alert">{error}</div>}

        <div style={{ display: "flex", gap: 12 }}>
          <button className="crown-btn" onClick={goPrev} disabled={loading}>← Back</button>
          <button
            className="crown-btn crown-btn-primary"
            onClick={handleNext}
            disabled={loading || studentIds.length === 0}
          >
            {loading ? "Staging…" : "Next →"}
          </button>
        </div>
      </div>
    </div>
  );
}
