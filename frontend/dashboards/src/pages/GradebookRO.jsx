import { useEffect, useMemo, useRef, useState } from "react";
import { getGradebookSections, getGradebookGrades } from "../api/gradebook";
import { getSchoolId, getToken } from "../lib/api";
import { csvEscape, downloadTextFile } from "../lib/export/csv";
import { pctFromCell, bgForPct } from "../lib/ui/gradeVisuals";

const keyOf = (name) => String(name ?? "").trim();
const HEADER_ROW_HEIGHT = 40;

function formatScore(earned, possible) {
  if (earned === null || earned === undefined || earned === "") return "—";
  const e = Number(earned);
  const p = Number(possible);
  if (!Number.isFinite(e) || !Number.isFinite(p) || p <= 0) return `${earned} / ${possible}`;
  const pct = Math.round((e / p) * 100);
  return `${e} / ${p}\n(${pct}%)`;
}

const calcRowTotals = (row, assignments) => {
  let earned = 0;
  let possible = 0;

  const grades = row?._scores || {};
  for (const a of assignments || []) {
    const key = a?._key ?? a?.id;
    const cell = grades?.[key];
    const pts = Number(cell?.points_earned);
    const max = Number(cell?.points_possible ?? a?.points_possible);

    if (Number.isFinite(pts) && Number.isFinite(max) && max > 0) {
      earned += pts;
      possible += max;
    }
  }

  const pct = possible > 0 ? Math.round((earned / possible) * 100) : null;
  return { earned, possible, pct };
};

const formatTotals = ({ earned, possible, pct }) => {
  if (!possible) return "—";
  return `${earned} / ${possible}\n(${pct ?? 0}%)`;
};

export function GradebookRO() {
  const token = getToken();
  const schoolId = getSchoolId();

  const [sections, setSections] = useState([]);
  const [selectedSectionId, setSelectedSectionId] = useState("");
  const [assignments, setAssignments] = useState([]);
  const [rows, setRows] = useState([]);

  const [loadingSections, setLoadingSections] = useState(false);
  const [loadingGrades, setLoadingGrades] = useState(false);

  // sorting state
  const [rowSort, setRowSort] = useState({ key: "name", dir: "asc" });
  const [colSort, setColSort] = useState({ key: "title", dir: "asc" });

  // no double-fetch guard
  const lastFetchedSectionRef = useRef("");
  
  // track if first section was auto-selected
  const autoSelectDoneRef = useRef(false);

  // abort handling
  const gradesAbortRef = useRef(null);

  // diagnostics state (kept from before)
  const [lastRequest, setLastRequest] = useState(null);
  const [lastError, setLastError] = useState(null);

  // Load sections once
  useEffect(() => {
    let alive = true;
    setLoadingSections(true);

    getGradebookSections()
      .then((data) => {
        if (!alive) return;
        // Handle paginated response: {total, limit, offset, results: [...]}
        const sectionsList = Array.isArray(data?.results) ? data.results : (Array.isArray(data) ? data : []);
        setSections(sectionsList);
        
        // Auto-select first ROSTERED section (roster_count > 0) to avoid empty grids
        if (!autoSelectDoneRef.current && sectionsList.length > 0) {
          autoSelectDoneRef.current = true;
          const rostered = sectionsList.filter(s => (s?.roster_count ?? 0) > 0);
          const defaultSection = rostered[0]?.section_id ?? sectionsList[0]?.section_id;
          if (defaultSection) {
            setSelectedSectionId(defaultSection);
          }
        }
      })
      .catch((err) => {
        // structured error panel will surface it
        console.error(err);
      })
      .finally(() => {
        if (!alive) return;
        setLoadingSections(false);
      });

    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Fetch grades when section changes (no double-fetch)
  useEffect(() => {
    if (!selectedSectionId) return;

    // guard: do not refetch same section
    if (lastFetchedSectionRef.current === selectedSectionId) return;
    lastFetchedSectionRef.current = selectedSectionId;

    // reset current grid immediately for clean UX
    setAssignments([]);
    setRows([]);
    setLoadingGrades(true);

    // optional abort previous
    if (gradesAbortRef.current) {
      try { gradesAbortRef.current.abort(); } catch {}
    }
    const controller = new AbortController();
    gradesAbortRef.current = controller;

    getGradebookGrades(selectedSectionId, { signal: controller.signal })
      .then((payload) => {
        // payload matches real JSON
        const a = Array.isArray(payload?.assignments) ? payload.assignments : [];
        const r = Array.isArray(payload?.rows) ? payload.rows : [];

        // minimal normalization
        // Keep assignment order; also precompute a stable lookup key
        const normalizedAssignments = a.map((x) => ({
          assignment_name: x.assignment_name,
          points_possible: x.points_possible,
          _key: keyOf(x.assignment_name),
        }));

        // Normalize score keys to trim whitespace
        const normalizedRows = r.map((row) => {
          const scores = row?.scores || {};
          const normScores = {};
          for (const [k, v] of Object.entries(scores)) {
            normScores[keyOf(k)] = v;
          }
          return {
            ...row,
            _scores: normScores,
          };
        });

        setAssignments(normalizedAssignments);
        setRows(normalizedRows);
        setLastRequest((prev) => ({ ...prev, status: 200, assignments: a.length, rows: r.length }));
      })
      .catch((err) => {
        // if aborted, ignore
        if (err?.name === "AbortError") return;
        console.error(err);
        setLastError({ message: err.message, url: err.url, status: err.status, body: err.body });
      })
      .finally(() => {
        setLoadingGrades(false);
      });

    return () => {
      try { controller.abort(); } catch {}
    };
  }, [selectedSectionId]);


  const isAuthed = !!token && !!schoolId;
  const isDev = import.meta.env.DEV;
  const hasAssignments = assignments.length > 0;
  const hasRows = rows.length > 0;

  // memoize assignment keys to avoid render churn
  const assignmentKeysForHeader = useMemo(
    () => assignments.map((a) => a._key),
    [assignments]
  );

  // memoize totals per student
  const totalsByStudentId = useMemo(() => {
    const map = new Map();
    for (const r of rows || []) {
      const s = r.student || {};
      const studentId = s.student_id || `${s.first_name}-${s.last_name}`;
      map.set(studentId, calcRowTotals(r, assignments));
    }
    return map;
  }, [rows, assignments]);

  // memoize assignment averages
  const assignmentAverages = useMemo(() => {
    const map = new Map();

    for (const a of assignments || []) {
      const key = a?._key ?? a?.id;
      let earned = 0;
      let possible = 0;
      let n = 0;

      for (const r of rows || []) {
        const cell = r?._scores?.[key];
        const pts = Number(cell?.points_earned);
        const max = Number(cell?.points_possible ?? a?.points_possible);

        if (Number.isFinite(pts) && Number.isFinite(max) && max > 0) {
          earned += pts;
          possible += max;
          n += 1;
        }
      }

      const pct = possible > 0 ? Math.round((earned / possible) * 100) : null;
      map.set(key, { earned, possible, pct, n });
    }

    return map;
  }, [rows, assignments]);

  // sorted rows (client-side)
  const sortedRows = useMemo(() => {
    const arr = Array.isArray(rows) ? [...rows] : [];
    const dir = rowSort.dir === "asc" ? 1 : -1;

    arr.sort((a, b) => {
      if (rowSort.key === "totalPct") {
        const s = a.student || {};
        const studentId = s.student_id || `${s.first_name}-${s.last_name}`;
        const s2 = b.student || {};
        const studentId2 = s2.student_id || `${s2.first_name}-${s2.last_name}`;

        const ta = totalsByStudentId.get(studentId);
        const tb = totalsByStudentId.get(studentId2);
        const pa = ta?.pct ?? -1;
        const pb = tb?.pct ?? -1;
        return (pa - pb) * dir;
      }

      // default: name
      const s = a.student || {};
      const s2 = b.student || {};
      const na = (`${s.last_name ?? ""} ${s.first_name ?? ""}`).toLowerCase().trim();
      const nb = (`${s2.last_name ?? ""} ${s2.first_name ?? ""}`).toLowerCase().trim();
      if (na < nb) return -1 * dir;
      if (na > nb) return 1 * dir;
      return 0;
    });

    return arr;
  }, [rows, rowSort, totalsByStudentId]);

  // sorted assignments (client-side)
  const sortedAssignments = useMemo(() => {
    const arr = Array.isArray(assignments) ? [...assignments] : [];
    const dir = colSort.dir === "asc" ? 1 : -1;

    arr.sort((a, b) => {
      const ka = a?._key ?? a?.id;
      const kb = b?._key ?? b?.id;

      if (colSort.key === "avgPct") {
        const sa = assignmentAverages.get(ka);
        const sb = assignmentAverages.get(kb);
        const pa = sa?.pct ?? -1;
        const pb = sb?.pct ?? -1;
        return (pa - pb) * dir;
      }

      // default: title
      const ta = (a.assignment_name || "").toLowerCase();
      const tb = (b.assignment_name || "").toLowerCase();
      if (ta < tb) return -1 * dir;
      if (ta > tb) return 1 * dir;
      return 0;
    });

    return arr;
  }, [assignments, colSort, assignmentAverages]);

  // CSV export
  const selectedSectionName =
    sections.find((s) => String(s.section_id) === String(selectedSectionId))?.name ||
    sections.find((s) => String(s.section_id) === String(selectedSectionId))?.course_name ||
    "";

  const buildGradebookCsv = () => {
    const cols = sortedAssignments.map((a) => ({
      key: a?._key ?? a?.id,
      title: a?.assignment_name || "Assignment",
    }));

    const header = [
      "Student",
      ...cols.map((c) => c.title),
      "Total Earned",
      "Total Possible",
      "Total %",
    ];

    const lines = [header.map(csvEscape).join(",")];

    for (const r of sortedRows) {
      const row = [];
      row.push(r.student?.first_name && r.student?.last_name ? `${r.student.last_name}, ${r.student.first_name}` : r.student_name || "");

      for (const c of cols) {
        const cell = r._scores?.[c.key] || null;
        const pts = cell?.points_earned ?? "";
        const max = cell?.points_possible ?? "";
        const pct = pctFromCell(cell);

        const cellText =
          pct == null && (pts === "" || max === "")
            ? ""
            : `${pts}/${max}${pct == null ? "" : ` (${Math.round(pct)}%)`}`;

        row.push(cellText);
      }

      const t = totalsByStudentId.get(r.student?.student_id || `${r.student?.first_name}-${r.student?.last_name}`) || { earned: "", possible: "", pct: null };
      row.push(t.earned ?? "");
      row.push(t.possible ?? "");
      row.push(t.pct == null ? "" : `${t.pct}%`);

      lines.push(row.map(csvEscape).join(","));
    }

    return lines.join("\n");
  };

  const onExportCsv = () => {
    const csv = buildGradebookCsv();
    const safeSection = (selectedSectionName || "section").replace(/[^a-z0-9-_]+/gi, "_");
    const filename = `gradebook_${safeSection}.csv`;
    downloadTextFile(filename, csv);
  };

  return (
    <div style={{ padding: 16, fontFamily: "system-ui, sans-serif" }}>
      <style>{`.muted{color:#666;font-size:0.9rem;margin-top:0.5rem}.error-box{margin:12px 0;padding:12px;border:1px solid #cc0000;background:#ffe6e6}.empty-state{margin:24px 0;padding:16px;border-left:4px solid #ddd;background:#f9f9f9}.empty-state h3{margin:0 0 8px 0;font-size:1.1rem}.debug-panel{margin:12px 0;padding:12px;background:#f0f8ff;border:1px solid #4a90e2;font-size:13px;font-family:monospace}.debug-panel h4{margin:0 0 8px 0;font-size:14px;font-family:system-ui}.debug-panel dl{margin:0;display:grid;grid-template-columns:150px 1fr;gap:4px}.debug-panel dt{font-weight:600}.debug-panel dd{margin:0;color:#333}`}</style>

      <h2>Gradebook (Read-Only)</h2>

      {isDev && (
        <div className="debug-panel">
          <h4>🔧 Request Diagnostics (DEV)</h4>
          <dl>
            <dt>API Base:</dt>
            <dd>{import.meta.env.VITE_API_BASE_URL || "(default)"}</dd>
            <dt>Token:</dt>
            <dd style={{ color: token ? "inherit" : "red", fontWeight: token ? "normal" : "bold" }}>
              {token ? `${token.length} chars` : "❌ MISSING"}
            </dd>
            <dt>School ID:</dt>
            <dd style={{ color: schoolId ? "inherit" : "red", fontWeight: schoolId ? "normal" : "bold" }}>
              {schoolId || "❌ MISSING"}
            </dd>
            {lastRequest && (
              <>
                <dt>Last Request:</dt>
                <dd>
                  {lastRequest.name || "grades"} → {lastRequest.url} 
                  {lastRequest.status && <span style={{ color: lastRequest.status === 200 ? "green" : "red" }}> [{lastRequest.status}]</span>}
                </dd>
              </>
            )}
            {lastRequest?.count !== undefined && (
              <>
                <dt>Sections Count:</dt>
                <dd>{lastRequest.count}</dd>
              </>
            )}
            {lastRequest?.assignments !== undefined && (
              <>
                <dt>Assignments:</dt>
                <dd>{lastRequest.assignments}</dd>
                <dt>Rows:</dt>
                <dd>{lastRequest.rows}</dd>
              </>
            )}
            {lastError && (
              <>
                <dt>Last Error:</dt>
                <dd style={{ color: "red" }}>
                  {lastError.message}
                  {lastError.status && ` [${lastError.status}]`}
                  {lastError.body && <div style={{ marginTop: 4, fontSize: 11, color: "#666" }}>{lastError.body}</div>}
                </dd>
              </>
            )}
          </dl>
        </div>
      )}

      {/* Sections chooser */}
      <div style={{ marginBottom: 12 }}>
        {loadingSections ? (
          <div>Loading sections…</div>
        ) : sections.length === 0 ? (
          <div className="empty-state">
            <h3>No sections available</h3>
            <p>There are no sections to display.</p>
          </div>
        ) : (
          <div>
            <label style={{ marginRight: 8, fontWeight: 500 }}>
              Section:&nbsp;
              <select
                value={selectedSectionId}
                onChange={(e) => {
                  // allow re-fetch if user re-selects
                  lastFetchedSectionRef.current = "";
                  setSelectedSectionId(e.target.value);
                }}
                style={{ padding: 6, minWidth: 300, fontSize: 14 }}
              >
                <option value="">— Select a Section —</option>
                {sections.map((s) => (
                  <option key={s.section_id} value={s.section_id}>
                    {s.course_name || s.name || s.section_id} {s.roster_count > 0 ? `(${s.roster_count} students)` : "(empty)"}
                  </option>
                ))}
              </select>
            </label>
          </div>
        )}
      </div>

      {/* Grades states */}
      {selectedSectionId && loadingGrades && <div>Loading grades…</div>}

      {selectedSectionId && !loadingGrades && !hasAssignments && (
        <div className="empty-state">
          <h3>No assignments yet</h3>
          <p>This section has no assignments or grades recorded.</p>
        </div>
      )}

      {selectedSectionId && !loadingGrades && hasAssignments && !hasRows && (
        <div className="empty-state">
          <h3>No students</h3>
          <p>This section has no enrolled students.</p>
        </div>
      )}

      {!loadingGrades && hasAssignments && hasRows && (
        <>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "flex-end",
              gap: 12,
              marginBottom: 10,
            }}
          >
            <button
              type="button"
              onClick={onExportCsv}
              style={{ padding: "6px 10px", fontSize: 13 }}
            >
              Export CSV ↓
            </button>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table style={{ borderCollapse: "collapse", minWidth: 900 }}>
            <thead>
              {/* Row 1: Titles */}
              <tr>
                <th
                  style={{
                    position: "sticky",
                    left: 0,
                    top: 0,
                    background: "#fff",
                    zIndex: 11,
                    borderBottom: "1px solid #ddd",
                    padding: "8px",
                    textAlign: "left",
                    fontWeight: 600,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span>Student</span>
                    <button
                      type="button"
                      onClick={() =>
                        setRowSort((s) => ({
                          key: "name",
                          dir: s.key === "name" ? (s.dir === "asc" ? "desc" : "asc") : "asc",
                        }))
                      }
                      style={{ fontSize: 12, padding: "2px 6px", cursor: "pointer", background: "none", border: "1px solid #ccc", borderRadius: "3px" }}
                    >
                      Name {rowSort.key === "name" ? (rowSort.dir === "asc" ? "↑" : "↓") : ""}
                    </button>
                    <button
                      type="button"
                      onClick={() =>
                        setRowSort((s) => ({
                          key: "totalPct",
                          dir: s.key === "totalPct" ? (s.dir === "asc" ? "desc" : "asc") : "desc",
                        }))
                      }
                      style={{ fontSize: 12, padding: "2px 6px", cursor: "pointer", background: "none", border: "1px solid #ccc", borderRadius: "3px" }}
                    >
                      Avg {rowSort.key === "totalPct" ? (rowSort.dir === "asc" ? "↑" : "↓") : ""}
                    </button>
                  </div>
                </th>

                {sortedAssignments.map((a) => (
                  <th
                    key={a._key}
                    style={{
                      position: "sticky",
                      top: 0,
                      background: "#fff",
                      zIndex: 10,
                      borderBottom: "1px solid #ddd",
                      padding: "8px",
                      whiteSpace: "nowrap",
                      textAlign: "center",
                      fontWeight: 600,
                    }}
                  >
                    <div>{a.assignment_name}</div>
                    <div style={{ fontSize: 12, opacity: 0.7 }}>
                      / {a.points_possible}
                    </div>
                  </th>
                ))}

                <th
                  style={{
                    position: "sticky",
                    right: 0,
                    top: 0,
                    background: "#fff",
                    zIndex: 12,
                    borderBottom: "1px solid #ddd",
                    padding: "8px",
                    textAlign: "center",
                    fontWeight: 600,
                    whiteSpace: "nowrap",
                  }}
                >
                  Total
                </th>
              </tr>

              {/* Row 2: Averages */}
              <tr>
                <th
                  style={{
                    position: "sticky",
                    left: 0,
                    top: HEADER_ROW_HEIGHT,
                    background: "#fff",
                    zIndex: 11,
                    borderBottom: "1px solid #ddd",
                    padding: "6px 8px",
                    textAlign: "left",
                    fontWeight: 400,
                    color: "#555",
                  }}
                >
                  <div style={{ display: "flex", gap: 8 }}>
                    <button
                      type="button"
                      onClick={() =>
                        setColSort((s) => ({
                          key: "title",
                          dir: s.key === "title" ? (s.dir === "asc" ? "desc" : "asc") : "asc",
                        }))
                      }
                      style={{ fontSize: 12, padding: "2px 6px", cursor: "pointer", background: "none", border: "1px solid #ccc", borderRadius: "3px" }}
                    >
                      Sort cols: Title {colSort.key === "title" ? (colSort.dir === "asc" ? "↑" : "↓") : ""}
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        setColSort((s) => ({
                          key: "avgPct",
                          dir: s.key === "avgPct" ? (s.dir === "asc" ? "desc" : "asc") : "desc",
                        }))
                      }
                      style={{ fontSize: 12, padding: "2px 6px", cursor: "pointer", background: "none", border: "1px solid #ccc", borderRadius: "3px" }}
                    >
                      Avg {colSort.key === "avgPct" ? (colSort.dir === "asc" ? "↑" : "↓") : ""}
                    </button>
                  </div>
                </th>

                {sortedAssignments.map((a) => {
                  const key = a?._key ?? a?.id;
                  const s = assignmentAverages.get(key);
                  const label =
                    s && s.pct != null ? `Avg: ${s.pct}% (n=${s.n})` : "Avg: —";

                  return (
                    <th
                      key={`${key}-avg`}
                      style={{
                        position: "sticky",
                        top: HEADER_ROW_HEIGHT,
                        background: "#fff",
                        zIndex: 10,
                        borderBottom: "1px solid #ddd",
                        padding: "6px 8px",
                        textAlign: "center",
                        fontWeight: 400,
                        color: "#555",
                        whiteSpace: "nowrap",
                      }}
                      title={s && s.possible > 0 ? `${s.earned} / ${s.possible}` : ""}
                    >
                      {label}
                    </th>
                  );
                })}

                <th
                  style={{
                    position: "sticky",
                    right: 0,
                    top: HEADER_ROW_HEIGHT,
                    background: "#fff",
                    zIndex: 12,
                    borderBottom: "1px solid #ddd",
                    padding: "6px 8px",
                    textAlign: "center",
                    fontWeight: 400,
                    color: "#555",
                    whiteSpace: "nowrap",
                  }}
                >
                  {/* blank or overall avg if desired */}
                </th>
              </tr>
            </thead>

            <tbody>
              {sortedRows.map((r) => {
                const s = r.student || {};
                const studentId = s.student_id || `${s.first_name}-${s.last_name}`;
                const label = `${s.last_name ?? ""}, ${s.first_name ?? ""}`.trim().replace(/^,|,$/g, "").trim();

                return (
                  <tr key={studentId}>
                    <td
                      style={{
                        position: "sticky",
                        left: 0,
                        background: "#fff",
                        zIndex: 1,
                        borderBottom: "1px solid #eee",
                        padding: "8px",
                      }}
                    >
                      <div>{label || "Unnamed Student"}</div>
                      <div style={{ fontSize: 12, opacity: 0.7 }}>
                        Grade {s.grade_level ?? "—"}
                      </div>
                    </td>

                    {sortedAssignments.map((a) => {
                      const cell = r._scores?.[a._key] || null;
                      const earned = cell?.points_earned ?? "";
                      const possible = cell?.points_possible ?? a.points_possible ?? "";
                      const pct = pctFromCell(cell);
                      const bg = bgForPct(pct);

                      return (
                        <td
                          key={`${studentId}:${a._key}`}
                          style={{
                            borderBottom: "1px solid #eee",
                            padding: "8px",
                            textAlign: "center",
                            lineHeight: "1.3",
                            background: bg,
                          }}
                        >
                          {formatScore(earned, possible).split('\n').map((line, i) => (
                            <div key={i}>{line}</div>
                          ))}
                        </td>
                      );
                    })}

                    {(() => {
                      const totals = totalsByStudentId.get(studentId) || { earned: 0, possible: 0, pct: null };
                      const text = formatTotals(totals);
                      const lines = String(text).split("\n");
                      const bg = bgForPct(totals?.pct);

                      return (
                        <td
                          style={{
                            position: "sticky",
                            right: 0,
                            background: bg ?? "#fff",
                            zIndex: 3,
                            borderLeft: "1px solid #f3f4f6",
                            borderBottom: "1px solid #eee",
                            padding: "8px 10px",
                            textAlign: "center",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {lines.map((ln, i) => (
                            <div key={i} style={{ lineHeight: "1.3" }}>
                              {ln}
                            </div>
                          ))}
                        </td>
                      );
                    })()}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        </>
      )}
    </div>
  );
}

