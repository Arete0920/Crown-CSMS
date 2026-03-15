export function isRoleAllowed(role, allowedRoles = []) {
  const normalizedAllowed = allowedRoles.map((value) => String(value).trim().toLowerCase());

  if (!normalizedAllowed.length) {
    return true;
  }

  return normalizedAllowed.includes(String(role || 'guest').trim().toLowerCase());
}
