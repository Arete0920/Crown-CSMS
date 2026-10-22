import type { DashboardApiPayload, DashboardRoleKey } from "./dashboardTypes";
import { fetchDashboardAlerts, fetchDashboardMe, fetchDashboardSummary } from "../../api/dashboards.js";

type SchoolDashboardContext = {
  apiBaseUrl: string;
  schoolId: string;
  token: string;
};

type DashboardFetchOptions = RequestInit & {
  schoolId?: string;
  token?: string;
};

type HttpJsonResult<T> = {
  ok: boolean;
  status: number;
  data: T | null;
  correlationId: string;
  error: string;
};

type DashboardMeResult = HttpJsonResult<Record<string, unknown>>;

type DashboardSummaryResult = HttpJsonResult<{
  widgets?: unknown[];
}>;

type DashboardAlertsResult = HttpJsonResult<{
  alerts?: unknown[];
}>;

function getSchoolDashboardContext(): SchoolDashboardContext {
  const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || "").trim().replace(/\/$/, "");

  try {
    return {
      apiBaseUrl,
      schoolId: sessionStorage.getItem("crown.school.id") || localStorage.getItem("crown.school.id") || localStorage.getItem("schoolId") || "",
      token: sessionStorage.getItem("crown.jwt.access") || "",
    };
  } catch {
    return {
      apiBaseUrl,
      schoolId: "",
      token: "",
    };
  }
}

function getStoredSchoolIdCandidates(): string[] {
  try {
    return [
      sessionStorage.getItem("crown.school.id") || "",
      localStorage.getItem("crown.school.id") || "",
      localStorage.getItem("schoolId") || "",
    ].filter((value, index, array) => Boolean(value) && array.indexOf(value) === index);
  } catch {
    return [];
  }
}

function getStoredTokenCandidates(): string[] {
  try {
    return [
      sessionStorage.getItem("crown.jwt.access") || "",
    ].filter(Boolean);
  } catch {
    return [];
  }
}

function buildDashboardRequestHeaders(init: DashboardFetchOptions | undefined, token: string, schoolId: string): Headers {
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (schoolId) {
    headers.set("X-School-Id", schoolId);
  }
  return headers;
}

async function fetchDashboardJsonCandidate<T>(url: string, init: DashboardFetchOptions | undefined, token: string, schoolId: string): Promise<T | null> {
  try {
    const response = await fetch(url, {
      ...init,
      credentials: "include",
      headers: buildDashboardRequestHeaders(init, token, schoolId),
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

async function fetchDashboardJsonWithFallback<T>(url: string, init?: DashboardFetchOptions): Promise<T | null> {
  const tokenCandidates = init?.token ? [init.token] : getStoredTokenCandidates();
  const schoolIdCandidates = init?.schoolId ? [init.schoolId] : getStoredSchoolIdCandidates();

  for (const token of tokenCandidates) {
    for (const schoolId of schoolIdCandidates) {
      const result = await fetchDashboardJsonCandidate<T>(url, init, token, schoolId);
      if (result) {
        return result;
      }
    }
  }

  return null;
}

async function safeFetchJson<T>(url: string, init?: RequestInit): Promise<T | null> {
  try {
    const headers = new Headers(init?.headers);
    headers.set("Accept", "application/json");

    const response = await fetch(url, {
      ...init,
      credentials: "include",
      headers,
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

function buildSchoolDashboardHeaders(): HeadersInit {
  const { schoolId, token } = getSchoolDashboardContext();
  const headers: Record<string, string> = {};

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  if (schoolId) {
    headers["X-School-Id"] = schoolId;
  }

  return headers;
}

export async function loadRoleDashboardPayload(roleKey: DashboardRoleKey): Promise<DashboardApiPayload | null> {
  return fetchDashboardJsonWithFallback<DashboardApiPayload>(`/api/v1/dashboards/roles/${roleKey}/`);
}

export async function loadSharedDashboardPayload(): Promise<DashboardApiPayload | null> {
  return fetchDashboardJsonWithFallback<DashboardApiPayload>("/api/v1/dashboards/shared/");
}

export async function loadMicrosoft365DashboardPayload(): Promise<DashboardApiPayload | null> {
  return fetchDashboardJsonWithFallback<DashboardApiPayload>("/api/v1/dashboards/microsoft365/");
}

// Connectivity endpoints are not certified business aggregate sources.
function validSchoolPayload(result: HttpJsonResult<unknown>, schoolId: string, field: 'roles' | 'widgets' | 'alerts'): boolean {
  const data = result.data;
  if (!result.ok || !schoolId || !data || typeof data !== 'object' || Array.isArray(data)) return false;
  const record = data as Record<string, unknown>;
  const meta = record.meta && typeof record.meta === 'object' && !Array.isArray(record.meta)
    ? record.meta as Record<string, unknown> : null;
  const returnedSchool = record.school_id ?? meta?.school_id;
  return String(returnedSchool ?? '') === schoolId && Array.isArray(record[field])
    && (field !== 'roles' || typeof record.default_route === 'string');
}

export async function loadSchoolAdministratorLiveSnapshot() {
  const { schoolId } = getSchoolDashboardContext();
  const [meResult, summaryResult, alertsResult] = await Promise.all([
    fetchDashboardMe(schoolId, 'school-administrator') as Promise<DashboardMeResult>,
    fetchDashboardSummary(schoolId, 'school-administrator') as Promise<DashboardSummaryResult>,
    fetchDashboardAlerts(schoolId, 'school-administrator') as Promise<DashboardAlertsResult>,
  ]);
  const meValid = validSchoolPayload(meResult, schoolId, 'roles');
  const summaryValid = validSchoolPayload(summaryResult, schoolId, 'widgets');
  const alertsValid = validSchoolPayload(alertsResult, schoolId, 'alerts');
  const successfulEndpointCount = Number(meValid) + Number(summaryValid) + Number(alertsValid);
  return {
    dashboardMe: meValid ? meResult.data : null,
    dashboardSummary: summaryValid ? summaryResult.data : null,
    dashboardAlerts: alertsValid ? alertsResult.data : null,
    serviceState: successfulEndpointCount === 3 ? 'connected' : successfulEndpointCount > 0 ? 'partial' : 'unavailable',
    successfulEndpointCount,
    endpointStatuses: { me: meResult.status, summary: summaryResult.status, alerts: alertsResult.status },
    dataState: 'sample',
    sourceLabel: 'Dashboard API connectivity only; school business totals are illustrative',
    lastSyncLabel: successfulEndpointCount + ' of 3 dashboard endpoints returned valid school-scoped data',
  };
}
