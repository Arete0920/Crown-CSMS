# dashboard-certification-center - Route and Component Reference

Status: collected
Date: 2026-06-19

## Route reference

- Frontend path constant: frontend/dashboards/src/routes/paths.js:148
  - DASHBOARD_CERTIFICATION_CENTER = /dashboard-certification-center
- Dashboard registry route entry: frontend/dashboards/src/config/dashboardRegistry.js:525
  - key: dashboard-certification-center
  - path: PATHS.DASHBOARD_CERTIFICATION_CENTER
  - component: DashboardCertificationCenter

## Component reference

- Component import: frontend/dashboards/src/config/dashboardRegistry.js:58
  - import DashboardCertificationCenter from ../pages/DashboardCertificationCenter
- Page component: frontend/dashboards/src/pages/DashboardCertificationCenter.jsx:4
  - renders CrownDashboardTemplate with dashboardCertificationCenter template key

## Guardrail note

- Current branch still marks this route ready in registry: frontend/dashboards/src/config/dashboardRegistry.js:534
- Separate lane PR #1115 already patched false-ready state to draft. This packet records current branch evidence only.
