import { getUserRoles, normalizeRoles } from "./roleAccess";

function parseStorageValue(raw) {
  if (!raw) return null;

  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

function normalizeRoleArray(raw) {
  if (Array.isArray(raw)) {
    return raw.filter(Boolean).map((role) => String(role).trim());
  }

  if (typeof raw === 'string') {
    return raw
      .split(',')
      .map((role) => role.trim())
      .filter(Boolean);
  }

  return [];
}

export function getCurrentUserRoles() {
  if (typeof window === 'undefined') {
    return [];
  }

  // Support lightweight demo/e2e role seeding keys.
  const seededRoles = [
    sessionStorage.getItem('crown.role'),
    localStorage.getItem('crown.role'),
    localStorage.getItem('crown.demo.role'),
  ].filter(Boolean);
  const seededNormalized = getUserRoles(seededRoles);
  if (seededNormalized.length > 0) {
    return seededNormalized;
  }

  const windowRoles = getUserRoles(window.__CROWN_USER_ROLES__);
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
