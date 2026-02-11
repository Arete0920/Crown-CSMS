/**
 * Request tracing for DEV mode
 * Logs API calls with tenant headers and correlation IDs for debugging
 */

import { getSelectedSchoolId } from "./authClient.js";

export function logApiRequest(method, url, details = {}) {
  if (!import.meta.env.DEV) return;

  const schoolId = getSelectedSchoolId();
  const timestamp = new Date().toISOString();
  const correlationId = details.correlationId || "—";

  console.group(`🔗 [API] ${method.toUpperCase()} ${url.split("/").slice(-2).join("/")}`);
  console.log(`Timestamp: ${timestamp}`);
  console.log(`Tenant (X-School-Id): ${schoolId || "none"}`);
  console.log(`Correlation ID: ${correlationId}`);
  if (details.message) console.log(`Message: ${details.message}`);
  console.groupEnd();
}

export function logApiError(method, url, error, details = {}) {
  if (!import.meta.env.DEV) return;

  const schoolId = getSelectedSchoolId();
  console.group(`❌ [API Error] ${method.toUpperCase()} ${url.split("/").slice(-2).join("/")}`);
  console.log(`Tenant (X-School-Id): ${schoolId || "none"}`);
  console.log(`Status: ${error.status || "unknown"}`);
  console.log(`Message: ${error.message || "unknown error"}`);
  if (details.body) console.log(`Body: ${details.body.slice(0, 200)}`);
  console.groupEnd();
}
