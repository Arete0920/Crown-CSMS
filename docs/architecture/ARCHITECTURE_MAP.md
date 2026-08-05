# CROWN Architecture Map

**Status:** CANONICAL  
**Owner:** CROWN Engineering  
**Effective date:** 2026-08-04

## Purpose

This document defines the owner-facing architectural shape of CROWN. It describes durable boundaries and accepted decisions visible in the repository. Release and production status are governed by `docs/CURRENT_RELEASE_STATUS.md` and GitHub issue #1619.

## Architectural principles

1. **One product, shared platform.** CROWN is a single multi-tenant platform. Tenant differences are expressed through school-scoped data, configuration, permissions, and enabled modules rather than tenant-specific forks.
2. **School context is a security boundary.** Protected work executes only after authentication, tenant resolution, tenant authorization, and domain authorization.
3. **Fail closed.** Missing, invalid, inactive, unknown, or unauthorized tenant and role context must be rejected before business logic performs protected reads or writes.
4. **Domain ownership is explicit.** Each durable record has one authoritative write domain. Compatibility models and bridges may remain, but they are not interchangeable with canonical records.
5. **Shared contracts precede convenience.** Frontend requests, API behavior, tenant propagation, identity, audit events, and integrations must follow shared contracts rather than page-specific or module-specific conventions.
6. **External systems remain outside the source-of-truth boundary.** Microsoft, payment providers, Azure, email, storage, and monitoring are integrations. Repository configuration does not prove their live state.
7. **Deployment identity is immutable.** A releasable build must be traceable to one exact source commit across build, image, deployment, and runtime identity.
8. **Recovery is architectural, not incidental.** Application rollback, database restore, secret rotation, and failed-rotation recovery require explicit procedures and proof.

## Runtime topology

```text
Browser / authorized client
        |
        v
React + Vite frontend
        |
        | HTTPS / versioned API contract
        v
Django + Django REST Framework
        |
        +--> authentication and principal resolution
        +--> canonical tenant resolution and enforcement
        +--> RBAC and domain permissions
        +--> domain services and transactions
        +--> audit and integration boundaries
        |
        v
PostgreSQL-oriented persistence

Optional runtime dependencies:
- Redis and Celery for asynchronous work
- Microsoft Entra and Microsoft Graph
- Azure App Service, Container Registry, and external secret management
- approved payment providers only when separately authorized
- Sentry or another approved monitoring service
```

## Trust boundaries

### Client boundary

The browser is untrusted. Client-provided school identifiers, role claims, object identifiers, totals, and workflow state must be revalidated by the backend.

### Authentication boundary

Session, JWT, Entra, and service identities identify the actor. Authentication alone does not authorize a school, role, domain action, or object.

### Tenant boundary

`request.crown_tenant` is the accepted canonical tenant context defined by `decisions/ADR-0001-tenant-resolution-and-enforcement.md`. `request.school_id` and `request.school` are compatibility projections. New tenant attributes are prohibited.

### Authorization boundary

Permission classes and domain services authorize actions within an already-authorized tenant. Cross-school override is exceptional, permission-controlled, request-scoped, and auditable.

### Persistence boundary

PostgreSQL is the production-oriented primary data store. SQLite remains a development and test option. Tenant ownership must be explicit in models, services, querysets, tasks, imports, exports, and reports.

### Integration boundary

External credentials and provider state are never architectural proof. Microsoft, payment, cloud, email, storage, and monitoring integrations require separate configuration, ownership, security, and runtime verification.

## Domain ownership

| Domain | Primary repository areas | Architectural responsibility |
|---|---|---|
| Platform identity and tenancy | `backend/core/`, tenant middleware and permissions | Schools, users, roles, canonical family/guardian/student identity, tenant enforcement |
| Admissions and enrollment | `backend/admissions/`, `backend/applications/`, related frontend routes | Inquiry, application, acceptance, enrollment handoff, identity compatibility bridges |
| Finance | `backend/ledger/`, `backend/billing/`, `backend/financial_aid/`, `backend/aid/` | Charges, balances, allocations, payment records, plans, aid applications and awards |
| Academics | `backend/academics/`, `backend/gradebook/`, `backend/curricula/` | Courses, sections, grading, curriculum, academic records |
| Student services | attendance, discipline, health, transportation, service-hours and related apps | School-scoped operational records and workflows |
| Communications and support | `backend/comms/`, `backend/support/` | Outbound communication, delivery boundaries, tickets, escalation |
| Governance and analytics | `backend/board_oversight/`, `backend/executive360/`, `backend/analytics/` | Board, executive, health, metric, and reporting surfaces |
| Frontend platform | `frontend/dashboards/` | Shared shell, routing, role surfaces, request contracts, components, state and accessibility |
| Operations | `.github/workflows/`, `docs/operations/`, deployment configuration | Build, test, deploy, health, monitoring, rollback, restore, maintenance |

App presence establishes structure, not completion of every optional capability.

## Accepted architecture decisions

- `decisions/ADR-0001-tenant-resolution-and-enforcement.md` — accepted canonical tenant contract; bounded tenant and RBAC release certification passed, while compatibility convergence remains incomplete.
- `ADR-001-CANONICAL-HOUSEHOLD-GUARDIAN-STUDENT.md` — accepted canonical operational write identity for `core.Family`, `core.Guardian`, and `core.Student`; compatibility convergence remains incomplete.

The authoritative decision list is `DECISION_INDEX.md`.

## Certification reference

The bounded release certification record is maintained in `docs/CURRENT_RELEASE_STATUS.md` and GitHub issue #1619. Those sources govern exact release identity, deployment, health, tenant and RBAC evidence, and payment containment. This architecture map intentionally avoids duplicating that evidence to reduce authority drift.

## Open architectural convergence

1. Complete migration to the canonical tenant context and retire redundant middleware only after equivalence and consumer proof.
2. Establish one canonical frontend request contract for API base URL, authentication, tenant headers, cookies, timeout, retries, error normalization, and cancellation.
3. Complete tenant-by-tenant reconciliation of identity compatibility domains through an expand-contract migration with rollback proof.
4. Maintain a current domain ownership and dependency graph for models, services, tasks, imports, exports, reports, APIs, and frontend consumers.
5. Consolidate overlapping CI, deployment, certification, and runtime-verification paths only after required-check and operational dependencies are mapped.
6. Prove asynchronous tenant binding, idempotency, retry behavior, and cleanup for every active task path.
7. Verify external integration ownership and configuration without committing credentials.
8. Execute the deferred full rollback, isolated restore, credential-rotation, and expanded monitoring exercises when required by operations, diligence, contract, or a future owner.
9. Create the missing ADRs listed in `DECISION_INDEX.md` before making material changes to those architectural boundaries.

## Change rules

- Architectural changes require an ADR when they alter trust boundaries, canonical data ownership, tenant resolution, public API contracts, deployment topology, or external integration authority.
- Compatibility layers are removed only after consumer inventory, migration rehearsal, rollback design, and representative verification.
- Runtime changes and documentation-only authority changes should remain in separate pull requests.
- No architecture document may describe an unimplemented target as verified source behavior.
- Post-release hardening must not silently redefine the immutable certified production identity.
