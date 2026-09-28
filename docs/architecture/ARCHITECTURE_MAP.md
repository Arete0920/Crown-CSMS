# CROWN Architecture Map

**Status:** CANONICAL  
**Owner:** CROWN Engineering  
**Last verified:** 2026-09-27

## Purpose

This document defines the owner-facing architectural shape of CROWN. It describes durable boundaries and accepted decisions visible in the repository. Release, recovery, deployment, and turnover status are governed by `docs/CURRENT_RELEASE_STATUS.md` and the current authorized owner-handoff/operational-transfer records. Crown-CSMS issue #14 is a completed historical engineering-program record. Crown2026 release records remain historical predecessor evidence only.

## Architectural principles

1. **One product, shared platform.** CROWN is a single multi-tenant platform. Tenant differences are expressed through school-scoped data, configuration, permissions, and enabled modules rather than tenant-specific forks.
2. **School context is a security boundary.** Protected work executes only after authentication, tenant resolution, tenant authorization, and domain authorization.
3. **Fail closed.** Missing, invalid, inactive, unknown, or unauthorized tenant and role context must be rejected before business logic performs protected reads or writes.
4. **Domain ownership is explicit.** Each durable record has one authoritative write domain. Compatibility models and bridges may remain, but they are not interchangeable with canonical records.
5. **Shared contracts precede convenience.** Frontend requests, API behavior, tenant propagation, identity, audit events, background jobs, and integrations must follow shared contracts rather than page-specific or module-specific conventions.
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
        | canonical protected transport / versioned API contract
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

Scheduled / asynchronous work
        |
        +--> platform orchestrator may enumerate active schools
        +--> each tenant-owned operation enters explicit tenant_context(school)
        +--> bounded retries / idempotency / audit semantics

Optional runtime dependencies:
- Redis and Celery for asynchronous work
- Microsoft Entra and Microsoft Graph
- Azure App Service, Container Registry, and external secret management
- approved payment providers only when separately authorized
- Sentry or another approved monitoring service
```

## Trust boundaries

### Client boundary

The browser is untrusted. Client-provided school identifiers, role claims, object identifiers, totals, and workflow state must be revalidated by the backend. Client-supplied role headers are never authorization authority.

### Frontend transport boundary

`frontend/dashboards/src/utils/authClient.js` is the accepted protected first-party transport authority defined by ADR-0002. It owns trusted API resolution, access-token propagation, selected-school context, credentials, timeout/cancellation, correlation, and structured failure behavior. Public/bootstrap/external/dev/test traffic may use explicit direct-fetch exceptions when authenticated school-operational semantics do not apply.

### Authentication boundary

Session, JWT, Entra, and service identities identify the actor. Authentication alone does not authorize a school, role, domain action, or object.

### Tenant boundary

`request.crown_tenant` is the accepted canonical request tenant context defined by ADR-0001. `request.school_id` and `request.school` are compatibility projections. New tenant attributes are prohibited.

Outside HTTP requests, tenant-owned background work follows ADR-0003: one tenant identifier and explicit `tenant_context(school)` per mutating tenant operation. Platform orchestrators may enumerate schools but may not perform one ambiguous unscoped cross-tenant mutation.

### Authorization boundary

Permission classes and domain services authorize actions within an already-authorized tenant. Persistent CROWN permission authority, rather than caller-controlled headers or generic Django staff status, governs protected domain access where the domain uses canonical RBAC. Cross-school override is exceptional, permission-controlled, request-scoped, and auditable.

### Persistence boundary

PostgreSQL is the production-oriented primary data store. SQLite remains a development and test option. Tenant ownership must be explicit in models, services, querysets, tasks, imports, exports, and reports.

### Integration boundary

External credentials and provider state are never architectural proof. Microsoft, payment, cloud, email, storage, and monitoring integrations require separate configuration, ownership, security, and runtime verification.

External payment processing is currently deferred, disabled, and fail closed. Provider-dependent scheduled retry and payout operations must not mutate state while this hold is active.

## Domain ownership

| Domain | Primary repository areas | Architectural responsibility |
|---|---|---|
| Platform identity and tenancy | `backend/core/`, tenant middleware and permissions | Schools, users, roles, canonical family/guardian/student identity, tenant enforcement |
| Admissions and enrollment | `backend/admissions/`, `backend/applications/`, related frontend routes | Inquiry, application, acceptance, enrollment handoff, identity compatibility bridges |
| Finance | `backend/ledger/`, `backend/billing/`, `backend/financial_aid/`, `backend/aid/` | Charges, balances, allocations, payment records, plans, aid applications and awards |
| Academics | `backend/academics/`, `backend/gradebook/`, `backend/curricula/`, `backend/student_records/` | Courses, sections, grading, curriculum, student records, official academic outputs and compatibility boundaries |
| Student services | attendance, discipline, health, transportation, service-hours and related apps | School-scoped operational records and workflows |
| Communications and support | `backend/comms/`, `backend/crown_api/views_comms.py`, `backend/support/` | Communication/read-history authority, delivery boundaries, tickets, escalation; external transport remains integration-scoped |
| HR and staff operations | `backend/hr/`, canonical Core staff identity | HR lifecycle/compliance while Core remains canonical identity authority; duplicate ownership must be explicitly reconciled |
| Activities and athletics | `backend/athletics/` and related apps | Teams, rosters, eligibility, events, clearance and object-level authority |
| Spiritual Life | `backend/spiritual_life/` | Formation, prayer, pastoral and mission-distinctive workflows with restricted-data boundaries |
| Governance and analytics | `backend/board_oversight/`, `backend/executive360/`, `backend/analytics/` | Board, executive, health, metric, and reporting surfaces |
| Frontend platform | `frontend/dashboards/` | Shared shell, routing, role surfaces, canonical protected request transport, components, state and accessibility |
| Operations | `.github/workflows/`, `docs/operations/`, deployment configuration | Build, test, deploy, health, monitoring, rollback, restore, maintenance |

App presence establishes structure, not completion of every optional capability.

## Accepted architecture decisions

- ADR-0001 — canonical request-time tenant resolution and enforcement.
- ADR-0002 — canonical protected frontend API transport and explicit exception policy.
- ADR-0003 — tenant-aware background jobs, per-school scheduled mutation, retry/idempotency boundary, and payment-hold behavior.
- ADR-001 — canonical operational write identity for `core.Family`, `core.Guardian`, and `core.Student`.

The authoritative decision list is `DECISION_INDEX.md`.

## Current release-verification boundary

Current source/release status is maintained in `docs/CURRENT_RELEASE_STATUS.md`; exact source identity is resolved directly from Git/GitHub and captured in immutable decision evidence. Transaction-time operational transfer is governed by the current owner-handoff/operational-transfer records and authorized parties. Those authorities govern repository certification, deployment/runtime evidence, recovery evidence, payment containment, and owner-turnover posture within their respective boundaries.

A repository SHA or green workflow matrix does not automatically inherit production certification. Any deployed production identity must be proven from exact source through build, deployment, runtime health, monitoring, and recovery evidence for the selected release.

## Open architectural convergence

1. Retire redundant tenant middleware only after complete consumer/equivalence proof.
2. Continue migration of any remaining protected direct-fetch consumers to ADR-0002; retain only explicit public/bootstrap/external/dev/test exceptions.
3. Complete tenant-by-tenant reconciliation of identity compatibility domains through an expand-contract migration with rollback proof where such migration is required.
4. Maintain a current domain ownership and dependency graph for models, services, tasks, imports, exports, reports, APIs, and frontend consumers.
5. Consolidate overlapping CI, deployment, certification, and runtime-verification paths only after required-check and operational dependencies are mapped.
6. Complete inventory of background tasks and management commands against ADR-0003; unscoped tenant mutation is prohibited.
7. Verify external integration ownership and configuration without committing credentials.
8. Execute or explicitly disposition current immutable rollback, operational restore, credential-rotation, and monitoring exercises required for owner handoff.
9. Create remaining ADRs listed in `DECISION_INDEX.md` before material changes to those boundaries.
10. Keep Student Records/report-card authority, HR/Core staff ownership, Communications/Microsoft transport, and Diadem Daycare Solutions integration/product boundaries as explicit follow-up architecture records rather than implying those roadmap boundaries are already converged.

## Change rules

- Architectural changes require an ADR when they alter trust boundaries, canonical data ownership, tenant resolution, protected frontend transport, background tenant execution, public API contracts, deployment topology, or external integration authority.
- Compatibility layers are removed only after consumer inventory, migration rehearsal, rollback design, and representative verification.
- Runtime changes and documentation-only authority changes should normally remain separately reviewable.
- No architecture document may describe an unimplemented target as verified source behavior.
- Historical predecessor certification must not be represented as current Crown-CSMS production identity.
