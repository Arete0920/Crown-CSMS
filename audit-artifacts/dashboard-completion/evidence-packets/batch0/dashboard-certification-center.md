# Dashboard Evidence Packet: dashboard-certification-center

Dashboard key: dashboard-certification-center
Module key: dashboard-certification-center
Owner: TBD
Independent reviewer: TBD
Status: PROOF_IN_PROGRESS / CERTIFICATION_BLOCKED
Date: 2026-06-18
Current proof commit SHA: 43e072dc49e849c33b9d979fd2892629dcb11048
Latest evidence packet update: 7a8390325af1cefe27bc6d744865ea8e3107fdd6

## 1. Contract

- Contract path: docs/dashboard-completion/contracts/batch0/dashboard-certification-center.md
- API response shape: dashboard_key, metrics, alerts, queue, meta
- KPI definitions: certification count, mapped-only count, pending independent review count, certification rate
- Alert definitions: no certified dashboards yet, owner/reviewer still TBD
- Queue/list definitions: assign owner, assign independent reviewer, wire proof state, attach runtime proof
- Freshness SLA: not yet proven
- Sensitivity classification: internal control dashboard; summary API is staff/superuser restricted as of commit 4666afcb95f7c948070bea914d1f1bff147d66ff
- Export rules: not yet proven

## 2. Backend proof

- Summary service path: backend/crown_api/dashboards/sample_payloads.py::dashboard_certification_center_sample_payload
- API route: /api/v1/dashboards/dashboard-certification-center/summary
- Payload builder: backend/crown_api/dashboards/payload_contract.py::build_dashboard_payload
- Backend test path: backend/crown_api/tests/test_dashboard_snapshot_summary_api.py
- Backend test result: PASS on Codespace main at 43e072dc49e849c33b9d979fd2892629dcb11048
- Full file run: `13 passed in 82.00s`

### Backend proof commands and results

```text
$ git status --short
<no output>

$ git rev-parse HEAD
43e072dc49e849c33b9d979fd2892629dcb11048

$ /workspaces/Crown2026/.venv/bin/python -m pytest backend/crown_api/tests/test_dashboard_snapshot_summary_api.py -q
.............                                                            [100%]
13 passed in 82.00s (0:01:22)
```

## 3. API permission proof

Result: PASS on Codespace main at 43e072dc49e849c33b9d979fd2892629dcb11048.

```text
$ /workspaces/Crown2026/.venv/bin/python -m pytest backend/crown_api/tests/test_dashboard_snapshot_summary_api.py::test_dashboard_certification_center_staff_user_receives_summary_payload -q
.                                                                        [100%]
1 passed in 80.77s (0:01:20)

$ /workspaces/Crown2026/.venv/bin/python -m pytest backend/crown_api/tests/test_dashboard_snapshot_summary_api.py::test_dashboard_certification_center_non_staff_user_is_forbidden -q
.                                                                        [100%]
1 passed in 80.15s (0:01:20)

$ /workspaces/Crown2026/.venv/bin/python -m pytest backend/crown_api/tests/test_dashboard_snapshot_summary_api.py::test_dashboard_certification_center_superuser_receives_summary_payload -q
.                                                                        [100%]
1 passed in 79.34s (0:01:19)
```

Interpretation:

- Staff user receives summary payload: PASS.
- Superuser receives summary payload: PASS.
- Authenticated non-staff user receives 403: PASS.
- Unauthenticated user receives 401 as part of file-level Batch 0 tests: PASS.

## 4. Frontend proof

- Dashboard page path: frontend/dashboards/src/pages/DashboardCertificationCenter.jsx
- API client/hook path: frontend/dashboards/src/hooks/useDashboardData.js
- Dashboard template path: frontend/dashboards/src/config/dashboardTemplates/dashboardCertificationCenterDashboard.js
- Registry path: frontend/dashboards/src/config/dashboardDataRegistry.js
- Live metadata test path: frontend/dashboards/src/config/dashboardTemplateLiveMetadata.test.js
- Frontend test result: pending current-main rerun after permission proof update

## 5. Runtime proof

- Environment: Codespace runtime startup and HTTP reachability partial proof
- URL: /dashboards/dashboard-certification-center
- Runtime proof packet: audit-artifacts/dashboard-completion/runtime-proof/batch0/dashboard-certification-center-codespace-runtime-partial-20260618.md
- Backend server startup: PASS from user-provided Codespace report
- Frontend server startup: PASS from user-provided Codespace report
- Frontend HTTP 200 reachability: PASS from user-provided Codespace report
- Browser-rendered title/metrics proof: NOT VERIFIED
- Screenshot/trace path: NOT PROVIDED
- Result: PARTIAL RUNTIME INFRASTRUCTURE PROOF ONLY; browser-rendered dashboard proof remains pending

## 6. Governance proof

- Owner assignment: pending
- Independent reviewer assignment: pending
- Dashboard-specific role matrix proof: API-level role proof passed for staff/superuser/non-staff; frontend role experience pending
- Dashboard-specific tenant proof: pending
- Evidence packet review: pending
- Certification decision: pending

## 7. Payload sample

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

## 8. Independent review

Reviewer: TBD
Date: TBD
Decision: PENDING
Notes: TC cannot self-approve certification-affecting work.

## 9. Certification decision

- Matrix row updated: not yet
- Status promoted to: PROOF_IN_PROGRESS / CERTIFICATION_BLOCKED
- Remaining blockers: owner assignment, independent reviewer assignment, browser-rendered title/metrics proof, screenshot or trace artifact, frontend role experience proof, tenant proof, evidence packet review, certification decision

## 10. Non-claims

This evidence packet does not certify the dashboard.
This evidence packet does not approve sandbox, pilot, production, or release GO.
