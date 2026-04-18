import { getUserRoles, normalizeRoles } from "./roleAccess";

function parseStorageValue(raw) {
  if (!raw) return null;

  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

export function getCurrentUserRoles() {
  if (typeof window === 'undefined') {
    return [];
  }

  const seededRoles = [
    sessionStorage.getItem('crown.role'),
    localStorage.getItem('crown.role'),
    localStorage.getItem('crown.demo.role'),
  ].filter(Boolean);
  const seededNormalized = getUserRoles(seededRoles);
  if (seededNormalized.length > 0) {
    return seededNormalized;
  }

  const windowRoles = getUserRoles(globalThis.__CROWN_USER_ROLES__);
  if (windowRoles.length > 0) {
    return windowRoles;
  }

  const directRoles = parseStorageValue(localStorage.getItem('crown_user_roles'));
  const directNormalized = getUserRoles(directRoles);
  if (directNormalized.length > 0) {
    return directNormalized;
  }

  const currentUser = parseStorageValue(localStorage.getItem('crown_current_user'));
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