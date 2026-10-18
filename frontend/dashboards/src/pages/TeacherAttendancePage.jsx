import { useEffect, useMemo, useState } from "react";
import { authenticatedFetch } from "../utils/authClient";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import ErrorBanner from "../components/ui/ErrorBanner";
import EmptyState from "../components/ui/EmptyState";

async function fetchJson(path, opts = {}) {
  const resp = await authenticatedFetch(path, opts);
  return resp.json();
}

export default function TeacherAttendancePage() {
  const [sections, setSections] = useState([]);
  const [sectionId, setSectionId] = useState("");
  const [roster, setRoster] = useState([]);
  const [statusMap, setStatusMap] = useState({});
  const [loadedSectionId, setLoadedSectionId] = useState("");
  const [msg, setMsg] = useState("");

  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);
  const attendanceReady = Boolean(sectionId) && loadedSectionId === sectionId;

  useEffect(() => {
    (async () => {
      setMsg("");
      try {
        const res = await fetchJson("/api/v1/academics/sections/");
        setSections(res?.results || res || []);
      } catch {
        setMsg("Failed to load sections.");
      }
    })();
  }, []);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    setMsg("");
    setRoster([]);
    setStatusMap({});
    setLoadedSectionId("");
    if (!sectionId) return;
    (async () => {
      try {
        const [r, saved] = await Promise.all([
          fetchJson(`/api/v1/academics/sections/${sectionId}/roster/`, { signal: controller.signal }),
          fetchJson("/api/v1/academics/classroom/operations/", {
            signal: controller.signal,
            query: { section_id: sectionId, date: today },
          }),
        ]);
        const items = r?.students || r?.results || r?.items || r || [];
        if (!Array.isArray(items) || saved?.source !== "live"
            || saved.section_id !== sectionId || saved.date !== today || !Array.isArray(saved.roster)) {
          throw new Error("Invalid saved attendance response.");
        }
        // Both APIs identify roster members by households.Student IDs. The
        // operations endpoint resolves their verified canonical attendance.
        const savedByStudent = new Map(saved.roster.map((student) => [student.id, student]));
        const nextMap = {};
        for (const s of items) {
          const sid = s.student_id || s.id || s.student?.id;
          const savedStudent = savedByStudent.get(sid);
          if (!sid || savedStudent?.identity_verified !== true) throw new Error("Attendance roster could not be verified.");
          const mark = savedStudent.attendance;
          const status = mark == null ? "present" : String(mark).toLowerCase();
          if (!["present", "absent", "tardy", "excused"].includes(status)) {
            throw new Error("Unrecognized saved attendance status.");
          }
          nextMap[sid] = status;
        }
        if (active) {
          setRoster(items);
          setStatusMap(nextMap);
          setLoadedSectionId(sectionId);
        }
      } catch {
        if (active) setMsg("Failed to load saved attendance. Reload the page to retry.");
      }
    })();
    return () => { active = false; controller.abort(); };
  }, [sectionId, today]);

  const submit = async () => {
    if (!attendanceReady) return;
    setMsg("");
    try {
      const items = Object.entries(statusMap).map(([student_id, status]) => ({
        student_id,
        status,
      }));
      const res = await fetchJson(`/api/v1/academics/sections/${sectionId}/attendance/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ date: today, items }),
      });
      setMsg(`Saved: created=${res.created} updated=${res.updated} (${res.date})`);
    } catch {
      setMsg("Submit failed. Check API + permissions.");
    }
  };

  return (
    <CrownLayout title="Teacher Attendance" subtitle="Mark daily attendance by section" mainClassName="crown-attendance">
      <h1 className="text-2xl font-semibold tracking-tight">Attendance Dashboard</h1>

      <div style={{ marginBottom: 12 }}>
        <label htmlFor="teacher-attendance-section">Section: </label>
        <select id="teacher-attendance-section" value={sectionId} onChange={(e) => setSectionId(e.target.value)}>
          <option value="">-- select --</option>
          {sections.map((s) => {
            const sid = s.section_id || s.id;
            return (
              <option key={sid} value={sid}>
                {s.course_name || s.name || s.title || s.course_code || sid}
              </option>
            );
          })}
        </select>
        <span style={{ marginLeft: 12 }}>Date: {today}</span>
        <button
          className="crown-btn crown-btn-primary"
          style={{ marginLeft: 12 }}
          disabled={!attendanceReady || roster.length === 0}
          onClick={submit}
        >
          Submit Attendance
        </button>
      </div>

      {msg && msg.startsWith("Saved") ? (
        <div style={{ marginBottom: 12, color: "var(--crown-success)" }}>{msg}</div>
      ) : (
        <ErrorBanner title="Attendance error" message={msg} />
      )}
      {sectionId && !attendanceReady && !msg && <div role="status">Loading saved attendance...</div>}
      {attendanceReady && !msg && roster.length === 0 && (
        <EmptyState
          title="No students in this section"
          message="If this is unexpected, check that the section has enrolled students."
          actionLabel="Reload"
          onAction={() => globalThis.location.reload()}
        />
      )}

      <table border="1" cellPadding="6" style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            <th>Student</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {roster.map((r, index) => {
            const sid = r.student_id || r.id || r.student?.id;
            const name = r.name || r.student_name || r.full_name || r.student?.name || sid || `student-${index}`;
            const rowKey = sid || `${name}-${index}`;
            return (
              <tr key={rowKey}>
                <td>{name}</td>
                <td>
                  <select
                    disabled={!attendanceReady}
                    value={statusMap[sid] || "present"}
                    onChange={(e) =>
                      setStatusMap((prev) => ({ ...prev, [sid]: e.target.value }))
                    }
                  >
                    <option value="present">present</option>
                    <option value="absent">absent</option>
                    <option value="tardy">tardy</option>
                    <option value="excused">excused</option>
                  </select>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </CrownLayout>
  );
}
