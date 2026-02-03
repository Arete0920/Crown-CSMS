import React, { useEffect, useMemo, useState } from "react";
import { getGradebookSections, getGradebookGrades } from "../api/gradebook";

export function GradebookRO() {
  const [sections, setSections] = useState([]);
  const [sectionId, setSectionId] = useState("");
  const [grid, setGrid] = useState(null);
  const [loadingSections, setLoadingSections] = useState(false);
  const [loadingGrid, setLoadingGrid] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    setLoadingSections(true);
    setError("");

    getGradebookSections()
      .then((data) => {
        if (!mounted) return;
        const results = data?.results ?? data ?? [];
        setSections(results);
        // auto-select first section
        if (results.length && !sectionId) {
          setSectionId(results[0].id);
        }
      })
      .catch((e) => {
        if (!mounted) return;
        setError(e?.message || "Failed to load sections.");
      })
      .finally(() => mounted && setLoadingSections(false));

    return () => {
      mounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!sectionId) return;
    let mounted = true;
    setLoadingGrid(true);
    setError("");

    getGradebookGrades(sectionId)
      .then((data) => mounted && setGrid(data))
      .catch((e) => mounted && setError(e?.message || "Failed to load gradebook."))
      .finally(() => mounted && setLoadingGrid(false));

    return () => {
      mounted = false;
    };
  }, [sectionId]);

  const { students, assignments } = useMemo(() => {
    // Backend returns: { section_id, assignments: [], rows: [] }
    // rows: [{ student: {}, scores: { "Assignment Name": { points_earned, points_possible } } }]
    const rows = grid?.rows ?? [];
    const assigns = grid?.assignments ?? [];
    
    const studentList = rows.map(row => row.student);
    
    return { students: studentList, assignments: assigns };
  }, [grid]);

  function sectionLabel(sec) {
    const course = sec?.course?.code || sec?.course?.name || "";
    const section = sec?.section_number || "";
    const term = sec?.term_ref?.name || "";
    return `${course} ${section} (${term})`.trim() || sec?.name || sec?.id;
  }

  function studentLabel(stu) {
    const first = stu?.first_name || "";
    const last = stu?.last_name || "";
    const name = `${last}, ${first}`.trim();
    return name || stu?.full_name || stu?.id;
  }

  function assignmentLabel(asn) {
    return asn?.assignment_name || asn?.name || asn?.title || asn?.id;
  }

  function findScore(rowIndex, assignmentName) {
    const row = grid?.rows?.[rowIndex];
    if (!row?.scores) return null;
    return row.scores[assignmentName] || null;
  }

  function formatScore(score) {
    if (!score) return "";
    const earned = score.points_earned ?? null;
    const possible = score.points_possible ?? null;
    if (earned == null && possible == null) return "";
    if (possible == null) return `${earned}`;
    return `${earned}/${possible}`;
  }

  return (
    <div style={{ padding: 16, fontFamily: 'system-ui, sans-serif' }}>
      <h2>Gradebook (Read-Only)</h2>

      {error ? (
        <div style={{ margin: "12px 0", padding: 12, border: "1px solid #cc0000", backgroundColor: '#ffe6e6' }}>
          <strong>Error:</strong> {error}
        </div>
      ) : null}

      <div style={{ margin: "12px 0" }}>
        <label style={{ marginRight: 8 }}>Section:</label>
        {loadingSections ? (
          <span>Loading…</span>
        ) : (
          <select value={sectionId} onChange={(e) => setSectionId(e.target.value)} style={{ padding: 4, minWidth: 300 }}>
            {sections.map((sec) => (
              <option key={sec.id} value={sec.id}>
                {sectionLabel(sec)}
              </option>
            ))}
          </select>
        )}
      </div>

      {loadingGrid ? <div>Loading gradebook…</div> : null}

      {!loadingGrid && students?.length ? (
        <div style={{ overflowX: "auto", border: "1px solid #ddd", marginTop: 16 }}>
          <table cellPadding="8" style={{ borderCollapse: "collapse", width: "100%", fontSize: 14 }}>
            <thead>
              <tr style={{ backgroundColor: '#f5f5f5' }}>
                <th style={{ borderBottom: "2px solid #ddd", textAlign: "left", position: 'sticky', left: 0, backgroundColor: '#f5f5f5' }}>Student</th>
                {assignments.map((a, idx) => (
                  <th key={idx} style={{ borderBottom: "2px solid #ddd", textAlign: "center", minWidth: 120 }}>
                    {assignmentLabel(a)}
                    <div style={{ fontSize: 11, color: '#666', fontWeight: 'normal' }}>
                      (/{a.points_possible || '?'})
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {students.map((s, studentIdx) => (
                <tr key={s.id || studentIdx}>
                  <td style={{ borderBottom: "1px solid #eee", fontWeight: 500, position: 'sticky', left: 0, backgroundColor: '#fff' }}>
                    {studentLabel(s)}
                  </td>
                  {assignments.map((a, assignIdx) => {
                    const score = findScore(studentIdx, assignmentLabel(a));
                    return (
                      <td key={assignIdx} style={{ borderBottom: "1px solid #eee", textAlign: "center" }}>
                        {formatScore(score)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {!loadingGrid && sectionId && !students?.length ? (
        <div style={{ marginTop: 16, padding: 12, backgroundColor: '#f0f0f0' }}>
          No roster data for this section.
        </div>
      ) : null}
    </div>
  );
}
