# CROWN System Architecture Overview

**Status:** CANONICAL SUPPORTING OVERVIEW  
**Owner:** CROWN Engineering  
**Effective date:** 2026-07-28

## Interpretation

This document summarizes repository-visible implementation and architectural convergence status. It does not certify production readiness and does not override `docs/CURRENT_RELEASE_STATUS.md`.

Evidence labels:

- **Verified in source** — directly represented by current repository code or configuration.
- **Accepted decision** — approved architecture authority listed in `DECISION_INDEX.md`.
- **Implementation convergence open** — accepted direction exists, but migration or retirement work remains.
- **Unverified externally** — depends on GitHub, Azure, provider, identity, contract, or live runtime state outside the repository.

## Core stack

| Layer | Repository-visible technology | Status |
|---|---|---|
| Backend | Django and Django REST Framework | Verified in source |
| Frontend | React, Vite, and MUI | Verified in source |
| Primary persistence | PostgreSQL through `DATABASE_URL` | Verified in source |
| Development/test persistence | SQLite-supported paths | Verified in source |
| Background work | Celery and Redis configuration | Verified in source; deployed operation unverified externally |
| Monitoring | Optional Sentry integration | Verified in source; provider state unverified externally |
| Hosting target | Azure App Service | Verified in workflow source; live state unverified externally |
| Container registry target | Azure Container Registry | Verified in workflow source; live RBAC unverified externally |
| Secret authority | Approved external secret manager such as Azure Key Vault | Target and operational requirement; live retrieval and rotation unverified externally |

## Runtime request path

```text
Browser or authorized client
  -> React frontend
  -> HTTPS versioned API request
  -> principal authentication
  -> canonical tenant resolution and authorization
  -> RBAC and domain permission enforcement
  -> domain service and transaction
  -> school-scoped persistence
  -> audit and external integration boundaries
  -> normalized API response
```

The browser is untrusted. Client-provided tenant, role, object, financial, workflow, and state claims require backend validation.

## Multi-tenant architecture

### Accepted decision

`decisions/ADR-0001-tenant-resolution-and-enforcement.md` defines the canonical tenant contract:

- one immutable tenant context at `request.crown_tenant`;
- `request.school_id` and `request.school` as compatibility projections;
- authentication before tenant authorization;
- explicit authorization for any cross-school override;
- fail-closed behavior for missing, invalid, inactive, unknown, or unauthorized school context;
- explicit tenant binding and cleanup for asynchronous work;
- no new tenant request attributes.

### Verified source behavior

- tenant-header resolution and validation exist for protected API paths;
- school context can be attached to requests;
- permission utilities can scope authorization to the resolved school;
- tested dashboard endpoints cover missing, invalid, unknown, matching, and conflicting tenant cases;
- request cleanup clears compatibility context after processing.

### Implementation convergence open

Current settings still register multiple tenant-related middleware layers:

1. `core.middleware.TenantIsolationMiddleware`;
2. `core.tenant_header_middleware.TenantHeaderRequiredMiddleware`;
3. `crown_api.tenant_middleware.TenantContextMiddleware`.

The accepted contract is authoritative, but permissions, querysets, tasks, scripts, exemption lists, and compatibility attributes have not been proven fully migrated. Redundant middleware must not be removed until consumer inventory and behavioral-equivalence evidence exist.

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
| Frontend platform | `frontend/dashboards` | Shared shell, routes, persona surfaces, components, state, transport, accessibility |
| Operations | workflows, deployment configuration, `docs/operations` | Build, test, deploy, monitor, recover, rotate, and maintain |

App registration demonstrates structure, not independent proof of completeness, tenant safety, or production enablement.

## Frontend transport architecture

More than one frontend request implementation currently resolves API location, authentication, tenant state, cookies, timeout behavior, and errors. No accepted frontend transport ADR is listed in `DECISION_INDEX.md`.

Required target characteristics include:

- one canonical request entry point;
- normalized API base URL handling;
- one authentication and cookie policy;
- canonical tenant-header propagation;
- consistent timeout, cancellation, retry, and idempotency behavior;
- normalized error and permission handling;
- explicit public-route exceptions;
- testable request metadata and observability.

Until an ADR is accepted and implemented, the repository must not claim universal use of one client.

## API architecture

- `/api/v1/` is the principal versioned API namespace visible in source.
- API version and deprecation middleware are represented in source.
- Public endpoint and CSRF exceptions require explicit policy and review.
- External support windows and partner commitments require separate release and contract authority.
- Serializers and views are transport adapters; durable business rules should reside in domain services and transactional boundaries where implemented.

## Asynchronous architecture

Celery and Redis configuration exist, but a complete task ownership and tenant-propagation inventory is not established by this overview.

Every active task path must eventually demonstrate:

- explicit serialized tenant identity;
- principal or service identity where required;
- idempotency or duplicate-delivery handling;
- bounded retries and poison-message behavior;
- context establishment and cleanup;
- audit and observability fields;
- no cross-tenant data access after retry or exception.

## External integrations

### Microsoft

Microsoft Entra authentication and Microsoft Graph paths are represented in source. Tenant registration, consent, credentials, mailbox licensing, ownership, and live delivery are unverified externally.

### Payments

Approved provider direction is CompuWerx and Metro Merchant Services. Stripe is not an approved CROWN production provider. Source stubs or historical references do not establish activation, compliance, settlement, refund, or webhook readiness. Payment processing remains disabled and fail closed under current release authority.

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

### Unverified externally

- current branch protection and required-check configuration;
- current Azure resources, RBAC, networking, slots, and settings;
- successful migration execution for a selected release;
- secret retrieval, rotation, revocation, and failed-rotation recovery;
- frontend/backend exact-commit alignment;
- provider activation and external observability state.

### Recovery limitation

A rollback-named workflow step is not equivalent to a proven application rollback, deployment-slot reversal, configuration restoration, or database restore. Production authorization requires explicit rollback and isolated database-restore drills with measured recovery objectives.

## Architectural priorities for a successor

1. Implement and verify the accepted canonical tenant contract.
2. Accept and implement a canonical frontend request ADR.
3. Complete identity compatibility convergence planning and rehearsal.
4. Establish a complete domain ownership and dependency map.
5. Define asynchronous task, retry, idempotency, and tenant-binding authority.
6. Consolidate deployment and verification topology around exact-commit identity.
7. Prove rollback, restore, secret rotation, and monitoring behavior.
8. Keep external payment processing disabled until separately authorized and certified.

## Release posture

**FROZEN / PRODUCTION NOT APPROVED / BUYER OPERATIONAL TURNOVER NOT APPROVED.**
