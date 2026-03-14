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

function buildQuery(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, String(value));
    }
  });
  const qs = query.toString();
  return qs ? `?${qs}` : "";
}

async function fetchAdmissionsEndpoint(path, params = {}) {
  const token = getToken();
  const schoolId = getSchoolId();

  if (!token || !schoolId) {
    throw new Error("Missing authentication credentials");
  }

  const url = `${API_BASE}${path}${buildQuery(params)}`;
  const response = await fetch(url, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      "X-School-Id": schoolId,
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

  return response.json();
}

export function fetchAdmissionsSummary(params = {}) {
  return fetchAdmissionsEndpoint("/api/v1/admissions/summary/", params);
}

export function fetchAdmissionsDrilldown(params = {}) {
  return fetchAdmissionsEndpoint("/api/v1/admissions/drilldown/", params);
}

export function fetchAdmissionsPriorityQueue(params = {}) {
  return fetchAdmissionsEndpoint("/api/admissions/priority-queue/", params);
}

export function fetchAdmissionsMetrics(params = {}) {
  return fetchAdmissionsEndpoint("/api/admissions/metrics/", params);
}

export function fetchAdmissionsTimeline(params = {}) {
  return fetchAdmissionsEndpoint("/api/admissions/timeline/", params);
}

