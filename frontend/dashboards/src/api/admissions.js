import { getToken, getSchoolId } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

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
