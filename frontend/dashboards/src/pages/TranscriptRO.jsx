import { useEffect, useState } from "react";
import { fetchStudents, fetchTranscript } from "../api/academics";
import { downloadOfficialTranscript, issueOfficialTranscript } from "../api/transcript.js";
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
    fetchTranscript(selectedStudentId)
      .then((data) => {
        setTranscript(data);
        setIssuance(null);
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
      const issued = await issueOfficialTranscript(selectedStudentId);
      setIssuance(issued);
      await downloadOfficialTranscript(issued.issuance_id, issued.filename);
    } catch (err) {
      setError(err.message);
    } finally {
      setIssuing(false);
    }
  };

  return (
    <CrownLayout title="Transcript" subtitle="Student Record">
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
          <button className="crown-btn" onClick={() => window.print()} disabled={!transcript}>
            Print Unofficial Copy
          </button>
          <button
            className="crown-btn crown-btn-primary"
            onClick={handleIssueOfficial}
            disabled={!transcript || issuing}
          >
            {issuing ? "Issuing..." : "Issue Official PDF"}
          </button>
        </div>

        <p style={{ margin: "0 0 12px", fontSize: 13, color: "var(--crown-muted)" }}>
          Official issuance is restricted to authorized registrar/head-of-school roles and creates an immutable audit snapshot with SHA-256 provenance.
        </p>
        {issuance ? (
          <div role="status" style={{ marginBottom: 12, fontSize: 13 }}>
            Official transcript issued. ID: <code>{issuance.issuance_id}</code> · Source SHA-256: <code>{issuance.source_sha256}</code>
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
              </tbody>
            </table>
          </div>

          {transcript.terms?.length ? transcript.terms.map((term, idx) => (
            <div key={term.term_id || idx} style={{ marginBottom: 32, pageBreakInside: "avoid" }}>
              <h3 style={{ marginTop: 0, marginBottom: 12, paddingBottom: 8, borderBottom: "2px solid var(--crown-ink)" }}>
                {term.term_name}
                {term.term_gpa !== null && term.term_gpa !== undefined ? (
                  <span style={{ float: "right", fontSize: 14, fontWeight: 400, color: "var(--crown-muted)" }}>
                    Term GPA: {Number(term.term_gpa).toFixed(2)}
                  </span>
                ) : null}
              </h3>
              <div style={{ fontSize: 12, color: "var(--crown-muted)", marginBottom: 8 }}>
                Attempted credits: {Number(term.attempted_credits || 0).toFixed(2)} · Earned credits: {Number(term.earned_credits || 0).toFixed(2)}
              </div>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, marginBottom: 16 }}>
                <thead>
                  <tr style={{ backgroundColor: "var(--crown-surface-2)", borderBottom: "2px solid var(--crown-border)" }}>
                    <th style={{ textAlign: "left", padding: "8px 12px" }}>Course</th>
                    <th style={{ textAlign: "left", padding: "8px 12px" }}>Course Name</th>
                    <th style={{ textAlign: "left", padding: "8px 12px" }}>Teacher</th>
                    <th style={{ textAlign: "center", padding: "8px 12px" }}>Grade</th>
                    <th style={{ textAlign: "center", padding: "8px 12px" }}>Letter</th>
                    <th style={{ textAlign: "center", padding: "8px 12px" }}>Credits</th>
                    <th style={{ textAlign: "center", padding: "8px 12px" }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {term.courses.map((course, courseIdx) => (
                    <tr key={course.section_id || courseIdx} style={{ borderBottom: "1px solid var(--crown-border)" }}>
                      <td style={{ padding: "8px 12px" }}>{course.course_code}</td>
                      <td style={{ padding: "8px 12px" }}>
                        {course.course_name}
                        {course.provider ? <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>{course.provider}</div> : null}
                        {course.dual_enrollment_label ? <div style={{ fontSize: 11, color: "var(--crown-muted)" }}>{course.dual_enrollment_label}</div> : null}
                      </td>
                      <td style={{ padding: "8px 12px" }}>{course.teacher_name || "-"}</td>
                      <td style={{ textAlign: "center", padding: "8px 12px" }}>{course.final_percent !== null && course.final_percent !== undefined ? `${Number(course.final_percent).toFixed(1)}%` : "-"}</td>
                      <td style={{ textAlign: "center", padding: "8px 12px", fontWeight: 600 }}>{course.final_letter || "-"}</td>
                      <td style={{ textAlign: "center", padding: "8px 12px" }}>{Number(course.credits || 0).toFixed(2)}</td>
                      <td style={{ textAlign: "center", padding: "8px 12px" }}>{course.status === "recorded" ? "Recorded" : "In Progress"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )) : (
            <p style={{ color: "var(--crown-muted)", fontStyle: "italic", textAlign: "center", padding: 40 }}>No transcript data available for this student.</p>
          )}

          <div style={{ marginTop: 32, padding: 16, backgroundColor: "var(--crown-surface-2)", border: "1px solid var(--crown-border)", borderRadius: 4 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 20 }}>
              <div>
                <h4 style={{ margin: "0 0 4px" }}>Cumulative GPA</h4>
                <p style={{ margin: 0, fontSize: 13, color: "var(--crown-muted)" }}>
                  Credit-weighted from recorded TranscriptEntry GPA points. In-progress Gradebook previews are excluded.
                </p>
                <p style={{ margin: "6px 0 0", fontSize: 13 }}>
                  Attempted credits: {Number(transcript.attempted_credits || 0).toFixed(2)} · Earned credits: {Number(transcript.earned_credits || 0).toFixed(2)}
                </p>
              </div>
              <div style={{ fontSize: 32, fontWeight: 700, color: "var(--crown-ink)" }}>
                {transcript.cumulative_gpa !== null && transcript.cumulative_gpa !== undefined ? Number(transcript.cumulative_gpa).toFixed(2) : "N/A"}
              </div>
            </div>
          </div>
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
