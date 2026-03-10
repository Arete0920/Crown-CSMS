import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { hasRouteAccess } from '../../config/dashboardRegistry';
import { getCurrentUserRoles } from '../../auth/roleAdapter';

export default function RoleRouteGuard({ allowedRoles, children }) {
  const location = useLocation();
  const userRoles = getCurrentUserRoles();

  if (hasRouteAccess(userRoles, allowedRoles)) {
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
