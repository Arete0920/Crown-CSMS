import { Navigate, useLocation } from 'react-router';
import { usePermissions } from '../../hooks/usePermissions';
import { PATHS } from '../../routes/paths';

export default function RequirePermission({ permission, anyOf = [], children }) {
  const { hasPermission, hasAnyPermission } = usePermissions();
  const location = useLocation();

  const allowed =
    permission ? hasPermission(permission) : anyOf.length ? hasAnyPermission(anyOf) : true;

  if (!allowed) {
    return (
      <Navigate
        to={PATHS.FORBIDDEN}
        replace
        state={{
          from: location.pathname,
          permission,
          anyOf,
        }}
      />
    );
  }

  return children;
}
