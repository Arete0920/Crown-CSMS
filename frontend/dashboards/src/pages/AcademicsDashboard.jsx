import { useEffect, useState } from 'react';

import {
  fetchParentStudents,
  fetchSections,
  fetchStudentSections,
  fetchSectionRoster,
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
  const [selectedSectionId, setSelectedSectionId] = useState(null);
  const [rosterData, setRosterData] = useState(null);
  const [rosterLoading, setRosterLoading] = useState(false);
  const [rosterError, setRosterError] = useState('');

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
                  <td>
                    <button
                      onClick={() => handleOpenRoster(row.section_id)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#0066cc',
                        cursor: 'pointer',
                        textDecoration: 'underline',
                        padding: 0,
                        font: 'inherit',
                      }}
                    >
                      {row.roster_count ?? 0} students
                    </button>
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

                  {/* Student List */}
                  <div>
                    <strong style={{ display: 'block', marginBottom: 8 }}>Roster</strong>
                    {(rosterData?.students ?? []).length === 0 ? (
                      <div style={{ fontSize: 12, color: '#666' }}>
                        No students enrolled.
                      </div>
                    ) : (
                      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                        {(rosterData?.students ?? []).map((student) => (
                          <li
                            key={student.student_id}
                            style={{
                              padding: '8px',
                              borderBottom: '1px solid #f0f0f0',
                              fontSize: 13,
                            }}
                          >
                            <div>{student.name}</div>
                            <div style={{ fontSize: 11, color: '#999' }}>
                              Grade {student.grade_level}
                            </div>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
