import CrownWizardStepHeader from "../../components/crown/CrownWizardStepHeader.jsx";
import "../../styles/crown-wizard.css";

export default function Step4Preview({ context, goNext, goPrev, stepIndex, totalSteps, steps }) {
  const courses = context.courses || [];
  const sections = context.sections || [];
  const term = context.term || "—";
  const schoolYear = context.schoolYear || "—";

  // Group sections by course
  const sectionsByCourse = {};
  for (const s of sections) {
    const code = s.course_code || "—";
    if (!sectionsByCourse[code]) sectionsByCourse[code] = [];
    sectionsByCourse[code].push(s);
  }

  return (
    <div>
      <CrownWizardStepHeader
        title="Preview"
        subtitle="Review your scheduling setup before committing."
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        steps={steps}
      />

      <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 20 }}>
        {/* Term summary */}
        <div style={{ padding: "12px 16px", background: "var(--crown-surface)", border: "1px solid var(--crown-border)", borderRadius: 6, fontSize: 13 }}>
          <div><strong>Term:</strong> {term}</div>
          <div style={{ marginTop: 4 }}><strong>School Year:</strong> {schoolYear}</div>
        </div>

        {/* Courses summary */}
        <div>
          <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>Courses ({courses.length})</div>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, border: "1px solid var(--crown-border)" }}>
            <thead>
              <tr style={{ background: "var(--crown-surface)", borderBottom: "1px solid var(--crown-border)" }}>
                <th style={{ padding: "6px 12px", textAlign: "left" }}>Code</th>
                <th style={{ padding: "6px 12px", textAlign: "left" }}>Name</th>
                <th style={{ padding: "6px 12px", textAlign: "left" }}>Department</th>
                <th style={{ padding: "6px 12px", textAlign: "right" }}>Credits</th>
              </tr>
            </thead>
            <tbody>
              {courses.map((c, i) => (
                <tr key={i} style={{ borderBottom: "1px solid var(--crown-border)" }}>
                  <td style={{ padding: "6px 12px", fontFamily: "monospace", fontWeight: 600 }}>{c.code}</td>
                  <td style={{ padding: "6px 12px" }}>{c.name}</td>
                  <td style={{ padding: "6px 12px", color: "var(--crown-muted)" }}>{c.department || "—"}</td>
                  <td style={{ padding: "6px 12px", textAlign: "right" }}>{c.credits}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Sections summary */}
        <div>
          <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>Sections ({sections.length})</div>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, border: "1px solid var(--crown-border)" }}>
            <thead>
              <tr style={{ background: "var(--crown-surface)", borderBottom: "1px solid var(--crown-border)" }}>
                <th style={{ padding: "6px 12px", textAlign: "left" }}>Course</th>
                <th style={{ padding: "6px 12px", textAlign: "left" }}>Teacher</th>
                <th style={{ padding: "6px 12px", textAlign: "left" }}>Grade Band</th>
              </tr>
            </thead>
            <tbody>
              {sections.map((s, i) => (
                <tr key={i} style={{ borderBottom: "1px solid var(--crown-border)" }}>
                  <td style={{ padding: "6px 12px", fontFamily: "monospace", fontWeight: 600 }}>{s.course_code}</td>
                  <td style={{ padding: "6px 12px" }}>{s.teacher_name || "—"}</td>
                  <td style={{ padding: "6px 12px" }}>{s.grade_band || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ display: "flex", gap: 12 }}>
          <button className="crown-btn" onClick={goPrev}>← Back</button>
          <button className="crown-btn crown-btn-primary" onClick={goNext}>Looks Good — Commit →</button>
        </div>
      </div>
    </div>
  );
}
