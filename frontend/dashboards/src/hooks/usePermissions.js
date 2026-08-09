import { useMemo } from 'react';
import {
  resolvePermissions,
  userHasAnyPermission,
  userHasPermission,
} from '../auth/permissions';
import { getCurrentUserRoles } from '../auth/roleAdapter';

function readCurrentUser() {
  try {
    const raw =
      window.localStorage.getItem('crown_user') ||
      window.localStorage.getItem('crown_current_user') ||
      window.sessionStorage.getItem('crown_user');

    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function mergePermissionIdentity(storedUser, seededRoles = []) {
  if (!Array.isArray(seededRoles) || seededRoles.length === 0) {
    return storedUser;
  }

  return {
    ...(storedUser || {}),
    roles: seededRoles,
  };
}

export function usePermissions() {
  const user = useMemo(
    () => mergePermissionIdentity(readCurrentUser(), getCurrentUserRoles()),
    [],
  );

  return {
    user,
    permissions: resolvePermissions(user),
    hasPermission: (permission) => userHasPermission(user, permission),
    hasAnyPermission: (needed) => userHasAnyPermission(user, needed),
  };
}
