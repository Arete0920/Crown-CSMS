# CROWN Architecture Review — 2026-08-08

**Status:** Active final handoff architecture review  
**Review authority:** GitHub issue #1925  
**Initial reviewed development source:** `5c52cc7cc8c1c2e4842fc88aea71eea7e20605d8`  
**Current synchronized architecture branch:** `agent/final-architecture-hardening-20260808`  
**Certified production source remains:** `17573fb649f74a3ba0f1b3fbc9e004108b3cf228`  
**Immutable production tag remains:** `prod-deploy-20260804-17573fb`

## Authority boundary

This record reports the current architecture inspection and hardening work. It does not move the certified production identity and does not authorize deployment of later development commits.

A governance deviation occurred when the initial version of this review file was accidentally written directly to `main` in commit `b23a176aa0347fd6cf45f415e3a60542a0c9c401`. The commit is retained transparently in history. All corrective architecture implementation after that point is branch/PR governed; no destructive history rewrite is authorized for that process error.

## Review objective

Inspect the live repository before owner handoff across:

- system and domain boundaries;
- authentication, authorization, tenant isolation, and audit;
- frontend request transport and provenance;
- persistence and identity authority;
- scheduled/background execution;
- payments and external integrations;
- deployment/release/recovery boundaries;
- compatibility and migration debt;
- architecture documentation and decision authority.

## Verified architectural strengths

1. CROWN is one shared multi-tenant product rather than tenant-specific forks.
2. ADR-0001 defines canonical request tenant authority through `request.crown_tenant`, explicit override authorization, and fail-closed protected-route behavior.
3. ADR-001 defines canonical operational writes for `core.Family`, `core.Guardian`, and `core.Student` while preserving compatibility domains until reconciliation proof exists.
4. `frontend/dashboards/src/utils/authClient.js` is a mature canonical protected frontend transport that owns API-base resolution, token and school propagation, credentials, timeout/cancellation, correlation, structured failures, and trusted-origin handling.
5. Shared frontend API wrappers already converge on that transport.
6. The active communications outbox binds delivery to explicit school tenant context and includes bounded retry/dead-letter handling.
7. Tenant bulk-write/delete protections, cross-school denial controls, explicit support override authority, and tenant decision audit mechanisms are present in source.
8. Dashboard registry/API-contract semantics are explicit; broad navigation fallback fails closed.
9. Certified release identity, deployment, tenant/RBAC proof, and payment containment are separately governed and do not silently follow development `main`.
10. Compatibility domains are retained rather than destructively collapsed without migration evidence.

## Immediate architecture findings and disposition

### A-01 — client-supplied demo-role compatibility authority

**Original finding:** Heritage sample-dashboard authorization consumed `X-Demo-Role`, creating duplicate client-controlled role input despite authenticated server-side `UserRole` records.

**Hardening implemented on architecture branch:**

- sample access now derives from authenticated Heritage school membership and server-side supported `UserRole` only;
- forged, absent, or unknown `X-Demo-Role` values cannot change authorization;
- cross-school sample access remains denied;
- negative regression tests prove the header carries no authorization authority.

`x-demo-role` remains in the generic CORS allow-header list as an inert compatibility allowance. Because the backend no longer consumes it for authorization and the current frontend does not send it, removal is cleanup rather than a security prerequisite. It should be removed in a future bounded settings cleanup rather than by risky broad replacement of the production settings file immediately before handoff.

**Disposition:** security authority defect corrected; inert configuration cleanup remains non-blocking.

### A-02 — canonical protected frontend transport not universal

**Original finding:** protected operational modules still duplicated authentication, tenant, API-base, timeout/error, or provenance behavior with direct `globalThis.fetch`.

**Hardening implemented:**

- ADR-0002 accepted: `authClient.js` is the protected first-party transport authority;
- Board Executive data migrated to canonical transport;
- Learning Continuity API migrated to canonical transport;
- shared CROWN Finance/Admissions KPI metrics migrated to canonical transport;
- contract tests prohibit reintroduction of duplicate behavior on those paths;
- explicit direct-fetch exceptions are defined for authentication/bootstrap, public sandbox/public-entry, external-origin, development-only, and test/certification traffic.

**Remaining convergence:** direct-fetch sites still require classification against ADR-0002. Public/bootstrap/external/test paths may remain; protected school-operational paths must migrate before they are materially changed or promoted as canonical clients.

**Disposition:** canonical authority established and key protected bypasses corrected; lower-risk consumer convergence remains controlled architecture debt, not duplicate authority.

### A-03 — mixed live/demo Board Executive provenance

**Original finding:** the Board Executive hook used four direct API calls, overlaid successful responses onto demo defaults, and marked the aggregate LIVE if any endpoint succeeded.

**Hardening implemented:**

- all four protected calls use canonical `authenticatedJson`;
- live classification requires all four required sources to succeed;
- any incomplete live set returns explicit DEMO fallback with `live=false`;
- regression tests prohibit `Promise.allSettled`, manual auth/tenant headers, and partial-live classification.

**Disposition:** corrected.

### A-04 — architecture documentation drift

**Original finding:** architecture documents still claimed no consolidated frontend client existed and retained pre-certification NO-GO/source identity language.

**Hardening implemented:**

- `ARCHITECTURE_MAP.md` reconciled to ADR-0002/ADR-0003 and certified-release/current-development identity separation;
- `SYSTEM_OVERVIEW.md` reconciled to actual transport and background-task implementation;
- `DECISION_INDEX.md` registers ADR-0002 and ADR-0003;
- this review record is reconciled to the live hardening program;
- tenant and identity supporting status records are being refreshed without claiming compatibility convergence that has not occurred.

**Disposition:** current authority corrected; historical evidence remains date-bounded provenance.

### A-05 — payment-dependent scheduled mutation while payments are disabled

**Finding:** Celery beat still scheduled dunning retry and payout-audit jobs even though the canonical payment hold prohibits provider-dependent mutation.

**Hardening implemented:**

- both scheduled ledger tasks now return the canonical `payment_integration_on_hold` disposition;
- both report `mutated=false` and do not call payment retry or payout-reconciliation services;
- regression tests prove the fail-closed scheduled behavior.

**Disposition:** corrected.

### A-06 — unscoped tenant mutation in scheduled jobs

**Finding:** billing grace enforcement and support SLA escalation executed broad cross-school mutation queries; analytics scheduled paths did not consistently establish canonical tenant context.

**Hardening implemented:**

- ADR-0003 accepted for tenant-aware background jobs;
- billing grace enforcement iterates active schools and executes one school under `tenant_context` with explicit `school_id` filtering;
- manual grace-period command follows the same contract;
- support SLA escalation iterates schools under tenant context and service filtering is tenant-explicit;
- manual support escalation is selected-tenant scoped;
- customer-health refresh executes per school under tenant context;
- predictive analytics queues one tenant ID per school and establishes tenant context during execution;
- background architecture contract tests enforce these invariants;
- retention purge remains preview-only by default with its separate execution/confirmation/global-authorization controls.

**Disposition:** corrected for the scheduled paths identified in the live beat schedule; future tasks must comply with ADR-0003.

## Accepted architecture decisions after review

- ADR-0001 — canonical request tenant resolution and enforcement.
- ADR-0002 — canonical protected frontend API transport and explicit exception policy.
- ADR-0003 — tenant-aware background jobs, retries/idempotency boundary, and payment-hold scheduled behavior.
- ADR-001 — canonical operational family/guardian/student write authority.

## Compatibility/convergence debt — intentionally not destructively collapsed

The following remain legitimate architecture convergence work and are not safe two-day rename/delete targets:

1. three registered tenant middleware layers;
2. `core` versus `households`/`crown_api` identity compatibility domains;
3. `curriculum` versus `curricula` responsibility overlap;
4. finance/accounting/aid/billing/ledger/journal/finance-setup responsibility boundaries;
5. `integrations` versus `integrations_real` authority;
6. `academics` versus `academics_ro` boundary;
7. aggregate/projection domains (`student_records`, `student360`, `parent360`, `executive360`);
8. multiple legitimate authentication mechanisms requiring normalized principal semantics.

Any consolidation requires complete consumer/dependency inventory, tenant/data reconciliation where applicable, expand-contract or equivalent migration design, exact-head regression evidence, and rollback/forward-fix proof.

## Decisions still required before future material boundary changes

The Decision Index intentionally leaves these unaccepted until current behavior and migration consequences are sufficiently defined:

1. domain ownership and allowed cross-domain dependency policy;
2. external integration adapter authority;
3. deployment/release/recovery topology;
4. reporting and analytics read-model boundaries;
5. file/document storage and lifecycle authority;
6. future payment-provider adapter and activation contract.

The absence of speculative ADRs is deliberate. Unimplemented future architecture must not be presented as verified current behavior.

## Handoff architecture standard

Before this hardening lane is closed:

- exact branch must be synchronized to current `main`;
- focused architecture tests and the full applicable CI suite must be terminal green;
- zero unresolved actionable review threads;
- no known critical/high architecture defect in the reviewed scope;
- current architecture map, system overview, decision index, and supporting status records must agree;
- certified production identity must remain distinct from the later development branch;
- any residual compatibility debt must be clearly documented and non-destructive.

No claim of architectural completion is valid until those exact-head checks settle successfully.
