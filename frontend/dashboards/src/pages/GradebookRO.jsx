import { useEffect, useMemo, useRef, useState } from "react";
import { getGradebookSections, getGradebookGrades, fetchGradebookDrilldown, patchGradeEntry, upsertAssignmentGrades } from "../api/gradebook";
import { patchAssignment } from "../api/academics";
import { getSchoolId, getToken } from "../lib/api";
import { csvEscape, downloadTextFile } from "../lib/export/csv";
import { pctFromCell, bgForPct } from "../lib/ui/gradeVisuals";
import { fmt2 } from "../utils/number";
import Drawer from "../components/Drawer";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import ErrorBanner from "../components/ui/ErrorBanner";


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
  return `${fmt2(earned)} / ${possible}\n(${pct ?? 0}%)`;
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
  const probedRef = useRef(false);

  // diagnostics state (kept from before)
  const [lastRequest, setLastRequest] = useState(null);
  const [lastError, setLastError] = useState(null);
  const [sectionError, setSectionError] = useState("");

  // drilldown state
  const [drilldownStudent, setDrilldownStudent] = useState(null);
  const [drilldownData, setDrilldownData] = useState(null);
  const [drilldownLoading, setDrilldownLoading] = useState(false);
  const [drilldownError, setDrilldownError] = useState("");

  // editing state
  const [editingAssignmentId, setEditingAssignmentId] = useState(null);
  const [savingAssignmentId, setSavingAssignmentId] = useState(null);
  const [editMsg, setEditMsg] = useState("");
  const [canWriteAssignments, setCanWriteAssignments] = useState(false);

  // ===== LANE4_GRADE_EDIT_UI =====
  const [lane4EditMode, setLane4EditMode] = useState(false);
  const [lane4Saving, setLane4Saving] = useState(false);
  const [lane4Msg, setLane4Msg] = useState(null);
  // cell edits keyed by "assignmentId:studentId" -> { points_earned }
  const [lane4Edits, setLane4Edits] = useState({});

  const lane4SetEdit = (assignmentId, studentId, patch) => {
    const k = `${assignmentId}:${studentId}`;
    setLane4Edits(prev => ({ ...prev, [k]: { ...(prev[k] || {}), ...patch } }));
  };

  const lane4ClearMsgSoon = () => {
    window.clearTimeout(window.__lane4MsgT);
    window.__lane4MsgT = window.setTimeout(() => setLane4Msg(null), 4000);
  };

  const lane4SaveAll = async () => {
    if (!selectedSectionId) {
      setLane4Msg({ type: 'error', text: 'No section selected; cannot save grades.' });
      lane4ClearMsgSoon();
      return;
    }

    const byAsn = {};
    for (const [k, v] of Object.entries(lane4Edits)) {
      const [assignmentId, studentId] = k.split(':');
      if (!assignmentId || !studentId) continue;
      if (!byAsn[assignmentId]) byAsn[assignmentId] = [];
      const row = { student_id: studentId };
      if (v.points_earned !== undefined && v.points_earned !== '') {
        row.points_earned = Number(v.points_earned);
      }
      byAsn[assignmentId].push(row);
    }

    const assignmentIds = Object.keys(byAsn);
    if (assignmentIds.length === 0) {
      setLane4Msg({ type: 'info', text: 'No grade edits to save.' });
      lane4ClearMsgSoon();
      return;
    }

    try {
      setLane4Saving(true);
      setLane4Msg(null);
      let total = 0;
      for (const assignmentId of assignmentIds) {
        const res = await upsertAssignmentGrades(selectedSectionId, assignmentId, byAsn[assignmentId]);
        total += (res && res.count) ? res.count : 0;
      }
      setLane4Msg({ type: 'success', text: `Saved ${total} grade row(s).` });
      lane4ClearMsgSoon();
      setLane4Edits({});
      setLane4EditMode(false);
      await refreshGradebook();
    } catch (e) {
      const msg = e?.message || 'Save failed.';
      setLane4Msg({ type: 'error', text: msg });
      lane4ClearMsgSoon();
    } finally {
      setLane4Saving(false);
    }
  };
  // ===== /LANE4_GRADE_EDIT_UI =====


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
        console.error(err);
        if (alive) setSectionError(err?.message || "Failed to load gradebook sections.");
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

    probedRef.current = false;

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
          assignment_id: x.assignment_id,
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

  // Probe write permissions once after assignments load
  useEffect(() => {
    if (probedRef.current) return;
    if (!token) return;
    if (!assignments?.length) return;

    const a = assignments[0];
    if (!a?.assignment_id) return;

    probedRef.current = true;
    probeCanWrite(a.assignment_id, a.points_possible);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, assignments]);


  const isAuthed = !!token && !!schoolId;
  const isDev = import.meta.env.DEV;
  const isDemoMode = import.meta.env.VITE_DEMO_MODE === "1";
  const showDevPanels = isDev && !isDemoMode;
  const hasAssignments = assignments.length > 0;
  const hasRows = rows.length > 0;

  // Lookup selected section details
  const selectedSection = useMemo(
    () => sections.find(s => s.section_id === selectedSectionId),
    [sections, selectedSectionId]
  );
  const rosterCount = selectedSection?.roster_count ?? 0;

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

  // Refresh gradebook data
  const refreshGradebook = async () => {
    if (!selectedSectionId) return;
    lastFetchedSectionRef.current = ""; // Clear guard to allow refetch
    setAssignments([]);
    setRows([]);
    setLoadingGrades(true);

    try {
      const payload = await getGradebookGrades(selectedSectionId);
      const a = Array.isArray(payload?.assignments) ? payload.assignments : [];
      const r = Array.isArray(payload?.rows) ? payload.rows : [];

      const normalizedAssignments = a.map((x) => ({
        assignment_id: x.assignment_id,
        assignment_name: x.assignment_name,
        points_possible: x.points_possible,
        _key: keyOf(x.assignment_name),
      }));

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
      lastFetchedSectionRef.current = selectedSectionId;
    } catch (err) {
      console.error(err);
      setEditMsg(`Failed to refresh: ${err.message}`);
    } finally {
      setLoadingGrades(false);
    }
  };

  // Drilldown handler
  const handleOpenDrilldown = async (studentId, studentName) => {
    setDrilldownStudent({ student_id: studentId, student_name: studentName });
    setDrilldownLoading(true);
    setDrilldownError("");
    try {
      const data = await fetchGradebookDrilldown(selectedSectionId, {
        bucket: "all",
        limit: 50,
        offset: 0,
      });
      setDrilldownData(data);
    } catch (err) {
      setDrilldownError(err.message);
    } finally {
      setDrilldownLoading(false);
    }
  };

  // Probe write permissions once on load
  const probeCanWrite = async (assignmentId, currentPointsPossible) => {
    try {
      // PATCH same value; backend validates and returns 200 if allowed
      await patchAssignment(assignmentId, { points_possible: String(currentPointsPossible) });
      setCanWriteAssignments(true);
    } catch (e) {
      // If 403 or other error, disable editing UI quietly
      setCanWriteAssignments(false);
    }
  };

  // Handle assignment points_possible editing
  const handleSavePointsPossible = async (assignmentId, newPoints) => {
    const trimmed = String(newPoints ?? "").trim();
    if (!trimmed) return;

    setSavingAssignmentId(assignmentId);
    setEditMsg("");

    try {
      await patchAssignment(assignmentId, { points_possible: trimmed });
      await refreshGradebook();
      setEditingAssignmentId(null);
      setEditMsg("✅ Points possible updated");
      setTimeout(() => setEditMsg(""), 3000);
    } catch (e) {
      setEditMsg(`❌ Failed to update points possible: ${String(e)}`);
    } finally {
      setSavingAssignmentId(null);
    }
  };


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
    <CrownLayout
      title="Gradebook"
      subtitle="Read Only"
      right={<button className="crown-btn" onClick={() => window.print()}>Print</button>}
    >
      <style>{`.muted{color:#666;font-size:0.9rem;margin-top:0.5rem}.error-box{margin:12px 0;padding:12px;border:1px solid #cc0000;background:#ffe6e6}.empty-state{margin:24px 0;padding:16px;border-left:4px solid #ddd;background:#f9f9f9}.empty-state h3{margin:0 0 8px 0;font-size:1.1rem}.debug-panel{margin:12px 0;padding:12px;background:#f0f8ff;border:1px solid #4a90e2;font-size:13px;font-family:monospace}.debug-panel h4{margin:0 0 8px 0;font-size:14px;font-family:system-ui}.debug-panel dl{margin:0;display:grid;grid-template-columns:150px 1fr;gap:4px}.debug-panel dt{font-weight:600}.debug-panel dd{margin:0;color:#333}`}</style>

      {/* Lane 4: Teacher grade-edit toolbar */}
      {canWriteAssignments && (
        <div style={{ marginBottom: 12, padding: '8px 12px', border: '1px solid #ddd', borderRadius: 4, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', background: lane4EditMode ? '#fffbf0' : '#fafafa' }}>
          <span style={{ fontWeight: 500, fontSize: 13 }}>Grade Edit</span>
          <button
            onClick={() => { setLane4EditMode(v => !v); setLane4Msg(null); }}
            disabled={lane4Saving}
            style={{ padding: '3px 10px', fontSize: 13, cursor: lane4Saving ? 'not-allowed' : 'pointer', fontWeight: lane4EditMode ? 600 : 400, border: '1px solid #bbb', borderRadius: 3, background: lane4EditMode ? '#1976d2' : '#fff', color: lane4EditMode ? '#fff' : '#333' }}
          >
            {lane4EditMode ? 'Editing ✓' : 'Edit Grades'}
          </button>
          {lane4EditMode && (
            <>
              <button
                onClick={lane4SaveAll}
                disabled={lane4Saving}
                style={{ padding: '3px 10px', fontSize: 13, cursor: lane4Saving ? 'not-allowed' : 'pointer', fontWeight: 600, border: '1px solid #1976d2', borderRadius: 3, background: '#1976d2', color: '#fff' }}
              >
                {lane4Saving ? 'Saving…' : 'Save Grades'}
              </button>
              <button
                onClick={() => { setLane4Edits({}); setLane4EditMode(false); setLane4Msg(null); }}
                disabled={lane4Saving}
                style={{ padding: '3px 10px', fontSize: 13, cursor: lane4Saving ? 'not-allowed' : 'pointer', border: '1px solid #bbb', borderRadius: 3, background: '#fff', color: '#555' }}
              >
                Cancel
              </button>
            </>
          )}
          {lane4Msg && (
            <span style={{ fontSize: 13, marginLeft: 8, color: lane4Msg.type === 'error' ? '#c62828' : lane4Msg.type === 'success' ? '#2e7d32' : '#555' }}>
              {lane4Msg.type === 'success' ? '✅ ' : lane4Msg.type === 'error' ? '⛔ ' : 'ℹ️ '}{lane4Msg.text}
            </span>
          )}
          {lane4EditMode && (
            <span style={{ fontSize: 12, color: '#888', marginLeft: 8 }}>Edit cells below, then click Save Grades.</span>
          )}
        </div>
      )}

      {showDevPanels && (
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

      <ErrorBanner title="Failed to load gradebook sections" message={sectionError} />

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

      {/* Debug panel: show selected section details */}
      {selectedSectionId && !loadingGrades && showDevPanels && (
        <div className="debug-panel" style={{ background: "#fff8e1", borderColor: "#ffa726" }}>
          <h4>📊 Selected Section State</h4>
          <dl>
            <dt>Section ID:</dt>
            <dd>{selectedSectionId}</dd>
            <dt>Roster Count:</dt>
            <dd>{rosterCount}</dd>
            <dt>Assignments:</dt>
            <dd>{assignments.length}</dd>
            <dt>Rows (students):</dt>
            <dd>{rows.length}</dd>
          </dl>
        </div>
      )}

      {selectedSectionId && !loadingGrades && !hasAssignments && (
        <div className="empty-state">
          <h3>No grades found</h3>
          <p>
            This section has no assignments or grades recorded.
            {isDev && <><br />Tip: Run <code style={{ background: "#f0f0f0", padding: "2px 6px", borderRadius: 3 }}>python manage.py seed_gradebook_demo --school-id &lt;uuid&gt;</code></>}
          </p>
        </div>
      )}

      {selectedSectionId && !loadingGrades && hasAssignments && !hasRows && (
        <div className="empty-state">
          <h3>No students enrolled</h3>
          <p>This section has {rosterCount === 0 ? "no enrolled students" : `${rosterCount} student(s) enrolled, but no grades returned`}.</p>
        </div>
      )}

      {!loadingGrades && hasAssignments && hasRows && (
        <>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 12,
              marginBottom: 10,
            }}
          >
            {editMsg && (
              <div
                style={{
                  padding: "6px 12px",
                  fontSize: 13,
                  background: editMsg.includes("✅") ? "#e6ffe6" : "#ffe6e6",
                  border: `1px solid ${editMsg.includes("✅") ? "#00cc00" : "#cc0000"}`,
                  borderRadius: 4,
                }}
              >
                {editMsg}
              </div>
            )}
            <div style={{ marginLeft: "auto" }}>
              <button
                type="button"
                className="crown-btn"
                onClick={onExportCsv}
              >
                Export CSV ↓
              </button>
            </div>
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
                    data-testid="gradebook-assignment-header"
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
                    <div style={{ marginBottom: 4 }}>{a.assignment_name}</div>
                    <div style={{ display: "flex", gap: 4, alignItems: "center", justifyContent: "center" }}>
                      {editingAssignmentId === a.assignment_id ? (
                        <input
                          type="number"
                          step="0.01"
                          defaultValue={a.points_possible}
                          disabled={savingAssignmentId === a.assignment_id}
                          style={{ width: 70, padding: 4, fontSize: 12 }}
                          onBlur={(e) => handleSavePointsPossible(a.assignment_id, e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") e.currentTarget.blur();
                            if (e.key === "Escape") setEditingAssignmentId(null);
                          }}
                          autoFocus
                        />
                      ) : (
                        <>
                          <span style={{ fontSize: 12, opacity: 0.7 }}>/ </span>
                          <button
                            type="button"
                            onClick={() => setEditingAssignmentId(a.assignment_id)}
                            disabled={!token || !canWriteAssignments}
                            title={!canWriteAssignments ? "Requires ADMIN/DIRECTOR" : "Click to edit points possible"}
                            style={{
                              fontSize: 12,
                              padding: "2px 6px",
                              cursor: token && canWriteAssignments ? "pointer" : "not-allowed",
                              background: "none",
                              border: "1px solid #ccc",
                              borderRadius: 3,
                              opacity: token && canWriteAssignments ? 0.7 : 0.4,
                            }}
                          >
                            {a.points_possible}
                          </button>
                        </>
                      )}
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
                  <tr key={studentId} data-testid="gradebook-row">
                    <td
                      style={{
                        position: "sticky",
                        left: 0,
                        background: "#fff",
                        zIndex: 1,
                        borderBottom: "1px solid #eee",
                        padding: "8px",
                        cursor: "pointer",
                        transition: "background 0.2s",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = "#f9f9f9")}
                      onMouseLeave={(e) => (e.currentTarget.style.background = "#fff")}
                      onClick={() => handleOpenDrilldown(s.student_id, label)}
                    >
                      <div style={{ fontWeight: 500 }}>{label || "Unnamed Student"}</div>
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
                          {lane4EditMode ? (
                            <input
                              type="number"
                              step="0.5"
                              min="0"
                              value={lane4Edits[`${a.assignment_id}:${studentId}`]?.points_earned ?? (earned === "" || earned === null ? "" : earned)}
                              onChange={(e) => lane4SetEdit(a.assignment_id, studentId, { points_earned: e.target.value })}
                              style={{ width: 72, textAlign: 'center', padding: '2px 4px', fontSize: 13, border: '1px solid #1976d2', borderRadius: 3 }}
                              aria-label={`Score for student on ${a.assignment_name}`}
                            />
                          ) : (
                            formatScore(earned, possible).split('\n').map((line, i) => (
                              <div key={i}>{line}</div>
                            ))
                          )}
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

        {/* Drilldown Drawer */}
        <Drawer
          open={!!drilldownStudent}
          onClose={() => setDrilldownStudent(null)}
          title={`Details: ${drilldownStudent?.student_name}`}
          width={520}
        >
          <div style={{ padding: "1.5rem" }}>
            <h2 style={{ marginTop: 0, marginBottom: "1.5rem", fontSize: "1.25rem" }}>
              Student Summary
            </h2>

            {drilldownError && (
              <div
                style={{
                  background: "#fee",
                  border: "1px solid #c33",
                  padding: "1rem",
                  borderRadius: "0.5rem",
                  marginBottom: "1rem",
                  color: "#c33",
                }}
              >
                <strong>Error:</strong> {drilldownError}
                <button
                  onClick={() => handleOpenDrilldown(drilldownStudent.student_id, drilldownStudent.student_name)}
                  style={{ marginLeft: "1rem", padding: "0.25rem 0.5rem" }}
                >
                  Retry
                </button>
              </div>
            )}

            {drilldownLoading && (
              <div style={{ padding: "2rem", textAlign: "center", color: "#666" }}>
                Loading...
              </div>
            )}

            {drilldownData && !drilldownLoading && (
              <>
                {drilldownData.rows.length === 0 ? (
                  <div style={{ padding: "2rem", textAlign: "center", color: "#666" }}>
                    No data available for this student.
                  </div>
                ) : (
                  <div>
                    <div style={{ marginBottom: "1.5rem" }}>
                      <strong>Section:</strong> {drilldownData.section_name}
                    </div>
                    <div style={{ marginBottom: "1.5rem" }}>
                      <strong>Total participants:</strong> {drilldownData.total}
                    </div>

                    <details
                      open
                      style={{
                        border: "1px solid #ddd",
                        borderRadius: "0.5rem",
                        padding: "1rem",
                        marginTop: "1rem",
                      }}
                    >
                      <summary style={{ cursor: "pointer", fontWeight: "bold", marginBottom: "0.5rem" }}>
                        Performance Breakdown
                      </summary>
                      {drilldownData.rows.map((row) => (
                        <div
                          key={row.student_id}
                          style={{
                            padding: "0.75rem",
                            borderBottom: "1px solid #eee",
                            fontSize: "0.875rem",
                          }}
                        >
                          <div>
                            <strong>{row.student_name}</strong> —{" "}
                            <span
                              style={{
                                background:
                                  row.pct >= 80 ? "#e8f5e9" : row.pct >= 70 ? "#fff9c4" : "#ffebee",
                                padding: "0.25rem 0.5rem",
                                borderRadius: "0.25rem",
                              }}
                            >
                              {row.pct.toFixed(1)}%
                            </span>
                          </div>
                          <div style={{ color: "#666", marginTop: "0.25rem", fontSize: "0.75rem" }}>
                            {row.total_points_earned} / {row.total_points_possible} points
                            {row.missing_count > 0 && ` • ${row.missing_count} missing`}
                            {row.status !== "normal" && ` • [${row.status}]`}
                          </div>
                        </div>
                      ))}
                    </details>
                  </div>
                )}
              </>
            )}
          </div>
        </Drawer>
        </>
      )}
    </CrownLayout>
  );
}

