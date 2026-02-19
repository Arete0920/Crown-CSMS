import React, { useEffect, useMemo, useState } from "react";
import api from "../lib/api";

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
        const res = await api.get("/api/v1/academics/sections/");
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
        const r = await api.get(`/api/v1/academics/sections/${sectionId}/roster/`);
        const items = r?.students || r?.results || r?.items || r || [];
        setRoster(items);
        const m = {};
        for (const s of items) {
          const sid = s.student_id || s.id || s.student?.id;
          if (sid) m[sid] = "present";
        }
        setStatusMap(m);
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
      const res = await api.post(
        `/api/v1/academics/sections/${sectionId}/attendance/`,
        { date: today, items }
      );
      setMsg(`Saved: created=${res.created} updated=${res.updated} (${res.date})`);
    } catch {
      setMsg("Submit failed. Check API + permissions.");
    }
  };

  return (
    <div style={{ padding: 16 }}>
      <h2>Teacher Attendance</h2>

      <div style={{ marginBottom: 12 }}>
        <label>Section: </label>
        <select value={sectionId} onChange={(e) => setSectionId(e.target.value)}>
          <option value="">-- select --</option>
          {sections.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name || s.course_name || s.title || s.id}
            </option>
          ))}
        </select>
        <span style={{ marginLeft: 12 }}>Date: {today}</span>
        <button
          style={{ marginLeft: 12 }}
          disabled={!sectionId || roster.length === 0}
          onClick={submit}
        >
          Submit Attendance
        </button>
      </div>

      {msg ? <div style={{ marginBottom: 12, color: msg.startsWith("Saved") ? "green" : "red" }}>{msg}</div> : null}

      <table border="1" cellPadding="6" style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            <th>Student</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {roster.map((r) => {
            const sid = r.student_id || r.id || r.student?.id;
            const name =
              r.name || r.student_name || r.full_name || r.student?.name || sid;
            return (
              <tr key={sid || Math.random()}>
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
    </div>
  );
}
