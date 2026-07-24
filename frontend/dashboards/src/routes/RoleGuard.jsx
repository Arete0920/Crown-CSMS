import { Navigate, useLocation } from 'react-router';
import { PATHS } from './paths';
import { useCurrentUserRole } from '../hooks/useCurrentUserRole';
import { isRoleAllowed } from './roleGuardRules';

/**
 * UX-only route guard.
 *
 * This component prevents obvious navigation mistakes in the browser, but it is
 * not an authorization boundary. Protected backend API endpoints must enforce
 * tenant, role, and permission checks server-side.
 */
export default function RoleGuard({ allowedRoles = [], children }) {
  const role = useCurrentUserRole();
  const location = useLocation();

  if (!isRoleAllowed(role, allowedRoles)) {
    return (
      <Navigate
        to={PATHS.FORBIDDEN}
        replace
        state={{
          from: location.pathname,
          role,
          allowedRoles: allowedRoles.map((value) => String(value).trim().toLowerCase()),
        }}
      />
    );
  }

  return children;
}
