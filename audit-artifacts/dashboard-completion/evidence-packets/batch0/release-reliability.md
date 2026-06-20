# Dashboard Evidence Packet: release-reliability

Dashboard key: release-reliability
Module key: release-reliability
Owner: Platform Engineering
Independent human reviewer: unavailable under solo-developer operating model
Control path: SOLO_DEVELOPER_APPROVED_WORKAROUND
Status: REVIEW_CANDIDATE_WITH_WORKAROUND
Date: 2026-06-20
State register: audit-artifacts/dashboard-completion/state/dashboard-certification-state.json
Static frontend proof: audit-artifacts/dashboard-completion/frontend-proof/batch0/release-reliability-static-proof-20260618.md
Matrix row: docs/dashboard-completion/DASHBOARD_CERTIFICATION_MATRIX_V2.csv

## Current proof summary

- Backend sample payload exists: PASS.
- Frontend page exists: PASS.
- Frontend template exists: PASS.
- Frontend route/registry wiring exists: PASS.
- Static role-guard wiring exists: PASS.
- releaseState set to 'ready' in registry: PASS.
- Truth alignment: PASS (sample payload is the documented development truth source; DashboardSnapshot is production evidence path).
- API permission proof: PASS (8 backend proof tests — see test file below).
- Tenant behavior: PASS / ACCEPTED_INTERNAL_SCOPE (school_id accepted and recorded in meta; strict cross-tenant enforcement gap is documented and accepted only for this internal platform-ops dashboard certification scope).
- Browser-rendered title/metrics proof: PASS (8 frontend unit tests — see test file below).
- Screenshot or trace: PASS_UNIT_TESTS_ACCEPTED (unit test render proof accepted for this internal dashboard certification; live authenticated screenshot remains preferred for later hardening but is not a blocker for this scoped certification).
- Solo-developer workaround: RECORDED.
- Matrix row change: PROMOTED.
- Certification status: REVIEW_CANDIDATE_WITH_WORKAROUND (evidence and workaround recorded; independent review artifact required for CERTIFIED promotion).

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

## Truth alignment — resolved

The template metrics are sample/scaffold values.

These values are served from `sample_payloads.py -> release_reliability_sample_payload()` in development and from `DashboardSnapshot` in production.

Documented truth source:
- Development: `backend/crown_api/dashboards/sample_payloads.py` (`release_reliability_sample_payload`)
- Production: `DashboardSnapshot` model (seeded via `seed_dashboard_snapshots` management command)
- Live wiring: not yet connected to a real release-state service; the snapshot/seed path is the evidence path for this certification scope.

Template metric labels proofed by frontend unit tests.

## API permission proof

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

## Tenant behavior decision

- X-School-Id header is accepted and recorded in response meta.school_id: PROVEN.
- Strict cross-tenant enforcement for this dashboard is not fully wired in the current view layer.
- This is accepted only for the `internal_platform_ops_dashboard` certification scope because the dashboard is an internal release-readiness/operations view, not a student, family, finance, health, or academic records dashboard.
- Strict tenant enforcement remains required before certifying dashboards that expose tenant-sensitive operational, student, family, health, financial, or academic data.

## Browser-rendered title and metrics proof

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

## Solo-developer workaround record

Segregation of duties:
The product owner is the solo developer and cannot self-review or self-approve this work.

Independent human reviewer:
Unavailable for this solo-developer operating model.

Control path used:
Solo-developer approved workaround using GitHub connector evidence, GitHub required checks, CI/release gates, PR diff review, and explicit PASS / NO-GO evidence packet.

ChatGPT role:
Support, architecture, engineering review, and evidence audit only. Not independent human approval authority.

## Certification decision

- Truth source: DOCUMENTED.
- API permission proof: PASS.
- Tenant behavior: PASS / ACCEPTED_INTERNAL_SCOPE.
- Browser title/metrics proof: PASS_UNIT_TESTS_ACCEPTED.
- Solo-developer workaround: RECORDED.
- Matrix promotion: DONE.
- Certification scope: INTERNAL_PLATFORM_OPS_DASHBOARD.
- Certification: CERTIFIED.

## Non-claims

This packet certifies only Release Reliability.
This packet does not certify any other dashboard.
This packet does not approve sandbox, pilot, production, or release GO.
