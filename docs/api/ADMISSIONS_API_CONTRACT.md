# Admissions and Enrollment API Contract

**Version:** 1.2.0
**Status:** CURRENT AUTHORITY
**Historical baseline verified:** 2026-08-08
**Historical source baseline:** `9090aa2463baf1e3afcfe3590da8e250c6e12d35`

The inquiry extensions are covered by `backend/crm_marketing/tests/test_inquiry_capture.py`
and the current change's validation evidence. Repository checks do not establish
deployed behavior.

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

### Family inquiry capture and continuity

`POST /api/v1/crm/inquiries/` records a family inquiry before an application or
household exists. Its school is resolved from an explicit school UUID, or an
unambiguous active school name in `campus`; contradictory tenant inputs fail.
An `Idempotency-Key` of 16–128 URL-safe characters is required. Clients generate
a random key once per submission and retain it across retries. Reusing the key
with different normalized content is rejected.

Required fields are `parent_name`, `email`, `grade_interest`, `entry_year`,
and `response_consent: true`. `campus` defaults to the resolved school name
when an explicit school UUID is provided; otherwise it must name the school
unambiguously. Optional fields include `phone`,
`school_id`, `request_type` (`info`, `tour`, `open_house`), `contact_preference`
(`email`, `phone`, `sms`), `follow_up_consent`, `source`, `referral_type`,
`referral_detail`, `campaign_id`, and the allowlisted `utm` attribution object.
A phone number is required for phone/SMS contact. SMS requires international
E.164 format, including the country code. Campaigns must be active and
belong to the same school. The honeypot `website` must be empty. Requests have
bounded text/body sizes and per-school IP/contact rate limits.

The response contains `inquiry_id`, `school_id`, `school_name`, `stage`,
`continuation_token`, `expires_at`, and next-step guidance. The token is a signed,
school/inquiry-bound capability with a 30-day expiry; do not log it, put it in a
URL, or expose it in staff list responses. An email match alone never grants
access to an existing inquiry. Possible duplicate contacts are visible only to
authorized staff in the same school.

`POST /api/v1/crm/inquiries/<uuid:inquiry_id>/start/`, with school context and
`continuation_token`, records the actual application-start milestone once.
The later `/api/v1/admissions/submit/` request includes `inquiry_id` and
`continuation_token`. Submission locks the inquiry, creates one household and
each child's application, preserves the original source and capture/start
timestamps, and links all applications to that inquiry. A valid capability
retry returns the stored receipt without creating another household or set of
applications. Invalid, mismatched, or expired capabilities never silently fall
back to a new unlinked application. Direct applications without inquiry fields
retain their existing submission path.

`GET /api/v1/crm/inquiries/` requires `admissions.view`. It returns scoped
inquiries, eligible owners, contact history, duplicate candidates, and edit
authority. The queue defaults to active pre-application inquiries. `stage=all`
includes history; exact `stage`, `unassigned=1`, and `overdue=1` filters are
supported. `overdue=1` always excludes submitted/closed inquiries. `count`
reports matching inquiries; up to 100 are returned per request.
`PATCH /api/v1/crm/inquiries/<uuid:inquiry_id>/` requires `admissions.edit` and
supports owner, follow-up time, pre-application stage, contact-history entries,
and enabling/disabling family reminders where the family has consented.
Staff can record a family withdrawal with `follow_up_consent: false`; this also
disables family reminders. This endpoint cannot grant or restore family consent,
and a simultaneous request to withdraw consent and enable reminders is rejected.
Ownership is restricted to active staff with admissions authority in that
school. Application decisions and enrollment remain controlled by admissions.

### Inquiry follow-up

Inquiry acknowledgments and owner notices use the shared communications outbox.
The existing Celery schedule invokes
`crm_marketing.tasks.process_inquiry_followups` every 15 minutes. It records
due staff work and the latest due day-1/day-3/day-7 reminder without sending a
backlog burst. Family reminders require recorded optional follow-up consent;
personal phone requests remain staff work. Delivery rechecks current consent,
ownership, and inquiry progression. Submitted or closed inquiries stop the
inquiry reminder sequence. Restored provider configuration can recover an
unqueued acknowledgment for an active inquiry no older than 24 hours; later
family reminders wait at least 24 hours after that acknowledgment is queued.
Queuing or provider acceptance is not confirmed
delivery and does not mark a staff task complete.

Email requires the existing verified Graph sender/credentials; SMS requires
the existing enabled provider. Missing configuration and unassigned owners
remain visible in the queue. A school-specific Teams destination is not
configured by this feature. Runtime acceptance must verify worker/Beat
execution and provider delivery in the intended school environment.

### Summary

`GET /api/v1/admissions/summary/`

Requires `admissions.view` and returns school-scoped admissions pipeline, conversion, velocity, stage-aging, source, workflow-engine, post-admission rollup, and command-intelligence data.

The command-intelligence payload is additive and derived from existing admissions truth plus the latest auditable enrollment-forecast and retention-support model runs when available. It includes a concise action queue for stale applications, accepted-to-enrolled follow-up, active inquiries, and current source context. Retention output is presented as a proactive support indicator, not as a prediction of an individual family's decision.

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
