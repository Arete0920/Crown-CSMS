# ADR-0006: CROWN CRM Relationship Center Domain Boundaries

**Status:** ACCEPTED BY PRODUCT-OWNER DIRECTION; EFFECTIVE ON GOVERNED INDEXED MERGE
**Date:** 2026-10-19
**Repository:** Arete0920/Crown-CSMS
**Inspected accepted-main baseline:** 433aa0b6cb54c3b5a86f50f5f3137c46ebb12940
**Product owner:** CROWN Product Owner
**Approval record:** Owner's October 19, 2026 direction to proceed with the documented CRM architecture and sequenced implementation; formal code, deployment, privacy and operational approvals remain separate. The accepted ADR takes effect only if this exact indexed PR passes applicable checks and is merged.
**Implementation status:** DESIGN ONLY; no schema, application, worker, provider, or deployment change
**Supersedes:** None

> This ADR is submitted for canonical admission in the same governed pull request that adds its accepted-index entry. Until merged, the accepted main index remains unchanged and this branch is only proposed authority. Source inspection is not deployed-runtime certification.

## Context and problem

CROWN already has a Django CRM/Marketing application, MarketingLead, MarketingCampaign, CampaignTouchpoint, public inquiry intake, admissions continuity, an authenticated staff inquiry queue, consent-aware follow-up processing, and campaign/inquiry reporting. It must support a larger school relationship lifecycle without creating competing operational identities or exposing restricted SIS data to marketing users.

Current source anchors:

- [CRM models](../../../backend/crm_marketing/models.py), [inquiry services](../../../backend/crm_marketing/inquiry_services.py), [CRM services](../../../backend/crm_marketing/services.py), and [CRM routes](../../../backend/crm_marketing/api/urls.py).
- [Admissions API contract](../../api/ADMISSIONS_API_CONTRACT.md), [canonical identity ADR](../ADR-001-CANONICAL-HOUSEHOLD-GUARDIAN-STUDENT.md), and [identity convergence ledger](../IDENTITY_MODEL_CONVERGENCE_LEDGER.md).
- [Communications outbox](../../../backend/comms/models.py) and [advancement relationship models](../../../backend/advancement/models_stage3.py).
- [Architecture decision index](../DECISION_INDEX.md) and [current release authority](../../CURRENT_RELEASE_STATUS.md).

## Decision drivers

1. Support inquiries, multiple child interests, follow-up tasks, visits, re-enrollment, alumni and advancement without an externally hosted CRM.
2. Preserve CROWN's accepted Core -> Modules -> Add-ons authority; a CRM 360 view is a projection, not an SIS writer.
3. Prevent tenant contamination, mistaken identity merges, lifecycle regressions, consent failures, and double sends.
4. Reuse Django, DRF, PostgreSQL, React, canonical API transport, CROWN permissions, Celery and the established communications outbox.
5. Deliver the smallest independently testable, reversible increments; do not add chargeable infrastructure merely for CRM.
6. Preserve current public inquiry, application-continuation, marketing, and communications API contracts.

## Proposed decision

### 1. Bounded context and deployment

Extend the existing crm_marketing Django application as the CRM Relationship Center bounded context in the current modular monolith. Retain one PostgreSQL-backed persistence authority, existing CROWN tenant enforcement and DRF transport, and the existing asynchronous communications infrastructure. No separate CRM application server, database, search cluster, external CRM synchronization, or new paid cloud service is authorized by this ADR.

**School CRM** stores school-owned relationship operations. **Arete's sales CRM for selling CROWN to schools** remains a separate business and data authority and must not query school CRM records across tenants.

### 2. Source-of-truth contracts

| Fact | Write authority | CRM access |
| --- | --- | --- |
| Prospect contact/group before verification | CRM | Create/update under school-scoped permission |
| Family/guardian/student operational identity | core.Family / core.Guardian / core.Student | Read via authorized adapter; verified references only |
| Admissions application/decision and confirmed enrollment | applications/admissions canonical services and events | Read and derive; no direct state mutation |
| Tuition, aid, payments, ledger | Respective finance domains | Role-filtered summary only when separately authorized |
| Donor, gifts, pledges, major-gift moves | advancement | Role-filtered references; no parallel donor ledger |
| Message content/outbox delivery status | comms | Request through approved service, project truthful status |
| Relationship tasks, staff interactions, CRM attribution | crm_marketing | Write through CRM services |
| Executive/marketing dashboard | No canonical business facts | Read model/projection only |

The accepted [identity ADR](../ADR-001-CANONICAL-HOUSEHOLD-GUARDIAN-STUDENT.md) takes precedence over older, conflicting historical inventories: current Core writes belong to core.Family, core.Guardian and core.Student; households and crown_api person/household models remain separate compatibility families until explicitly reconciled. No CRM code may bypass the existing identity convergence controls.

### 3. Relationship model and lifecycle

The proposed schema is additive; names below are design candidates and not existing models.

- **ProspectContact:** adult prospect contact identity scoped to a school; may carry more than one verified channel, but never be identified or authorized merely by email.
- **ProspectGroup:** one school-scoped prospect relationship/family group; it is NOT a canonical Core family.
- **ProspectGroupMember:** explicit relationship between an adult prospect contact and a group; permits shared email and nontraditional family structures without overwriting relationships.
- **EnrollmentInterest:** a separate child/grade/academic-year interest or opportunity; initially may be anonymous. It can later reference a verified canonical application and/or student, but not create or own them.
- **VerifiedIdentityLink:** a reviewed CRM prospect-to-Core or advancement reference containing actor, method/evidence reference, linked-at timestamp, status and tenant; no auto-merge by email/name/phone.
- **CRMTask:** durable actionable work with school, relation/opportunity, purpose, owner, due date, priority, state, completion and idempotency key; a scheduled notification is not task completion.
- **CRMConsentEvent:** append-only provenance for permitted purpose, channel, grant/withdrawal, time and source; a legacy inquiry response-consent flag must not be upgraded to broad marketing or SMS consent.
- **CRMInteraction:** later general relationship-centric manual activity. Existing CampaignTouchpoint remains historical/operational truth for current inquiry workflows until a separately reviewed single-writer migration. Never dual-write two supposed canonical interaction histories.
- **CRMRelationshipProjection:** a permission-filtered read-only aggregation, not an operational identity table and not a source for underlying module writes.

**Compatibility requirement:** Preserve MarketingLead, its single application FK, its applications many-to-many link, stages, the public intake receipt, and existing routes until each legacy consumer is inventoried and a distinct expand-contract change proves equivalence. Initially CRM group/interest records may reference an existing MarketingLead; backfills must be idempotent and reversible.

**Opportunity stage:** A child/academic-year opportunity derives its stage from authoritative admissions events; a family overview derives an aggregate. Family status is not a last-child-wins write. If one linked child has confirmed enrollment, a later sibling update must not erase that fact. Additional open interests stay visible independently. An admissions stage must not be inferred from an unverified CRM label.

**Known concurrent corrective work:** Draft PR [#353](https://github.com/Arete0920/Crown-CSMS/pull/353) addresses the existing sibling family-stage regression. This proposal does not duplicate or supersede that patch. Verify its accepted final form before implementing lifecycle changes.

### 4. Tenant and authorization contract

- Derive school scope exclusively from canonical tenant context per ADR-0001; never trust browser-provided school_id or client role.
- Every CRM write, lookup, join, import, export, background job and report must be school-scoped. Reject foreign-school related objects before persistence. A database FK alone does not prove the related object's school matches.
- Use canonical protected frontend transport per ADR-0002 and per-school task context per ADR-0003.
- Separate capabilities: crm.view, crm.manage, crm.assign, crm.export, crm.identity.link, crm.communications.send, and CRM admin configuration. These are proposed codes requiring explicit seed, grants and tests, not automatic aliases of marketing.view or admissions.view.
- Admissions, advancement, finance, student-care, health, spiritual life, discipline, and custody records remain separately permissioned. CRM access never conveys access to their full records.
- No platform-wide school contact search, shared Arete audience export, or unauthorized cross-school matching.
- Audit identity linking/unlinking, merges, exports, task delegation, permission changes, consent events, and external communication requests.

### 5. Consent, communications and privacy

- Capture adult-facing inquiries and minimize prospective-minor data; grade/year interest need not store a child's name.
- Distinguish inquiry response from optional continuing marketing, transactional messages, SMS, and different channels/purposes. Current flags are retained for backward compatibility and are not blanket permissions.
- Existing CROWN_INQUIRY_NOTIFICATIONS_ENABLED remains default false. Neither this ADR nor a schema/UI rollout enables provider dispatch.
- Only comms owns durable provider delivery/outbox state. CRM may display queued, suppressed, retried, provider-accepted and confirmed-delivered states if supported by trustworthy receipts; provider acceptance is not proof of delivery.
- Recheck current consent, channel restrictions, stage, owner authority and tenant immediately before dispatch. Suppress unauthorized stale queued messages with durable audit evidence.
- Establish approved school-specific retention/deletion, correction, access logging, staff assignment, and restricted-note classification policies before broad marketing exports.
- Do not surface confidential student records, health, discipline, pastoral or financial-aid details in broad relationship timelines or marketing segments.

### 6. API and event contract

Retain all existing /api/v1/crm/inquiries/* and /api/v1/crm/campaigns/* behavior. Candidate new protected endpoints, subject to separately accepted API design:

~~~text
GET    /api/v1/crm/relationships/
GET    /api/v1/crm/relationships/{id}/
GET    /api/v1/crm/relationships/{id}/timeline/
GET    /api/v1/crm/tasks/
POST   /api/v1/crm/tasks/
PATCH  /api/v1/crm/tasks/{id}/
POST   /api/v1/crm/identity-links/
GET    /api/v1/crm/opportunities/
~~~

Each list must use bounded server-side pagination, ordering and appropriate rate controls; no bulk unrestricted search. Mutations require authorization, object-school validation, idempotency where retryable, concurrency protection, and an audit trail.

Proposed versioned event vocabulary (not proof of existing event support):

~~~text
crm.inquiry.received.v1
crm.task.created.v1
crm.task.completed.v1
admissions.application.submitted.v1
admissions.enrollment.confirmed.v1
comms.message.status.changed.v1
~~~

Events are published after a committed authoritative transaction, with a durable outbox or an equivalent documented, tested failure-recovery mechanism. Consumers are tenant-bound, idempotent and tolerate duplicates and reordering. No unapproved direct cross-domain table writes.

### 7. Query, concurrency and operational requirements

- Index candidate objects on school_id plus status/owner/due date and stable identifiers. Apply select_for_update and uniqueness guards where duplicate tasks, identity links, or concurrent transitions could be created.
- Use bounded batched reads for family/applications and timelines; avoid one notification/timeline fetch per item in large queues. Establish query-count and PostgreSQL EXPLAIN evidence before claiming a specific performance fix.
- Report family inquiries, child applications and confirmed enrollments with explicitly different units and conversion denominators.
- Keep estimated campaign financial output clearly separate from canonical tuition/aid/ledger actuals.
- Use additive migrations, backfill checkpoints, tenant-by-tenant reconciliation, protected rollback, and no destructive replacement of identity tables.
- Release proof requires exact-head CI, tenant negatives, migrations in PostgreSQL, relevant browser/API tests, deployment identity, and runtime evidence where claimed.

## Options considered

1. **Standalone third-party CRM / new microservice:** Rejected for the initial release due to duplicate identities, synchronization complexity, tenant trust boundaries, ongoing infrastructure expense and uncertain deployment operations.
2. **Expand core.Family / Student into a CRM store:** Rejected: prospects and marketing activities are not SIS identity truth; broad CRM writes would increase privacy and migration risk.
3. **Create another donor/advancement CRM:** Rejected: advancement already owns donor, Relationship, Prospect and Move records.
4. **Incrementally extend crm_marketing (preferred):** Reuses the accepted inquiry flow while introducing explicit prospect, task and relationship boundaries and read-only adapters to canonical domains.

## Consequences

Benefits: unified admissions/relationship experience, clearer ownership, fewer new dependencies, cheaper infrastructure and safer incremental release.

Costs: temporary compatibility adapters; provenance-aware linking; careful tenant-by-tenant reconciliation; multiple scoped permissions; additional tests; and eventual explicit decisions about historical CampaignTouchpoint versus future CRMInteraction write authority.

## Decision and acceptance dependencies

1. Admit this owner-directed ADR through the governed PR and same-commit accepted-index update. Before merge it is not canonical main authority.
2. Complete the detailed [Phase-0 gap and delivery specification](../../product/CROWN_CRM_RELATIONSHIP_CENTER_PHASE0_20261019.md).
3. Validate or disposition draft PR #353 independently; do not conflate correction with new CRM feature PRs.
4. Approve contact/group identity linkage and consent purposes before any additive migration or live send.
5. Require evidence and rollback design for each numbered implementation slice.

## Verification and rollback rule

This is a documentation-only architecture decision; no migrations, queues, notifications, integrations, production resources or tenant data have changed. If rejected, close/revert the design PR without operational rollback. Acceptance of these domain boundaries is not approval of any unverified code, migration, outbound communication, paid service, deployment, or live operating posture. ADR authority begins only after the reviewed, indexed PR merges with the applicable protected checks passing.
