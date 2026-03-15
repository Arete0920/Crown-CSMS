import * as DashboardRegistryModule from "./dashboardRegistry.js";
import { WIZARD_ROUTE_DEFINITIONS } from "../routes/wizards.js";
import {
  getReleaseState,
  hasPlaceholderLikeText,
  isProductionReady,
} from "./releaseState.js";
import { getPathFromItem, normalizePath } from "./shellOwnership.js";

export const REQUIRED_READY_ROUTE_FIELDS = ["moduleKey", "moduleType", "owner"];

export const REQUIRED_READY_FLAGS = [
  "shellReady",
  "uxReady",
  "accessReady",
  "dataReady",
];

function getDashboardRegistrySource() {
  return (
    DashboardRegistryModule.DASHBOARD_REGISTRY ||
    DashboardRegistryModule.dashboardRegistry ||
    DashboardRegistryModule.default ||
    []
  );
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function getComponentRef(entry = {}) {
  return (
    entry.component ||
    entry.Component ||
    entry.pageComponent ||
    entry.viewComponent ||
    entry.element?.type ||
    null
  );
}

function getComponentName(entry = {}) {
  const componentRef = getComponentRef(entry);

  if (!componentRef) return "";

  if (typeof componentRef === "string") return componentRef;

  return (
    componentRef.displayName ||
    componentRef.name ||
    componentRef.render?.displayName ||
    componentRef.render?.name ||
    ""
  );
}

function getReadiness(entry = {}) {
  return entry.readiness || entry.certification || entry.audit || {};
}

function annotate(entries = [], source = "unknown", moduleType = "unknown") {
  return asArray(entries)
    .map((entry) => {
      const path = normalizePath(getPathFromItem(entry));
      const componentName = getComponentName(entry);
      const readiness = getReadiness(entry);

      return {
        ...entry,
        __source: source,
        __moduleType: entry.moduleType || moduleType || "",
        __owner: entry.owner || "",
        __path: path,
        __releaseState: getReleaseState(entry),
        __componentName: componentName,
        __readiness: readiness,
      };
    })
    .filter((entry) => entry.__path);
}

export function getOwnedModuleEntries() {
  return [
    ...annotate(getDashboardRegistrySource(), "dashboardRegistry", "dashboard"),
    ...annotate(WIZARD_ROUTE_DEFINITIONS, "wizardRoutes", "wizard"),
  ];
}

export function getReadyModuleEntries() {
  return getOwnedModuleEntries().filter((entry) => isProductionReady(entry));
}

export function getReadyRoutesMissingRequiredFields() {
  return getReadyModuleEntries().flatMap((entry) => {
    return REQUIRED_READY_ROUTE_FIELDS.filter((field) => {
      const value =
        field === "moduleType"
          ? entry.moduleType || entry.__moduleType
          : entry[field] || entry[`__${field}`];

      return !value;
    }).map((field) => ({
      type: "missing-required-field",
      field,
      entry,
    }));
  });
}

export function getReadyRoutesWithoutConcreteComponent() {
  return getReadyModuleEntries()
    .filter((entry) => !getComponentRef(entry) || !entry.__componentName)
    .map((entry) => ({
      type: "missing-component",
      entry,
    }));
}

export function getReadyRoutesMissingRequiredFlags() {
  return getReadyModuleEntries().flatMap((entry) => {
    return REQUIRED_READY_FLAGS.filter((flag) => !(flag in entry.__readiness)).map((flag) => ({
      type: "missing-readiness-flag",
      flag,
      entry,
    }));
  });
}

export function getReadyRoutesWithFalseReadinessFlags() {
  return getReadyModuleEntries().flatMap((entry) => {
    return REQUIRED_READY_FLAGS.filter((flag) => entry.__readiness[flag] !== true).map((flag) => ({
      type: "false-readiness-flag",
      flag,
      entry,
    }));
  });
}

export function getReadyRoutesWithPlaceholderSignals() {
  const placeholderComponentPattern =
    /(placeholder|comingsoon|coming_soon|notready|underconstruction|unavailable)/i;

  return getReadyModuleEntries()
    .filter((entry) => {
      const componentName = entry.__componentName || "";
      return (
        hasPlaceholderLikeText(entry) ||
        placeholderComponentPattern.test(componentName)
      );
    })
    .map((entry) => ({
      type: "placeholder-signal-on-ready-route",
      entry,
    }));
}

export function getReadyRoutesWithInvalidPath() {
  return getReadyModuleEntries()
    .filter((entry) => !entry.__path || entry.__path === "/wizards")
    .map((entry) => ({
      type: "invalid-ready-path",
      entry,
    }));
}

export function getDuplicateReadyModuleKeys() {
  const counts = new Map();

  getReadyModuleEntries().forEach((entry) => {
    const key = String(entry.moduleKey || "").trim();
    if (!key) return;
    counts.set(key, (counts.get(key) || 0) + 1);
  });

  return [...counts.entries()]
    .filter(([, count]) => count > 1)
    .map(([moduleKey, count]) => ({
      type: "duplicate-ready-module-key",
      moduleKey,
      count,
    }));
}

export function getFakeReadyRoutes() {
  return [
    ...getReadyRoutesMissingRequiredFields(),
    ...getReadyRoutesWithoutConcreteComponent(),
    ...getReadyRoutesMissingRequiredFlags(),
    ...getReadyRoutesWithFalseReadinessFlags(),
    ...getReadyRoutesWithPlaceholderSignals(),
    ...getReadyRoutesWithInvalidPath(),
    ...getDuplicateReadyModuleKeys(),
  ];
}

export function getModuleReadinessSummary() {
  const readyRoutes = getReadyModuleEntries();

  return {
    readyRouteCount: readyRoutes.length,
    fakeReadyRouteCount: getFakeReadyRoutes().length,
    missingFieldCount: getReadyRoutesMissingRequiredFields().length,
    missingComponentCount: getReadyRoutesWithoutConcreteComponent().length,
    missingFlagCount: getReadyRoutesMissingRequiredFlags().length,
    falseFlagCount: getReadyRoutesWithFalseReadinessFlags().length,
    placeholderSignalCount: getReadyRoutesWithPlaceholderSignals().length,
    duplicateModuleKeyCount: getDuplicateReadyModuleKeys().length,
  };
}
