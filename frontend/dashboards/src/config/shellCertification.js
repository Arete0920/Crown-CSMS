import dashboardNavConfig from "../components/navigation/dashboardNavConfig";
import * as DashboardRegistryModule from "./dashboardRegistry.js";
import { WIZARD_ROUTE_DEFINITIONS } from "../routes/wizards.js";
import {
  STATIC_SHELL_PATHS,
  flattenNavItems,
  getPathFromItem,
  normalizePath,
} from "./shellOwnership.js";
import {
  getReleaseState,
  hasPlaceholderLikeText,
  isProductionReady,
} from "./releaseState.js";

function getDashboardRegistrySource() {
  return (
    DashboardRegistryModule.DASHBOARD_REGISTRY ||
    DashboardRegistryModule.dashboardRegistry ||
    DashboardRegistryModule.default ||
    []
  );
}

function annotate(entries = [], source = "unknown") {
  return (Array.isArray(entries) ? entries : [])
    .map((entry) => {
      const path = normalizePath(getPathFromItem(entry));
      return {
        ...entry,
        __source: source,
        __path: path,
        __releaseState: getReleaseState(entry),
      };
    })
    .filter((entry) => entry.__path);
}

export function getOwnedRouteEntries() {
  const staticEntries = STATIC_SHELL_PATHS.map((path) => ({
    path,
    releaseState: "ready",
    owner: "staticShell",
  }));

  return [
    ...annotate(staticEntries, "staticShell"),
    ...annotate(getDashboardRegistrySource(), "dashboardRegistry"),
    ...annotate(WIZARD_ROUTE_DEFINITIONS, "wizardRoutes"),
  ];
}

export function getUncertifiedOwnedRoutes() {
  return getOwnedRouteEntries().filter((entry) => !entry.__releaseState);
}

export function getNonReadyOwnedRoutes() {
  return getOwnedRouteEntries().filter((entry) => !isProductionReady(entry));
}

export function getReadyOwnedRoutes() {
  return getOwnedRouteEntries().filter((entry) => isProductionReady(entry));
}

export function getPathToOwnedRouteMap() {
  const map = new Map();

  getOwnedRouteEntries().forEach((entry) => {
    if (!map.has(entry.__path)) {
      map.set(entry.__path, []);
    }
    map.get(entry.__path).push(entry);
  });

  return map;
}

export function getReleaseStateConflicts() {
  const map = getPathToOwnedRouteMap();

  return [...map.entries()]
    .map(([path, entries]) => {
      const states = [...new Set(entries.map((entry) => entry.__releaseState || ""))];
      return { path, states, entries };
    })
    .filter((item) => item.states.length > 1);
}

export function getActiveNavEntries() {
  return flattenNavItems(dashboardNavConfig)
    .map((item) => ({
      ...item,
      __path: normalizePath(getPathFromItem(item)),
    }))
    .filter((item) => {
      if (!item.__path) return false;
      if (item.external) return false;
      if (item.disabled) return false;
      if (item.comingSoon) return false;
      return true;
    });
}

export function getActiveNavTargetFindings() {
  const pathMap = getPathToOwnedRouteMap();

  return getActiveNavEntries().flatMap((navItem) => {
    const owned = pathMap.get(navItem.__path) || [];

    if (owned.length === 0) {
      return [
        {
          type: "unowned-nav-target",
          navItem,
        },
      ];
    }

    const nonReady = owned.filter((entry) => !isProductionReady(entry));

    if (nonReady.length > 0) {
      return [
        {
          type: "non-ready-nav-target",
          navItem,
          ownedEntries: nonReady,
        },
      ];
    }

    return [];
  });
}

export function getPlaceholderLikeReadyRoutes() {
  return getReadyOwnedRoutes().filter((entry) => hasPlaceholderLikeText(entry));
}
