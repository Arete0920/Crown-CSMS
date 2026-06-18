# Dashboard Evidence Packet: compliance-audit

Dashboard key: compliance-audit
Module key: compliance-audit
Owner: TBD
Independent reviewer: TBD
Status: PROOF_IN_PROGRESS
Date: 2026-06-18
Branch: feat/dashboard-batch0-control-services-20260618
Commit SHA: 2ebc116c

## 1. Contract

- Contract path: docs/dashboard-completion/contracts/batch0/compliance-audit.md
- KPI definitions: active audits, controls passing, open findings, reviews due in 30 days
- Alert definitions: evidence package due date, remediation plans needed
- Queue/table/list definitions: audit tracker, finding register, evidence vault, control matrix
- Drilldown definitions: contract draft only; no runtime drilldown proof captured yet
- served_from rules: sample fallback allowed in non-production; backend sample payload returns served_from=sample
- Freshness SLA: not yet proven
- Sensitivity classification: internal
- Redaction rules: not yet proven
- Export rules: not yet proven

## 2. Backend proof

- Summary service path: backend/crown_api/dashboards/sample_payloads.py::compliance_audit_sample_payload
- API route: /api/dashboards/compliance-audit/summary (reverse('dashboard-summary', kwargs={'dashboard_key': 'compliance-audit'}))
- Serializer/schema: backend/crown_api/dashboards/payload_contract.py::build_dashboard_payload
- Permission class/path: backend/crown_api/dashboards/views.py::DashboardSummaryView (IsAuthenticated)
- Tenant enforcement path: backend/crown_api/dashboards/views.py::`_school_id_from_request` and `_resolve_school_strict`
- Entitlement check path: not separately implemented for this dashboard in the current proof slice
- Audit event path: not yet proven
- Backend test path: backend/crown_api/tests/test_dashboard_snapshot_summary_api.py
- Backend test command: python -m pytest crown_api\tests\test_dashboard_snapshot_summary_api.py
- Backend test result: PASS (8 passed)

## 3. Frontend proof

- Dashboard page path: frontend/dashboards/src/pages/ComplianceAuditDashboard.jsx
- API client/hook path: frontend/dashboards/src/hooks/useDashboardData.js
- KPI component path: frontend/dashboards/src/components/crown-dashboard/CrownDashboardTemplate.jsx
- Alert/status component path: frontend/dashboards/src/components/crown-dashboard/CrownDashboardTemplate.jsx
- Queue/table component path: frontend/dashboards/src/components/crown-dashboard/CrownDashboardTemplate.jsx
- Empty state proof: not yet captured for this dashboard
- Error state proof: not yet captured for this dashboard
- Forbidden state proof: not yet captured for this dashboard
- Frontend test path: frontend/dashboards/src/components/crown-dashboard/CrownDashboardTemplate.test.jsx; frontend/dashboards/src/tests/apiContractRegistry.test.js
- Frontend test command: npm run lint; npm run test:contracts; npm run verify:dashboard-completeness
- Frontend test result: PASS (lint: 0 errors, 2 warnings; test:contracts: 9 passed; verify:dashboard-completeness: PASS)

## 4. Runtime proof

- Environment: local backend test runtime (pytest)
- URL: /api/dashboards/compliance-audit/summary
- User role tested: not yet captured
- Tenant tested: role-contract and tenant-isolation suites executed for dashboard APIs (non-keyed summary endpoints)
- Playwright test path: not yet captured
- Playwright command: not yet captured
- Screenshot/trace path: not yet captured
- Result: backend runtime proof captured via automated tests; browser runtime proof pending

## 5. Security proof

- Unauthenticated denied: PASS for dashboard summary APIs in backend/crown_api/tests/test_dashboards_role_contract.py::test_unauthenticated_returns_401
- Unauthorized role denied: PARTIAL (covered for cross-tenant dashboard summary contract endpoints; keyed batch0 endpoint-specific role denial not yet captured)
- Authorized role allowed: PASS in backend/crown_api/tests/test_dashboard_snapshot_summary_api.py::test_batch0_summary_routes_serve_sample_payloads_in_development
- Direct URL tested: PASS for /api/dashboards/compliance-audit/summary in backend/crown_api/tests/test_dashboard_snapshot_summary_api.py
- Cross-tenant blocked: PARTIAL (PASS for dashboard summary contract endpoint in backend/crown_api/tests/test_dashboards_role_contract.py::test_cross_tenant_access_blocked; keyed batch0 summary endpoint-specific cross-tenant proof pending)
- Sensitive field redaction: not yet captured for keyed batch0 summary endpoints
- Small-cell suppression, if applicable: not yet captured
- Export permission proof, if applicable: not yet captured

## 6. Payload sample

{
  "dashboard_key": "compliance-audit",
  "metrics": [
    { "label": "Open Compliance Items", "value": "11" },
    { "label": "Audits Completed This Year", "value": "4" },
    { "label": "Policies Reviewed", "value": "23" },
    { "label": "Training Completion Rate", "value": "87%" }
  ],
  "alerts": [
    { "title": "3 compliance items are past due by 14+ days", "level": "High", "secondary": "Escalate to administration immediately." },
    { "title": "Annual policy review is 60% complete - deadline in 30 days", "level": "Medium", "secondary": "Accelerate review sessions." },
    { "title": "13% of staff have not completed required compliance training", "level": "Low", "secondary": "Final reminder before enforcement date." }
  ],
  "queue": [
    "Escalate 3 overdue compliance items to administration",
    "Schedule remaining policy review sessions before deadline",
    "Send final compliance training reminders to staff",
    "Publish compliance status report to board"
  ],
  "meta": { "school_id": "heritage-demo", "served_from": "sample" }
}

## 7. Independent review

Reviewer:
Date:
Decision: PENDING
Notes:

## 8. Certification decision

- Matrix row updated:
- Status promoted to: PROOF_IN_PROGRESS
- Remaining blockers: keyed endpoint tenant/role denial proof, browser runtime proof, independent review
