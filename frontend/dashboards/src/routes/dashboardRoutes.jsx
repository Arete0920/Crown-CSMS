import React from 'react';
import { DASHBOARD_REGISTRY } from '../config/dashboardRegistry';
import RoleRouteGuard from '../components/routing/RoleRouteGuard';
import ReleaseStateRoute from '../components/routing/ReleaseStateRoute';

export const dashboardRoutes = DASHBOARD_REGISTRY.map((dashboard) => {
  const Component = dashboard.component;

  return {
    path: dashboard.path,
    element: (
      <RoleRouteGuard allowedRoles={dashboard.roles || dashboard.allowedRoles || []}>
        <ReleaseStateRoute route={dashboard}>
          <Component />
        </ReleaseStateRoute>
      </RoleRouteGuard>
    ),
  };
});
