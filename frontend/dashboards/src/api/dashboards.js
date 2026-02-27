/**
 * dashboards.js — API client for the Crown unified dashboard API.
 * Uses httpJson for structured error handling and Crown's session-storage
 * credential convention (crown.jwt.access, crown.school.id).
 */
import { httpJson } from "../lib/http.js";

function getSchoolId() {
  try { return sessionStorage.getItem("crown.school.id") || ""; }
  catch { return ""; }
}

function getToken() {
  try { return sessionStorage.getItem("crown.jwt.access") || ""; }
  catch { return ""; }
}

function _headers(schoolId, role) {
  const h = {
    "Accept": "application/json",
    "Content-Type": "application/json",
  };
  const sid = schoolId || getSchoolId();
  const tok = getToken();
  if (sid) h["X-School-Id"] = sid;
  if (tok) h["Authorization"] = `Bearer ${tok}`;
  // Demo/dev role override (only active when server allows ALLOW_DEMO_ROLE_HEADER=1)
  if (role) h["X-Demo-Role"] = role;
  return h;
}

/**
 * GET /api/dashboards/me/
 * Returns { school_id, display_name, roles, default_route, features }
 */
export async function fetchDashboardMe(schoolId, role) {
  return httpJson("/api/dashboards/me/", {
    method: "GET",
    credentials: "include",
    headers: _headers(schoolId, role),
  });
}

/**
 * GET /api/dashboards/summary/
 * Returns { role, school_id, generated_at, widgets: DashboardWidget[] }
 */
export async function fetchDashboardSummary(schoolId, role) {
  return httpJson("/api/dashboards/summary/", {
    method: "GET",
    credentials: "include",
    headers: _headers(schoolId, role),
  });
}

/**
 * GET /api/dashboards/drilldown/?widget=<key>
 * Returns { widget, school_id, page, has_more, rows }
 */
export async function fetchDashboardDrilldown(widgetKey, schoolId, role) {
  const params = new URLSearchParams({ widget: widgetKey });
  return httpJson(`/api/dashboards/drilldown/?${params}`, {
    method: "GET",
    credentials: "include",
    headers: _headers(schoolId, role),
  });
}

/**
 * GET /api/dashboards/alerts/
 * Returns { school_id, generated_at, alerts: DashboardAlert[] }
 */
export async function fetchDashboardAlerts(schoolId, role) {
  return httpJson("/api/dashboards/alerts/", {
    method: "GET",
    credentials: "include",
    headers: _headers(schoolId, role),
  });
}
