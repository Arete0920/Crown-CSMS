import dashboardNavConfig from "../components/navigation/dashboardNavConfig";
import * as DashboardRegistryModule from "./dashboardRegistry";
import { WIZARD_ROUTE_DEFINITIONS } from "../routes/wizards";

export const STATIC_SHELL_PATHS = [
  "/",
  "/login",
  "/logout",
  "/not-authorized",
  "/unauthorized",
  "/wizards",
  "/gradebook",
  "/classrooms",
  "/attendance",
  "/board",
  "/integrity",
  "/parent",
  "/academics/parent-snapshot",
  "/finance/invoices",
  "/student",
  "/academics/student-work",
  "/admissions",
  "/admissions/pipeline",
  "/aftercare/roster",
  "/communications",
  "/communications-director",
];

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

export function normalizePath(value) {
  let path = String(value ?? "").trim();
  if (!path) return "";

  if (
    /^https?:\/\//i.test(path) ||
    /^mailto:/i.test(path) ||
    /^tel:/i.test(path)
  ) {
    return path;
  }

  path = path.split("?")[0].split("#")[0];

  if (!path.startsWith("/")) {
    path = `/${path}`;
  }

  path = path.replace(/\/{2,}/g, "/");

  if (path.length > 1 && path.endsWith("/")) {
    path = path.slice(0, -1);
  }

  return path || "/";
}

export function getDashboardRegistrySource() {
  return (
    DashboardRegistryModule.DASHBOARD_REGISTRY ||
    DashboardRegistryModule.dashboardRegistry ||
    DashboardRegistryModule.default ||
    []
  );
}

export function getPathFromItem(item) {
  if (!item || typeof item !== "object") return "";
  return normalizePath(item.href || item.to || item.path || "");
}

export function flattenNavItems(items = [], parents = []) {
  if (!Array.isArray(items)) return [];

  return items.flatMap((item) => {
    const current = {
      ...item,
      __parents: parents,
      __resolvedPath: getPathFromItem(item),
    };

    const children = Array.isArray(item.children)
      ? flattenNavItems(item.children, [...parents, item.label || item.title || item.name || ""])
      : [];

    return [current, ...children];
  });
}

export function getNavLinks(items = dashboardNavConfig) {
  return flattenNavItems(items).filter((item) => {
    if (!item.__resolvedPath) return false;
    if (item.external) return false;
    return true;
  });
}

export function getDashboardRegistryPaths() {
  const registry = getDashboardRegistrySource();
  if (!Array.isArray(registry)) return [];

  return unique(
    registry
      .map((item) => getPathFromItem(item))
      .filter(Boolean)
  );
}

export function getWizardPaths() {
  return unique(
    (Array.isArray(WIZARD_ROUTE_DEFINITIONS) ? WIZARD_ROUTE_DEFINITIONS : [])
      .map((item) => getPathFromItem(item))
      .filter(Boolean)
  );
}

export function getOwnedShellPaths() {
  return unique([
    ...STATIC_SHELL_PATHS.map((path) => normalizePath(path)),
    ...getDashboardRegistryPaths(),
    ...getWizardPaths(),
  ]);
}

export function getUnownedNavLinks() {
  const owned = new Set(getOwnedShellPaths());

  return getNavLinks().filter((item) => {
    const path = item.__resolvedPath;

    if (!path) return false;
    if (item.disabled || item.comingSoon) return false;
    if (/^https?:\/\//i.test(path)) return false;
    if (/^mailto:/i.test(path)) return false;
    if (/^tel:/i.test(path)) return false;

    return !owned.has(path);
  });
}

export function getDuplicateOwnedPaths() {
  const counts = new Map();

  [
    ...getDashboardRegistryPaths(),
    ...getWizardPaths(),
  ].forEach((path) => {
    counts.set(path, (counts.get(path) || 0) + 1);
  });

  return [...counts.entries()]
    .filter(([, count]) => count > 1)
    .map(([path, count]) => ({ path, count }));
}

export function getLikelyPlaceholderNavLinks() {
  const placeholderPattern =
    /(coming-soon|placeholder|under-construction|not-ready|unavailable)/i;

  return getNavLinks().filter((item) => {
    const text = [
      item.label,
      item.title,
      item.name,
      item.__resolvedPath,
    ]
      .filter(Boolean)
      .join(" ");

    return placeholderPattern.test(text);
  });
}
