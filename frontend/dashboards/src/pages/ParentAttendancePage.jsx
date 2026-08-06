import { useEffect, useState } from "react";
import { authenticatedFetch } from "../utils/authClient";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import ErrorBanner from "../components/ui/ErrorBanner";
import EmptyState from "../components/ui/EmptyState";

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
    <CrownLayout title="Parent Attendance" subtitle="View your student's attendance record">
      <div style={{ marginBottom: 12 }}>
        <div>Student: </div>
        <select value={studentId} onChange={(e) => setStudentId(e.target.value)}>
          <option value="">-- select --</option>
          {students.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name || s.full_name || s.student_name || s.id}
            </option>
          ))}
        </select>
      </div>

      <ErrorBanner title="Attendance error" message={msg} />
      {studentId && !msg && rows.length === 0 && (
        <EmptyState
          title="No attendance records found"
          message="If this is unexpected, verify the student has attendance data available."
          actionLabel="Reload"
          onAction={() => window.location.reload()}
        />
      )}

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
    </CrownLayout>
  );
}

