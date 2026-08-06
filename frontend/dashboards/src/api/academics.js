/**
 * Academics read-only API client
 * Connects to /api/v1/academics/* endpoints
 */

import { authenticatedFetch } from "../utils/authClient.js";

// Normalize base URL once (prevents double-slash bugs)
const rawBase = import.meta.env.VITE_API_BASE_URL || "";
const API_BASE = rawBase.endsWith("/") ? rawBase.slice(0, -1) : rawBase;

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

/**
 * PATCH an assignment (points_possible, name, category_id, due_date, etc.)
 * 
 * @param {string} assignmentId - Assignment UUID
 * @param {Object} payload - Fields to update
 * @param {string} [payload.name] - Assignment name
 * @param {string} [payload.points_possible] - Decimal as string (e.g., "50" or "50.00")
 * @param {string} [payload.category_id] - Category UUID
 * @param {string|null} [payload.due_date] - ISO date string (YYYY-MM-DD) or null
 * @param {string|null} [payload.assigned_date] - ISO date string (YYYY-MM-DD) or null
 * @param {boolean} [payload.is_published] - Publication status
 * @returns {Promise<Object>} Updated assignment data
 */
export async function patchAssignment(assignmentId, payload) {
  const url = `${API_BASE}/api/v1/academics/assignments/${encodeURIComponent(assignmentId)}/`;
  const res = await authenticatedFetch(url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`PATCH assignment failed (${res.status}): ${text}`);
  }
  return res.json();
}

/**
 * PATCH a category (weight_percent, name, is_active, etc.)
 * 
 * @param {string} categoryId - Category UUID
 * @param {Object} payload - Fields to update
 * @param {string} [payload.name] - Category name
 * @param {string} [payload.weight_percent] - Decimal as string 0-100 (e.g., "25" or "25.00")
 * @param {number} [payload.sort_order] - Display order
 * @param {boolean} [payload.is_active] - Active status
 * @returns {Promise<Object>} Updated category data
 */
export async function patchCategory(categoryId, payload) {
  const url = `${API_BASE}/api/v1/academics/categories/${encodeURIComponent(categoryId)}/`;
  const res = await authenticatedFetch(url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`PATCH category failed (${res.status}): ${text}`);
  }
  return res.json();
}

/**
 * Fetch all assignments for a section
 * 
 * @param {string} sectionId - Section UUID
 * @returns {Promise<{assignments: Array}>} List of assignments with category info
 */
export function fetchSectionAssignments(sectionId) {
  if (!sectionId) throw new Error('sectionId is required');
  return _fetchJson(`${API_BASE}/api/v1/academics/sections/${encodeURIComponent(sectionId)}/assignments/`);
}

/**
 * Fetch graduation audit for a student
 * 
 * @param {string} studentId - Student UUID
 * @returns {Promise<Object>} Graduation audit data including credits and on_track status
 */
export function fetchGraduationAudit(studentId) {
  if (!studentId) throw new Error('studentId is required');
  
  // Fail fast if session keys missing (prevents confusing 403 loops)
  const token = sessionStorage.getItem("crown.jwt.access") || "";
  const schoolId = sessionStorage.getItem("crown.school.id") || "";
  if (!token) throw new Error("Missing access token (sessionStorage: crown.jwt.access)");
  if (!schoolId) throw new Error("Missing school id (sessionStorage: crown.school.id)");
  
  return _fetchJson(`${API_BASE}/api/v1/graduation/audit/${encodeURIComponent(studentId)}/`);
}

