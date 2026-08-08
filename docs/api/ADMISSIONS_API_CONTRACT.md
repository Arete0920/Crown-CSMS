# Admissions and Enrollment API Contract

**Version:** 1.1.0  
**Status:** CURRENT AUTHORITY  
**Last verified:** 2026-08-08  
**Verified source baseline:** `9090aa2463baf1e3afcfe3590da8e250c6e12d35`

## Routing authority

The canonical admissions API is mounted at `/api/v1/admissions/*`.

CROWN intentionally mounts `/api/*` as a compatibility alias of the same `api_v1_urls` tree. Therefore `/api/admissions/*` may expose both canonical aliases and the retained legacy admissions subtree. New integrations should prefer `/api/v1/admissions/*` unless a route is explicitly documented as compatibility-only.

Do not infer deployment hostnames from this contract. Deployment identity and live endpoint authority belong to the current release-status and deployment evidence for the exact release SHA.

## Authentication and tenant scope

Protected endpoints require authenticated CROWN identity and tenant resolution. Normal authenticated access is school-scoped and permission-scoped.

Admissions permissions:

- `admissions.view` — read admissions pipeline, drilldown, state, contract and event surfaces.
- `admissions.edit` — mutate admissions/enrollment workflow state.

Staff/superuser behavior is an explicit administrative override only where the implementation documents it; ordinary users must satisfy tenant-scoped CROWN RBAC.

## Canonical public and staff endpoints

### Public configuration

`GET /api/v1/admissions/public-config/`

Returns current application-fee and assessment/interview configuration. Public bootstrap does not require a tenant header.

### Public submission

`POST /api/v1/admissions/submit/`

Persists the canonical UUID-based admissions records and returns the application status center, checklist/document continuity, fee/finance handoff, reviewer summary, enrollment continuity, and next-step orchestration.

Submission supports request correlation, abuse controls, and idempotency. A repeated valid `Idempotency-Key` replays the prior result rather than creating duplicate applications.

### Summary

`GET /api/v1/admissions/summary/`

Requires `admissions.view` and returns school-scoped admissions pipeline, conversion, velocity, source, workflow-engine and post-admission rollup data.

### Drilldown

`GET /api/v1/admissions/drilldown/`

Requires `admissions.view`.

Supported filters include academic year, stage, source, limit and offset. Stage values are:

- `inquiry`
- `tour_scheduled`
- `tour_completed`
- `application_started`
- `application_submitted`
- `in_review`
- `accepted`
- `waitlisted`
- `declined`
- `enrolled`

`results` is the canonical page collection for new clients. `rows` remains an identical compatibility alias. The previously documented June 1, 2026 removal date was not executed and is superseded; removal now requires a separately tested/versioned client-retirement change.

### Enrollment state

`GET /api/v1/admissions/applications/<uuid:application_id>/enrollment-state/`

Requires `admissions.view`.

`POST /api/v1/admissions/applications/<uuid:application_id>/enrollment-state/update/`

Requires `admissions.edit`. The state machine controls contract and deposit progression and records workflow events.

### Enrollment contract

- `GET /api/v1/admissions/applications/<uuid:application_id>/contract/`
- `POST /api/v1/admissions/applications/<uuid:application_id>/contract/update/`
- `POST /api/v1/admissions/applications/<uuid:application_id>/contract/amend/`

Read requires `admissions.view`; mutation requires `admissions.edit`.

Contract records are versioned and support issued, signed, countersigned and superseded history with line items and financial totals.

### Lifecycle chain

`POST /api/v1/admissions/applications/<uuid:application_id>/lifecycle-chain/update/`

Requires `admissions.edit` and is available only after acceptance.

Enrollment confirmation fails closed unless:

- contract status is `countersigned`; and
- deposit status is `paid` or `waived`.

Classroom readiness and parent-portal activation require enrollment confirmation.

### Event replay

`GET /api/v1/admissions/applications/<uuid:application_id>/event-replay/`

Requires `admissions.view` and returns the scoped application event history used to explain/replay workflow state.

## Compatibility admissions subtree

The retained `admissions` Django app supports compatibility and bridge surfaces, including:

- `GET /api/admissions/applications/`
- `GET /api/admissions/applications/<int:application_id>/`
- `POST /api/admissions/enroll/`
- admissions director priority/metrics/timeline routes

The compatibility application identifier is an integer. These endpoints do not replace the canonical UUID `applications.Application` workflow.

Compatibility enrollment must be tenant scoped, permission controlled, guarded by the legacy transition graph, audited, idempotent, and consistent with the canonical enrollment projection.

## Data and lifecycle authority

See `docs/admissions/ADMISSIONS_ENROLLMENT_AUTHORITY_20260808.md` for the authoritative distinction between:

- canonical application record status;
- computed funnel stage;
- canonical contract/deposit/enrollment state;
- legacy compatibility application status;
- canonical and compatibility identity domains.

## Contract verification

The contract is considered verified only when exact-head CI passes the applicable admissions endpoint, RBAC/tenant, conversion-wizard, migration, frontend contract, and golden-path tests. Documentation alone is not certification.
