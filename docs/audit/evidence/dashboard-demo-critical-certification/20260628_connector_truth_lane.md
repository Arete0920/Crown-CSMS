# Demo-Critical Dashboard Truth Lane — 2026-06-28

## Control branch

`fix/dashboard-demo-critical-certification-20260628`

Base commit: `70b0c4700de8079b14fdbd986d040c314a856fa2` (#1192 squash merge)

## Scope

This lane is limited to sandbox/demo-critical dashboard truth handling. It does not redesign the dashboard shell, create route sprawl, delete broad artifacts, or claim full dashboard certification.

## Product rule enforced

A sandbox/demo-critical dashboard may not silently present scaffold, sample, or fallback data as live. Each demo-critical dashboard must resolve to:

- a dashboard summary API endpoint;
- a disclosed fallback/sample data state when live data is unavailable;
- explicit `meta.served_from` provenance;
- `live_certified: false` unless separately proven through the dashboard certification program;
- a sandbox/demo-only boundary for fallback data;
- a regression test preventing demo-critical dashboards from losing this truth contract.

## Demo-critical dashboard set

- school-administrator
- admissions
- registrar
- billing
- financial-aid
- attendance
- gradebook
- communications
- scheduling
- parent
- teacher
- student
- dashboard-certification-center
- release-reliability
- compliance-audit

## Code changes

- `frontend/dashboards/src/config/dashboardDataRegistry.js`
  - adds `DEMO_CRITICAL_DASHBOARD_KEYS`;
  - adds disclosed demo-critical fallback summary generation;
  - forces demo-critical scaffold fallback disclosure on the explicit demo-critical set and existing control dashboards;
  - prevents caller metadata from overriding reserved truth-contract fields: `served_from`, `certification_candidate`, `live_certified`, and `sandbox_demo_only`;
  - labels fallback/sample data with `served_from`, `live_certified: false`, and `sandbox_demo_only: true`.
- `frontend/dashboards/src/config/dashboardDemoCriticalTruth.test.js`
  - asserts the demo-critical set;
  - asserts each dashboard has a summary endpoint;
  - asserts each dashboard has disclosed fallback/sample provenance;
  - asserts fallback data does not claim live certification.

## Remaining certification boundary

This lane improves demo/sandbox truth handling. It does not close #863 or #1089 by itself.

#863 remains open until preview/template metrics are either replaced with live service/API data or documented as sandbox-only fallback with full runtime proof.

#1089 remains open until the dashboard program reaches the required certification statuses: data contracted, API wired, UI wired, permission proven, tenant proven, runtime proven, evidence packet attached, independent review complete, and certification promoted.

## Required validation

Run from `frontend/dashboards`:

```bash
npm run test -- src/config/dashboardDemoCriticalTruth.test.js src/config/dashboardTemplateContract.test.js
npm run build
```

Then open the PR and require all GitHub checks to pass before merge.