import { DASHBOARD_REGISTRY } from '../config/dashboardRegistry';
import RoleRouteGuard from '../components/routing/RoleRouteGuard';
import ReleaseStateRoute from '../components/routing/ReleaseStateRoute';

const IS_SANDBOX = Boolean(
  String(import.meta.env.VITE_DEMO_MODE || '').toLowerCase() === 'sandbox'
  || String(import.meta.env.VITE_SANDBOX_MODE || '') === '1'
);

export const dashboardRoutes = DASHBOARD_REGISTRY.map((dashboard) => {
  const Component = dashboard.component;
  const dashboardElement = <Component />;

  return {
    path: dashboard.path,
    element: (
      <RoleRouteGuard allowedRoles={dashboard.roles || dashboard.allowedRoles || []}>
        {IS_SANDBOX ? (
          dashboardElement
        ) : (
          <ReleaseStateRoute route={dashboard}>
            {dashboardElement}
          </ReleaseStateRoute>
        )}
      </RoleRouteGuard>
    ),
  };
});
