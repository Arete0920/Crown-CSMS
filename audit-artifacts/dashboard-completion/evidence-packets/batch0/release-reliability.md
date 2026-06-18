# Dashboard Evidence Packet: release-reliability

Dashboard key: release-reliability
Module key: release-reliability
Owner: TBD
Independent reviewer: TBD
Status: PROOF_IN_PROGRESS / CERTIFICATION_BLOCKED
Date: 2026-06-18
Branch: feat/dashboard-batch0-control-services-20260618
Commit SHA: ee9dc6753185fa0fe6affb77bfff129136398b27

## 1. Contract

- Contract path: docs/dashboard-completion/contracts/batch0/release-reliability.md
- API response shape: dashboard_key, metrics, alerts, queue, meta
- KPI definitions: deployment count, open production incidents, failed checks, release readiness
- Alert definitions: contract gate failure, build SHA mismatch, incomplete release proof packet
- Queue/list definitions: gate review queue, environment alignment queue, incident postmortem queue, readiness summary queue
- Freshness SLA: not yet proven
- Sensitivity classification: internal
- Export rules: not yet proven

## 2. Backend proof

- Summary service path: backend/crown_api/dashboards/sample_payloads.py::release_reliability_sample_payload
- API route: /api/dashboards/release-reliability/summary
- Payload builder: backend/crown_api/dashboards/payload_contract.py::build_dashboard_payload
- Backend test path: backend/crown_api/tests/test_dashboard_snapshot_summary_api.py
- Backend test result: prior local proof reported PASS; current PR-head CI still requires final review after all workflow runs complete

## 3. Frontend proof

- Dashboard page path: frontend/dashboards/src/pages/ReleaseReliabilityDashboard.jsx
- API client/hook path: frontend/dashboards/src/hooks/useDashboardData.js
- Registry path: frontend/dashboards/src/config/dashboardDataRegistry.js
- Frontend test result: prior local proof reported lint 0 errors / 2 warnings, contracts PASS, dashboard completeness PASS; current PR-head CI still requires final review after all workflow runs complete

## 4. Runtime proof

- Environment: backend API test runtime only so far
- URL: /api/dashboards/release-reliability/summary
- Browser runtime proof: pending
- Screenshot/trace path: pending
- Result: backend API proof partial; browser/runtime proof pending

## 5. Governance proof

- Owner assignment: pending
- Independent reviewer assignment: pending
- Dashboard-specific role matrix proof: pending
- Dashboard-specific tenant proof: pending
- Evidence packet review: pending
- Certification decision: pending

## 6. Payload sample

```json
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
```

## 7. Independent review

Reviewer: TBD
Date: TBD
Decision: PENDING
Notes: TC cannot self-approve certification-affecting work.

## 8. Certification decision

- Matrix row updated: not yet
- Status promoted to: PROOF_IN_PROGRESS / CERTIFICATION_BLOCKED
- Remaining blockers: owner assignment, independent reviewer assignment, browser runtime proof, evidence packet completion, review-thread closure
