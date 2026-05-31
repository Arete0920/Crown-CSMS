# CROWN Dashboard Data Provenance Contract — 2026-05-29

## Decision

**REQUIRED FOR DASHBOARD COMPLETION.**

No dashboard, KPI tile, chart, table, status, activity feed, or operational summary may be certified complete unless its data provenance is explicit, testable, tenant-scoped, and current to the reviewed commit.

## Required provenance fields

Every dashboard widget must declare or derive the following metadata:

```json
{
  "dashboardKey": "attendance",
  "widgetKey": "attendance.dailyAbsenceRate",
  "dataState": "live",
  "sourceType": "backend_service",
  "sourceService": "AttendanceDashboardService",
  "sourceEndpoint": "/api/v1/dashboards/attendance/",
  "sourceModelOrQuery": "AttendanceRecord tenant-filtered aggregate",
  "tenantFiltered": true,
  "roleScoped": true,
  "fallbackAllowed": false,
  "sampleAllowed": false,
  "sandboxOnly": false,
  "freshnessTarget": "real_time_or_less_than_15_minutes",
  "lastVerifiedAt": "TBD",
  "evidencePath": "TBD"
}
```

## Allowed `dataState` values

| Value | Certification meaning |
|---|---|
| `live` | Real tenant-scoped service/API/model data. Eligible for completion if all tests pass. |
| `sandbox` | Synthetic sandbox data, explicitly labeled. Not eligible for production completion. |
| `sample` | Static/demo/sample data. Not eligible for completion. |
| `fallback` | Fallback when live data unavailable. Not eligible for completion unless explicitly certified for degraded mode. |
| `unavailable` | Feature has no data source. Not eligible for completion. |
| `error` | Runtime failure. Not eligible for completion. |
| `unknown` | Missing provenance. Not eligible for completion. |

## Prohibited certification patterns

A dashboard must fail certification if any ready-state widget:

- Uses `BASE_NOTE` preview text.
- Uses static metric arrays without live service provenance.
- Uses hard-coded school/user/student/family examples.
- Uses backend sample payloads in production/full-completion mode.
- Falls back silently from live data to sample data.
- Hides `sample`, `fallback`, `sandbox`, `unavailable`, or `error` behind a ready/healthy state.
- Lacks tenant-filter evidence.
- Lacks role-scope evidence.

## Required tests

Each dashboard must have tests proving:

1. Live data path succeeds for an authorized role.
2. Unauthorized role is denied.
3. Cross-tenant data is not visible.
4. Sample/fallback payloads are refused in production/full-completion certification mode.
5. Error/unavailable state is displayed honestly.
6. Widget provenance is exported into evidence.
7. The dashboard cannot be marked complete without all required provenance fields.

## Required evidence output

Dashboard completion gates must produce:

```text
.crown-audit/dashboard-provenance/latest/00_SUMMARY.md
.crown-audit/dashboard-provenance/latest/10_widget_provenance.csv
.crown-audit/dashboard-provenance/latest/20_missing_or_invalid_provenance.csv
.crown-audit/dashboard-provenance/latest/30_sample_fallback_violations.csv
.crown-audit/dashboard-provenance/latest/99_STATUS.json
```

## Completion rule

A dashboard is complete only when:

- Every widget is `live` or explicitly certified for its deployment context.
- Every widget is tenant-filtered and role-scoped.
- No hidden sample/fallback/preview source remains.
- Runtime evidence proves successful rendering.
- API evidence proves backend data source correctness.
- Accessibility and responsive evidence are current.
- Evidence artifacts are current to the reviewed commit.

## Status

Contract: **DOCUMENTED**

Implementation: **NOT GREEN until dashboard provenance is implemented and verified.**
