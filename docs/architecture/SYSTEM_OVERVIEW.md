# CROWN System Architecture Overview

**Status:** CANONICAL SUPPORTING OVERVIEW  
**Owner:** CROWN Engineering  
**Effective date:** 2026-08-08

## Interpretation

This document summarizes repository-visible implementation and architectural convergence status. It does not redefine the certified production identity and does not override `docs/CURRENT_RELEASE_STATUS.md` or GitHub issue #1619.

Evidence labels:

- **Verified in source** — directly represented by repository code or configuration.
- **Accepted decision** — approved architecture authority listed in `DECISION_INDEX.md`.
- **Implementation convergence open** — accepted direction exists, but migration or retirement work remains.
- **Externally evidenced separately** — operational proof is governed by release/handoff evidence rather than inferred from source.

## Core stack

| Layer | Repository-visible technology | Status |
|---|---|---|
| Backend | Django and Django REST Framework | Verified in source |
| Frontend | React, Vite, and MUI | Verified in source |
| Primary persistence | PostgreSQL through `DATABASE_URL` | Verified in source |
| Development/test persistence | SQLite-supported paths | Verified in source |
| Background work | Celery and Redis configuration | Verified in source; active task paths are subject to ADR-0003 |
| Monitoring | Optional Sentry integration | Verified in source; live provider state governed separately |
| Hosting target | Azure App Service | Verified in workflow source; certified release deployment evidence governed by #1619 |
| Container registry target | Azure Container Registry | Verified in workflow source; live operational ownership governed separately |
| Secret authority | External environment/secret-store controls | Source references verified; live inventory/rotation governed separately |

## Runtime request path

```text
Browser or authorized client
  -> React frontend
  -> ADR-0002 canonical protected transport
  -> HTTPS versioned API request
  -> principal authentication
  -> ADR-0001 canonical tenant resolution and authorization
  -> RBAC and domain permission enforcement
  -> domain service and transaction
  -> school-scoped persistence
  -> audit and external integration boundaries
  -> normalized API response
```

The browser is untrusted. Client-provided tenant, role, object, financial, workflow, and state claims require backend validation. Client-supplied role headers are not authorization authority.

## Multi-tenant architecture

### Accepted request-time decision

`decisions/ADR-0001-tenant-resolution-and-enforcement.md` defines the canonical request tenant contract:

- one immutable tenant context at `request.crown_tenant`;
- `request.school_id` and `request.school` as compatibility projections;
- authentication before tenant authorization;
- explicit authorization for cross-school override;
- fail-closed behavior for missing, invalid, inactive, unknown, or unauthorized school context;
- no new tenant request attributes.

### Accepted background-execution decision

`decisions/ADR-0003-tenant-aware-background-jobs.md` defines tenant ownership outside HTTP requests:

- tenant-owned mutation executes under one explicit school/tenant identity;
- platform orchestrators may enumerate active schools but execute each tenant operation separately;
- `tenant_context(school)` is established and restored for tenant-owned scheduled work;
- payment-dependent scheduled jobs do not mutate while external payment processing is deferred;
- retries are bounded and must respect idempotency and failure-containment rules.

### Verified source behavior

- tenant-header resolution and validation exist for protected API paths;
- school context can be attached to requests;
- permission utilities scope authorization to the resolved school;
- dashboard tests cover missing, invalid, unknown, matching, and conflicting tenant cases;
- request cleanup clears compatibility context after processing;
- communications outbox tenant binding is explicit;
- final architecture hardening makes billing grace, support escalation, customer-health refresh, and predictive analytics tenant-explicit;
- provider-dependent dunning and payout scheduled tasks return the canonical payment hold without mutation.

### Implementation convergence open

Current settings still register multiple tenant-related middleware layers:

1. `core.middleware.TenantIsolationMiddleware`;
2. `core.tenant_header_middleware.TenantHeaderRequiredMiddleware`;
3. `crown_api.tenant_middleware.TenantContextMiddleware`.

The accepted contract is authoritative. Redundant middleware must not be removed until complete consumer inventory and behavioral-equivalence evidence exist.

## Identity and household architecture

### Accepted decision

`ADR-001-CANONICAL-HOUSEHOLD-GUARDIAN-STUDENT.md` establishes:

- `core.Family` as the canonical operational family record;
- `core.Guardian` as the canonical operational guardian record;
- `core.Student` as the canonical operational student record;
- school-scoped, transactional, fail-closed writes;
- no silent copying, merging, reassignment, or identifier remapping between identity domains.

### Compatibility domains

The following remain active compatibility or read domains:

- `households.Household`, `households.Guardian`, and `households.Student`;
- `crown_api` person, household, membership, and student models;
- admissions compatibility references and `core.HouseholdFamilyLink`;
- guardian-household wizard session payloads as workflow state rather than identity authority.

Compatibility convergence remains open. Retirement requires a complete consumer graph, deterministic mapping, tenant-by-tenant reconciliation, expand-contract migration rehearsal, integrity counts, rollback or forward-fix design, and exact-commit approval.

## Domain architecture

| Domain | Principal areas | Responsibility |
|---|---|---|
| Platform identity and tenancy | `core`, authentication, permissions, tenant middleware | Schools, users, roles, canonical family/guardian/student identity, tenant security boundary |
| Admissions and enrollment | `admissions`, `applications`, enrollment-related code | Inquiry, application, acceptance, enrollment handoff, compatibility bridges |
| Finance | `ledger`, `billing`, `financial_aid`, `aid` | Charges, balances, allocations, payment records, plans, aid applications and awards |
| Academics | `academics`, `gradebook`, `curricula` | Courses, sections, curriculum, grading, academic records |
| Student operations | attendance, discipline, health, transportation, service-hours and related apps | School-scoped operational workflows and records |
| Communications and support | `comms`, `support` | Messaging, delivery boundaries, tickets, escalation |
| Governance and analytics | `board_oversight`, `executive360`, `analytics` | Board, executive, health, metric, export, and reporting surfaces |
| Frontend platform | `frontend/dashboards` | Shared shell, routes, persona surfaces, components, state, ADR-0002 transport, accessibility |
| Operations | workflows, deployment configuration, `docs/operations` | Build, test, deploy, monitor, recover, rotate, and maintain |

App registration demonstrates structure, not independent proof of completeness, tenant safety, or production enablement.

## Frontend transport architecture

### Accepted decision

`decisions/ADR-0002-canonical-frontend-api-transport.md` establishes `frontend/dashboards/src/utils/authClient.js` as the protected first-party API transport authority.

It owns:

- API-base resolution;
- trusted first-party URL determination;
- access-token propagation;
- selected-school `X-School-Id` propagation;
- credentials;
- timeout and cancellation;
- correlation behavior;
- structured HTTP failure handling;
- protection against leaking CROWN auth/tenant context to untrusted external origins.

Shared wrappers already converge on this transport. Final architecture hardening migrates verified protected consumers including Board Executive data, Learning Continuity, and shared CROWN dashboard metrics.

Direct browser fetch remains permitted only for explicit authentication/bootstrap, public sandbox/public-entry, external-origin, development-only, and test/certification cases whose semantics are outside the authenticated school-operational transport contract.

### Provenance rule

A dashboard aggregate may be labeled live only when all data required by that live contract is live. Partial live results must not be merged with demo/fixture data and presented as one live aggregate. Board Executive now follows this all-or-nothing rule.

## API architecture

- `/api/v1/` is the principal versioned API namespace visible in source.
- API version and deprecation middleware are represented in source.
- Public endpoint and CSRF exceptions require explicit policy and review.
- Serializers and views are transport adapters; durable business rules should reside in domain services and transactional boundaries where implemented.
- Tenant identity and role authorization are backend responsibilities regardless of frontend route or header behavior.

## Asynchronous architecture

ADR-0003 is the accepted background-execution contract.

Verified aligned paths include:

- communications outbox tenant binding with bounded retry/dead-letter behavior;
- billing grace-period enforcement by active school under tenant context;
- support SLA escalation by active school under tenant context;
- customer-health refresh by active school under tenant context;
- predictive analytics queue fan-out by school plus tenant-context execution;
- retention purge preview by default with separate execution/confirmation safeguards;
- payment dunning and daily payout scheduled jobs fail closed/no mutation while payment integration is on hold.

Remaining background tasks and management commands must be inventoried against the same contract before material changes. Unscoped tenant mutation is prohibited.

## External integrations

### Microsoft

Microsoft Entra authentication and Microsoft Graph paths are represented in source. Tenant registration, consent, credentials, mailbox licensing, ownership, and live delivery are operational facts governed outside source documentation.

### Payments

No external payment processor is approved or active for the certified release. Payment processing is disabled and fail closed and provider selection/implementation is deferred to the new owner. Provider-specific activation requires a separate accepted architecture decision and provider-specific certification.

### Cloud, email, storage, and monitoring

These systems are adapters outside the application source-of-truth boundary. Each requires verified ownership, credentials, permissions, retention, failure handling, and operational monitoring before authorized use.

## Deployment architecture

### Verified in workflow source

- tag-triggered production deployment paths exist;
- deployment images can be SHA-tagged;
- Azure authentication includes OIDC and legacy service-principal support;
- preflight, test, image scan, health, database-status, integrity, and release-identity checks are represented;
- workflow, image, and runtime SHA comparison paths exist;
- allowlisted application-setting behavior and migration execution controls are represented.

### Certified-release evidence boundary

The exact certified production release, deployment run, health, identity, bounded RBAC/tenant proof, and payment containment are governed by `docs/CURRENT_RELEASE_STATUS.md` and #1619. Later development `main` commits do not inherit that certification automatically.

### Deferred operational maturity

Measured rollback/isolated-restore exercises, exhaustive credential rotation/break-glass, expanded alert/tabletop exercises, and transaction-specific ownership transfer remain separately disclosed maturity or successor work unless later executed and accepted.

A rollback-named workflow step is not equivalent to a measured application rollback and isolated database restore.

## Architectural priorities for a successor

1. Preserve ADR-0001 tenant authority and retire compatibility middleware only after equivalence proof.
2. Preserve ADR-0002 as the one protected frontend transport authority; keep public/bootstrap exceptions explicit.
3. Preserve ADR-0003 tenant-explicit background execution and payment hold.
4. Complete identity compatibility convergence planning and rehearsal before retirement of legacy identity domains.
5. Maintain a current domain ownership and dependency map before consolidating overlapping apps.
6. Create the remaining ADRs in `DECISION_INDEX.md` before material changes to integration, deployment/recovery, reporting, storage, or payment-provider boundaries.
7. Keep exact certified-production identity separate from development `main` until a later release is independently selected, deployed, and certified.

## Release posture

The certified production release remains the immutable identity recorded in `docs/CURRENT_RELEASE_STATUS.md` and #1619 and is **PASS / COMPLETE for its bounded supported scope**.

Development `main` has advanced beyond that certified source. The final architecture-hardening branch is development work and is **not automatically production-certified** until it passes its own review and, if selected for production, the applicable exact-source release/deployment/certification process.
