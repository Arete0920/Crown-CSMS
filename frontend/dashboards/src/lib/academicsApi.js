// frontend/dashboards/src/lib/academicsApi.js
// Thin wrapper around apiFetch for academics endpoints.
// Uses the canonical auth layer (authClient.js → authenticatedFetch).

import { apiFetch } from "./api";

async function apiGet(path) {
  const res = await apiFetch(path);
  return res.json();
}

async function apiPostJson(path, body) {
  const res = await apiFetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}

// ── Sections ──────────────────────────────────────────────

export async function listSections() {
  return apiGet("/api/academics/sections/");
}

// ── Assignments (nested under section) ────────────────────

export async function listAssignments(sectionId) {
  return apiGet(
    `/api/academics/sections/${encodeURIComponent(sectionId)}/assignments/`
  );
}

// ── Submissions ───────────────────────────────────────────

export async function listSubmissions(assignmentId) {
  return apiGet(
    `/api/academics/submissions/?assignment_id=${encodeURIComponent(assignmentId)}`
  );
}

export async function listStudentSubmissions(studentId) {
  return apiGet(
    `/api/academics/submissions/?student_id=${encodeURIComponent(studentId)}`
  );
}

// ── Grading ───────────────────────────────────────────────

export async function gradeSubmission(submissionId, numericScore, teacherFeedback = "") {
  return apiPostJson("/api/academics/grades/grade/", {
    submission_id: submissionId,
    numeric_score: numericScore,
    teacher_feedback: teacherFeedback,
  });
}

// ── Mastery ───────────────────────────────────────────────

export async function listMastery(studentId) {
  return apiGet(
    `/api/academics/mastery/?student_id=${encodeURIComponent(studentId)}`
  );
}

// ── Transcript ────────────────────────────────────────────

export async function listTranscript(studentId) {
  return apiGet(
    `/api/academics/transcript-entries/?student_id=${encodeURIComponent(studentId)}`
  );
}
