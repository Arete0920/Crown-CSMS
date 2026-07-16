/**
 * dashboards.js — API client for the Crown unified dashboard API.
 * Uses the canonical authenticated client for API-base resolution, credentials,
 * tenant context, bearer authentication, and structured failures.
 */
import { authenticatedFetch } from "../utils/authClient.js";

function parseErrorBody(body) {
  if (!body) return null;
  if (typeof body === "object") return body;
  try {
    return JSON.parse(body);
  } catch {
    return { detail: String(body) };
  }
}

async function jsonRequest(path, init = {}) {
  try {
    const response = await authenticatedFetch(path, {
      credentials: "include",
      ...init,
    });
    const data = await response.json();
    return {
      ok: true,
      status: response.status,
      data,
      correlationId: response.headers?.get?.("x-correlation-id") || "",
      error: "",
    };
  } catch (error) {
    const data = parseErrorBody(error?.body);
    return {
      ok: false,
      status: Number(error?.status || 0),
      data,
      correlationId: error?.correlationId || "",
      error: data?.detail || data?.message || error?.message || "Dashboard request failed",
    };
  }
}

function requestHeaders(schoolId, role) {
  return {
    "X-Demo-Role": role,
    "X-School-Id": schoolId,
  };
}

export function fetchDashboardMe(schoolId, role) {
  return jsonRequest("/api/dashboards/me/", {
    method: "GET",
    headers: requestHeaders(schoolId, role),
  });
}

export function fetchDashboardSummary(schoolId, role) {
  return jsonRequest("/api/dashboards/summary/", {
    method: "GET",
    headers: requestHeaders(schoolId, role),
  });
}

export function fetchDashboardDrilldown(widget, schoolId, role) {
  const query = new URLSearchParams({ widget: String(widget || "") });
  return jsonRequest(`/api/dashboards/drilldown/?${query.toString()}`, {
    method: "GET",
    headers: requestHeaders(schoolId, role),
  });
}

export function fetchDashboardAlerts(schoolId, role) {
  return jsonRequest("/api/dashboards/alerts/", {
    method: "GET",
    headers: requestHeaders(schoolId, role),
  });
}
