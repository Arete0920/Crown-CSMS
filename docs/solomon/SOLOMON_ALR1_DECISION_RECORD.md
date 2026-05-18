# SOLOMON ALR-1 Decision Record

Status: ARCHITECTURE LOCK REVIEW
Phase: Pre-Phase 2
Implementation: NOT STARTED
Decision Date: 2024-05-22 10:00:00

## Objective

Lock foundational SOLOMON architecture decisions before persistent models, migrations, or live integrations are introduced.

## Section 1 - Boundary Lock

Decision: PASS

Locked boundary:

- CROWN executes workflows.
- SOLOMON governs institutional intelligence, resources, knowledge, curriculum/resource metadata, governance references, and contextual delivery.
- Microsoft provides identity, collaboration, productivity, and document infrastructure.
- Governance controls all canonical content and integration behavior.

## Section 2 - Canonical Naming Lock

Decision: PASS

Approved initial Phase 2 model naming:

- SolomonCategory
- SolomonTopic
- SolomonAudience
- SolomonResource
- SolomonPlaybook
- SolomonContextRule
- SolomonResourceVersion

Deferred model names:

- SolomonPublisher
- SolomonCurriculumCourse
- SolomonCurriculumUnit
- SolomonCurriculumLesson
- SolomonScriptureReference
- SolomonDevotionalResource

Deferred models are not approved for Phase 2 implementation.

## Section 3 - Governance Lifecycle Lock

Decision: PASS

Required governance metadata:

- status
- owner
- approver
- review_date
- version
- visibility
- license_type
- publisher
- school_scope
- created_at
- updated_at

Approved lifecycle states:

- draft
- approved
- published
- archived

Rules:

- No unapproved canonical content.
- No publisher content ingestion without rights.
- No cross-tenant resource exposure.
- No spiritual-life content without review and approval.
- No production module may rely on draft SOLOMON content.

## Section 4 - Tenant Scope Lock

Decision: PASS

Approved scope model:

- global
- organization
- school
- role
- audience

Tenant rules:

- SOLOMON resources must fail closed by default.
- School-specific content must not leak across tenants.
- Global canonical resources must be explicitly marked global.
- Future resource access must support role and audience filtering.
- Any live integration must preserve existing CROWN tenant-isolation behavior.

## Section 5 - Microsoft Boundary Lock

Decision: PASS

Locked separation:

- Microsoft Entra owns identity.
- Microsoft Teams owns collaboration.
- SharePoint and OneDrive own document storage.
- Outlook and Calendar own productivity communication.
- SOLOMON owns metadata, governance, institutional intelligence, contextual resource organization, and canonical content rules.

SOLOMON must not duplicate Microsoft 365 document-editing or collaboration functions.

## Section 6 - Read-Only Integration Lock

Decision: PASS

Approved early integration philosophy:

- Read-only first.
- Feature-flagged first.
- No write APIs in the first implementation pass.
- No live production module dependency during Phase 2.
- No migrations touching existing onboarding tables.
- No removal of existing onboarding SOLOMON-like models until migration proof exists.
- No AI functionality.

Feature flag requirement:

SOLOMON_ENABLED = False by default

## Section 7 - Phase 2 Approval Decision

Decision: APPROVED WITH LIMITS

Phase 2 may proceed only with:

- additive models inside backend/solomon
- no live module wiring
- no root URL integration
- no production behavior change
- no curriculum/scripture/devotional/publisher models yet
- no AI
- no Microsoft sync
- no data migration from onboarding
- no removal or modification of existing onboarding models

## Phase 2 Scope

Approved Phase 2 implementation may include only:

- SolomonCategory
- SolomonTopic
- SolomonAudience
- SolomonResource
- SolomonResourceVersion
- SolomonPlaybook
- SolomonContextRule

Approved model purpose:

- establish canonical knowledge/resource structure
- establish governance lifecycle
- establish role/audience/visibility metadata
- establish future contextual delivery structure

## Phase 2 Required Proof

Before Phase 2 is considered complete:

- Django check passes
- Solomon tests pass
- migrations are additive only
- no existing onboarding migrations modified
- no production module wiring added
- no release-gate files modified
- no Docker/deployment files modified
- git diff confirms allowed file boundaries only

## Final ALR-1 Decision

ALR-1 PASSED.

Phase 2 core knowledge models are approved to begin under the limits above.
