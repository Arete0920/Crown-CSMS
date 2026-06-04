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

type DashboardMeResult = {
  ok: boolean;
  data: Record<string, unknown> | null;
};

type DashboardSummaryResult = {
  ok: boolean;
  data: {
    widgets?: unknown[];
  } | null;
};

type DashboardAlertsResult = {
  ok: boolean;
  data: {
    alerts?: unknown[];
  } | null;
};

function getSchoolDashboardContext(): SchoolDashboardContext {
  const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || "").trim().replace(/\/$/, "");

  try {
    return {
      apiBaseUrl,
      schoolId: sessionStorage.getItem("crown.school.id") || localStorage.getItem("crown.school.id") || localStorage.getItem("schoolId") || "",
      token: sessionStorage.getItem("crown.jwt.access") || localStorage.getItem("crown.jwt.access") || "",
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
      localStorage.getItem("crown.jwt.access") || "",
    ].filter((value, index, array) => Boolean(value) && array.indexOf(value) === index);
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

function hasLiveDashboardPayload(
  meResult: DashboardMeResult,
  summaryResult: DashboardSummaryResult,
  alertsResult: DashboardAlertsResult,
): boolean {
  return Boolean(meResult.ok && meResult.data) || Boolean(summaryResult.ok && summaryResult.data) || Boolean(alertsResult.ok && alertsResult.data);
}

function buildLiveDashboardSourceLabel(
  meResult: DashboardMeResult,
  summaryResult: DashboardSummaryResult,
  alertsResult: DashboardAlertsResult,
): string {
  const parts: string[] = [];
  if (meResult.ok && meResult.data) parts.push("dashboard me");
  if (summaryResult.ok && summaryResult.data) parts.push("dashboard summary");
  if (alertsResult.ok && alertsResult.data) parts.push("dashboard alerts");
  return parts.join(" + ");
}

function buildLiveDashboardLastSyncLabel(widgetCount: number, alertCount: number): string {
  const detail = widgetCount || alertCount ? ` (${widgetCount} widgets, ${alertCount} alerts)` : "";
  return `Live dashboard summary${detail}`;
}

export async function loadSchoolAdministratorLiveSnapshot() {
  const { schoolId } = getSchoolDashboardContext();

  const [meResult, summaryResult, alertsResult] = await Promise.all([
    fetchDashboardMe(schoolId, "school-administrator") as Promise<DashboardMeResult>,
    fetchDashboardSummary(schoolId, "school-administrator") as Promise<DashboardSummaryResult>,
    fetchDashboardAlerts(schoolId, "school-administrator") as Promise<DashboardAlertsResult>,
  ]);

  const dashboardMe = meResult.ok ? meResult.data : null;
  const dashboardSummary = summaryResult.ok ? summaryResult.data : null;
  const dashboardAlerts = alertsResult.ok ? alertsResult.data : null;
  const live = hasLiveDashboardPayload(meResult, summaryResult, alertsResult);
  const widgetCount = Array.isArray(dashboardSummary?.widgets) ? dashboardSummary.widgets.length : 0;
  const alertCount = Array.isArray(dashboardAlerts?.alerts) ? dashboardAlerts.alerts.length : 0;
  const sourceLabel = live ? buildLiveDashboardSourceLabel(meResult, summaryResult, alertsResult) : "Dashboard template data";

  return {
    dashboardMe,
    dashboardSummary,
    dashboardAlerts,
    dataState: live ? "live" : "fallback",
    sourceLabel: live ? `Live data from ${sourceLabel}` : sourceLabel,
    lastSyncLabel: live ? buildLiveDashboardLastSyncLabel(widgetCount, alertCount) : "Using configured fallback data",
  };
}
