/**
 * Academics read-only API client
 * Connects to /api/v1/academics/* endpoints
 */

import { authenticatedFetch } from "../utils/authClient.js";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function _fetchJson(url) {
  const res = await authenticatedFetch(url);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Request failed (${res.status}): ${text}`);
  }
  return res.json();
}

export function fetchAcademicYears({ limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  return _fetchJson(`${API_BASE}/api/v1/academics/years/?${params}`);
}

export function fetchTerms({ academicYearId, limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (academicYearId) params.set("academic_year", academicYearId);
  return _fetchJson(`${API_BASE}/api/v1/academics/terms/?${params}`);
}

export function fetchCourses({ academicYearId, termId, termCode, limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (academicYearId) params.set("academic_year", academicYearId);
  if (termId) params.set("term_id", termId);
  if (termCode) params.set("term", termCode);
  return _fetchJson(`${API_BASE}/api/v1/academics/courses/?${params}`);
}

export function fetchSections({ academicYearId, termId, termCode, studentId, teacherId, limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (academicYearId) params.set("academic_year", academicYearId);
  if (termId) params.set("term_id", termId);
  if (termCode) params.set("term", termCode);
  if (studentId) params.set("student_id", studentId);
  if (teacherId) params.set("teacher_id", teacherId);
  return _fetchJson(`${API_BASE}/api/v1/academics/sections/?${params}`);
}

export function fetchParentStudents() {
  return _fetchJson(`${API_BASE}/api/v1/academics/parents/me/students/`);
}

export function fetchStudentSections(studentId) {
  return _fetchJson(`${API_BASE}/api/v1/academics/students/${studentId}/sections/`);
}

export function fetchStudents({ limit = 100, offset = 0 } = {}) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  return _fetchJson(`${API_BASE}/api/v1/students/?${params}`);
}

export function fetchTranscript(studentId) {
  return _fetchJson(`${API_BASE}/api/v1/academics/transcript/${studentId}/`);
}

export function fetchSectionRoster(sectionId) {
  if (!sectionId) throw new Error('sectionId is required');
  return _fetchJson(`${API_BASE}/api/v1/academics/sections/${encodeURIComponent(sectionId)}/roster/`);
}
