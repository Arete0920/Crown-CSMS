import { authenticatedFetch } from "../utils/authClient.js";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function _fetchJson(path, { schoolId } = {}) {
  const headers = {};
  if (schoolId) headers["X-School-Id"] = schoolId;

  const res = await authenticatedFetch(`${API_BASE}${path}`, { headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Request failed (${res.status}): ${text}`);
  }
  return res.json();
}

export async function listClassrooms({ schoolId } = {}) {
  return _fetchJson(`/api/classroom/classrooms/`, { schoolId });
}

export async function getClassroom({ id, schoolId }) {
  return _fetchJson(`/api/classroom/classrooms/${id}/`, { schoolId });
}

export async function getClassroomSnapshot({ id, schoolId }) {
  return _fetchJson(`/api/classroom/classrooms/${id}/snapshot/`, { schoolId });
}
