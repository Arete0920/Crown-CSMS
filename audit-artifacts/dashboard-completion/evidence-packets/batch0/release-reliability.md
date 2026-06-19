# Dashboard Evidence Packet: release-reliability

Dashboard key: release-reliability
Module key: release-reliability
Owner: Platform Engineering
Independent reviewer: TBD (INDEPENDENT_REVIEW_REQUIRED)
Status: REVIEW_CANDIDATE / TRUTH_ALIGNED / API_PERMISSION_PROVEN / TENANT_BEHAVIOR_DOCUMENTED / BROWSER_PROOF_PASS_UNIT_TESTS / NOT_CERTIFIED
Date: 2026-06-19
State register: audit-artifacts/dashboard-completion/state/dashboard-certification-state.json
Static frontend proof: audit-artifacts/dashboard-completion/frontend-proof/batch0/release-reliability-static-proof-20260618.md
Browser proof: audit-artifacts/dashboard-completion/browser-proof/batch0/release-reliability-browser-proof-20260619.md
Review marker: docs/dashboard-completion/batch0/release-reliability-packet/10_review_workaround_marker.md
Matrix row candidate: docs/dashboard-completion/batch0/release-reliability-packet/11_matrix_candidate.json

## Current proof summary

- Backend sample payload exists: PASS.
- Frontend page exists: PASS.
- Frontend template exists: PASS.
- Frontend route/registry wiring exists: PASS.
- Static role-guard wiring exists: PASS.
- releaseState set to 'ready' in registry: PASS.
- Truth alignment: PASS (sample payload is the documented development truth source).
- API permission proof: PASS (8 backend proof tests — see test file below).
- Tenant proof: PASS / GAP_DOCUMENTED (school_id accepted and recorded in meta; strict cross-tenant enforcement not yet wired for this dashboard — see gap note).
- Browser-rendered title/metrics proof: PASS (8 frontend unit tests — see test file below).
- Screenshot or trace: PASS_UNIT_TESTS (unit test render proof; live authenticated screenshot remains pending).
- Independent review: PENDING (INDEPENDENT_REVIEW_REQUIRED).
- Matrix row change: CANDIDATE ONLY.
- Certification: NOT CERTIFIED.

## Contract

- Contract path: docs/dashboard-completion/contracts/batch0/release-reliability.md
- API response shape: dashboard_key, metrics, alerts, queue, meta
- KPI definitions: deployment count, open production incidents, failed checks, release readiness
- Alert definitions: contract gate failure, build SHA mismatch, incomplete release proof packet
- Queue/list definitions: gate review queue, environment alignment queue, incident postmortem queue, readiness summary queue
- Freshness SLA: not yet proven
- Sensitivity classification: internal
- Export rules: not yet proven

## Static frontend proof

Connector inspection verified:

- `frontend/dashboards/src/pages/ReleaseReliabilityDashboard.jsx` exists.
- Page renders `CrownDashboardTemplate`.
- Page uses template key `releaseReliability`.
- Template file exists at `frontend/dashboards/src/config/dashboardTemplates/releaseReliabilityDashboard.js`.
- Registry path exists at `frontend/dashboards/src/config/dashboardRegistry.js`.
- Route path resolves to `/release-reliability-dashboard`.
- Dashboard registry route generator wraps dashboards in `RoleRouteGuard` and `ReleaseStateRoute`.
- Main router includes `...dashboardRoutes`.

## Truth alignment — resolved (2026-06-19)

The template metrics are sample/scaffold values.
These values are served from `sample_payloads.py -> release_reliability_sample_payload()` in development and from `DashboardSnapshot` in production.

Documented truth source:
- Development: `backend/crown_api/dashboards/sample_payloads.py` (`release_reliability_sample_payload`)
- Production: `DashboardSnapshot` model (seeded via `seed_dashboard_snapshots` management command)
- Live wiring: not yet connected to a real release-state service; the snapshot/seed path is the evidence path for this stage.

Template metric labels proofed by frontend unit tests.

## API permission proof (2026-06-19)

Test file: `backend/crown_api/tests/test_release_reliability_dashboard_proof.py`

Tests run and result:

```text
test_release_reliability_summary_rejects_unauthenticated_request      PASS
test_release_reliability_summary_returns_200_for_authenticated_user    PASS
test_release_reliability_sample_payload_has_contract_fields            PASS
test_release_reliability_sample_payload_has_release_kpis               PASS
test_release_reliability_development_payload_is_served_from_sample     PASS
test_release_reliability_snapshot_takes_priority_over_sample_in_production PASS
test_release_reliability_production_without_snapshot_returns_503        PASS
test_release_reliability_tenant_header_recorded_in_meta                PASS

8 passed in approx. 69s
```

## Tenant behavior documentation

- X-School-Id header is accepted and recorded in response meta.school_id: PROVEN.
- Strict cross-tenant isolation for this dashboard is not fully wired in the current view layer.
- This packet treats that as a documented gap that blocks final certification until resolved or formally accepted by the review gate.

## Browser-rendered title and metrics proof (2026-06-19)

Test file: `frontend/dashboards/src/pages/ReleaseReliabilityDashboard.test.jsx`

Tests run and result:

```text
template key resolves to releaseReliability                    PASS
title field is non-empty and contains release context          PASS
metrics array has deployment-count KPI                         PASS
metrics array has incident KPI                                 PASS
dataSource is live_api                                         PASS
apiEndpoint is declared and starts with /api/v1/               PASS
liveDataKey is declared                                        PASS
page component renders without throwing                        PASS

8 passed in approx. 19ms
```

## Required final gate before certification

- Complete independent review or record approved solo-maintainer workaround marker.
- Verify live browser screenshot with authenticated crown_platform_ops session or explicitly record accepted unit-proof substitute.
- Resolve or explicitly accept the strict cross-tenant enforcement gap for this dashboard.
- Only after that gate, update the matrix row to CERTIFIED.

## Certification decision

- Truth source: DOCUMENTED.
- API permission proof: PASS.
- Tenant proof: PASS / GAP_DOCUMENTED.
- Browser title/metrics proof: PASS_UNIT_TESTS.
- Screenshot or trace: PASS_UNIT_TESTS; live browser screenshot pending or needs accepted substitute marker.
- Independent review: PENDING — INDEPENDENT_REVIEW_REQUIRED.
- Matrix promotion: CANDIDATE ONLY.
- Certification: NOT CERTIFIED.

## Non-claims

This packet does not certify the dashboard.
This packet does not certify any other dashboard.
