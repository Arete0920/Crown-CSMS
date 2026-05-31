# CROWN Final 95+ Backend/API Completion Queue - 2026-05-30

Status: ACTIVE FINAL-SPRINT CONTROL ARTIFACT
Authority: Non-shipping execution queue until promoted by `docs/CURRENT_RELEASE_STATUS.md`.

## Purpose

This queue defines the backend/API closure path required to move CROWN toward 95+ production readiness without guessing, deferring, or hiding incomplete surfaces.

No backend area can score 95+ until its API, tenant scope, RBAC/object permission, data integrity, tests, and evidence are complete.

## Backend/API closure standard

Every production backend surface must prove:

1. Canonical URL path.
2. Serializer/schema coverage where applicable.
3. Tenant isolation.
4. Role permission coverage.
5. Object-level authorization.
6. Input validation.
7. Error envelope consistency.
8. Audit/event logging for sensitive operations.
9. Idempotency for mutating financial/admissions/enrollment flows.
10. Tests proving positive and negative behavior.

## P0 backend/API gates

| Gate | Status | Required evidence |
|---|---|---|
| `python backend/manage.py check` | NOT VERIFIED on latest connector commits | VS Code evidence output |
| `python backend/manage.py makemigrations --check --dry-run` | NOT VERIFIED on latest connector commits | VS Code evidence output |
| `python backend/manage.py check --deploy` | NOT VERIFIED on latest connector commits | VS Code evidence output |
| Tenant isolation suite | NOT VERIFIED on latest connector commits | VS Code evidence output |
| Admissions endpoint suite | NOT VERIFIED on latest connector commits | VS Code evidence output |
| Aftercare suite | NOT VERIFIED on latest connector commits | VS Code evidence output |
| Later-tier metrics suite | NOT VERIFIED on latest connector commits | VS Code evidence output |
| Protected-spine packet | NOT DONE | Full current candidate packet |
| Deploy parity packet | NOT DONE | Current candidate deploy proof |

## Backend/API module queue

### 1. Identity / RBAC / Tenant

Status: NOT DONE

Required closure:

- Reconcile backend role codes with frontend role aliases.
- Prove tenant header behavior for every sensitive module.
- Prove object permission behavior for student, household, finance, aid, admissions, gradebook, attendance, and communications objects.
- Confirm audit logging for sensitive read/write surfaces.

Required tests:

- positive same-tenant access,
- cross-tenant denial,
- missing tenant denial,
- role denial,
- object-level denial,
- super/admin permitted path where appropriate.

### 2. Core SIS / Student Records

Status: NOT DONE

Required closure:

- Student/family/guardian/household CRUD/read APIs.
- Parent scoping and staff scoping.
- Record change audit trail.
- Transcript/report/export guard coverage.
- Data import/migration reconciliation.

### 3. Admissions

Status: PARTIAL / NOT DONE

Required closure:

- Public config, submit, summary, drilldown, timeline, priority queue, metrics route proof.
- Submission validation proof.
- Rate limit/idempotency proof.
- Checklist creation proof.
- CRM hook degraded-path proof.
- Finance fee/waiver handoff proof.
- Staff review and decision proof.

### 4. Enrollment / Re-enrollment

Status: NOT DONE

Required closure:

- Accepted-to-enrolled state transitions.
- Contract issue/sign/countersign/amend proof.
- Deposit paid/waived proof.
- Classroom readiness proof.
- Parent portal activation proof.
- Regression tests for invalid transition denial.

### 5. Billing / Tuition / Payments / Ledger

Status: NOT DONE

Required closure:

- Tuition plan setup.
- Fee schedule setup.
- Obligations/invoices/statements.
- Payment intent/provider handoff.
- Reconciliation and exceptions.
- Ledger immutability/reversal proof.
- Parent billing view and finance staff view.
- Tenant/RBAC/object proof.

### 6. Financial Aid

Status: NOT DONE

Required closure:

- Application intake.
- Review/award decision.
- Budget tracking.
- Award letter status.
- Contract/billing sync.
- Family affordability risk signals.
- Tenant/RBAC/object proof.

### 7. Academic operations

Status: NOT DONE

Modules:

- Attendance.
- Gradebook.
- Scheduling.
- Curriculum.
- Lesson plans.
- Scope and sequence.
- LMS/learning continuity.

Required closure:

- Teacher flows.
- Parent/student visibility.
- Admin exceptions.
- Reporting/export.
- Tenant/RBAC proof.

### 8. Operations modules

Status: NOT DONE

Modules:

- HR.
- Facilities.
- Health office.
- Transportation.
- Food service.
- IT support.
- Safety/security.
- Fine arts.
- Library/media.
- Extended care.
- Summer camp.
- Spiritual life/service hours.
- Advancement/alumni.
- Board/governance.
- Platform operations.

Required closure:

- API surface classified as production, compatibility, placeholder, or hidden.
- Module-specific tests.
- Dashboard metrics route proof where surfaced.
- Tenant/RBAC/object proof.

## First-failure rule

When local evidence is produced, fix only the first failing backend/API gate before broadening scope. Do not make multiple speculative backend edits without proof.

## Required final artifacts

1. `FINAL_API_CONTRACT_AUDIT.md`
2. `FINAL_ROLE_PERMISSION_MATRIX.md`
3. `FINAL_BACKEND_PROTECTED_SPINE_PACKET.md`
4. `FINAL_MODULE_API_ACCEPTANCE_MATRIX.md`
5. `FINAL_DEPLOY_PARITY_PACKET.md`

## Production scoring lock

Backend/API score remains below 95 until all P0 gates pass on the exact release candidate SHA and every surfaced module row has current proof.
