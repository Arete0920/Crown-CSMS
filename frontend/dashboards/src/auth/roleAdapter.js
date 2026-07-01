import { getUserRoles, normalizeRoles } from "./roleAccess";

function parseStorageValue(raw) {
  if (!raw) return null;

  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

function readStorageValue(key) {
  if (typeof window === "undefined") return null;

  const sessionValue = parseStorageValue(sessionStorage.getItem(key));
  if (sessionValue) return sessionValue;

  return parseStorageValue(localStorage.getItem(key));
}

function collectSeededRoleValues() {
  if (typeof window === "undefined") return [];

  return [
    sessionStorage.getItem("crown.role"),
    sessionStorage.getItem("crown.active.role"),
    localStorage.getItem("crown.role"),
    localStorage.getItem("crown.active.role"),
    localStorage.getItem("crown.demo.role"),
  ].filter(Boolean);
}

export function getCurrentUserRoles() {
  if (typeof window === "undefined") {
    return [];
  }

  const seededNormalized = getUserRoles(collectSeededRoleValues());
  if (seededNormalized.length > 0) {
    return seededNormalized;
  }

  const windowRoles = getUserRoles(globalThis.__CROWN_USER_ROLES__);
  if (windowRoles.length > 0) {
    return windowRoles;
  }

  const directRoles = readStorageValue("crown_user_roles");
  const directNormalized = getUserRoles(directRoles);
  if (directNormalized.length > 0) {
    return directNormalized;
  }

  const currentUser = readStorageValue("crown_current_user") ?? readStorageValue("crown_user");
  const currentUserRoles = getUserRoles(currentUser);
  if (currentUserRoles.length > 0) {
    return currentUserRoles;
  }

  return [];
}

export function getEffectiveRoles(authPayload) {
  return getUserRoles(authPayload);
}

export function getPrimaryRole(authPayload) {
  const roles = getEffectiveRoles(authPayload);
  return roles[0] || null;
}

export function normalizeAllowedRoles(roles) {
  return normalizeRoles(roles);
}
