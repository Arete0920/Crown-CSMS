import { useEffect, useState } from "react";
import { fetchStudents, fetchTranscript } from "../api/academics";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import ErrorBanner from "../components/ui/ErrorBanner.jsx";

export function TranscriptRO() {
  const [students, setStudents] = useState([]);
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [transcript, setTranscript] = useState(null);
  const [loadingStudents, setLoadingStudents] = useState(true);
  const [loadingTranscript, setLoadingTranscript] = useState(false);
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
      .catch((err) => {
        console.error("Failed to load students:", err);
        setError(`Failed to load students: ${err.message}`);
      })
      .finally(() => setLoadingStudents(false));
  }, []);

  useEffect(() => {
    if (!selectedStudentId) {
      return;
    }

    fetchTranscript(selectedStudentId)
      .then((data) => {
        setTranscript(data);
        setError(null);
      })
      .catch((err) => {
        console.error("Failed to load transcript:", err);
        setError(`Failed to load transcript: ${err.message}`);
        setTranscript(null);
      })
      .finally(() => setLoadingTranscript(false));
  }, [selectedStudentId]);

  const handleStudentChange = (event) => {
    setLoadingTranscript(true);
    setSelectedStudentId(event.target.value);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <CrownLayout title="Transcript" subtitle="Read Only">
      <div className="no-print" style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", gap: 16, alignItems: "center", marginBottom: 16 }}>
          <label htmlFor="transcript-student-select" style={{ fontWeight: 500 }}>
            Student:
          </label>
          <select
            id="transcript-student-select"
            value={selectedStudentId}
            onChange={handleStudentChange}
            disabled={loadingStudents}
            aria-label="Student"
            style={{
              padding: "6px 12px",
              fontSize: 14,
              borderRadius: 4,
              border: "1px solid var(--crown-border)",
              minWidth: 300,
            }}
          >
            {loadingStudents ? <option>Loading students...</option> : null}
            {!loadingStudents && students.length === 0 ? <option>No students found</option> : null}
            {students.map((student) => (
              <option key={student.id} value={student.id}>
                {student.last_name}, {student.first_name} {student.middle_name || ""} - Grade {student.grade_level || "?"}
              </option>
            ))}
          </select>

          <button
            className="crown-btn crown-btn-primary"
            onClick={handlePrint}
            disabled={!transcript}
          >
            Print
          </button>
        </div>

        {error ? <ErrorBanner title="Transcript error" message={error} /> : null}
      </div>

      {loadingTranscript ? (
        <div style={{ textAlign: "center", padding: 40, color: "var(--crown-muted)" }}>
          <p>Loading transcript...</p>
        </div>
      ) : null}

      {!loadingTranscript && transcript ? (
        <div className="transcript-content">
          <div style={{ marginBottom: 32 }}>
            <h2 style={{ marginTop: 0, marginBottom: 8 }}>Academic Transcript</h2>
            <table style={{ fontSize: 14, borderCollapse: "collapse" }}>
              <tbody>
                <tr>
                  <td style={{ paddingRight: 16, fontWeight: 500 }}>Student:</td>
                  <td>
                    {transcript.student.last_name}, {transcript.student.first_name}
                  </td>
                </tr>
                <tr>
                  <td style={{ paddingRight: 16, fontWeight: 500 }}>Student ID:</td>
                  <td style={{ fontFamily: "var(--crown-font-mono)", fontSize: 12 }}>
                    {transcript.student.student_id}
                  </td>
                </tr>
                <tr>
                  <td style={{ paddingRight: 16, fontWeight: 500 }}>Grade Level:</td>
                  <td>{transcript.student.grade_level || "-"}</td>
                </tr>
              </tbody>
            </table>
          </div>

          {transcript.terms && transcript.terms.length > 0 ? (
            <div>
              {transcript.terms.map((term, idx) => (
                <div key={term.term_id || idx} style={{ marginBottom: 32, pageBreakInside: "avoid" }}>
                  <h3
                    style={{
                      marginTop: 0,
                      marginBottom: 12,
                      paddingBottom: 8,
                      borderBottom: "2px solid var(--crown-ink)",
                    }}
                  >
                    {term.term_code}
                    {term.term_gpa_mvp !== null && term.term_gpa_mvp !== undefined ? (
                      <span style={{ float: "right", fontSize: 14, fontWeight: 400, color: "var(--crown-muted)" }}>
                        Term GPA (MVP): {Number(term.term_gpa_mvp).toFixed(2)}
                      </span>
                    ) : null}
                  </h3>

                  {term.courses && term.courses.length > 0 ? (
                    <table
                      style={{
                        width: "100%",
                        borderCollapse: "collapse",
                        fontSize: 13,
                        marginBottom: 16,
                      }}
                    >
                      <thead>
                        <tr style={{ backgroundColor: "var(--crown-surface-2)", borderBottom: "2px solid var(--crown-border)" }}>
                          <th style={{ textAlign: "left", padding: "8px 12px" }}>Course</th>
                          <th style={{ textAlign: "left", padding: "8px 12px" }}>Course Name</th>
                          <th style={{ textAlign: "left", padding: "8px 12px" }}>Teacher</th>
                          <th style={{ textAlign: "center", padding: "8px 12px" }}>Grade</th>
                          <th style={{ textAlign: "center", padding: "8px 12px" }}>Letter</th>
                          <th style={{ textAlign: "center", padding: "8px 12px" }}>Credits</th>
                        </tr>
                      </thead>
                      <tbody>
                        {term.courses.map((course, courseIdx) => (
                          <tr
                            key={course.section_id || courseIdx}
                            style={{ borderBottom: "1px solid var(--crown-border)" }}
                          >
                            <td style={{ padding: "8px 12px" }}>{course.course_code}</td>
                            <td style={{ padding: "8px 12px" }}>{course.course_name}</td>
                            <td style={{ padding: "8px 12px" }}>{course.teacher_name || "-"}</td>
                            <td style={{ textAlign: "center", padding: "8px 12px" }}>
                              {course.final_percent !== null && course.final_percent !== undefined
                                ? `${Math.round(course.final_percent)}%`
                                : "-"}
                            </td>
                            <td style={{ textAlign: "center", padding: "8px 12px", fontWeight: 600 }}>
                              {course.final_letter || "-"}
                            </td>
                            <td style={{ textAlign: "center", padding: "8px 12px" }}>
                              {course.credits !== null && course.credits !== undefined
                                ? Number(course.credits).toFixed(1)
                                : "-"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <p style={{ color: "var(--crown-muted)", fontStyle: "italic" }}>No courses for this term.</p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: "var(--crown-muted)", fontStyle: "italic", textAlign: "center", padding: 40 }}>
              No transcript data available for this student.
            </p>
          )}

          {transcript.cumulative_gpa_mvp !== null && transcript.cumulative_gpa_mvp !== undefined ? (
            <div
              style={{
                marginTop: 32,
                padding: 16,
                backgroundColor: "var(--crown-surface-2)",
                border: "1px solid var(--crown-border)",
                borderRadius: 4,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <h4 style={{ margin: 0, marginBottom: 4 }}>Cumulative GPA (MVP)</h4>
                  <p style={{ margin: 0, fontSize: 13, color: "var(--crown-muted)" }}>
                    This is a placeholder calculation pending grade weighting and official credit values.
                  </p>
                </div>
                <div style={{ fontSize: 32, fontWeight: 700, color: "var(--crown-ink)" }}>
                  {Number(transcript.cumulative_gpa_mvp).toFixed(2)}
                </div>
              </div>
            </div>
          ) : null}

          {transcript.notes && transcript.notes.length > 0 ? (
            <div style={{ marginTop: 24, fontSize: 12, color: "var(--crown-muted)", borderTop: "1px solid var(--crown-border)", paddingTop: 16 }}>
              <p style={{ margin: 0, marginBottom: 8, fontWeight: 500 }}>Notes:</p>
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                {transcript.notes.map((note, idx) => (
                  <li key={idx} style={{ marginBottom: 4 }}>
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}

      <style>{`
        @media print {
          .no-print, .crown-sidebar, .crown-pagehead {
            display: none !important;
          }
          body {
            margin: 0;
            padding: 20px;
          }
          .transcript-content {
            width: 100%;
          }
          h2, h3 {
            page-break-after: avoid;
          }
          table {
            page-break-inside: avoid;
          }
        }
      `}</style>
    </CrownLayout>
  );
}
