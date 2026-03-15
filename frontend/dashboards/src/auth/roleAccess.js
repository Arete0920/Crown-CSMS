export const ROLE_EQUIVALENCE_GROUPS = [
  ["super_admin"],
  ["head_of_school", "school_admin"],
  ["finance", "finance_admin", "finance_director"],
  ["admissions", "admissions_manager"],
  ["registrar"],
  ["advancement", "advancement_officer"],
  ["facilities", "facilities_manager"],
  ["it", "it_support"],
  ["safety", "safety_manager"],
  ["security", "security_officer"],
  ["hr", "hr_manager"],
  ["transportation", "transportation_manager"],
  ["food_service", "food_service_manager"],
  ["athletic_director", "athletics_director"],
  ["health", "health_office"],
  ["board", "board_member"],
  ["office_manager", "office"],
  ["academic_admin", "academics"],
  ["teacher"],
  ["parent"],
  ["student"],
];

export const ROLE_ALIAS_LOOKUP = ROLE_EQUIVALENCE_GROUPS.reduce((lookup, group) => {
  group.forEach((role) => {
    lookup[role] = group;
  });
  return lookup;
}, {});

function asToken(value) {
  return String(value ?? "").trim().toLowerCase();
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function extractArrayRoles(value) {
  if (!Array.isArray(value)) return [];
  return value.flatMap((entry) => {
    if (typeof entry === "string") return [entry];
    if (entry && typeof entry === "object") {
      return [entry.code, entry.role, entry.name, entry.slug, entry.value].filter(Boolean);
    }
    return [];
  });
}

export function normalizeRoles(input) {
  const raw = [];

  if (Array.isArray(input)) {
    raw.push(...input);
  } else if (typeof input === "string") {
    raw.push(input);
  } else if (input && typeof input === "object") {
    raw.push(
      input.role,
      input.primaryRole,
      input.role_code,
      input.roleCode,
      input.code,
      input.name,
      ...extractArrayRoles(input.roles),
      ...extractArrayRoles(input.userRoles),
      ...extractArrayRoles(input.groups),
      ...extractArrayRoles(input.memberships),
    );
  }

  const expanded = [];

  raw.forEach((value) => {
    const token = asToken(value);
    if (!token) return;

    expanded.push(token);

    const aliases = ROLE_ALIAS_LOOKUP[token] || [];
    aliases.forEach((alias) => expanded.push(alias));
  });

  return unique(expanded);
}

export function getUserRoles(userLike) {
  if (!userLike) return [];

  const direct = normalizeRoles(userLike);
  if (direct.length) return direct;

  if (userLike.user) {
    const nestedUser = normalizeRoles(userLike.user);
    if (nestedUser.length) return nestedUser;
  }

  if (userLike.profile) {
    const nestedProfile = normalizeRoles(userLike.profile);
    if (nestedProfile.length) return nestedProfile;
  }

  if (userLike.data) {
    const nestedData = normalizeRoles(userLike.data);
    if (nestedData.length) return nestedData;
  }

  return [];
}

export function hasAnyRole(userLike, allowedRoles = []) {
  const effectiveUserRoles = getUserRoles(userLike);
  const effectiveAllowedRoles = normalizeRoles(allowedRoles);

  if (effectiveAllowedRoles.length === 0) return true;
  if (effectiveUserRoles.length === 0) return false;

  return effectiveAllowedRoles.some((role) => effectiveUserRoles.includes(role));
}

export function hasAllRoles(userLike, requiredRoles = []) {
  const effectiveUserRoles = getUserRoles(userLike);
  const effectiveRequiredRoles = normalizeRoles(requiredRoles);

  if (effectiveRequiredRoles.length === 0) return true;
  if (effectiveUserRoles.length === 0) return false;

  return effectiveRequiredRoles.every((role) => effectiveUserRoles.includes(role));
}

export function isAccessAllowed(userLike, accessConfig = {}) {
  const allowedRoles = accessConfig.roles || accessConfig.allowedRoles || [];
  const requiredPermissions = accessConfig.permissions || [];

  const roleAllowed = hasAnyRole(userLike, allowedRoles);

  if (!Array.isArray(requiredPermissions) || requiredPermissions.length === 0) {
    return roleAllowed;
  }

  const permissionSet = Array.isArray(userLike?.permissions)
    ? new Set(userLike.permissions.map((value) => String(value).trim()))
    : null;

  if (!permissionSet) {
    return roleAllowed;
  }

  if (permissionSet.has('*')) {
    return true;
  }

  return requiredPermissions.some((permission) => permissionSet.has(permission));
}

export function filterVisibleNav(items = [], userLike) {
  return items.reduce((acc, item) => {
    const children = Array.isArray(item.children)
      ? filterVisibleNav(item.children, userLike)
      : [];

    const hasDirectAccess = isAccessAllowed(userLike, item);
    const hasVisibleChildren = children.length > 0;
    const hasExplicitAccessRule =
      Array.isArray(item.roles) || Array.isArray(item.allowedRoles) || Array.isArray(item.permissions);

    if (hasDirectAccess || hasVisibleChildren || !hasExplicitAccessRule) {
      acc.push({
        ...item,
        ...(Array.isArray(item.children) ? { children } : {}),
      });
    }

    return acc;
  }, []);
}
