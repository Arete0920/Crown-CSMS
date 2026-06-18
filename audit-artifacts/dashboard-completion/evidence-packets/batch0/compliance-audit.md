# Dashboard Evidence Packet: compliance-audit

Dashboard key: compliance-audit
Module key: compliance-audit
Owner: TBD
Independent reviewer: TBD
Status: PROOF_IN_PROGRESS / CERTIFICATION_BLOCKED
Date: 2026-06-18
Branch: feat/dashboard-batch0-control-services-20260618
Commit SHA: ee9dc6753185fa0fe6affb77bfff129136398b27

## 1. Contract

- Contract path: docs/dashboard-completion/contracts/batch0/compliance-audit.md
- API response shape: dashboard_key, metrics, alerts, queue, meta
- KPI definitions: open compliance items, completed audits, policies reviewed, training completion rate
- Alert definitions: overdue compliance items, annual policy review pace, incomplete training
- Queue/list definitions: overdue item escalation, policy review sessions, training reminders, board status report
- Freshness SLA: not yet proven
- Sensitivity classification: internal
- Export rules: not yet proven

## 2. Backend proof

- Summary service path: backend/crown_api/dashboards/sample_payloads.py::compliance_audit_sample_payload
- API route: /api/dashboards/compliance-audit/summary
- Payload builder: backend/crown_api/dashboards/payload_contract.py::build_dashboard_payload
- Backend test path: backend/crown_api/tests/test_dashboard_snapshot_summary_api.py
- Backend test result: prior local proof reported PASS; current PR-head CI still requires final review after all workflow runs complete

## 3. Frontend proof

- Dashboard page path: frontend/dashboards/src/pages/ComplianceAuditDashboard.jsx
- API client/hook path: frontend/dashboards/src/hooks/useDashboardData.js
- Registry path: frontend/dashboards/src/config/dashboardDataRegistry.js
- Frontend test result: prior local proof reported lint 0 errors / 2 warnings, contracts PASS, dashboard completeness PASS; current PR-head CI still requires final review after all workflow runs complete

## 4. Runtime proof

- Environment: backend API test runtime only so far
- URL: /api/dashboards/compliance-audit/summary
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
