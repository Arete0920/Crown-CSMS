# CROWN System Architecture Overview

## Authority and interpretation

This document summarizes repository-visible architecture. It is not production certification and does not override `docs/CURRENT_RELEASE_STATUS.md`.

Use these evidence labels:

- **Verified in source** — directly supported by current repository code or configuration.
- **Target architecture** — intended direction that still requires implementation or operational proof.
- **Unverified externally** — depends on GitHub, Azure, provider, identity, contract, or runtime state outside the repository.

Issue comments and architecture preparation packets are not accepted ADRs. Accepted decisions must be reviewed and committed under `docs/architecture/decisions/`.

## Core stack

| Layer | Repository-visible technology | Evidence status |
|---|---|---|
| Backend | Django + Django REST Framework | Verified in source |
| Frontend | React + Vite + MUI | Verified in source |
| Primary database | PostgreSQL through `DATABASE_URL`; SQLite is available for development/test paths | Verified in source |
| Background queue | Celery + Redis configuration | Verified in source; deployed operation not proven here |
| Error monitoring | Optional Sentry integration in production configuration | Verified in source; external project state unverified |
| Hosting target | Azure App Service | Verified in deployment workflow; live state unverified here |
| Container registry target | Azure Container Registry | Verified in deployment workflow; live RBAC state unverified here |
| Production secret authority | Azure Key Vault or another explicitly approved external secret manager | Target architecture; operational proof remains open in #1294 and #1296 |

## Core modules

| Domain | Principal apps | Purpose |
|---|---|---|
| Admissions | `admissions`, `applications` | Inquiry, application, and enrollment workflows |
| Ledger and billing | `ledger`, `billing` | Charges, payments, allocation, and financial operations |
| Financial aid | `financial_aid`, `aid` | Application, award, and officer workflows |
| Academics | `academics`, `gradebook`, `curricula` | Courses, sections, grades, and records |
| Discipline | `discipline` | Incidents and actions |
| Service hours | `servicehours` | Community-service tracking and approval |
| Board governance | `board_oversight` | Board metrics and governance workflows |
| Onboarding | `onboarding` | Imports, setup tasks, and activation workflows |
| Executive health | `executive360` | Executive and institutional health surfaces |
| Support | `support` | Tickets and escalation workflows |
| Analytics | `analytics` | Health scoring and exports |
| Communications | `comms` | Messaging and outbox delivery |
| HR | `hr` | Staff records and workflows |

App registration demonstrates repository structure, not independent proof that every module is complete, live, tenant-safe, or production-enabled.

## Multi-tenant architecture

### Verified source behavior

- `TenantHeaderRequiredMiddleware` validates tenant context for protected API routes.
- `resolve_tenant_school_id()` recognizes the canonical and legacy tenant headers and authenticated-user fallback.
- Role and permission utilities can scope authorization to `request.school`.
- Dashboard regression tests cover missing, invalid, unknown, correct, and conflicting tenant cases for tested dashboard endpoints.
- Request cleanup clears thread-local school context after middleware processing.

### Consolidation debt

Current settings register three tenant-related middleware layers:

1. `core.middleware.TenantIsolationMiddleware`
2. `core.tenant_header_middleware.TenantHeaderRequiredMiddleware`
3. `crown_api.tenant_middleware.TenantContextMiddleware`

They do not share one fully authoritative request contract. Enforcement is distributed across middleware, permissions, views, and query logic. #1352 is the preparation lane for an accepted ADR and consolidation implementation.

Do not infer either universal coverage or an active cross-tenant vulnerability from this overview. Universal protection requires endpoint, model, task, script, integration, and runtime evidence.

## Data architecture

The repository contains overlapping household, guardian, family, person, and student representations. #1353 tracks the inventory, accepted-model decision, migration rehearsal, reconciliation, and rollback evidence.

Until an ADR is accepted and migration evidence exists:

- do not designate one model family as canonical by implication;
- do not remove or rename legacy models destructively;
- do not claim data corruption merely because duplication exists;
- do not claim equivalence merely because names overlap.

Billing is designed around household responsibility, but the exact canonical household identity remains part of the #1353 decision.

## Frontend request architecture

The frontend currently contains more than one API request implementation. Shared authentication and dashboard clients independently resolve API location, token state, tenant state, headers, cookies, timeout behavior, and error handling.

#1351 tracks the inventory and accepted ADR for one canonical request contract. Until that decision is accepted and implemented, this document must not claim that all frontend traffic uses one client.

## API policy

- `/api/v1/` is the principal versioned API namespace visible in the repository.
- `APIVersionMiddleware` applies version/deprecation behavior configured in source.
- Breaking-change support windows and external partner commitments require explicit release and contract authority; this overview does not create them.

## External integrations

### Microsoft

- Microsoft Entra authentication and Microsoft Graph communication paths are represented in source and configuration.
- External tenant registration, credentials, mailbox licensing, consent, and live delivery remain operational evidence questions.

### Payments

- Approved production-provider direction is CompuWerx and Metro Merchant Services under #1298.
- Stripe is not an approved CROWN production provider.
- Repository stubs or historical references do not constitute provider support, activation, compliance, settlement, refund, or webhook proof.

## Deployment architecture

### Verified in workflow source

- production deployment is tag-triggered through GitHub Actions;
- deployment images are SHA-tagged;
- Azure authentication supports OIDC and a legacy service-principal path;
- preflight, test, image scan, health, database-status, integrity, and release-identity checks exist;
- workflow, Azure image, and live runtime SHA are compared during release verification;
- the workflow applies allowlisted application settings and sets `RUN_MIGRATIONS=true`.

### Not proven by source alone

- current live GitHub branch-protection settings;
- current Azure resource configuration;
- successful migration execution for a specific deployment;
- production secret-store retrieval and rotation;
- payment-provider activation;
- frontend/backend live SHA alignment outside a completed evidence record.

### Recovery limitation

The current workflow's rollback-named step does not itself restore a prior image, deployment slot, application setting set, or database state. #1270 remains the controlling rollback, restore, and recovery-drill blocker.

## Branch protection

Repository documentation cannot establish current GitHub administrative settings. See `docs/BRANCH_PROTECTION_SETTINGS.md` for the required target and verification procedure. Treat branch protection as **unverified externally** until a dated live settings record is captured.

## Architecture work currently in preparation

- #1351 — canonical frontend request client.
- #1352 — canonical tenant resolution and enforcement contract.
- #1353 — canonical household, guardian, and student data model.
- #1337 — CI and certification architecture consolidation.
- #1343 — repository authority, provenance, and documentation stabilization.

These are open work items, not completed architecture decisions.

## Release posture

**CONTROLLED SANDBOX CANDIDATE / PRODUCTION NOT APPROVED**.
