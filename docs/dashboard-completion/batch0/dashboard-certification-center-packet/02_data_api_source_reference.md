# dashboard-certification-center - Data/API/Source Reference

Status: collected
Date: 2026-06-19

## Frontend data source wiring

- Data registry entry: frontend/dashboards/src/config/dashboardDataRegistry.js:184
  - createDataConfig(dashboardSummaryPath('dashboard-certification-center'))
- Fallback payload source: frontend/dashboards/src/config/dashboardDataRegistry.js:187
  - dashboard_key = dashboard-certification-center
- Template API endpoint reference: frontend/dashboards/src/config/dashboardTemplates/dashboardCertificationCenterDashboard.js:25
  - /api/v1/dashboards/dashboard-certification-center/summary

## Backend API route

- Dashboard summary slug route: backend/crown_api/dashboards/urls.py:20
  - <slug:dashboard_key>/summary -> DashboardSummaryView (name: dashboard-summary)
- Dashboards URL include under api/v1: backend/crown_api/urls.py:76
  - api/v1/dashboards/ include crown_api.dashboards.urls

## Source note

- Served payload mode for this endpoint is validated in tests as sample under development override.
