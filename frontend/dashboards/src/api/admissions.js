import { apiGet, apiGetList, apiPost } from './request';
import { buildApiPath } from '../utils/apiContracts';

/**
 * Fetch admissions applications list (staff-only)
 * @returns {Promise<Array>} - array of application objects
 */
export const getAdmissionsApplications = async () => {
  return apiGetList(buildApiPath('admissions.applications.list'));
};

/**
 * Enroll an accepted applicant. Moves status ACCEPTED â†’ ENROLLED.
 * @param {number} applicationId - AdmissionsApplication PK
 * @returns {Promise<{ok, student_id, name, message}>}
 */
export const enrollApplicant = async (applicationId) => {
  const path = buildApiPath('admissions.applications.enroll', {
    applicationId,
  });

  return apiPost(path, { application_id: applicationId });
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
  return apiGet(`${path}${buildQuery(params)}`);
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

