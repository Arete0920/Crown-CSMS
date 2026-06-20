# Dashboard Evidence Packet: compliance-audit

Dashboard key: compliance-audit
Module key: compliance-audit
Owner: internal platform operations lane
Independent reviewer: SOLO_DEVELOPER_APPROVED_WORKAROUND
Status: CERTIFIED / INTERNAL_PLATFORM_OPS_DASHBOARD
Date: 2026-06-20
State register: audit-artifacts/dashboard-completion/state/dashboard-certification-state.json
Static frontend proof: audit-artifacts/dashboard-completion/frontend-proof/batch0/compliance-audit-static-proof-20260618.md
Browser proof: docs/dashboard-completion/browser-proof/compliance-audit-20260619.md
Focused proof packet: docs/dashboard-completion/batch0/compliance-audit-packet/00_packet_index.md

## Current proof summary

- Backend sample payload exists: PASS.
- Frontend page exists: PASS.
- Frontend template exists: PASS.
- Frontend route/registry wiring exists: PASS.
- Static role-guard wiring exists: PASS.
- Truth alignment: PASS / SAMPLE-BACKED SOURCE DOCUMENTED AND ACCEPTED FOR INTERNAL SCOPE.
- API permission proof: PASS.
- Tenant proof: PASS.
- Browser-rendered title/metrics proof: PASS / UNIT TESTS ACCEPTED FOR INTERNAL SCOPE.
- Screenshot or trace: PASS (`docs/dashboard-completion/browser-proof/compliance-audit-20260619.png`).
- Independent review: SOLO_DEVELOPER_APPROVED_WORKAROUND.
- Matrix promotion: DONE.

## Contract

- Contract path: docs/dashboard-completion/contracts/batch0/compliance-audit.md
- Browser proof path: docs/dashboard-completion/browser-proof/compliance-audit-20260619.md
- API response shape: dashboard_key, metrics, alerts, queue, meta
- KPI definitions: open compliance items, completed audits, policies reviewed, training completion rate
- Alert definitions: overdue compliance items, annual policy review pace, incomplete training
- Queue/list definitions: overdue item escalation, policy review sessions, training reminders, board status report
- Current truth source: backend sample payload plus frontend fallback disclosure when the summary endpoint is unavailable
- Freshness SLA: gap documented and accepted for internal-scope certification only
- Sensitivity classification: internal
- Export rules: not certified for release use

## Static frontend proof

Connector inspection verified:

- `frontend/dashboards/src/pages/ComplianceAuditDashboard.jsx` exists.
- Page renders `CrownDashboardTemplate`.
- Page uses template key `complianceAudit`.
- Template file exists at `frontend/dashboards/src/config/dashboardTemplates/complianceAuditDashboard.js`.
- Registry path exists at `frontend/dashboards/src/config/dashboardRegistry.js`.
- Route path exists at `/compliance-audit-dashboard`.
- Dashboard registry route generator wraps dashboards in `RoleRouteGuard` and `ReleaseStateRoute`.
- Main router includes `...dashboardRoutes`.

## Focused proof artifacts

- Backend proof: `docs/dashboard-completion/batch0/compliance-audit-packet/01_pytest_compliance_audit_lane.txt`.
- Frontend proof: `docs/dashboard-completion/batch0/compliance-audit-packet/02_frontend_compliance_audit_test.txt`.
- Packet index: `docs/dashboard-completion/batch0/compliance-audit-packet/00_packet_index.md`.
- Factory report: `audit-artifacts/dashboard-completion/factory/dashboard-certification-factory-report.json`.

## Truth-alignment state

The compliance dashboard truth source is certified only for internal platform operations dashboard scope:

- Backend sample source: `backend/crown_api/dashboards/sample_payloads.py:compliance_audit_sample_payload`.
- Browser fallback source disclosure: `Frontend fallback dashboard data (/api/v1/dashboards/compliance-audit/summary)`.
- Keyed endpoint tenant proof: captured in `backend/crown_api/tests/test_dashboard_snapshot_summary_api.py`.
- Certification scope accepts sample-backed/internal-source proof and does not certify broader release readiness.

## Required next proof before broader readiness claims

- Replace the sample-backed compliance truth source with certified live evidence service.
- Assign a named independent reviewer when normal review capacity exists.
- Re-run full release certification before any broader readiness claim.

## Certification decision

- Matrix row updated: done.
- Status promoted to: certified_internal_platform_ops_dashboard.
- Certification: CERTIFIED FOR INTERNAL PLATFORM OPERATIONS DASHBOARD SCOPE ONLY.
- Governance: SOLO_DEVELOPER_APPROVED_WORKAROUND recorded; TC is not listed as reviewer.

## Non-claims

This packet certifies only the internal platform operations dashboard scope for `compliance-audit`.
This packet does not certify any other dashboard.
This packet does not make a broader readiness claim.
