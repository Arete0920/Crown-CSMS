# CROWN Current Release Status

Date: 2026-07-17
Purpose: Canonical repository-level release posture for CROWN.

## Canonical Authority

1. This file records the repository-level release posture at the observed main SHA below.
2. Live GitHub state, exact-SHA workflow results, deployed runtime evidence, and external infrastructure evidence control when they differ from this snapshot.
3. Historical GO, SHIP, PASS, RELEASE_READY, PARTIAL, candidate-SHA, local transcript, and superseded evidence documents are non-authoritative unless explicitly incorporated here.
4. Product-surface completion, scaffold certification, source intent, or a passing subset of checks does not authorize production.
5. Current controlling posture is **CONTROLLED SANDBOX CANDIDATE / PRODUCTION NOT APPROVED**.

## Current Repository Snapshot

- Repository: `tcmegahan/Crown2026`
- Default branch: `main`
- Main SHA after PR #1389: `44bc5718cd66be871ad201e810b9a2707563e8c8`
- PR #1389 merged on 2026-07-17 after exact-head CI, crawler, dashboard completion, Playwright, migration-contract, tenant-isolation, security, release, and broad test gates completed successfully.
- Open pull-request state must be checked live. This snapshot was prepared after #1389 merged and #1390 was closed unmerged.
- Production deployment identity is not asserted by this document.
- Branch-protection and external platform configuration must be verified from live administration state.

## Current Decision

- Repository-wide decision: **SANDBOX_RELEASE_CANDIDATE**.
- Production release decision: **NOT APPROVED**.
- No payment processor is approved or active for production implementation while the Product Owner payment-processing hold remains in force.

## Implemented Architecture and Controls

### Mainline and CI stabilization

- PR #1373 restored the complete dashboard client, corrected board-dashboard routing, repaired sandbox crawler behavior, and corrected tenant-bound test fixtures.
- Release, route, contract, dashboard, tenant, dependency, security, and broad test workflows are operating on the current architecture.

### Frontend API transport

- PR #1375 established the canonical authenticated frontend transport for API-base resolution, credentials, bearer authentication, tenant headers, correlation identifiers, timeouts, cancellation, and structured failures.
- The duplicate dashboard-specific transport was removed.
- Issue #1351 remains open until final same-SHA authenticated browser/network evidence and residual direct-client inventory are complete.

### Tenant boundary

- PR #1364 introduced the immutable canonical request tenant context and centralized cross-school conflict enforcement.
- Issue #1352 remains open for explicit override permission, complete audit events, background-task tenant propagation, exemption reconciliation, and safe redundant-middleware retirement.

### Canonical identity direction

- PR #1386 declared `core.Family`, `core.Guardian`, and `core.Student` canonical for guardian-household operational writes and added transaction-safe, tenant-bound, idempotent behavior.
- Issue #1353 remains open for complete consumer inventory, compatibility mapping, representative data reconciliation, migration rehearsal, rollback proof, and legacy retirement criteria.

### Dashboard data truth

- Issue #1289 is complete: snapshot, sample, scaffold, fallback, hybrid, unknown, or unrelated API evidence cannot be represented as live dashboard proof.
- Issue #1272 is complete: the `/board` Microsoft asset blocker was resolved.
- Authenticated persona and tenant-context evidence remain open under #1274, #1287, and #1276.

### Controlled schema migration

- PR #1389 established an explicit exact-SHA migration workflow and the `migrate_with_lock` command.
- Production execution requires PostgreSQL, production-environment approval, exact-SHA checkout, fail-closed secret validation, and a database advisory lock.
- Issue #1387 remains open until migration authority is removed from ordinary web startup and the full interruption, contention, failure, recovery, and web-non-mutation matrix is proven.

### Application rollback

- PR #1378 established immutable prior-known-good image rollback with ACR tag validation, `BUILD_SHA` alignment, restart, and exact runtime health and identity verification.
- Issue #1270 remains open until a controlled rollback drill, isolated database restore drill or approved equivalent, and measured RTO/RPO evidence are recorded.

### Production secrets

- PR #1369 added external Vault/Azure Key Vault architecture, read-only policy templates, rotation procedures, audit requirements, and break-glass controls.
- Issues #1294 and #1296 remain open until external configuration, workload/deployment identity, sanitized audit evidence, rotation exercises, and break-glass exercise evidence exist.

### Payments

- Issue #1298 remains open but payment-provider implementation is **HOLD / BACKLOG** by Product Owner instruction.
- No Stripe, Metro, CompuWerx/CompuWorks, Square, or other provider may be represented as selected, supported, active, certified, or production-ready without a signed agreement and explicit written implementation authorization.
- Provider-neutral accounting, billing, ledger, invoice, balance, and payment-plan work may continue only when it does not initiate or process an external payment.

## Active Release-Critical Work

Ordered by dependency and release risk:

1. #1387 — complete schema cutover: remove web-start migration authority and prove interruption, contention, failure blocking, repeated execution, recovery, and web non-mutation.
2. #1274, #1287, #1276 — run one consolidated authenticated Playwright/browser evidence campaign for school administrator, teacher, parent, tenant context, console, network, and visual QA.
3. #1270 — execute controlled immutable rollback and database restore drills; record RTO/RPO.
4. #1294 and #1296 — prove external secret-store identities, audit logging, rotation, failed rotation, and break-glass operation.
5. #1352 and #1353 — complete residual tenant and identity convergence evidence.
6. #1275 — reconcile final release authority only after all preceding blockers close.
7. #1374 — close the final sprint only after every required same-SHA, runtime, recovery, secret, and authority artifact is linked.

## Product Completion Evidence

Historical module, dashboard, wizard, widget, and component completion evidence remains useful for product-surface coverage. It does not independently authorize production.

- Modules: historical product-scope coverage recorded.
- Dashboards: internal surface and completion-gate coverage recorded; authenticated live-data proof remains required.
- Wizards: 50-wizard deep-dive, parity, and completion assertions passed on the #1389 exact head.
- Controlled sandbox: candidate posture only.
- Production: **NOT APPROVED**.

## Required Production Entry Gates

Production authorization requires all of the following on one approved release identity:

1. Required GitHub checks settle with no pending, failed, or cancelled required gate.
2. Frontend and backend deployed identities are proven and reconciled to the approved release.
3. Authenticated school-administrator, teacher, and parent browser flows pass with screenshots, console, network, role, tenant, and provenance evidence.
4. Tenant context is proven across login, navigation, API traffic, and data access without weakened enforcement.
5. Web startup no longer mutates schema; the controlled migration stage and recovery matrix are proven.
6. Immutable application rollback and database restore are drilled with accepted RTO/RPO.
7. External secret-store configuration, least-privilege identities, audit logging, rotation, and break-glass operation are proven.
8. Payment functionality remains disabled unless separately authorized and certified.
9. Release-visible visual QA has no unexplained console, network, asset, authorization, or provenance failure.
10. Release notes, changelog, deployment and recovery runbooks, current main SHA, and final authority record are reconciled.
11. Explicit Founder/Product Owner production authorization is recorded only after all preceding gates pass.

## Allowed Language

Allowed:

- "CROWN is in controlled sandbox release-candidate posture."
- "CROWN has substantial product-surface and exact-head CI evidence."
- "Production release is not approved."
- "Several foundational architecture controls are implemented; operational and live-runtime evidence remains open."

Not allowed:

- forbidden claim: "CROWN is unrestricted production ready."
- "CROWN is production GO."
- "All dashboards are live" without authenticated same-SHA network evidence.
- "Recovery is proven" without timestamped rollback and restore drills.
- forbidden claim: "External secrets are production ready" from repository templates alone.
- "Payment processing is supported" while the Product Owner hold remains active.
- "Independent review is complete" without independent evidence.
- "An open or unmerged PR is shipped authority."

## Current Final Status

**CONTROLLED SANDBOX CANDIDATE / PRODUCTION NOT APPROVED**.
