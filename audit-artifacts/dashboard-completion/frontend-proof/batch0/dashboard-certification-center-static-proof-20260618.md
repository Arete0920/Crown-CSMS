# Static Frontend Proof: dashboard-certification-center

Date: 2026-06-18
Dashboard key: dashboard-certification-center
Issue: #1109
Evidence status: STATIC FRONTEND PROOF / NOT CERTIFIED

## Scope

This proof packet records connector-verifiable static frontend wiring for the Dashboard Certification Center.

It does not replace browser-rendered runtime proof or screenshot/trace evidence.

## Verified repository facts

### Page component exists

Path: `frontend/dashboards/src/pages/DashboardCertificationCenter.jsx`

Observed content:

```jsx
import CrownDashboardTemplate from '../components/crown-dashboard/CrownDashboardTemplate.jsx';
import { getDashboardTemplate } from '../config/dashboardTemplates/index.js';

export default function DashboardCertificationCenter() {
  const config = getDashboardTemplate('dashboardCertificationCenter');
  return <CrownDashboardTemplate config={config} roleKey="dashboardCertificationCenter" />;
}
```

Interpretation:

- The route target is a real React page component.
- The page renders through the shared `CrownDashboardTemplate` shell.
- The page uses template key `dashboardCertificationCenter`.
- The page passes role key `dashboardCertificationCenter`.

### Template exists and exposes truthful baseline values

Path: `frontend/dashboards/src/config/dashboardTemplates/dashboardCertificationCenterDashboard.js`

Observed static values:

- `key: 'dashboardCertificationCenter'`
- `activePath: '/dashboard-certification-center'`
- `apiEndpoint: '/api/v1/dashboards/dashboard-certification-center/summary'`
- `liveDataKey: 'dashboardCertificationCenter'`
- Metric: `Dashboards Certified = 0`
- Metric: `Mapped Only = 40`
- Metric: `Pending Review = 0`
- Metric: `Cert Rate = 0%`
- Alert: `No dashboards are certified yet`
- Alert: `Owner and independent reviewer are still TBD`

Interpretation:

- Static template does not overclaim certification.
- Static template aligns with the current verified 0/40 certification posture.
- Static template references the intended summary API endpoint.

### Data registry entry exists

Path: `frontend/dashboards/src/config/dashboardDataRegistry.js`

Observed static entry:

```js
'dashboard-certification-center': createDataConfig(dashboardSummaryPath('dashboard-certification-center'), {
  allowScaffoldFallback: true,
  fallbackData: {
    dashboard_key: 'dashboard-certification-center',
    metrics: [
      { label: 'Dashboards Certified', value: '0' },
      { label: 'Mapped Only', value: '40' },
      { label: 'Pending Independent Review', value: '0' },
      { label: 'Cert Rate', value: '0%' },
    ],
    alerts: [
      {
        title: 'No dashboards are certified yet',
        level: 'High',
        secondary: 'Current verified state remains 40 mapped dashboards and 0 live-data certified dashboards.',
      },
      {
        title: 'Owner and independent reviewer are still TBD',
        level: 'High',
        secondary: 'Assign governance roles before certification promotion.',
      },
    ],
    queue: [
      'Assign dashboard certification owner',
      'Assign independent dashboard certification reviewer',
      'Wire certification proof state from the dashboard matrix',
      'Attach permission, tenant, and runtime proof',
    ],
    meta: {
      certification_candidate: 'hybrid',
      fallback_source: 'frontend_scaffold',
    },
  },
}),
```

Interpretation:

- The frontend data registry points the dashboard to `/api/v1/dashboards/dashboard-certification-center/summary` through `dashboardSummaryPath`.
- Fallback data does not certify dashboards.
- Fallback data marks itself as frontend scaffold.

### Dashboard registry entry exists

Path: `frontend/dashboards/src/config/dashboardRegistry.js`

Observed static entry:

```js
createDashboard({
  key: 'dashboard-certification-center',
  label: 'Dashboard Certification Center',
  path: PATHS.DASHBOARD_CERTIFICATION_CENTER,
  tier: 7,
  section: 'Platform Operations',
  allowedRoles: PLATFORM_CERT_TEAM,
  component: DashboardCertificationCenter,
})
```

Observed role group:

```js
const PLATFORM_CERT_TEAM = [...new Set([...RELEASE_TEAM, ...COMPLIANCE_TEAM, ...MASTER_CONTROL])];
```

Observed access helper:

```js
export function hasRouteAccess(userRoles, allowedRoles) {
  const normalizedUserRoles = normalizeEffectiveRoles(userRoles);
  const normalizedAllowedRoles = normalizeEffectiveRoles(allowedRoles);

  if (normalizedUserRoles.includes('super_admin')) {
    return true;
  }

  return normalizedAllowedRoles.some((role) => normalizedUserRoles.includes(role));
}
```

Interpretation:

- The dashboard is registered in the central dashboard registry.
- Its browser route is role-limited to platform certification / release / compliance / master-control roles.
- `super_admin` has explicit route access bypass.

### Route path exists

Path: `frontend/dashboards/src/routes/paths.js`

Observed static value:

```js
DASHBOARD_CERTIFICATION_CENTER: '/dashboard-certification-center'
```

Interpretation:

- The canonical frontend route path exists.

### Dashboard registry routes are spread into router

Path: `frontend/dashboards/src/routes/dashboardRoutes.jsx`

Observed static content:

```jsx
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
```

Path: `frontend/dashboards/src/routes/router.jsx`

Observed static content:

```jsx
...dashboardRoutes,
```

Interpretation:

- The dashboard registry is transformed into routed pages.
- The dashboard registry routes are included in the browser router.
- The certification center dashboard route is protected by `RoleRouteGuard` using the dashboard's registered allowed roles.

## Static frontend proof result

- Page component exists: PASS.
- Template key exists: PASS.
- Static metrics do not overclaim certification: PASS.
- API endpoint is configured: PASS.
- Data registry entry exists: PASS.
- Dashboard registry entry exists: PASS.
- Canonical route path exists: PASS.
- Dashboard registry routes are included in router: PASS.
- Static role guard wiring exists: PASS.

## Not proven by this packet

- Browser rendered title visible.
- Browser rendered metrics visible.
- Browser values match live API response at runtime.
- Staff browser session can access route.
- Non-staff browser session is blocked.
- Screenshot or trace artifact exists.
- Independent reviewer has approved evidence.

## Certification impact

This advances frontend static wiring proof only.

It does not certify the dashboard.
It does not approve sandbox, pilot, production, or release GO.
