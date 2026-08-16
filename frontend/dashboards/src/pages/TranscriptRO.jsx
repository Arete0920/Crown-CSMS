import { useEffect, useState } from "react";
import { fetchStudents, fetchTranscript } from "../api/academics";
import { downloadOfficialTranscriptPdf, issueOfficialTranscript } from "../api/transcript";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import ErrorBanner from "../components/ui/ErrorBanner.jsx";

export function TranscriptRO() {
  const [students, setStudents] = useState([]);
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [transcript, setTranscript] = useState(null);
  const [loadingStudents, setLoadingStudents] = useState(true);
  const [loadingTranscript, setLoadingTranscript] = useState(false);
  const [issuing, setIssuing] = useState(false);
  const [issuance, setIssuance] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStudents({ limit: 200 })
      .then((data) => {
        const results = data?.results || [];
        setStudents(results);
        if (results.length > 0) {
          setSelectedStudentId((currentId) => currentId || results[0].id);
          setLoadingTranscript(true);
        }
      })
      .catch((err) => setError(`Failed to load students: ${err.message}`))
      .finally(() => setLoadingStudents(false));
  }, []);

  useEffect(() => {
    if (!selectedStudentId) return;
    setIssuance(null);
    fetchTranscript(selectedStudentId)
      .then((data) => {
        setTranscript(data);
        setError(null);
      })
      .catch((err) => {
        setError(`Failed to load transcript: ${err.message}`);
        setTranscript(null);
      })
      .finally(() => setLoadingTranscript(false));
  }, [selectedStudentId]);

  const handleStudentChange = (event) => {
    setLoadingTranscript(true);
    setSelectedStudentId(event.target.value);
  };

  const handleIssueOfficial = async () => {
    if (!selectedStudentId) return;
    setIssuing(true);
    setError(null);
    try {
      const record = await issueOfficialTranscript(selectedStudentId);
      const blob = await downloadOfficialTranscriptPdf(record.issuance_id);
      const href = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = href;
      anchor.download = `official-transcript-${selectedStudentId}.pdf`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(href);
      setIssuance(record);
    } catch (err) {
      setError(err.message || "Official transcript issuance failed.");
    } finally {
      setIssuing(false);
    }
  };

  return (
    <CrownLayout title="Transcript" subtitle="Academic Record">
      <div className="no-print" style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", marginBottom: 16 }}>
          <label htmlFor="transcript-student-select" style={{ fontWeight: 500 }}>Student:</label>
          <select
            id="transcript-student-select"
            value={selectedStudentId}
            onChange={handleStudentChange}
            disabled={loadingStudents}
            aria-label="Student"
            style={{ padding: "6px 12px", fontSize: 14, borderRadius: 4, border: "1px solid var(--crown-border)", minWidth: 300 }}
          >
            {loadingStudents ? <option>Loading students...</option> : null}
            {!loadingStudents && students.length === 0 ? <option>No students found</option> : null}
            {students.map((student) => (
              <option key={student.id} value={student.id}>
                {student.last_name}, {student.first_name} {student.middle_name || ""} - Grade {student.grade_level || "?"}
              </option>
            ))}
          </select>
          <button className="crown-btn" onClick={() => window.print()} disabled={!transcript}>Print Working Copy</button>
          <button
            className="crown-btn crown-btn-primary"
            onClick={handleIssueOfficial}
            disabled={!transcript || issuing}
          >
            {issuing ? "Issuing..." : "Issue Official PDF"}
          </button>
        </div>
        {issuance ? (
          <div role="status" style={{ fontSize: 13, color: "var(--crown-muted)", marginBottom: 12 }}>
            Official transcript issued. ID: <code>{issuance.issuance_id}</code> · Artifact SHA-256: <code>{issuance.artifact_sha256}</code>
          </div>
        ) : null}
        {error ? <ErrorBanner title="Transcript error" message={error} /> : null}
      </div>

      {loadingTranscript ? (
        <div style={{ textAlign: "center", padding: 40, color: "var(--crown-muted)" }}>Loading transcript...</div>
      ) : null}

      {!loadingTranscript && transcript ? (
        <div className="transcript-content">
          <div style={{ marginBottom: 28 }}>
            <h2 style={{ marginTop: 0, marginBottom: 8 }}>Academic Transcript</h2>
            <table style={{ fontSize: 14, borderCollapse: "collapse" }}>
              <tbody>
                <tr><td style={{ paddingRight: 16, fontWeight: 500 }}>Student:</td><td>{transcript.student.last_name}, {transcript.student.first_name}</td></tr>
                <tr><td style={{ paddingRight: 16, fontWeight: 500 }}>Student ID:</td><td style={{ fontFamily: "var(--crown-font-mono)", fontSize: 12 }}>{transcript.student.student_id}</td></tr>
                <tr><td style={{ paddingRight: 16, fontWeight: 500 }}>Grade Level:</td><td>{transcript.student.grade_level || "-"}</td></tr>
                <tr><td style={{ paddingRight: 16, fontWeight: 500 }}>Attempted Credits:</td><td>{Number(transcript.attempted_credits || 0).toFixed(2)}</td></tr>
                <tr><td style={{ paddingRight: 16, fontWeight: 500 }}>Earned Credits:</td><td>{Number(transcript.earned_credits || 0).toFixed(2)}</td></tr>
              </tbody>
            </table>
          </div>

          {transcript.terms?.length ? transcript.terms.map((term, idx) => (
            <div key={term.term_id || `${term.term_code}-${idx}`} style={{ marginBottom: 30, pageBreakInside: "avoid" }}>
              <h3 style={{ marginTop: 0, marginBottom: 12, paddingBottom: 8, borderBottom: "2px solid var(--crown-ink)" }}>
                {term.term_name || term.term_code}
                {term.term_gpa !== null && term.term_gpa !== undefined ? (
                  <span style={{ float: "right", fontSize: 14, fontWeight: 400, color: "var(--crown-muted)" }}>
                    Term GPA: {Number(term.term_gpa).toFixed(2)}
                  </span>
                ) : null}
              </h3>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, marginBottom: 12 }}>
                <thead>
                  <tr style={{ backgroundColor: "var(--crown-surface-2)", borderBottom: "2px solid var(--crown-border)" }}>
                    <th style={{ textAlign: "left", padding: "8px 10px" }}>Course</th>
                    <th style={{ textAlign: "left", padding: "8px 10px" }}>Course Name</th>
                    <th style={{ textAlign: "left", padding: "8px 10px" }}>Teacher</th>
                    <th style={{ textAlign: "center", padding: "8px 10px" }}>Grade</th>
                    <th style={{ textAlign: "center", padding: "8px 10px" }}>Credits</th>
                    <th style={{ textAlign: "center", padding: "8px 10px" }}>Earned</th>
                    <th style={{ textAlign: "center", padding: "8px 10px" }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {term.courses.map((course, courseIdx) => (
                    <tr key={course.section_id || courseIdx} style={{ borderBottom: "1px solid var(--crown-border)" }}>
                      <td style={{ padding: "8px 10px" }}>{course.course_code}</td>
                      <td style={{ padding: "8px 10px" }}>
                        {course.course_name}
                        {course.dual_enrollment_label ? <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>{course.dual_enrollment_label}</div> : null}
                        {course.provider ? <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>{course.provider}</div> : null}
                      </td>
                      <td style={{ padding: "8px 10px" }}>{course.teacher_name || "-"}</td>
                      <td style={{ textAlign: "center", padding: "8px 10px" }}>
                        <strong>{course.final_letter || "-"}</strong>
                        {course.final_percent !== null && course.final_percent !== undefined ? <div style={{ fontSize: 11 }}>{Number(course.final_percent).toFixed(1)}%</div> : null}
                      </td>
                      <td style={{ textAlign: "center", padding: "8px 10px" }}>{Number(course.credits || 0).toFixed(2)}</td>
                      <td style={{ textAlign: "center", padding: "8px 10px" }}>{Number(course.earned_credits || 0).toFixed(2)}</td>
                      <td style={{ textAlign: "center", padding: "8px 10px" }}>{course.record_status === "final" ? "Final" : "In Progress"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )) : (
            <p style={{ color: "var(--crown-muted)", fontStyle: "italic", textAlign: "center", padding: 40 }}>No transcript data available for this student.</p>
          )}

          <div style={{ marginTop: 28, padding: 16, backgroundColor: "var(--crown-surface-2)", border: "1px solid var(--crown-border)", borderRadius: 4 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h4 style={{ margin: 0, marginBottom: 4 }}>Cumulative GPA</h4>
                <p style={{ margin: 0, fontSize: 13, color: "var(--crown-muted)" }}>Credit-weighted GPA from finalized transcript records.</p>
              </div>
              <div style={{ fontSize: 32, fontWeight: 700, color: "var(--crown-ink)" }}>
                {transcript.cumulative_gpa !== null && transcript.cumulative_gpa !== undefined ? Number(transcript.cumulative_gpa).toFixed(2) : "-"}
              </div>
            </div>
          </div>

          {transcript.notes?.length ? (
            <div style={{ marginTop: 24, fontSize: 12, color: "var(--crown-muted)", borderTop: "1px solid var(--crown-border)", paddingTop: 16 }}>
              <p style={{ margin: 0, marginBottom: 8, fontWeight: 500 }}>Notes:</p>
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {transcript.notes.map((note, idx) => <li key={idx} style={{ marginBottom: 4 }}>{note}</li>)}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}

      <style>{`
        @media print {
          .no-print, .crown-sidebar, .crown-pagehead { display: none !important; }
          body { margin: 0; padding: 20px; }
          .transcript-content { width: 100%; }
          h2, h3 { page-break-after: avoid; }
          table { page-break-inside: avoid; }
        }
      `}</style>
    </CrownLayout>
  );
}
