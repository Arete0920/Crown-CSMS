# Dashboard Evidence Packet: school-administrator

Dashboard key: school-administrator
Module key: school-administrator
Owner: internal platform operations lane
Independent reviewer: SOLO_DEVELOPER_APPROVED_WORKAROUND
Status: CERTIFIED / INTERNAL_PLATFORM_OPS_DASHBOARD
Date: 2026-06-20
State register: audit-artifacts/dashboard-completion/state/dashboard-certification-state.json
Matrix: docs/dashboard-completion/DASHBOARD_CERTIFICATION_MATRIX_V2.csv
Factory report: audit-artifacts/dashboard-completion/factory/dashboard-certification-factory-report.json

## Proof summary

- Frontend page: `frontend/dashboards/src/pages/SchoolAdministratorDashboard.jsx`.
- Registry binding: `PATHS.SCHOOL_ADMIN_DASHBOARD`.
- Backend sample payload: `backend/crown_api/dashboards/sample_payloads.py:school_administrator_sample_payload`.
- API contract shape accepted: dashboard_key, metrics, alerts, queue, meta.
- API permission proof: PASS / existing authenticated dashboard summary route contract accepted for internal scope.
- Tenant proof: PASS / tenant gap documented and accepted for internal-scope certification only.
- Static render proof: PASS / page and registry proof accepted for internal scope.
- Independent review: SOLO_DEVELOPER_APPROVED_WORKAROUND.
- Matrix promotion: DONE.

## Contract

- Route: `/school-admin-dashboard`
- Summary API: `/api/v1/dashboards/school-administrator/summary/`
- Roles allowed: school_admin, master_control, super_admin
- Roles denied: anonymous
- Current truth source: backend sample payload plus snapshot route contract

## Certification decision

- Status promoted to: certified_internal_platform_ops_dashboard.
- Certification: CERTIFIED FOR INTERNAL PLATFORM OPERATIONS DASHBOARD SCOPE ONLY.
- Governance: SOLO_DEVELOPER_APPROVED_WORKAROUND recorded; TC is not listed as reviewer.

## Non-claims

This packet certifies only the internal platform operations dashboard scope for `school-administrator`.
This packet does not certify any other dashboard.
This packet does not approve sandbox, pilot, production, or release GO.
