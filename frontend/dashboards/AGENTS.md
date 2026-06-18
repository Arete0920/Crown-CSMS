# Dashboard Frontend Agent Contract

This contract applies to `frontend/dashboards/**`.

## Evidence Boundary

A dashboard is not complete because it is registered or mapped.

A dashboard can be called LIVE only when current evidence proves:

1. route registration;
2. rendered UI proof;
3. authenticated API/data source wiring;
4. tenant-scoped data behavior;
5. loading, empty, and error states;
6. role visibility behavior;
7. automated or captured runtime evidence;
8. no mock-only data in the certified path.

## Scope Discipline

Do not perform broad UI rewrites, style-only churn, dependency upgrades, route rewires, package changes, or dashboard registry changes unless explicitly scoped.

## Required Proof

For dashboard work, capture and report:

- changed files;
- route(s) touched;
- API/data source(s) used;
- test command output;
- screenshot or runtime proof if UI claim is made;
- whether mock data remains in the certified path.

## Validation

Use the narrowest relevant checks first. Examples:

```powershell
npm run test -- --run
npm run build
```

Use actual project scripts when they differ.

## Forbidden Claims

Do not claim dashboard live-data readiness from:

- registry presence alone;
- route presence alone;
- static card rendering alone;
- mock data;
- screenshots without authenticated data-source proof.

## Closeout

Report:

- files changed;
- route(s) affected;
- data source proof;
- validation run;
- remaining dashboard risks;
- independent review status.
