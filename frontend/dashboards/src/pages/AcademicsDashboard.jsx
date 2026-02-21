import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import {
  fetchParentStudents,
  fetchSections,
  fetchStudentSections,
  fetchSectionRoster,
} from '../api/academics.js';
import { getGradebookGrades, getSectionAssignments } from '../api/gradebook.js';
import { getSelectedSchoolId } from '../utils/authClient.js';
import { logApiRequest, logApiError } from '../utils/requestTracing.js';
import { CurriculumPacingCard } from '../components/CurriculumPacingCard.jsx';
import CrownLayout from '../components/crown/CrownLayout.jsx';

export function AcademicsDashboard() {
  const [schoolId, setSchoolId] = useState('');
  const [sections, setSections] = useState([]);
  const [sectionsError, setSectionsError] = useState('');
  const [parentStudents, setParentStudents] = useState([]);
  const [studentSchedules, setStudentSchedules] = useState({});
  const [parentError, setParentError] = useState('');
  const [lookupId, setLookupId] = useState('');
  const [lookupRows, setLookupRows] = useState([]);
  const [lookupError, setLookupError] = useState('');
  const [selectedSectionId, setSelectedSectionId] = useState(null);
  const [rosterData, setRosterData] = useState(null);
  const [rosterLoading, setRosterLoading] = useState(false);
  const [rosterError, setRosterError] = useState('');
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [studentGradesLoading, setStudentGradesLoading] = useState(false);
  const [studentGradesError, setStudentGradesError] = useState('');
  const [studentGradeRow, setStudentGradeRow] = useState(null);
  const [assignmentsLoading, setAssignmentsLoading] = useState(false);
  const [assignmentsError, setAssignmentsError] = useState('');
  const [assignments, setAssignments] = useState(null);

  // Initialize schoolId from authClient (which checks sessionStorage first, then localStorage)
  useEffect(() => {
    const id = getSelectedSchoolId();
    setSchoolId(id);
  }, []);

  useEffect(() => {
    fetchSections()
      .then((data) => setSections(data.results || []))
      .catch((err) => setSectionsError(err.message));
  }, []);

  useEffect(() => {
    fetchParentStudents()
      .then((students) => {
        setParentStudents(students || []);
        return Promise.all(
          (students || []).map((st) =>
            fetchStudentSections(st.student_id).then((rows) => ({
              studentId: st.student_id,
              rows: rows || [],
            }))
          )
        );
      })
      .then((results) => {
        if (!results) return;
        const next = {};
        results.forEach((r) => {
          next[r.studentId] = r.rows;
        });
        setStudentSchedules(next);
      })
      .catch((err) => setParentError(err.message));
  }, []);

  const handleLookup = () => {
    setLookupError('');
    setLookupRows([]);
    const trimmed = (lookupId || '').trim();
    if (!trimmed) return;
    fetchStudentSections(trimmed)
      .then((rows) => setLookupRows(rows || []))
      .catch((err) => setLookupError(err.message));
  };

  const handleOpenRoster = async (sectionId) => {
    setSelectedSectionId(sectionId);
    setRosterLoading(true);
    setRosterError('');
    setRosterData(null);
    setSelectedStudent(null);
    setStudentGradeRow(null);
    setStudentGradesError('');
    setStudentGradesLoading(false);
    setAssignments(null);
    setAssignmentsError('');
    setAssignmentsLoading(false);

    try {
      const data = await fetchSectionRoster(sectionId);
      setRosterData(data);
    } catch (err) {
      // err could be Error | string | object depending on _fetchJson
      const msg =
        (err && typeof err === 'object' && 'message' in err && err.message) ||
        (typeof err === 'string' && err) ||
        'Failed to load roster.';
      setRosterError(msg);
    } finally {
      setRosterLoading(false);
    }
  };

  const handleCloseRoster = () => {
    setSelectedSectionId(null);
    setRosterData(null);
    setRosterError('');
    setSelectedStudent(null);
    setStudentGradeRow(null);
    setStudentGradesError('');
    setStudentGradesLoading(false);
    setAssignments(null);
    setAssignmentsError('');
    setAssignmentsLoading(false);
  };

  const handleOpenStudent = (student) => {
    setSelectedStudent(student);
    setStudentGradeRow(null);
    setStudentGradesError('');
    setAssignments(null);
    setAssignmentsError('');
  };

  const handleCloseStudent = () => {
    setSelectedStudent(null);
    setStudentGradeRow(null);
    setStudentGradesError('');
    setAssignments(null);
    setAssignmentsError('');
  };

  const handleLoadAssignments = async () => {
    if (!selectedSectionId) {
      setAssignmentsError('Missing section id.');
      return;
    }

    setAssignmentsLoading(true);
    setAssignmentsError('');
    setAssignments(null);

    try {
      logApiRequest('GET', `/api/v1/academics/sections/${selectedSectionId}/assignments/`, {
        message: 'Loading assignments for section',
      });

      const data = await getSectionAssignments(selectedSectionId);
      const items = data?.assignments ?? [];

      if (items.length === 0) {
        logApiRequest('GET', `/api/v1/academics/sections/${selectedSectionId}/assignments/`, {
          message: 'No assignments found (demo data may be limited)',
        });
        // Empty state is expected during demo
        return;
      }

      setAssignments(items);
    } catch (err) {
      logApiError('GET', `/api/v1/academics/sections/${selectedSectionId}/assignments/`, err, {
        body: err.body || '',
      });
      const msg =
        (err && typeof err === 'object' && 'message' in err && err.message) ||
        (typeof err === 'string' && err) ||
        'Failed to load assignments.';
      setAssignmentsError(msg);
    } finally {
      setAssignmentsLoading(false);
    }
  };

  const handleLoadStudentGradebook = async () => {
    if (!selectedSectionId) {
      setStudentGradesError('Missing section id.');
      return;
    }
    if (!selectedStudent?.student_id) {
      setStudentGradesError('Missing student id.');
      return;
    }

    setStudentGradesLoading(true);
    setStudentGradesError('');
    setStudentGradeRow(null);

    try {
      logApiRequest('GET', `/api/v1/gradebook/sections/${selectedSectionId}/grades/`, {
        message: `Loading gradebook for ${selectedStudent.name}`,
      });

      const data = await getGradebookGrades(selectedSectionId);

      const rows = data?.rows ?? [];
      const row =
        rows.find((r) => r?.student?.student_id === selectedStudent.student_id) ?? null;

      if (!row) {
        // Empty state: no grades yet, but this is normal during demo
        logApiRequest('GET', `/api/v1/gradebook/sections/${selectedSectionId}/grades/`, {
          message: 'No gradebook row found (demo data may be limited)',
        });
        setStudentGradeRow(null);
        return;
      }

      setStudentGradeRow(row);
    } catch (err) {
      logApiError('GET', `/api/v1/gradebook/sections/${selectedSectionId}/grades/`, err, {
        body: err.body || '',
      });
      const msg =
        (err && typeof err === 'object' && 'message' in err && err.message) ||
        (typeof err === 'string' && err) ||
        'Failed to load gradebook.';
      setStudentGradesError(msg);
    } finally {
      setStudentGradesLoading(false);
    }
  };

  return (
    <CrownLayout title="Academics" subtitle="Read Only">

      {/* Curriculum Pacing Summary */}
      <section style={{ marginBottom: 32 }}>
        <CurriculumPacingCard schoolId={schoolId} />
      </section>

      <section style={{ marginBottom: 32 }}>
        <h2>Teacher Sections</h2>
        {sectionsError ? (
          <div style={{ color: 'crimson' }}>{sectionsError}</div>
        ) : (
          <table border="1" cellPadding="8" style={{ borderCollapse: 'collapse', width: '100%' }}>
            <thead>
              <tr>
                <th>Course</th>
                <th>Term</th>
                <th>Teacher</th>
                <th>Roster Count</th>
              </tr>
            </thead>
            <tbody>
              {sections.map((row) => (
                <tr key={row.section_id}>
                  <td>{row.course_code} — {row.course_name}</td>
                  <td>{row.term_code || row.term_id}</td>
                  <td>{row.teacher_name || '—'}</td>
                  <td>
                    <Link to={`/gradebook/${row.section_id}`}>
                      {row.roster_count ?? 0} students
                    </Link>
                  </td>
                </tr>
              ))}
              {sections.length === 0 && (
                <tr>
                  <td colSpan="4">No sections available.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </section>

      <section style={{ marginBottom: 32 }}>
        <h2>Parent Students</h2>
        {parentError ? (
          <div style={{ color: 'crimson' }}>{parentError}</div>
        ) : (
          <div>
            {parentStudents.length === 0 && <div>No linked students.</div>}
            {parentStudents.map((st) => (
              <div key={st.student_id} style={{ marginBottom: 16 }}>
                <strong>{st.first_name} {st.last_name}</strong> (Grade {st.grade_level})
                <table border="1" cellPadding="8" style={{ borderCollapse: 'collapse', width: '100%', marginTop: 8 }}>
                  <thead>
                    <tr>
                      <th>Course</th>
                      <th>Term</th>
                      <th>Teacher</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(studentSchedules[st.student_id] || []).map((row) => (
                      <tr key={`${st.student_id}-${row.section_id}`}>
                        <td>{row.course_code} — {row.course_name}</td>
                        <td>{row.term_code || row.term_id}</td>
                        <td>{row.teacher_name || '—'}</td>
                      </tr>
                    ))}
                    {(studentSchedules[st.student_id] || []).length === 0 && (
                      <tr>
                        <td colSpan="3">No sections available.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2>Student Schedule Lookup</h2>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
          <input
            type="text"
            placeholder="Student UUID"
            value={lookupId}
            onChange={(e) => setLookupId(e.target.value)}
            style={{ width: 320 }}
          />
          <button onClick={handleLookup}>Load</button>
        </div>
        {lookupError && <div style={{ color: 'crimson' }}>{lookupError}</div>}
        <table border="1" cellPadding="8" style={{ borderCollapse: 'collapse', width: '100%' }}>
          <thead>
            <tr>
              <th>Course</th>
              <th>Term</th>
              <th>Teacher</th>
            </tr>
          </thead>
          <tbody>
            {lookupRows.map((row) => (
              <tr key={`lookup-${row.section_id}`}>
                <td>{row.course_code} — {row.course_name}</td>
                <td>{row.term_code || row.term_id}</td>
                <td>{row.teacher_name || '—'}</td>
              </tr>
            ))}
            {lookupRows.length === 0 && (
              <tr>
                <td colSpan="3">No sections loaded.</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      {selectedSectionId && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            justifyContent: 'flex-end',
            zIndex: 1000,
          }}
        >
          <div
            data-testid="roster-drawer"
            style={{
              width: '100%',
              maxWidth: 480,
              backgroundColor: 'white',
              display: 'flex',
              flexDirection: 'column',
              height: '100%',
            }}
          >
            {/* Header */}
            <div
              style={{
                padding: 16,
                borderBottom: '1px solid #e0e0e0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                {rosterData && (
                  <>
                    <h3 style={{ margin: '0 0 4px 0' }}>{rosterData.section_name}</h3>
                    <p style={{ margin: 0, fontSize: 12, color: '#666' }}>
                      {rosterData.course_code}
                    </p>
                  </>
                )}
              </div>
              <button
                onClick={handleCloseRoster}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: 20,
                  cursor: 'pointer',
                  color: '#666',
                }}
              >
                ✕
              </button>
            </div>

            {/* Content */}
            <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
              {rosterLoading && <div>Loading roster...</div>}
              {rosterError && <div style={{ color: 'crimson' }}>Error: {rosterError}</div>}
              {rosterData && (
                <>
                  {/* Term + Teacher */}
                  <div style={{ marginBottom: 16 }}>
                    {rosterData.term && (
                      <div style={{ marginBottom: 8 }}>
                        <strong>Term:</strong> {rosterData.term.name}
                      </div>
                    )}
                    {rosterData.teacher && (
                      <div>
                        <strong>Teacher:</strong> {rosterData.teacher.name} ({rosterData.teacher.email})
                      </div>
                    )}
                  </div>

                  {/* Student Count Badge */}
                  {(() => {
                    const rosterCount =
                      rosterData?.counts?.students ??
                      (rosterData?.students?.length ?? 0);
                    return (
                      <div
                        style={{
                          backgroundColor: '#e8f4f8',
                          padding: '8px 12px',
                          borderRadius: 4,
                          marginBottom: 16,
                          fontSize: 12,
                        }}
                      >
                        <strong>{rosterCount}</strong> students enrolled
                      </div>
                    );
                  })()}

                  {/* Student Snapshot OR Student List */}
                  <div>
                    {selectedStudent ? (
                      <div style={{ border: '1px solid #eee', borderRadius: 6, padding: 12 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <strong>Student Snapshot</strong>
                          <button
                            onClick={handleCloseStudent}
                            style={{
                              background: 'none',
                              border: 'none',
                              cursor: 'pointer',
                              color: '#0066cc',
                              padding: 0,
                              font: 'inherit',
                            }}
                          >
                            ← Back to roster
                          </button>
                        </div>

                        <div style={{ marginTop: 10 }}>
                          <div style={{ fontSize: 14, fontWeight: 600 }}>{selectedStudent.name}</div>
                          <div style={{ marginTop: 4, fontSize: 12, color: '#666' }}>
                            Grade: {selectedStudent.grade_level}
                          </div>
                          <div style={{ marginTop: 4, fontSize: 12, color: '#666' }}>
                            Enrollment: {selectedStudent.enrollment_status ?? 'Unknown'}
                          </div>
                          <div style={{ marginTop: 4, fontSize: 12, color: '#999' }}>
                            Student ID: {selectedStudent.student_id}
                          </div>
                        </div>

                        <div style={{ marginTop: 12 }}>
                          <strong style={{ display: 'block', marginBottom: 8, fontSize: 12 }}>Quick links</strong>

                          <button
                            data-testid="btn-load-gradebook"
                            onClick={handleLoadStudentGradebook}
                            disabled={studentGradesLoading}
                            style={{ width: '100%', padding: 8, marginBottom: 8, cursor: 'pointer' }}
                          >
                            {studentGradesLoading ? 'Loading gradebook...' : 'Load gradebook'}
                          </button>
                          <button disabled style={{ width: '100%', padding: 8, marginBottom: 8 }}>
                            Attendance (coming soon)
                          </button>
                          <button
                            data-testid="btn-load-assignments"
                            onClick={handleLoadAssignments}
                            disabled={assignmentsLoading}
                            style={{ width: '100%', padding: 8, marginBottom: 8, cursor: 'pointer' }}
                          >
                            {assignmentsLoading ? 'Loading assignments...' : 'Load assignments'}
                          </button>
                        </div>

                        {studentGradesError && (
                          <div
                            style={{
                              marginTop: 10,
                              color: 'crimson',
                              fontSize: 12,
                              backgroundColor: '#ffe8e8',
                              padding: 10,
                              borderRadius: 4,
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                            }}
                          >
                            <span>{studentGradesError}</span>
                            <button
                              onClick={handleLoadStudentGradebook}
                              style={{
                                background: 'none',
                                border: 'none',
                                color: '#0066cc',
                                cursor: 'pointer',
                                padding: '0 4px',
                                font: 'inherit',
                                textDecoration: 'underline',
                              }}
                            >
                              Retry
                            </button>
                          </div>
                        )}

                        {!studentGradesError && !studentGradeRow && (
                          <div
                            style={{
                              marginTop: 10,
                              color: '#666',
                              fontSize: 12,
                              backgroundColor: '#f5f5f5',
                              padding: 10,
                              borderRadius: 4,
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                            }}
                          >
                            <span>No gradebook data yet (demo data may be limited).</span>
                            <button
                              onClick={handleLoadStudentGradebook}
                              style={{
                                background: 'none',
                                border: 'none',
                                color: '#0066cc',
                                cursor: 'pointer',
                                padding: '0 4px',
                                font: 'inherit',
                                textDecoration: 'underline',
                              }}
                            >
                              Refresh
                            </button>
                          </div>
                        )}

                        {studentGradeRow && (
                          <div style={{ marginTop: 10 }}>
                            <strong style={{ display: 'block', marginBottom: 6, fontSize: 12 }}>
                              Gradebook (section)
                            </strong>

                            <div style={{ fontSize: 12, color: '#666', marginBottom: 6 }}>
                              Scores shown are per-assignment points earned / possible.
                            </div>

                            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                              {Object.entries(studentGradeRow.scores ?? {}).slice(0, 8).map(([k, v]) => (
                                <li key={k} style={{ padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
                                  <div style={{ fontSize: 13 }}>{k}</div>
                                  <div style={{ fontSize: 11, color: '#999' }}>
                                    {(v?.points_earned ?? '—')} / {(v?.points_possible ?? '—')}
                                  </div>
                                </li>
                              ))}
                            </ul>

                            {Object.keys(studentGradeRow.scores ?? {}).length > 8 && (
                              <div style={{ marginTop: 6, fontSize: 11, color: '#999' }}>
                                Showing first 8 items.
                              </div>
                            )}
                          </div>
                        )}

                        {assignmentsError && (
                          <div
                            style={{
                              marginTop: 10,
                              color: 'crimson',
                              fontSize: 12,
                              backgroundColor: '#ffe8e8',
                              padding: 10,
                              borderRadius: 4,
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                            }}
                          >
                            <span>{assignmentsError}</span>
                            <button
                              onClick={handleLoadAssignments}
                              style={{
                                background: 'none',
                                border: 'none',
                                color: '#0066cc',
                                cursor: 'pointer',
                                padding: '0 4px',
                                font: 'inherit',
                                textDecoration: 'underline',
                              }}
                            >
                              Retry
                            </button>
                          </div>
                        )}

                        {!assignmentsError && assignments && assignments.length === 0 && (
                          <div
                            style={{
                              marginTop: 10,
                              color: '#666',
                              fontSize: 12,
                              backgroundColor: '#f5f5f5',
                              padding: 10,
                              borderRadius: 4,
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                            }}
                          >
                            <span>No assignments yet (demo data may be limited).</span>
                            <button
                              onClick={handleLoadAssignments}
                              style={{
                                background: 'none',
                                border: 'none',
                                color: '#0066cc',
                                cursor: 'pointer',
                                padding: '0 4px',
                                font: 'inherit',
                                textDecoration: 'underline',
                              }}
                            >
                              Refresh
                            </button>
                          </div>
                        )}

                        {assignments && (
                          <div style={{ marginTop: 10 }}>
                            <strong style={{ display: 'block', marginBottom: 6, fontSize: 12 }}>
                              Assignments (section)
                            </strong>

                            <div style={{ fontSize: 12, color: '#666', marginBottom: 6 }}>
                              All assignments in this section with max points possible.
                            </div>

                            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                              {assignments.slice(0, 8).map((a) => (
                                <li key={a.assignment_name} style={{ padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
                                  <div style={{ fontSize: 13 }}>{a.assignment_name}</div>
                                  <div style={{ fontSize: 11, color: '#999' }}>
                                    Points Possible: {a.points_possible ?? '—'}
                                  </div>
                                </li>
                              ))}
                            </ul>

                            {assignments.length > 8 && (
                              <div style={{ marginTop: 6, fontSize: 11, color: '#999' }}>
                                Showing first 8 of {assignments.length} items.
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ) : (
                      <>
                        <strong style={{ display: 'block', marginBottom: 8 }}>Roster</strong>

                        {(rosterData?.students ?? []).length === 0 ? (
                          <div style={{ fontSize: 12, color: '#666' }}>No students enrolled.</div>
                        ) : (
                          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                            {(rosterData?.students ?? []).map((student) => (
                              <li
                                key={student.student_id}
                                onClick={() => handleOpenStudent(student)}
                                role="button"
                                tabIndex={0}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter' || e.key === ' ') handleOpenStudent(student);
                                }}
                                style={{
                                  padding: '8px',
                                  borderBottom: '1px solid #f0f0f0',
                                  fontSize: 13,
                                  cursor: 'pointer',
                                }}
                                title="Open student snapshot"
                              >
                                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                                  <div>
                                    <div>{student.name}</div>
                                    <div style={{ fontSize: 11, color: '#999' }}>
                                      Grade {student.grade_level}
                                    </div>
                                  </div>
                                  <div style={{ fontSize: 11, color: '#999', alignSelf: 'center' }}>
                                    ›
                                  </div>
                                </div>
                              </li>
                            ))}
                          </ul>
                        )}
                      </>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </CrownLayout>
  );
}
