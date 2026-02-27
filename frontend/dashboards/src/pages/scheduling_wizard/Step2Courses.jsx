import { useState } from "react";
import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import { saveSchedulingCourses } from "../../api/scheduling_wizard.js";
import "../../styles/crown-wizard.css";

function emptyRow() {
  return { code: "", name: "", department: "", credits: "1.0" };
}

export default function Step2Courses({ context, setContext, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const [rows, setRows] = useState(
    context.courses && context.courses.length > 0 ? context.courses : [emptyRow()]
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
    const filled = rows.filter((r) => r.code.trim() || r.name.trim());
    if (filled.length === 0) { setError("At least one course is required."); return; }

    const codes = filled.map((r) => r.code.trim().toUpperCase());
    const dupes = codes.filter((c, i) => codes.indexOf(c) !== i);
    if (dupes.length > 0) { setError(`Duplicate course codes: ${[...new Set(dupes)].join(", ")}`); return; }

    const payload = filled.map((r) => ({
      code: r.code.trim().toUpperCase(),
      name: r.name.trim(),
      department: r.department.trim(),
      credits: r.credits,
    }));

    setLoading(true);
    setError(null);
    try {
      const data = await saveSchedulingCourses(context.sessionId, payload);
      setContext({ ...context, courses: payload, coursesData: data });
      goNext();
    } catch (e) {
      const msgs = e.body?.errors || e.body?.error;
      setError(Array.isArray(msgs) ? msgs.join("; ") : msgs || e.message || "Failed to save courses.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Courses"
        subtitle="Define the courses to be offered this term. Each course needs a unique code."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 12 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr style={{ background: "var(--crown-surface)", borderBottom: "1px solid var(--crown-border)" }}>
              <th style={{ padding: "6px 10px", textAlign: "left", width: "18%" }}>Code *</th>
              <th style={{ padding: "6px 10px", textAlign: "left", width: "30%" }}>Name *</th>
              <th style={{ padding: "6px 10px", textAlign: "left", width: "28%" }}>Department</th>
              <th style={{ padding: "6px 10px", textAlign: "left", width: "14%" }}>Credits</th>
              <th style={{ padding: "6px 10px", width: "10%" }}></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} style={{ borderBottom: "1px solid var(--crown-border, #eee)" }}>
                <td style={{ padding: "4px 8px" }}>
                  <input
                    className="crown-input"
                    value={row.code}
                    onChange={(e) => updateRow(i, "code", e.target.value)}
                    placeholder="MATH101"
                    style={{ width: "100%", boxSizing: "border-box", textTransform: "uppercase" }}
                  />
                </td>
                <td style={{ padding: "4px 8px" }}>
                  <input
                    className="crown-input"
                    value={row.name}
                    onChange={(e) => updateRow(i, "name", e.target.value)}
                    placeholder="Algebra I"
                    style={{ width: "100%", boxSizing: "border-box" }}
                  />
                </td>
                <td style={{ padding: "4px 8px" }}>
                  <input
                    className="crown-input"
                    value={row.department}
                    onChange={(e) => updateRow(i, "department", e.target.value)}
                    placeholder="Mathematics"
                    style={{ width: "100%", boxSizing: "border-box" }}
                  />
                </td>
                <td style={{ padding: "4px 8px" }}>
                  <input
                    className="crown-input"
                    type="number"
                    min="0"
                    step="0.25"
                    value={row.credits}
                    onChange={(e) => updateRow(i, "credits", e.target.value)}
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
          + Add Course
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
