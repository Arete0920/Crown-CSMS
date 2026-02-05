import { useEffect, useState } from 'react';

import {
  fetchParentStudents,
  fetchSections,
  fetchStudentSections,
} from '../api/academics.js';

export function AcademicsDashboard() {
  const [sections, setSections] = useState([]);
  const [sectionsError, setSectionsError] = useState('');
  const [parentStudents, setParentStudents] = useState([]);
  const [studentSchedules, setStudentSchedules] = useState({});
  const [parentError, setParentError] = useState('');
  const [lookupId, setLookupId] = useState('');
  const [lookupRows, setLookupRows] = useState([]);
  const [lookupError, setLookupError] = useState('');

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

  return (
    <div style={{ padding: 24, fontFamily: 'system-ui, sans-serif' }}>
      <h1>Academics (Read-only)</h1>

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
                  <td>{row.roster_count ?? 0}</td>
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
    </div>
  );
}
