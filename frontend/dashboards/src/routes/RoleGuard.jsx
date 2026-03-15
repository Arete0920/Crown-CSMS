import { Navigate, useLocation } from 'react-router-dom';
import { PATHS } from './paths';
import { useCurrentUserRole } from '../hooks/useCurrentUserRole';
import { isRoleAllowed } from './roleGuardRules';

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
