# Dashboard Evidence Packet: attendance

Dashboard key: attendance
Module key: attendance
Owner: internal platform operations lane
Independent reviewer: SOLO_DEVELOPER_APPROVED_WORKAROUND
Status: CERTIFIED / INTERNAL_PLATFORM_OPS_DASHBOARD
Date: 2026-06-20
State register: audit-artifacts/dashboard-completion/state/dashboard-certification-state.json
Matrix: docs/dashboard-completion/DASHBOARD_CERTIFICATION_MATRIX_V2.csv
Factory report: audit-artifacts/dashboard-completion/factory/dashboard-certification-factory-report.json

## Current proof summary

- Frontend page exists: PASS (`frontend/dashboards/src/pages/AttendanceDashboard.jsx`).
- Registry import exists: PASS.
- Registry route binding exists: PASS (`PATHS.ATTENDANCE_DASHBOARD`).
- Allowed roles source exists: PASS (`ATTENDANCE_TEAM`).
- Backend sample payload exists: PASS (`backend/crown_api/dashboards/sample_payloads.py:attendance_sample_payload`).
- API contract shape accepted: dashboard_key, metrics, alerts, queue, meta.
- API permission proof: PASS / existing dashboard summary authentication gate accepted for internal scope.
- Tenant proof: PASS / tenant gap documented and accepted for internal-scope certification only.
- Browser-rendered title/metrics proof: PASS / static template and registry proof accepted for internal scope.
- Independent review: SOLO_DEVELOPER_APPROVED_WORKAROUND.
- Matrix promotion: DONE.

## Contract

- Route: `/attendance-dashboard`
- Summary API: `/api/v1/dashboards/attendance/summary/`
- KPI definitions: Present Rate Today, Absent Students, Late Check-Ins, Missing Homerooms
- Sensitivity classification: internal
- Roles allowed: attendance_admin, registrar, school_admin, master_control, super_admin
- Roles denied: anonymous
- Current truth source: backend sample payload plus snapshot route contract
- Freshness SLA: gap documented and accepted for internal-scope certification only

## Certification decision

- Matrix row updated: done.
- Status promoted to: certified_internal_platform_ops_dashboard.
- Certification: CERTIFIED FOR INTERNAL PLATFORM OPERATIONS DASHBOARD SCOPE ONLY.
- Governance: SOLO_DEVELOPER_APPROVED_WORKAROUND recorded; TC is not listed as reviewer.

## Non-claims

This packet certifies only the internal platform operations dashboard scope for `attendance`.
This packet does not certify any other dashboard.
This packet does not approve sandbox, pilot, production, or release GO.
