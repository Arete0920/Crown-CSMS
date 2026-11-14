import { apiGet, apiGetList, apiPost } from './request';
import { buildApiPath } from '../utils/apiContracts';

function createRequestIdentity() {
  const seed = globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`;
  const key = String(seed);
  return {
    requestId: key,
    idempotencyKey: `admissions-submit-${key}`,
  };
}

/**
 * Fetch admissions applications list.
 * @returns {Promise<Array>} - array of application objects
 */
export const getAdmissionsApplications = async () => {
  // A high-concurrency Windows local demo can queue a real read beyond the
  // ordinary 15s transport budget. Retain the normal deadline everywhere else.
  return apiGetList(buildApiPath('admissions.applications.list'), {
    timeout: import.meta.env.VITE_LOCAL_DEMO === '1' ? 45000 : undefined,
  });
};

export const updateApplicantReview = async (applicationId) => {
  return apiPost('/api/admissions/review-update/', { application_id: applicationId });
};

export const decideApplicant = async (applicationId, decision) => {
  return apiPost('/api/admissions/decision/', {
    application_id: applicationId,
    decision,
  });
};

/**
 * Enroll an accepted applicant. Moves status ACCEPTED → ENROLLED.
 * @param {number} applicationId - AdmissionsApplication PK
 * @returns {Promise<{ok, student_id, name, message}>}
 */
export const enrollApplicant = async (applicationId) => {
  return apiPost(buildApiPath('admissions.enroll'), { application_id: applicationId });
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

export function fetchAdmissionsPublicConfig({ schoolId = "", campus = "", term = "" } = {}) {
  return fetchAdmissionsEndpoint("/api/v1/admissions/public-config/", {
    ...(term && (schoolId || campus) ? { ...(schoolId ? { school_id: schoolId } : {}), ...(campus ? { campus } : {}), term } : {}),
  });
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

export function submitAdmissionsIntake(payload = {}, options = {}) {
  const identity = createRequestIdentity();
  return apiPost("/api/v1/admissions/submit/", payload, {
    headers: {
      'X-Request-Id': identity.requestId,
      'Idempotency-Key': options.idempotencyKey || identity.idempotencyKey,
      ...(options.schoolId ? { 'X-School-Id': options.schoolId } : {}),
    },
  });
}
