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

  const windowRoles = normalizeRoleArray(window.__CROWN_USER_ROLES__);
  if (windowRoles.length > 0) {
    return [...new Set(windowRoles)];
  }

  const directRoles = parseStorageValue(localStorage.getItem('crown_user_roles'));
  const directNormalized = normalizeRoleArray(directRoles);
  if (directNormalized.length > 0) {
    return [...new Set(directNormalized)];
  }

  const currentUser = parseStorageValue(localStorage.getItem('crown_current_user'));
  if (currentUser && Array.isArray(currentUser.roles)) {
    return [...new Set(normalizeRoleArray(currentUser.roles))];
  }

  return [];
}
