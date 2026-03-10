import React from 'react';
import { DASHBOARD_REGISTRY } from '../config/dashboardRegistry';
import RoleRouteGuard from '../components/routing/RoleRouteGuard';

export const dashboardRoutes = DASHBOARD_REGISTRY.map((dashboard) => {
  const Component = dashboard.component;

  return {
    path: dashboard.path,
    element: (
      <RoleRouteGuard allowedRoles={dashboard.allowedRoles}>
        <Component />
      </RoleRouteGuard>
    ),
  };
});
