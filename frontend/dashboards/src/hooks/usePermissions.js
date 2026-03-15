import { useMemo } from 'react';
import {
  resolvePermissions,
  userHasAnyPermission,
  userHasPermission,
} from '../auth/permissions';

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

export function usePermissions() {
  const user = useMemo(() => readCurrentUser(), []);

  return {
    user,
    permissions: resolvePermissions(user),
    hasPermission: (permission) => userHasPermission(user, permission),
    hasAnyPermission: (needed) => userHasAnyPermission(user, needed),
  };
}
