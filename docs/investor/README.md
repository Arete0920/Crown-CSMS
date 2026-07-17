# CROWN Technical Diligence Overview

## Purpose

This is the controlled starting point for prospective owners, technical diligence reviewers, strategic partners, and authorized executive stakeholders.

It summarizes the product, repository structure, current engineering controls, and open hardening work. It does not replace source review, clean-clone verification, security testing, operational drills, or the current release-authority record.

## Product summary

CROWN is a multi-tenant Christian School Management Solution designed to coordinate institutional workflows across admissions, enrollment, academics, attendance, student records, gradebook, billing, accounting, financial aid, communications, portals, governance, transportation, athletics, safety, spiritual life, and related school operations.

The product is implemented as a broad modular web application rather than a single-purpose prototype.

## Current technical shape

- Backend: Django and Django REST Framework.
- Frontend: React and Vite.
- Primary production database direction: PostgreSQL.
- Authentication and identity integrations include application authentication and Microsoft Entra-related support.
- Deployment and infrastructure materials are oriented around Azure and GitHub Actions.
- Browser validation uses Playwright alongside unit, contract, backend, security, dependency, and release checks.
- Local development uses VS Code, GitHub, and PowerShell where appropriate.

## Repository authority

The authoritative repository is `tcmegahan/Crown2026`. The public-facing product name is CROWN.

Start with:

1. root `README.md`;
2. `docs/canonical/REPOSITORY_MANIFEST.md`;
3. `docs/canonical/CANONICAL_DOCUMENT_INDEX.md`;
4. `docs/engineering/DEV_SETUP.md`;
5. `docs/CURRENT_RELEASE_STATUS.md`;
6. `SECURITY.md`;
7. `docs/operations/README.md`.

Generated evidence, archived status files, copied command output, and historical reports do not override current canonical records.

## Verified strengths visible in the repository

### Product breadth

The codebase contains substantial backend and frontend implementation across a wide school-operations surface.

### Automated validation

The repository contains backend tests, frontend unit and contract tests, Playwright suites, security scanning, dependency review, route and dashboard checks, release gates, and evidence-generation workflows.

### Tenant and authorization hardening

The current architecture includes a canonical request tenant context and centralized cross-school conflict enforcement. Residual tenant-context migration and same-SHA browser proof remain open work.

### Frontend transport consolidation

Authenticated frontend API traffic is being consolidated through one canonical client that owns API-base resolution, authentication, tenant context, correlation identifiers, timeout and cancellation behavior, credentials, and structured failures.

### Canonical identity direction

Operational guardian, family, and student writes have been directed to the canonical `core` identity models. Compatibility-domain reconciliation, representative data migration rehearsal, rollback proof, and legacy retirement criteria remain open.

### Release and recovery controls

The repository includes exact-SHA validation, controlled schema-migration authority, immutable image rollback controls, secret-handling architecture, and release-governance documentation. Several controls still require live operational drills or external-platform evidence before production approval.

## Current risks and open work

CROWN is in controlled sandbox release-candidate posture. Production release is not approved.

The principal remaining technical risks are:

1. removing schema-migration authority from ordinary web startup and proving the controlled migration and recovery matrix;
2. completing authenticated persona, tenant-context, network, console, and visual browser evidence on one approved release identity;
3. executing application rollback and database restore drills with measured recovery objectives;
4. proving external secret-store identities, audit logging, rotation, failed-rotation handling, and break-glass operation;
5. completing residual tenant and identity-model convergence;
6. reducing legacy documentation and historical repository noise so current authority is immediately understandable;
7. proving that a successor can clone, configure, test, deploy, operate, recover, and administer the system without undocumented assumptions.

## Diligence review sequence

A technical reviewer should:

1. verify repository access, ownership, branch protection, required checks, and administrator control;
2. perform a clean clone and follow the canonical developer setup without informal assistance;
3. install dependencies from lock and requirements files and record all deviations;
4. run backend, frontend, contract, security, dependency, and browser suites at an exact commit;
5. inspect the architecture, module boundaries, tenant model, authentication, authorization, data model, API transport, background work, and deployment topology;
6. trace representative critical workflows from browser route through API, authorization, tenant context, service logic, canonical models, database writes, audit events, and rendered response;
7. review dependency licenses, vulnerability results, secret-scanning results, and software-supply-chain controls;
8. inspect migration history, schema ownership, data-retention behavior, backup and restore procedures, and rollback design;
9. review operational access, cloud resources, external integrations, domains, certificates, secrets, monitoring, logging, and incident procedures;
10. assess maintainability by implementing and validating a small representative change in an isolated branch;
11. reconcile all findings against the current release-status record and open risk register.

## Appropriate claims

Appropriate:

- CROWN has substantial product-surface implementation and automated validation.
- Several foundational architecture and release controls are implemented.
- CROWN remains in controlled sandbox release-candidate posture.
- Production approval depends on current exact-SHA runtime and operational evidence.

Not appropriate without current evidence:

- unrestricted production readiness;
- complete tenant-isolation proof;
- complete recovery proof;
- complete external secret-store proof;
- universal live-data certification;
- independent technical approval.

## Ownership-transfer standard

A transfer is not complete until the successor has verified repository administration, cloud and external-service ownership, local setup, testing, deployment, rollback, restore, secret access, monitoring, incident response, and the authority to operate and change the platform.

The controlling release posture remains `docs/CURRENT_RELEASE_STATUS.md`.
