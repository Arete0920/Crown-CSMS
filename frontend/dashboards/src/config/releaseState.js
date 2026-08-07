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
