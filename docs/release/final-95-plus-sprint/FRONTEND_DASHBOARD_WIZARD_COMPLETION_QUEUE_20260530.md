# CROWN Final 95+ Frontend / Dashboard / Wizard Completion Queue - 2026-05-30

Status: ACTIVE FINAL-SPRINT CONTROL ARTIFACT
Authority: Non-shipping execution queue until promoted by `docs/CURRENT_RELEASE_STATUS.md`.

## Purpose

This queue defines what must be completed and proven before any frontend, dashboard, wizard, navigation, or role journey can score 95+.

A page existing is not completion. A route existing is not completion. A dashboard card existing is not completion. A wizard shell existing is not completion.

## Frontend completion standard

Every production frontend surface must prove:

1. Canonical route exists.
2. Route is public, role-guarded, release-gated, or explicitly hidden.
3. Page renders without runtime error.
4. Page has loading, empty, error, degraded, and unavailable states where relevant.
5. Data source is live/proven or honestly labeled fallback/sample/stale/unavailable.
6. Role journey is executable for the intended persona.
7. CTAs are not dead links.
8. Responsive layout is acceptable.
9. Accessibility release check passes or exceptions are documented and accepted.
10. Tests exist and pass on current candidate SHA.

## P0 frontend gates

| Gate | Status | Required evidence |
|---|---|---|
| `npm ci` | NOT VERIFIED on latest connector commits | VS Code evidence output |
| `npm run lint` | NOT VERIFIED on latest connector commits | VS Code evidence output |
| `npm run test:contracts` | NOT VERIFIED on latest connector commits | VS Code evidence output |
| `npm run check:shell-certification` | NOT VERIFIED on latest connector commits | VS Code evidence output |
| `npm run check:shell-backend-contract-parity` | NOT VERIFIED on latest connector commits | VS Code evidence output |
| `npm run verify:dashboard-completeness` | NOT VERIFIED on latest connector commits | VS Code evidence output |
| `npm run build` | NOT VERIFIED on latest connector commits | VS Code evidence output |
| `node scripts/release/verify-api-contracts.mjs` | NOT VERIFIED on latest connector commits | VS Code evidence output |
| `node scripts/release/verify-navigation-surface.mjs` | NOT VERIFIED on latest connector commits | VS Code evidence output |

## Dashboard closure queue

### Required dashboard matrices

1. `FINAL_DASHBOARD_KPI_PROVENANCE_MATRIX.md`
2. `FINAL_DASHBOARD_ROUTE_GUARD_MATRIX.md`
3. `FINAL_DASHBOARD_RELEASE_STATE_MATRIX.md`
4. `FINAL_DASHBOARD_ACCESSIBILITY_MATRIX.md`

### Dashboard classification required for every registry row

| Field | Required |
|---|---|
| Dashboard key | Yes |
| Label/title | Yes |
| Path | Yes |
| Tier | Yes |
| Section | Yes |
| Component | Yes |
| Allowed roles | Yes |
| Release state | Yes |
| Readiness flags | Yes |
| Data source | Yes |
| KPI source | Yes |
| API route | Yes if data-backed |
| Empty/error/degraded state | Yes |
| Tests | Yes |
| Score | Required final score |

### Dashboard production rule

A dashboard cannot be production-visible unless:

- releaseState is `ready`, `live`, or `production`,
- readiness flags are all true,
- no placeholder signals are present,
- source labels/data states are truthful,
- route guard is correct,
- tests pass.

## Wizard closure queue

### Required wizard matrices

1. `FINAL_WIZARD_COMPLETION_MATRIX.md`
2. `FINAL_WIZARD_API_PREFIX_MATRIX.md`
3. `FINAL_WIZARD_ROLE_GUARD_MATRIX.md`
4. `FINAL_WIZARD_E2E_PROOF_MATRIX.md`

### Wizard classification required for every wizard route

| Field | Required |
|---|---|
| Path | Yes |
| Component | Yes |
| Name | Yes |
| API prefix | Yes |
| Roles | Yes |
| Release state | Yes |
| Readiness flags | Yes |
| Backend session endpoint | Yes |
| End-to-end test | Yes for production |
| Placeholder classification | Required if not production-ready |

### Wizard production rule

A wizard cannot be production-visible unless:

- route is role guarded,
- release state is ready/live/production,
- readiness flags are all true,
- backend API prefix resolves and is tested,
- save/continue/commit path is tested,
- empty/error/degraded states are handled.

## Role journey closure queue

### Required journey proofs

| Journey | Status | Required proof |
|---|---|---|
| Prospective parent admissions | NOT DONE | Start -> apply -> submit -> status/checklist |
| Parent | NOT DONE | Student, attendance, grades, billing, aid, comms, learning status |
| Student | NOT DONE | Schedule, assignments/learning, grades, service where applicable |
| Teacher | NOT DONE | Attendance, gradebook, comments/comms, lesson plans, online learning |
| Registrar | NOT DONE | Records, enrollment, transcripts, scheduling, documents |
| Finance | NOT DONE | Tuition, billing, payments, reconciliation, reports |
| Aid director | NOT DONE | Aid intake, review, awards, budget, communications |
| Admissions | NOT DONE | Pipeline, review, decision, accepted-to-enrolled |
| School admin/head | NOT DONE | Command center, risk, action queues, module oversight |
| Operations staff | NOT DONE | HR/facilities/health/transport/food/IT/safety workflows |
| Board | NOT DONE | Governance, metrics, packets, risk/compliance |
| Platform ops | NOT DONE | Tenant health, implementation, migration, release reliability |

## Anti-phantom frontend rule

The following are not enough for completion:

- component import exists,
- route path exists,
- registry row exists,
- dashboard title renders,
- wizard shell renders,
- placeholder copy exists,
- mock/sample data exists.

Completion requires proof that the surfaced journey works with the right data, role, API, and state handling.

## First-failure rule

When local frontend evidence is produced, fix only the first failing frontend gate before broadening scope. Do not do broad visual redesign while contract/build/lint gates are failing.

## Required final artifacts

1. `FINAL_ROUTE_GUARD_AUDIT.md`
2. `FINAL_DASHBOARD_KPI_PROVENANCE_MATRIX.md`
3. `FINAL_WIZARD_COMPLETION_MATRIX.md`
4. `FINAL_ROLE_JOURNEY_PROOF_MATRIX.md`
5. `FINAL_FRONTEND_RELEASE_PROOF.md`

## Production scoring lock

Frontend/dashboard/wizard score remains below 95 until every P0 frontend gate passes on the exact release candidate SHA and every production-visible route/dashboard/wizard has proof.
