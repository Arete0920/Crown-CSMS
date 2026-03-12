import { getToken, getSchoolId } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

/**
 * Fetch admissions applications list (staff-only)
 * @returns {Promise<Array>} - array of application objects
 */
export const getAdmissionsApplications = async () => {
  const token = getToken();
  const schoolId = getSchoolId();

  if (!token || !schoolId) {
    throw new Error("Missing authentication credentials");
  }

  const url = `${API_BASE}/api/admissions/applications/`;

  const response = await fetch(url, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const body = await response.text();
    const err = new Error(`Admissions API error: ${response.status}`);
    err.status = response.status;
    err.body = body;
    err.url = url;
    throw err;
  }

  const data = await response.json();
  return Array.isArray(data) ? data : [];
};

/**
 * Enroll an accepted applicant. Moves status ACCEPTED â†’ ENROLLED.
 * @param {number} applicationId - AdmissionsApplication PK
 * @returns {Promise<{ok, student_id, name, message}>}
 */
export const enrollApplicant = async (applicationId) => {
  const token = getToken();
  const schoolId = getSchoolId();

  if (!token || !schoolId) {
    throw new Error("Missing authentication credentials");
  }

  const url = `${API_BASE}/api/admissions/enroll/`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ application_id: applicationId }),
  });

  const data = await response.json();

  if (!response.ok) {
    const err = new Error(data.detail || `Enroll error: ${response.status}`);
    err.status = response.status;
    throw err;
  }

  return data;
};

