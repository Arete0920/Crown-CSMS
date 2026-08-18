# CROWN System Architecture Overview

**Status:** CANONICAL SUPPORTING OVERVIEW  
**Owner:** CROWN Engineering  
**Last verified:** 2026-08-17

## Interpretation

This document summarizes repository-visible implementation and architectural convergence status. It does not redefine release, deployment, recovery, or owner-turnover authority. Those claims are governed by `docs/CURRENT_RELEASE_STATUS.md`, the canonical document index, and Crown-CSMS issue #14.

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
| Hosting target | Azure App Service | Verified in workflow source; live deployed identity governed separately |
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
  -> persistent CROWN RBAC and domain permission enforcement
  -> domain service and transaction
  -> school-scoped persistence
  -> audit and external integration boundaries
  -> normalized API response
```

The browser is untrusted. Client-provided tenant, role, object, financial, workflow, and state claims require backend validation. Client-supplied role headers and generic Django staff status are not substitutes for canonical domain authority where persistent CROWN permissions apply.

## Multi-tenant architecture

ADR-0001 defines one canonical request tenant context at `request.crown_tenant`, with compatibility projections at `request.school_id` and `request.school`. Missing, invalid, inactive, unknown, or unauthorized school context must fail closed.

ADR-0003 defines tenant ownership outside HTTP requests: tenant-owned mutation runs under one explicit school identity, platform orchestrators may enumerate schools but execute each tenant operation separately, and provider-dependent payment jobs must not mutate while payment processing is disabled.

Current settings still contain multiple tenant-related middleware layers. The accepted contract is authoritative; redundant middleware must not be removed until complete consumer inventory and behavioral-equivalence evidence exist.

## Identity and household architecture

ADR-001 establishes `core.Family`, `core.Guardian`, and `core.Student` as canonical operational write authorities. Compatibility/read domains remain in households, crown_api, admissions bridges, and workflow/session models. Compatibility retirement requires consumer inventory, deterministic mapping, tenant-by-tenant reconciliation, migration rehearsal, integrity counts, and rollback/forward-fix design.

## Domain architecture

| Domain | Principal areas | Responsibility / current boundary |
|---|---|---|
| Platform identity and tenancy | `core`, authentication, permissions, tenant middleware | Schools, users, roles, canonical identity, tenant boundary |
| Admissions and enrollment | `admissions`, `applications`, enrollment-related code | Inquiry, application, acceptance, enrollment handoff, compatibility bridges |
| Finance | `ledger`, `billing`, `financial_aid`, `aid` | Charges, balances, allocations, payment records, plans, aid |
| Academics / student records | `academics`, `gradebook`, `curricula`, `student_records` | Courses, sections, curriculum, grading, student records, official-output boundaries |
| Student operations | attendance, discipline, health, transportation, service-hours | School-scoped operational workflows and restricted data |
| Communications and support | `comms`, canonical `crown_api` communications views, `support` | Communication history/read authority, delivery boundaries, support; Microsoft/SMS transport remains broader integration scope |
| HR and staff operations | `hr`, canonical Core staff identity | HR lifecycle/compliance; HR/Core identity ownership convergence remains a follow-up |
| Athletics and activities | `athletics` and related apps | Teams, rosters, events, eligibility, clearance, coach object authority |
| Spiritual Life | `spiritual_life` | Formation, prayer, pastoral, and restricted student/pastoral data |
| Governance and analytics | `board_oversight`, `executive360`, `analytics` | Board, executive, health, metric, export, reporting |
| Frontend platform | `frontend/dashboards` | Shared shell, routes, persona surfaces, components, state, ADR-0002 transport, accessibility |
| Operations | workflows, deployment configuration, `docs/operations` | Build, test, deploy, monitor, recover, rotate, maintain |

App registration demonstrates structure, not independent proof of completion, tenant safety, external configuration, or production enablement.

## Frontend transport architecture

ADR-0002 establishes `frontend/dashboards/src/utils/authClient.js` as the protected first-party API transport authority. It owns trusted API-base resolution, access-token propagation, selected-school context, credentials, timeout/cancellation, correlation, structured failure handling, and protection against leaking CROWN auth/tenant context to untrusted origins.

Direct browser fetch remains permitted only for explicit authentication/bootstrap, public sandbox/public-entry, external-origin, development-only, and test/certification cases whose semantics are outside the authenticated school-operational transport contract.

A dashboard aggregate may be labeled live only when all data required by that live contract is live. Partial live results must not be mixed with demo/fixture data and presented as one live aggregate.

## API and asynchronous architecture

- `/api/v1/` is the principal versioned API namespace represented in source.
- Tenant identity and role authorization are backend responsibilities regardless of frontend route or header behavior.
- Durable business rules should live in domain services and transactional boundaries where implemented.
- Background tenant mutation must follow ADR-0003 and explicit tenant context.
- Payment-dependent background work remains fail closed while external payment processing is disabled.

## External integrations

### Microsoft

Microsoft Entra authentication and Graph-related paths exist in source. Tenant registration, consent, credentials, licensing, immutable Entra-object linkage, SDS/roster synchronization, Teams/Exchange transport configuration, and live provider behavior are operational/integration facts governed separately. The broader Microsoft Education program remains explicit follow-up scope.

### Payments

No external payment processor is approved or active for the current turnover source. Payment processing is disabled and fail closed. Provider-specific activation requires a separately accepted architecture decision, contract/configuration authority, credentials, and provider-specific certification.

### Cloud, email, storage, and monitoring

These systems are adapters outside the application source-of-truth boundary. Each requires verified ownership, credentials, permissions, retention, failure handling, and operational monitoring before authorized use.

## Deployment and recovery architecture

Workflow source contains protected production-deployment, exact-SHA/image, health, migration, rollback, and isolated-restore mechanics. The current turnover sequence must keep these distinctions explicit:

- **repository/source evidence** — source and CI behavior for one exact SHA;
- **deployed runtime evidence** — exact build/image/runtime identity and health;
- **rollback evidence** — authorized immutable application rollback execution against the selected release;
- **restore evidence** — operational backup identity plus isolated restore and integrity proof tied to the selected release;
- **turnover evidence** — successor-controlled accounts, credentials/recovery factors, monitoring, billing/vendors, acceptance, and seller-access removal.

A workflow or runbook existing in source is not equivalent to an executed operational drill.

## Current architectural convergence

1. Retire redundant tenant middleware only after complete equivalence proof.
2. Continue migration of remaining protected direct-fetch consumers to ADR-0002; keep exceptions explicit.
3. Complete identity compatibility convergence before retiring legacy identity domains.
4. Maintain a current domain ownership/dependency graph before consolidating overlapping apps.
5. Reconcile HR/Core Staff ownership before migrating or deleting duplicate lifecycle/identity fields.
6. Complete Student Records/report-card authority and behavioral proof without duplicating Transcript/Gradebook authority.
7. Treat Communications/Microsoft transport, canonical recipient policy, SMS/outbox, and provider-side configuration as explicit roadmap/integration work rather than completed current authority.
8. Define Little Lambs daycare-specific authority before representing it as a separately completed product beyond Aftercare compatibility.
9. Execute or explicitly disposition immutable rollback, operational restore, credential-rotation, monitoring, and transfer exercises required by the owner handoff.
10. Create additional ADRs listed in `DECISION_INDEX.md` before material changes to those boundaries.

## Release posture

Current Crown-CSMS release/runtime/turnover posture is governed by `docs/CURRENT_RELEASE_STATUS.md`. Historical Crown2026 deployment and certification records remain provenance only and do not define current Crown-CSMS production identity.
