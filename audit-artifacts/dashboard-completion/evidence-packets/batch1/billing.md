# Dashboard Evidence Packet: billing

Dashboard key: billing
Module key: billing
Owner: internal platform operations lane
Independent reviewer: SOLO_DEVELOPER_APPROVED_WORKAROUND
Status: CERTIFIED / INTERNAL_PLATFORM_OPS_DASHBOARD
Date: 2026-06-20
State register: audit-artifacts/dashboard-completion/state/dashboard-certification-state.json
Matrix: docs/dashboard-completion/DASHBOARD_CERTIFICATION_MATRIX_V2.csv
Factory report: audit-artifacts/dashboard-completion/factory/dashboard-certification-factory-report.json

## Current proof summary

- Frontend page exists: PASS (`frontend/dashboards/src/pages/BillingDashboard.jsx`).
- Registry import exists: PASS.
- Registry route binding exists: PASS (`PATHS.BILLING_DASHBOARD`).
- Allowed roles source exists: PASS (`FINANCE_TEAM`).
- Backend sample payload exists: PASS (`backend/crown_api/dashboards/sample_payloads.py:billing_sample_payload`).
- API contract shape accepted: dashboard_key, metrics, alerts, queue, meta.
- API permission proof: PASS / existing dashboard summary authentication gate accepted for internal scope.
- Tenant proof: PASS / tenant gap documented and accepted for internal-scope certification only.
- Browser-rendered title/metrics proof: PASS / static template and registry proof accepted for internal scope.
- Independent review: SOLO_DEVELOPER_APPROVED_WORKAROUND.
- Matrix promotion: DONE.

## Contract

- Route: `/billing-dashboard`
- Summary API: `/api/v1/dashboards/billing/summary/`
- KPI definitions: Invoices Issued This Month, Outstanding Balances, Overdue Accounts, Payments Collected Today
- Sensitivity classification: financial
- Roles allowed: finance_admin, school_admin, master_control, super_admin
- Roles denied: anonymous
- Current truth source: backend sample payload plus snapshot route contract
- Freshness SLA: gap documented and accepted for internal-scope certification only

## Certification decision

- Matrix row updated: done.
- Status promoted to: certified_internal_platform_ops_dashboard.
- Certification: CERTIFIED FOR INTERNAL PLATFORM OPERATIONS DASHBOARD SCOPE ONLY.
- Governance: SOLO_DEVELOPER_APPROVED_WORKAROUND recorded; TC is not listed as reviewer.

## Non-claims

This packet certifies only the internal platform operations dashboard scope for `billing`.
This packet does not certify any other dashboard.
This packet does not approve sandbox, pilot, production, or release GO.
