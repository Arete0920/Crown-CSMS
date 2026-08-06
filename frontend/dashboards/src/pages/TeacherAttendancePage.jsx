import { useEffect, useMemo, useState } from "react";
import { authenticatedFetch } from "../utils/authClient";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import ErrorBanner from "../components/ui/ErrorBanner";
import EmptyState from "../components/ui/EmptyState";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function fetchJson(path, opts = {}) {
  const resp = await authenticatedFetch(`${API_BASE}${path}`, opts);
  return resp.json();
}

export default function TeacherAttendancePage() {
  const [sections, setSections] = useState([]);
  const [sectionId, setSectionId] = useState("");
  const [roster, setRoster] = useState([]);
  const [statusMap, setStatusMap] = useState({});
  const [msg, setMsg] = useState("");

  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);

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
    if (!sectionId) return;
    (async () => {
      setMsg("");
      setRoster([]);
      setStatusMap({});
      try {
        const r = await fetchJson(`/api/v1/academics/sections/${sectionId}/roster/`);
        const items = r?.students || r?.results || r?.items || r || [];
        setRoster(items);
        const nextMap = {};
        for (const s of items) {
          const sid = s.student_id || s.id || s.student?.id;
          if (sid) nextMap[sid] = "present";
        }
        setStatusMap(nextMap);
      } catch {
        setMsg("Failed to load roster.");
      }
    })();
  }, [sectionId]);

  const submit = async () => {
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
          {sections.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name || s.course_name || s.title || s.id}
            </option>
          ))}
        </select>
        <span style={{ marginLeft: 12 }}>Date: {today}</span>
        <button
          className="crown-btn crown-btn-primary"
          style={{ marginLeft: 12 }}
          disabled={!sectionId || roster.length === 0}
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
      {sectionId && !msg && roster.length === 0 && (
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
                    value={statusMap[sid] || "present"}
                    onChange={(e) =>
                      setStatusMap((prev) => ({ ...prev, [sid]: e.target.value }))
                    }
                  >
                    <option value="present">present</option>
                    <option value="absent">absent</option>
                    <option value="tardy">tardy</option>
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
