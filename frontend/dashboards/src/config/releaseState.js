export const RELEASE_STATES = {
  READY: "ready",
  LIVE: "live",
  PRODUCTION: "production",
  DRAFT: "draft",
  PLACEHOLDER: "placeholder",
  COMING_SOON: "coming_soon",
  HIDDEN: "hidden",
  DISABLED: "disabled",
};

export const READY_RELEASE_STATES = new Set([
  RELEASE_STATES.READY,
  RELEASE_STATES.LIVE,
  RELEASE_STATES.PRODUCTION,
]);

export const NON_READY_RELEASE_STATES = new Set([
  RELEASE_STATES.DRAFT,
  RELEASE_STATES.PLACEHOLDER,
  RELEASE_STATES.COMING_SOON,
  RELEASE_STATES.HIDDEN,
  RELEASE_STATES.DISABLED,
]);

// These registry rows predate the current dashboard-fit canon and still carry
// stale `ready` flags. The fit matrix classifies School Administrator as
// Scaffold and Release Reliability as Hybrid. Until their live/certified data,
// freshness, backend dashboard-key access, performance, and independent-review
// requirements are proven, production release-state evaluation must fail closed.
const DASHBOARD_RELEASE_STATE_OVERRIDES = new Map([
  ["school-administrator", RELEASE_STATES.DRAFT],
  ["release-reliability", RELEASE_STATES.DRAFT],
]);

export const PLACEHOLDER_TEXT_PATTERN =
  /(coming soon|placeholder|under construction|not ready|unavailable|future module|future release)/i;

export function normalizeReleaseState(value) {
  const normalized = String(value ?? "").trim().toLowerCase();

  if (!normalized) return "";

  if (normalized === "prod") return RELEASE_STATES.PRODUCTION;
  if (normalized === "coming-soon") return RELEASE_STATES.COMING_SOON;

  return normalized;
}

export function getReleaseState(routeLike = {}) {
  const key = String(routeLike.key || routeLike.moduleKey || "").trim();
  if (DASHBOARD_RELEASE_STATE_OVERRIDES.has(key)) {
    return DASHBOARD_RELEASE_STATE_OVERRIDES.get(key);
  }

  return normalizeReleaseState(
    routeLike.releaseState ||
      routeLike.release_status ||
      routeLike.status ||
      routeLike.routeStatus ||
      routeLike.readiness ||
      ""
  );
}

export function isProductionReady(routeLike = {}) {
  return READY_RELEASE_STATES.has(getReleaseState(routeLike));
}

export function isExplicitlyNonReady(routeLike = {}) {
  return NON_READY_RELEASE_STATES.has(getReleaseState(routeLike));
}

export function hasPlaceholderLikeText(routeLike = {}) {
  const text = [
    routeLike.label,
    routeLike.title,
    routeLike.name,
    routeLike.description,
    routeLike.subtitle,
    routeLike.href,
    routeLike.path,
  ]
    .filter(Boolean)
    .join(" ");

  return PLACEHOLDER_TEXT_PATTERN.test(text);
}

export function shouldHideFromProductionShell(routeLike = {}) {
  return !isProductionReady(routeLike);
}

export function getSafeFallbackPath(routeLike = {}) {
  return routeLike.fallbackPath || "/wizards";
}
