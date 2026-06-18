# Dashboard Evidence Packet: dashboard-certification-center

Dashboard key: dashboard-certification-center
Module key: dashboard-certification-center
Owner: TBD
Independent reviewer: TBD
Status: PROOF_IN_PROGRESS / CERTIFICATION_BLOCKED
Date: 2026-06-18
Branch: feat/dashboard-batch0-control-services-20260618
Commit SHA: ee9dc6753185fa0fe6affb77bfff129136398b27

## 1. Contract

- Contract path: docs/dashboard-completion/contracts/batch0/dashboard-certification-center.md
- API response shape: dashboard_key, metrics, alerts, queue, meta
- KPI definitions: certification count, mapped-only count, pending independent review count, certification rate
- Alert definitions: no certified dashboards yet, owner/reviewer still TBD
- Queue/list definitions: assign owner, assign independent reviewer, wire proof state, attach runtime proof
- Freshness SLA: not yet proven
- Sensitivity classification: internal
- Export rules: not yet proven

## 2. Backend proof

- Summary service path: backend/crown_api/dashboards/sample_payloads.py::dashboard_certification_center_sample_payload
- API route: /api/dashboards/dashboard-certification-center/summary
- Payload builder: backend/crown_api/dashboards/payload_contract.py::build_dashboard_payload
- Backend test path: backend/crown_api/tests/test_dashboard_snapshot_summary_api.py
- Backend test result: prior local proof reported PASS; current PR-head CI still requires final review after all workflow runs complete
- Connector note: backend sample payload metrics were partly aligned to 0/0/0/0%, but alerts and queue text still require final truth alignment before draft exit

## 3. Frontend proof

- Dashboard page path: frontend/dashboards/src/pages/DashboardCertificationCenter.jsx
- API client/hook path: frontend/dashboards/src/hooks/useDashboardData.js
- Dashboard template path: frontend/dashboards/src/config/dashboardTemplates/dashboardCertificationCenterDashboard.js
- Registry path: frontend/dashboards/src/config/dashboardDataRegistry.js
- Live metadata test path: frontend/dashboards/src/config/dashboardTemplateLiveMetadata.test.js
- Frontend test result: prior local proof reported lint 0 errors / 2 warnings, contracts PASS, dashboard completeness PASS; current PR-head CI still requires final review after all workflow runs complete

## 4. Runtime proof

- Environment: backend API test runtime only so far
- URL: /api/dashboards/dashboard-certification-center/summary
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

Expected truthful Certification Center payload baseline until real proof state is wired:

```json
{
  "dashboard_key": "dashboard-certification-center",
  "metrics": [
    { "label": "Dashboards Certified", "value": "0" },
    { "label": "Mapped Only", "value": "40" },
    { "label": "Pending Independent Review", "value": "0" },
    { "label": "Cert Rate", "value": "0%" }
  ],
  "alerts": [
    { "title": "No dashboards are certified yet", "level": "High", "secondary": "Current verified state remains 40 mapped dashboards and 0 live-data certified dashboards." },
    { "title": "Owner and independent reviewer are still TBD", "level": "High", "secondary": "Assign governance roles before certification promotion." }
  ],
  "queue": [
    "Assign dashboard certification owner",
    "Assign independent dashboard certification reviewer",
    "Wire certification proof state from the dashboard matrix",
    "Attach runtime proof"
  ],
  "meta": { "school_id": "heritage-demo", "served_from": "sample" }
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
- Remaining blockers: owner assignment, independent reviewer assignment, backend sample payload text alignment, browser runtime proof, evidence packet completion, review-thread closure
