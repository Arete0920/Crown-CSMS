import { Navigate, useLocation } from 'react-router';
import { getCurrentUserRoles } from '../../auth/roleAdapter';
import { hasAnyRole } from '../../auth/roleAccess';

export default function RoleRouteGuard({ allowedRoles, children }) {
  const location = useLocation();
  const userRoles = getCurrentUserRoles();
  const allowed = hasAnyRole(userRoles, allowedRoles);

  if (allowed) {
    return children;
  }

  return (
    <Navigate
      to="/not-authorized"
      replace
      state={{ from: location.pathname }}
    />
  );
}
