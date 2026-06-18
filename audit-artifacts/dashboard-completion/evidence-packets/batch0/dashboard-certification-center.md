# Dashboard Evidence Packet: dashboard-certification-center

Dashboard key: dashboard-certification-center
Module key: dashboard-certification-center
Owner: TBD
Independent reviewer: TBD
Status: PROOF_IN_PROGRESS
Date: 2026-06-18
Branch: feat/dashboard-batch0-control-services-20260618
Commit SHA: 2ebc116c

## 1. Contract

- Contract path: docs/dashboard-completion/contracts/batch0/dashboard-certification-center.md
- KPI definitions: dashboard certification volume, pending review queue, failed certification, certification rate
- Alert definitions: review queue backlog, failed dashboard correction guidance
- Queue/table/list definitions: review queue, corrections queue, certification report queue, reviewer roster checks
- Drilldown definitions: contract draft only; no runtime drilldown proof captured yet
- served_from rules: sample fallback allowed in non-production; backend sample payload returns served_from=sample
- Freshness SLA: not yet proven
- Sensitivity classification: internal
- Redaction rules: not yet proven
- Export rules: not yet proven

## 2. Backend proof

- Summary service path: backend/crown_api/dashboards/sample_payloads.py::dashboard_certification_center_sample_payload
- API route: /api/dashboards/dashboard-certification-center/summary (reverse('dashboard-summary', kwargs={'dashboard_key': 'dashboard-certification-center'}))
- Serializer/schema: backend/crown_api/dashboards/payload_contract.py::build_dashboard_payload
- Permission class/path: backend/crown_api/dashboards/views.py::DashboardSummaryView (IsAuthenticated)
- Tenant enforcement path: backend/crown_api/dashboards/views.py::`_school_id_from_request` and `_resolve_school_strict`
- Entitlement check path: not separately implemented for this dashboard in the current proof slice
- Audit event path: not yet proven
- Backend test path: backend/crown_api/tests/test_dashboard_snapshot_summary_api.py
- Backend test command: python -m pytest crown_api\tests\test_dashboard_snapshot_summary_api.py
- Backend test result: PASS (8 passed)

## 3. Frontend proof

- Dashboard page path: frontend/dashboards/src/pages/DashboardCertificationCenter.jsx
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

- Environment: not yet captured
- URL: not yet captured
- User role tested: not yet captured
- Tenant tested: not yet captured
- Playwright test path: not yet captured
- Playwright command: not yet captured
- Screenshot/trace path: not yet captured
- Result: pending runtime proof

## 5. Security proof

- Unauthenticated denied: not yet captured
- Unauthorized role denied: not yet captured
- Authorized role allowed: not yet captured
- Direct URL tested: not yet captured
- Cross-tenant blocked: not yet captured
- Sensitive field redaction: not yet captured
- Small-cell suppression, if applicable: not yet captured
- Export permission proof, if applicable: not yet captured

## 6. Payload sample

{
  "dashboard_key": "dashboard-certification-center",
  "metrics": [
    { "label": "Dashboards Certified", "value": "41" },
    { "label": "Pending Review", "value": "6" },
    { "label": "Failed Certification", "value": "2" },
    { "label": "Cert Rate", "value": "91%" }
  ],
  "alerts": [
    { "title": "Six dashboards are still in the review queue", "level": "High", "secondary": "Clear the queue before end of week." },
    { "title": "Two failed dashboards need correction guidance", "level": "Medium", "secondary": "Return feedback packages before resubmission." }
  ],
  "queue": [
    "Complete review queue clearance",
    "Return correction guidance for failed dashboards",
    "Publish the quarterly certification report",
    "Verify reviewer training records"
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
- Remaining blockers: runtime proof, security proof, independent review
