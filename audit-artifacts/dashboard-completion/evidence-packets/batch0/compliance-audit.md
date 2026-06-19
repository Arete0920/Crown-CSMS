# Dashboard Evidence Packet: compliance-audit

Dashboard key: compliance-audit
Module key: compliance-audit
Owner: TBD
Independent reviewer: TBD
Status: MAPPED / STATIC_FRONTEND_PROOF / SAMPLE_TRUTH_SOURCE_DOCUMENTED / API_AND_TENANT_PROOF_CAPTURED / BROWSER_PROOF_CAPTURED / CERTIFICATION_BLOCKED
Date: 2026-06-19
State register: audit-artifacts/dashboard-completion/state/dashboard-certification-state.json
Static frontend proof: audit-artifacts/dashboard-completion/frontend-proof/batch0/compliance-audit-static-proof-20260618.md
Browser proof: docs/dashboard-completion/browser-proof/compliance-audit-20260619.md

## Current proof summary

- Backend sample payload exists: PASS.
- Frontend page exists: PASS.
- Frontend template exists: PASS.
- Frontend route/registry wiring exists: PASS.
- Static role-guard wiring exists: PASS.
- Truth alignment: SAMPLE-BACKED SOURCE DOCUMENTED / LIVE SOURCE NOT VERIFIED.
- API permission proof: PASS.
- Tenant proof: PASS.
- Browser-rendered title/metrics proof: PASS.
- Screenshot or trace: PASS (`docs/dashboard-completion/browser-proof/compliance-audit-20260619.png`).
- Independent review: PENDING.
- Matrix promotion: NOT DONE.

## Contract

- Contract path: docs/dashboard-completion/contracts/batch0/compliance-audit.md
- Browser proof path: docs/dashboard-completion/browser-proof/compliance-audit-20260619.md
- API response shape: dashboard_key, metrics, alerts, queue, meta
- KPI definitions: open compliance items, completed audits, policies reviewed, training completion rate
- Alert definitions: overdue compliance items, annual policy review pace, incomplete training
- Queue/list definitions: overdue item escalation, policy review sessions, training reminders, board status report
- Current truth source: backend sample payload plus frontend fallback disclosure when the summary endpoint is unavailable
- Freshness SLA: not yet proven
- Sensitivity classification: internal
- Export rules: not yet proven

## Static frontend proof

Connector inspection verified:

- `frontend/dashboards/src/pages/ComplianceAuditDashboard.jsx` exists.
- Page renders `CrownDashboardTemplate`.
- Page uses template key `complianceAudit`.
- Template file exists at `frontend/dashboards/src/config/dashboardTemplates/complianceAuditDashboard.js`.
- Registry path exists at `frontend/dashboards/src/config/dashboardRegistry.js`.
- Route path resolves to `/compliance-audit-dashboard`.
- Dashboard registry route generator wraps dashboards in `RoleRouteGuard` and `ReleaseStateRoute`.
- Main router includes `...dashboardRoutes`.

## Truth-alignment state

The current compliance dashboard truth source is documented but not live-certified:

- Backend sample source: `backend/crown_api/dashboards/sample_payloads.py:compliance_audit_sample_payload`
- Browser fallback source: `Frontend fallback dashboard data (/api/v1/dashboards/compliance-audit/summary)`
- Keyed endpoint tenant proof: captured in `backend/crown_api/tests/test_dashboard_snapshot_summary_api.py`

This closes the proof gap for truth-source disclosure, API permission behavior, tenant enforcement, and browser-rendered title/metrics capture without promoting the dashboard to certified/live status.

## Required next proof

- Replace the sample-backed compliance truth source with certified live evidence service.
- Assign valid owner and independent reviewer.
- Complete independent review.
- Promote matrix only after proof is complete.

## Certification decision

- Matrix row updated: not yet.
- Status promoted to: not yet.
- Certification: NOT CERTIFIED.

## Non-claims

This packet does not certify the dashboard.
This packet does not approve sandbox, pilot, production, or release GO.
