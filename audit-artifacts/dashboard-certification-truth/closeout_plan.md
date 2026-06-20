# Dashboard Certification Closeout Plan

## Current Truth

```json
{
  "registry_count": 40,
  "matrix_count": 42,
  "state_register_count": 40,
  "factory_count": 0,
  "certified_count": 0,
  "certifiable_now_count": 0,
  "missing_review_only_count": 0,
  "missing_proof_count": 40,
  "missing_implementation_count": 0
}
```

## Ranked Path

1. Reconcile denominator mismatch in a separate matrix/scorecard PR (no product code).
2. Batch 0 first: dashboard-certification-center, release-reliability, compliance-audit.
3. For each dashboard lane, close proof gates in this order: permission, tenant, runtime/browser, evidence packet, independent review/workaround record, matrix/state promotion.
4. Keep certification reporting PRs separate from implementation PRs.

## Blocker Groups

```json
{
  "missing_proof": 40
}
```

## Actions That Close Multiple Dashboards

1. Standardize tenant-proof test harness for dashboard summary endpoints.
2. Standardize permission-proof matrix per route and role for dashboard endpoints.
3. Standardize browser/runtime proof capture packet schema for all dashboard lanes.
4. Add independent review/workaround record template linked from matrix rows.

## Separation Rules

- Keep product implementation separate from certification reporting and scorecard reconciliation.
- Do not mark CERTIFIED until matrix, state register, evidence packet, runtime proof, and review/workaround record all agree.

## Verified Time Estimate

- NOT VERIFIED: Batch 0 truth closure evidence-only updates: 1 to 2 days.
- Remaining 39 dashboard proof completion depends on implementation and test readiness; NOT VERIFIED in this audit-only lane.