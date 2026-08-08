# Admissions and Enrollment Authority

**Status:** Current handoff authority  
**Verified source baseline:** `9090aa2463baf1e3afcfe3590da8e250c6e12d35`  
**Authority date:** 2026-08-08

## Purpose

This record removes ambiguity between CROWN's canonical admissions/enrollment workflow and retained compatibility domains. It does not authorize destructive model convergence or compatibility-table removal.

## Canonical workflow authority

The canonical public admissions workflow is the UUID-based `applications` domain:

- `applications.Application`
- `applications.Applicant`
- `applications.ApplicationEvent`
- `applications.ApplicationChecklistItem`
- `applications.ApplicationChecklistDocument`
- `applications.EnrollmentContract`
- `applications.views_admissions`

`crown_api.admissions_runtime.admissions_summary` is a provenance wrapper around `applications.views_admissions.admissions_summary`; it is not a second behavior implementation.

Canonical public routes are under `/api/v1/admissions/*`. `/api/*` is an intentional compatibility alias of the same API tree.

## Identity write authority

Per the accepted canonical identity architecture:

- `core.Family` is the canonical family write record.
- `core.Guardian` is the canonical guardian write record.
- `core.Student` is the canonical student write record.
- `households.*` is a compatibility/read domain.
- `crown_api` person/household/student models are compatibility records.

Admissions may bridge these domains, but compatibility records do not supersede canonical core identity authority.

## Legacy admissions compatibility domain

`admissions.AdmissionsApplication`, `AdmissionsReview`, `AdmissionsDecision`, and `AdmissionsAuditEvent` remain active compatibility records for legacy director/linkage/enrollment surfaces and canonical-to-legacy bridging.

They are not the canonical public intake or contract/deposit authority.

Compatibility routes include the legacy admissions subtree such as `/api/admissions/applications/` and `/api/admissions/enroll/`.

## Lifecycle vocabulary

The following concepts are distinct and must not be treated as interchangeable:

### Canonical application record status

Stored on `applications.Application`:

- `DRAFT`
- `SUBMITTED`
- `IN_REVIEW`
- `DECIDED`

### Canonical funnel stage

Computed from application status plus `ApplicationEvent` history:

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

This computed stage is the admissions-funnel reporting authority.

### Canonical post-acceptance enrollment state

Enrollment readiness is event/contract based and includes:

- contract state: `not_started -> sent -> signed -> countersigned`
- deposit state: `pending -> invoiced -> paid` or `waived`
- enrollment confirmation event
- classroom readiness event
- parent portal activation event

Enrollment confirmation requires a **countersigned contract** and a **paid or waived deposit**. Classroom readiness and parent-portal activation require enrollment confirmation.

### Legacy compatibility status

Stored on `admissions.AdmissionsApplication`:

- `DRAFT`
- `SUBMITTED`
- `UNDER_REVIEW`
- `NEEDS_INFO`
- `ACCEPTED`
- `WAITLISTED`
- `DENIED`
- `WITHDRAWN`
- `ENROLLED`

Legacy external transitions must use the guarded admissions service. `WAITLISTED -> ENROLLED` is not legal; waitlisted applications must first reach `ACCEPTED`.

## Enrollment conversion authority

The canonical UUID workflow owns contract/deposit readiness and enrollment confirmation. Once canonical enrollment is confirmed, it bridges the appropriate result into the legacy admissions domain.

Legacy single-record or batch conversion surfaces must not invent separate contract/deposit rules. They must:

1. remain tenant scoped;
2. require tenant-scoped admissions edit authority (or explicit administrative override);
3. enforce the legacy transition graph;
4. write the admissions audit event;
5. activate the linked compatibility SIS student when present;
6. remain idempotent;
7. fail closed when the selected record changed state before commit.

## API response authority

For `/api/v1/admissions/drilldown/`:

- `results` is canonical for new consumers.
- `rows` remains a supported compatibility alias until separately versioned retirement is proven safe.

The expired June 1, 2026 removal date is superseded.

## Non-goals for handoff repair

This authority does not:

- delete or rename compatibility tables;
- silently remap IDs;
- collapse the canonical and legacy application models;
- infer a contract/deposit relation where no verified foreign-key authority exists;
- authorize production or payment-provider activation.

## Required certification evidence

Final admissions/enrollment certification should prove:

1. public submission persists one canonical application without replay duplication;
2. tenant and RBAC boundaries fail closed;
3. checklist/document lifecycle remains scoped to the application;
4. accepted-state contract and deposit transitions are valid and audited/event-backed;
5. enrollment confirmation is blocked until contract/deposit prerequisites pass;
6. canonical enrollment bridges to legacy status without illegal stage jumps;
7. legacy conversion is guarded, audited, idempotent, and tenant scoped;
8. selected-cohort verification cannot be satisfied by unrelated enrolled records;
9. canonical identity authority is preserved without duplicate uncontrolled writers;
10. exact-head CI is green before merge.
