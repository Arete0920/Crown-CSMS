# Dashboard Evidence Packet: release-reliability

Dashboard key: release-reliability
Module key: release-reliability
Owner: TBD
Independent reviewer: TBD
Status: PROOF_IN_PROGRESS
Date: 2026-06-18
Branch: feat/dashboard-batch0-control-services-20260618
Commit SHA: 2ebc116c

## 1. Contract

- Contract path: docs/dashboard-completion/contracts/batch0/release-reliability.md
- KPI definitions: deployment count, open production incidents, failed checks, release readiness
- Alert definitions: contract gate failure, build SHA mismatch, incomplete release proof packet
- Queue/table/list definitions: gate review queue, environment alignment queue, incident postmortem queue, readiness summary queue
- Drilldown definitions: contract draft only; no runtime drilldown proof captured yet
- served_from rules: sample fallback allowed in non-production; backend sample payload returns served_from=sample
- Freshness SLA: not yet proven
- Sensitivity classification: internal
- Redaction rules: not yet proven
- Export rules: not yet proven

## 2. Backend proof

- Summary service path: backend/crown_api/dashboards/sample_payloads.py::release_reliability_sample_payload
- API route: /api/dashboards/release-reliability/summary (reverse('dashboard-summary', kwargs={'dashboard_key': 'release-reliability'}))
- Serializer/schema: backend/crown_api/dashboards/payload_contract.py::build_dashboard_payload
- Permission class/path: backend/crown_api/dashboards/views.py::DashboardSummaryView (IsAuthenticated)
- Tenant enforcement path: backend/crown_api/dashboards/views.py::`_school_id_from_request` and `_resolve_school_strict`
- Entitlement check path: not separately implemented for this dashboard in the current proof slice
- Audit event path: not yet proven
- Backend test path: backend/crown_api/tests/test_dashboard_snapshot_summary_api.py
- Backend test command: python -m pytest crown_api\tests\test_dashboard_snapshot_summary_api.py
- Backend test result: PASS (8 passed)

## 3. Frontend proof

- Dashboard page path: frontend/dashboards/src/pages/ReleaseReliabilityDashboard.jsx
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
- URL: /api/dashboards/release-reliability/summary
- User role tested: not yet captured
- Tenant tested: role-contract and tenant-isolation suites executed for dashboard APIs (non-keyed summary endpoints)
- Playwright test path: not yet captured
- Playwright command: not yet captured
- Screenshot/trace path: not yet captured
- Result: backend runtime proof captured via automated tests; browser runtime proof pending

## 5. Security proof

- Unauthenticated denied: PASS for keyed endpoint /api/dashboards/release-reliability/summary in backend/crown_api/tests/test_dashboard_snapshot_summary_api.py::test_batch0_summary_routes_require_authentication
- Unauthorized role denied: PARTIAL (covered for cross-tenant dashboard summary contract endpoints; keyed batch0 endpoint-specific role denial not yet captured)
- Authorized role allowed: PASS in backend/crown_api/tests/test_dashboard_snapshot_summary_api.py::test_batch0_summary_routes_serve_sample_payloads_in_development
- Direct URL tested: PASS for /api/dashboards/release-reliability/summary in backend/crown_api/tests/test_dashboard_snapshot_summary_api.py
- Cross-tenant blocked: PARTIAL (PASS for dashboard summary contract endpoint in backend/crown_api/tests/test_dashboards_role_contract.py::test_cross_tenant_access_blocked; keyed batch0 summary endpoint-specific cross-tenant proof pending)
- Sensitive field redaction: not yet captured for keyed batch0 summary endpoints
- Small-cell suppression, if applicable: not yet captured
- Export permission proof, if applicable: not yet captured

## 6. Payload sample

{
  "dashboard_key": "release-reliability",
  "metrics": [
    { "label": "Deployments This Month", "value": "9" },
    { "label": "Open Production Incidents", "value": "2" },
    { "label": "Failed Checks in Last 24h", "value": "4" },
    { "label": "Release Readiness", "value": "Watch" }
  ],
  "alerts": [
    { "title": "Contract gate failed on last main candidate build", "level": "High", "secondary": "Platform engineering follow-up required." },
    { "title": "Two environments are not on expected build SHA", "level": "High", "secondary": "Verify deployment alignment." },
    { "title": "Release proof packet is incomplete for one deploy", "level": "Medium", "secondary": "Complete evidence before certification." }
  ],
  "queue": [
    "Review failed release gate evidence",
    "Verify environment build SHA alignment",
    "Close open production incident postmortem tasks",
    "Publish release readiness summary"
  ],
  "meta": { "school_id": "platform", "served_from": "sample" }
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
