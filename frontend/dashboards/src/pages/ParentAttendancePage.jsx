import React, { useEffect, useState } from "react";
import { authenticatedFetch } from "../utils/authClient";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function fetchJson(path, opts = {}) {
  const resp = await authenticatedFetch(`${API_BASE}${path}`, opts);
  return resp.json();
}

export default function ParentAttendancePage() {
  const [students, setStudents] = useState([]);
  const [studentId, setStudentId] = useState("");
  const [rows, setRows] = useState([]);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    (async () => {
      setMsg("");
      try {
        const res = await fetchJson("/api/v1/academics/parents/me/students/");
        setStudents(res?.results || res || []);
      } catch {
        setMsg("Failed to load parent students.");
      }
    })();
  }, []);

  useEffect(() => {
    if (!studentId) return;
    (async () => {
      setMsg("");
      setRows([]);
      try {
        const res = await fetchJson(`/api/v1/students/${studentId}/attendance/`);
        setRows(res?.results || res || []);
      } catch {
        setMsg("Failed to load attendance.");
      }
    })();
  }, [studentId]);

  return (
    <div style={{ padding: 16 }}>
      <h2>Parent Attendance</h2>

      <div style={{ marginBottom: 12 }}>
        <label>Student: </label>
        <select value={studentId} onChange={(e) => setStudentId(e.target.value)}>
          <option value="">-- select --</option>
          {students.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name || s.full_name || s.student_name || s.id}
            </option>
          ))}
        </select>
      </div>

      {msg ? <div style={{ marginBottom: 12, color: "red" }}>{msg}</div> : null}

      <table border="1" cellPadding="6" style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            <th>Date</th>
            <th>Status</th>
            <th>Course</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, idx) => (
            <tr key={r.id || idx}>
              <td>{r.date || r.day || r.attendance_date || ""}</td>
              <td>{r.status || r.code || r.state || ""}</td>
              <td>{r.course_name || r.course || r.section_name || ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
