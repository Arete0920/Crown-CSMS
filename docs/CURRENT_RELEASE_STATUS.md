# CROWN Current Release Status

**Date:** 2026-07-21  
**Observed main SHA:** `d5bd1d88c01edb74cd1720a152904a3d38a3b70f`

## Canonical decision

CROWN's final release target is **FULL PRODUCTION RELEASE AUTHORIZATION**.

The current evidence decision remains **PRODUCTION NOT APPROVED** until every required production gate passes on one unchanged approved release identity.

A controlled sandbox release is not the target and is not an acceptable substitute for production readiness. Sandbox and demo fixtures may be used only as bounded test data or test identities where they do not weaken production-mode authentication, authorization, tenant isolation, provenance or operational controls.

Live GitHub state, exact-SHA workflow results, deployed-runtime evidence and external-platform evidence control when they differ from this snapshot. Product-surface completion, source intent, scaffold evidence or a passing subset of checks does not authorize production.

## Approved scope and explicit exclusions

All authorized CROWN product and operational functionality is in production-readiness scope except:

1. **External payment processing:** deferred until a processor is selected, contracted, authorized, implemented and separately certified. Payment entry points must remain disabled and fail closed.
2. **Buyer/successor handoff execution:** deferred until a buyer or successor scope is explicitly authorized.

Provider-neutral accounting, billing, ledger, invoice, balance, payment-record and payment-plan functionality remains in scope and must operate correctly without initiating or confirming an external payment.

## Substantially implemented

- broad product/module, dashboard and wizard coverage evidence;
- canonical authenticated frontend transport;
- canonical request tenant context and cross-school conflict enforcement;
- explicit tenant-override authorization;
- exact-SHA controlled schema migration outside ordinary web startup;
- immutable-image rollback architecture;
- live-runtime crawler for identity, authentication, tenant context, routes, screenshots, network, console, accessibility and provenance;
- repository architecture for external secret storage, rotation, audit and break-glass control.

These controls still require the open runtime and operational evidence identified below.

## Active production-readiness blockers

1. **#1274, #1287, #1276 and residual #1351:** one exact deployed identity and authenticated administrator, teacher, parent, student and board browser/network/tenant/visual evidence across the complete authorized surface inventory.
2. **#1270:** controlled application rollback and isolated database restore with reconciliation and measured RTO/RPO.
3. **#1294 and #1296:** external secret-store identity, audit, rotation, failed-rotation, revocation and break-glass exercises.
4. **#1352:** complete tenant audit evidence, background-task binding, exemption reconciliation and residual consumer convergence.
5. **#1353:** canonical household, guardian and student consumer mapping, reconciliation rehearsal, rollback proof and safe legacy retirement criteria.
6. **#1425:** student-data privacy and school compliance evidence, including FERPA/COPPA/PPRA positions, CIPA claim boundary, state-law review, data inventory, notices, DPA, incident exercise and legal review.
7. **#1394:** CI proof hierarchy and duplicate-workflow rationalization.
8. **#1277:** final release notes, changelog and runbook reconciliation.
9. **#1275 and #1374:** final same-SHA authority reconciliation and Founder/Product Owner decision.

## Production crawler and Playwright requirement

The crawler, Playwright suites, API-contract tests and backend tests must be reconciled against a complete inventory of active routes, dashboards, modules, wizards, APIs, background tasks and enabled integrations.

Every active surface must be mapped to an authoritative proof mechanism or explicitly classified as payment-processing excluded, handoff excluded or not applicable with rationale. The production campaign must run against deployed non-local frontend and backend identities and must record roles, tenant context, redirects, screenshots, network activity, console results, accessibility, provenance and final disposition.

The controlling execution matrix is `docs/engineering/PRODUCTION_READINESS_EXECUTION_MATRIX_20260719.md`.

## Payment-processing hold

No payment processor has been selected.

Issue #1298 was closed as deferred for the current release scope, not as completed or approved. External payment-provider implementation remains on hold. Payment functionality must remain disabled. No provider may be represented as selected, supported, active, certified or production-ready.

## Buyer and transfer boundary

No buyer, successor or new owner has been selected or approved. Buyer analysis, transaction support, successor clean-room execution and ownership-transfer work are outside the current production-release scope.

The repository must remain reproducible and documented, but no current material may claim that a handoff is scheduled, accepted or complete.

## Compliance claim boundary

CROWN has a documented student-data privacy and compliance framework with substantial repository-level controls. Final deployed-runtime, operational, contractual, jurisdiction-specific and legal validation remains open under #1425.

Allowed:

- "CROWN is designed to support schools in meeting applicable student-data privacy and security obligations."
- "Final compliance validation remains in progress."

Not allowed:

- "FERPA certified";
- "COPPA certified";
- "compliance guaranteed";
- "approved by a regulator";
- any universal compliance claim unsupported by current evidence and review.

## Production entry requirements

Production authorization requires, on one approved release identity:

- all required repository checks terminal and green;
- exact frontend/backend deployed identity;
- complete surface inventory mapped to crawler, Playwright, API, backend, operational or manual proof;
- authenticated role, tenant, network, console, screenshot, accessibility and provenance evidence;
- complete tenant and privileged-access audit evidence;
- application rollback and database restore drills with accepted RTO/RPO;
- external secret-store operational exercises;
- compliance evidence and legal/contractual readiness for the approved scope;
- payment functionality disabled and fail closed;
- final release documentation reconciliation;
- explicit Founder/Product Owner authorization.

## Current final status

**TARGET: FULL PRODUCTION RELEASE AUTHORIZATION**  
**CURRENT DECISION: PRODUCTION NOT APPROVED**