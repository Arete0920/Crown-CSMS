import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { stageSchedulingSections } from "../../api/scheduling_wizard.js";
import "../../styles/crown-wizard.css";

function emptyRow() {
  return { course_code: "", teacher_name: "", grade_band: "" };
}

export default function Step3Sections({ context, setContext, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const courses = context.courses || [];
  const courseCodes = courses.map((c) => c.code || c.code);

  const [rows, setRows] = useState(
    context.sections && context.sections.length > 0 ? context.sections : [emptyRow()]
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
    const filled = rows.filter((r) => r.course_code.trim());
    if (filled.length === 0) { setError("At least one section is required."); return; }

    const payload = filled.map((r) => ({
      course_code: r.course_code.trim().toUpperCase(),
      teacher_name: r.teacher_name.trim(),
      grade_band: r.grade_band.trim(),
    }));

    setLoading(true);
    setError(null);
    try {
      const data = await stageSchedulingSections(context.sessionId, payload);
      setContext({ ...context, sections: payload, sectionsData: data });
      goNext();
    } catch (e) {
      const msgs = e.body?.errors || e.body?.error;
      setError(Array.isArray(msgs) ? msgs.join("; ") : msgs || e.message || "Failed to stage sections.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Sections"
        subtitle="Assign teachers and grade bands to each course section."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 12 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr style={{ background: "var(--crown-surface)", borderBottom: "1px solid var(--crown-border)" }}>
              <th style={{ padding: "6px 10px", textAlign: "left", width: "28%" }}>Course *</th>
              <th style={{ padding: "6px 10px", textAlign: "left", width: "36%" }}>Teacher</th>
              <th style={{ padding: "6px 10px", textAlign: "left", width: "20%" }}>Grade Band</th>
              <th style={{ padding: "6px 10px", width: "10%" }}></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} style={{ borderBottom: "1px solid var(--crown-border, #eee)" }}>
                <td style={{ padding: "4px 8px" }}>
                  {courseCodes.length > 0 ? (
                    <select
                      className="crown-input"
                      value={row.course_code}
                      onChange={(e) => updateRow(i, "course_code", e.target.value)}
                      style={{ width: "100%", boxSizing: "border-box" }}
                    >
                      <option value="">— select —</option>
                      {courseCodes.map((code) => (
                        <option key={code} value={code}>{code}</option>
                      ))}
                    </select>
                  ) : (
                    <input
                      className="crown-input"
                      value={row.course_code}
                      onChange={(e) => updateRow(i, "course_code", e.target.value)}
                      placeholder="MATH101"
                      style={{ width: "100%", boxSizing: "border-box", textTransform: "uppercase" }}
                    />
                  )}
                </td>
                <td style={{ padding: "4px 8px" }}>
                  <input
                    className="crown-input"
                    value={row.teacher_name}
                    onChange={(e) => updateRow(i, "teacher_name", e.target.value)}
                    placeholder="Mr. Smith"
                    style={{ width: "100%", boxSizing: "border-box" }}
                  />
                </td>
                <td style={{ padding: "4px 8px" }}>
                  <input
                    className="crown-input"
                    value={row.grade_band}
                    onChange={(e) => updateRow(i, "grade_band", e.target.value)}
                    placeholder="9"
                    style={{ width: "100%", boxSizing: "border-box" }}
                  />
                </td>
                <td style={{ padding: "4px 8px", textAlign: "center" }}>
                  {rows.length > 1 && (
                    <button
                      onClick={() => removeRow(i)}
                      style={{ background: "none", border: "none", color: "var(--crown-danger, #c0392b)", cursor: "pointer", fontSize: 16 }}
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
          + Add Section
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
