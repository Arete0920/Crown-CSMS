import * as DashboardRegistryModule from "../config/dashboardRegistry";
import { isProductionReady } from "../config/releaseState";
import { WIZARD_ROUTE_DEFINITIONS } from "../routes/wizards";

function uniqueSorted(list, sortKey = "path") {
  return [...list].sort((a, b) => {
    const left = String(a?.[sortKey] ?? "");
    const right = String(b?.[sortKey] ?? "");
    return left.localeCompare(right);
  });
}

function normalizePath(value) {
  let path = String(value ?? "").trim();
  if (!path) return "";

  if (!path.startsWith("/")) {
    path = `/${path}`;
  }

  path = path.replace(/\/{2,}/g, "/");

  if (path.length > 1 && path.endsWith("/")) {
    path = path.slice(0, -1);
  }

  return path;
}

function getDashboardRegistrySource() {
  return (
    DashboardRegistryModule.DASHBOARD_REGISTRY ||
    DashboardRegistryModule.dashboardRegistry ||
    DashboardRegistryModule.default ||
    []
  );
}

function buildWizardContractEntry(entry) {
  return {
    moduleKey: String(entry.moduleKey || "").trim(),
    path: normalizePath(entry.path),
    apiPrefix: String(entry.apiPrefix || "").trim(),
    requiresAuth: true,
    requiresSchoolHeader: true,
    schoolHeaderName: "X-School-Id",
    probeSchoolId: "1",
    acceptableUnauthenticatedStatusCodes: [401, 403],
    acceptableMissingSchoolHeaderStatusCodes: [400, 403],
    acceptableAuthenticatedStatusCodes: [200, 403, 405],
    requiresSeededSuccess: true,
    seededSuccessProbeMethod: "POST",
    acceptableSeededSuccessStatusCodes: [201],
    expectedJsonTopLevelKinds: ["array", "object"],
  };
}

export function getFrontendWizardContract() {
  return uniqueSorted(
    (Array.isArray(WIZARD_ROUTE_DEFINITIONS) ? WIZARD_ROUTE_DEFINITIONS : [])
      .filter((entry) => isProductionReady(entry))
      .filter((entry) => entry.apiPrefix)
      .map(buildWizardContractEntry),
    "path"
  );
}

export function getFrontendDashboardContract() {
  return uniqueSorted(
    (Array.isArray(getDashboardRegistrySource()) ? getDashboardRegistrySource() : [])
      .filter((entry) => isProductionReady(entry))
      .filter((entry) => entry.apiContractKey)
      .map((entry) => ({
        moduleKey: String(entry.moduleKey || "").trim(),
        path: normalizePath(entry.path),
        apiContractKey: String(entry.apiContractKey || "").trim(),
      })),
    "path"
  );
}

export function getFrontendShellBackendContract() {
  return {
    version: 3,
    wizards: getFrontendWizardContract(),
    dashboardModules: getFrontendDashboardContract(),
  };
}
