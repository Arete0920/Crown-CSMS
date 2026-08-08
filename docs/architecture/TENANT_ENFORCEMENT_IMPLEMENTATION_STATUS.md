# CROWN Tenant Enforcement Implementation Status

**Status:** Controlled architecture supporting record  
**Owner:** Founder/Product Owner and CROWN Engineering  
**Effective date:** 2026-08-08  
**Related authority:** `decisions/ADR-0001-tenant-resolution-and-enforcement.md`  
**Background execution authority:** `decisions/ADR-0003-tenant-aware-background-jobs.md`  
**Related issues:** #1626, #1753, #1619, #1925

## Purpose

This record reconciles accepted tenant architecture with current repository implementation. It is not a substitute for the certified-release evidence in `docs/CURRENT_RELEASE_STATUS.md` and #1619, and it does not imply that later development `main` commits are production-certified.

## Verified request-time implementation

### Canonical tenant context

`backend/crown_api/tenant.py` defines:

- immutable `TenantContext`;
- canonical and legacy tenant-header resolution;
- authenticated-principal and unambiguous role-based school fallback;
- explicit tenant-override authorization;
- canonical request binding through `request.crown_tenant`;
- compatibility projections for existing request consumers.

### Protected-route enforcement

`backend/core/tenant_header_middleware.py`:

- enforces tenant context after authentication for protected API routes;
- rejects malformed and missing tenant identifiers where required;
- rejects inactive, unknown, and unauthorized cross-school selection;
- permits cross-school selection only through explicit override authority;
- requires audit persistence for authorized override;
- binds and clears request-thread tenant context through controlled request lifecycle.

### Compatibility adapters

The active middleware stack still contains:

1. `core.middleware.TenantIsolationMiddleware`;
2. `core.tenant_header_middleware.TenantHeaderRequiredMiddleware`;
3. `crown_api.tenant_middleware.TenantContextMiddleware`.

ADR-0001 is the authority. The extra registered layers remain compatibility/migration debt and must not be interpreted as three independent tenant authorities.

No middleware layer is to be removed solely on naming overlap. Retirement requires complete consumer/equivalence proof and a bounded rollback path.

## Role and client-input boundary

Client-provided role claims are not tenant or authorization authority.

The 2026-08-08 architecture hardening removes `X-Demo-Role` from Heritage sample-dashboard authorization logic. Sample access now requires:

- authenticated Heritage user;
- Heritage request school;
- Heritage user school binding;
- persisted server-side `UserRole` matching a supported sandbox persona role.

A forged, absent, or unknown client demo-role header cannot change the authorization result. The generic CORS header allowance may remain temporarily as inert compatibility configuration, but it carries no backend authorization semantics.

## Background tenant implementation

ADR-0003 extends tenant architecture beyond HTTP requests.

Verified aligned source paths include:

- communications outbox: explicit school context around delivery plus bounded retry/dead-letter handling;
- billing grace enforcement: active-school orchestration, `tenant_context(school)`, and explicit `school_id` service filtering;
- support SLA escalation: active-school orchestration, tenant context, explicit service filtering, and selected-tenant manual trigger;
- customer-health refresh: one active school at a time under tenant context;
- predictive analytics: one explicit tenant ID per queued run and tenant context during model execution;
- retention purge: preview-only by default with separate confirmation and global-authorization safeguards;
- payment-dependent dunning/payout beat tasks: fail closed/no mutation while external payment processing is deferred.

`backend/tests/test_background_job_architecture_contract.py` protects these architectural invariants.

## Query, permission, and audit consumers

Current source:

- prefers canonical tenant context in shared queryset/audit mixins where migrated;
- retains documented compatibility aliases where needed;
- records structured tenant decisions through the audit path;
- protects bulk tenant mutation with fail-closed tenant-context guardrails;
- applies explicit school predicates in newly hardened scheduled services whose models do not rely on the tenant-scoped model manager.

## Certified-release boundary

The bounded supported-role/RBAC/tenant certification for production source `17573fb649f74a3ba0f1b3fbc9e004108b3cf228` is recorded as PASS/COMPLETE in `docs/CURRENT_RELEASE_STATUS.md` and #1619.

This supporting record does not re-certify later development changes. Architecture hardening after that source requires its own exact-head CI and, if selected for production, the applicable exact-source deployment/certification process.

## Remaining controlled convergence

The following remain architecture debt rather than known duplicate authorities:

1. enumerate and classify remaining legacy tenant request-attribute consumers;
2. retire redundant middleware only after full equivalence proof;
3. continue representative object-level authorization and tenant regression coverage as modules evolve;
4. inventory every future Celery task, scheduled command, import/export, report, and integration against ADR-0003;
5. prohibit new unscoped tenant-owned background mutation;
6. preserve explicit, auditable support/platform override boundaries;
7. keep current frontend tenant propagation aligned with ADR-0002 while treating backend authorization as authoritative.

## Middleware retirement acceptance criteria

Retirement requires:

- complete consumer and exemption inventory;
- exact-head session/JWT/Entra/DRF/public/protected/override/cleanup tests;
- proof that no active consumer depends on removed request attributes or middleware ordering;
- tenant negative and privilege-escalation regression proof;
- rollback or forward-fix design;
- governed review and merge evidence.

## Current disposition

- ADR-0001 request-time tenant authority: **IMPLEMENTED / ACCEPTED**.
- Certified bounded production tenant/RBAC proof: **PASS / COMPLETE for certified release identity**.
- ADR-0003 background tenant contract: **ACCEPTED; key scheduled mutation paths hardened on final architecture branch**.
- Client-supplied demo-role authorization authority: **REMOVED from sample-dashboard decision**.
- Middleware compatibility retirement: **OPEN / NON-DESTRUCTIVE CONVERGENCE**.
- Later development branch production certification: **NOT AUTOMATIC; exact-source evidence required before deployment**.
