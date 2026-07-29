# CROWN Tenant Enforcement Implementation Status

**Status:** Controlled architecture supporting record  
**Owner:** Founder/Product Owner and CROWN Engineering  
**Effective date:** 2026-07-29  
**Related authority:** `decisions/ADR-0001-tenant-resolution-and-enforcement.md`  
**Related issues:** #1626, #1753, #1619  
**Observed source identity:** `f4828184c89a92c39950341d1efcfb6807c7b835`

## Purpose

This record reconciles the accepted tenant-resolution decision with the implementation visible in the repository. It records source-grounded completion and remaining evidence without claiming deployed-runtime, universal endpoint, database, task, or production certification.

## Verified source implementation

### Canonical tenant context

`backend/crown_api/tenant.py` defines:

- immutable `TenantContext`;
- canonical and legacy tenant-header resolution;
- authenticated-principal and unambiguous role-based school fallback;
- explicit tenant-override authorization;
- canonical request binding through `request.crown_tenant`;
- compatibility aliases for `request.school_id`, `request.school`, `request.tenant_school`, and `request.tenant_school_id`.

### Protected-route enforcement

`backend/core/tenant_header_middleware.py`:

- enforces tenant context after authentication for protected API routes;
- rejects malformed tenant identifiers;
- rejects missing tenant context where required;
- rejects unauthorized cross-school selection before business logic;
- rejects inactive or unknown schools;
- permits cross-school selection only through explicit override authority;
- requires successful audit persistence before an authorized override proceeds;
- binds and clears request-thread tenant context in a `finally` path.

### Compatibility adapters

The active middleware stack still includes three tenant-related layers:

1. `core.middleware.TenantIsolationMiddleware`;
2. `core.tenant_header_middleware.TenantHeaderRequiredMiddleware`;
3. `crown_api.tenant_middleware.TenantContextMiddleware`.

Current source shows the first and third layers acting as compatibility adapters around the enforcing middleware. Their continued registration is migration debt, not proof of three independent tenant authorities.

### Query and audit consumers

Current source:

- prefers `request.crown_tenant` in `TenantQuerySetMixin` and `AuditLogMixin`;
- retains legacy fallback aliases for compatibility;
- persists structured tenant decisions through `crown_api.audit.audit_tenant_decision()`;
- records actor type, principal school, selected school, resolution source, header presence, override request and authorization, route, method, correlation ID, outcome, and reason.

### Focused tests

`backend/tests/test_tenant_decision_audit_and_dashboard_context.py` includes focused source-level regression coverage for:

- denied cross-school override with structured audit evidence;
- denial remaining fail closed when audit persistence fails;
- authorized support override with persisted evidence;
- authorized override failing closed when required audit evidence cannot persist;
- dashboard header requirements;
- ordinary staff denial for cross-school access;
- support-role authorization through canonical context.

These tests are present in source. This record does not assert that they passed on the current SHA because the GitHub connector did not execute them.

## ADR implementation reconciliation

The following ADR-0001 implementation elements are visibly present in source:

- canonical immutable tenant-context type;
- canonical resolver and request binding;
- header-versus-principal conflict detection;
- explicit override authorization;
- fail-closed protected-route enforcement;
- compatibility aliases;
- structured decision auditing;
- request-thread cleanup;
- focused cross-school and audit regression tests.

## Remaining convergence work

The following remain open and must not be represented as complete:

1. enumerate every tenant-context consumer, exemption, permission, queryset, service, task, script, integration, test, and frontend sender;
2. migrate all remaining consumers away from direct legacy attributes where appropriate;
3. prove background-task tenant binding and cleanup;
4. prove no exemption-list broadening and classify each exempt route;
5. establish representative object-level authorization coverage across modules;
6. verify complete role matrix for administrator, teacher, parent, student, board, support, service, and superuser actors;
7. execute cross-tenant negative tests and privilege-escalation tests on one current immutable SHA;
8. verify audit completeness for actor, tenant, action, object, timestamp, and outcome across representative mutations;
9. execute authenticated browser, API, job, and deployed-runtime proof;
10. retire or reduce compatibility middleware only after consumer inventory and equivalence proof.

## Middleware retirement boundary

No middleware layer should be removed solely because the canonical context now exists. Retirement requires:

- a complete consumer inventory;
- exact-head tests covering session, JWT, DRF fixtures, public routes, protected routes, overrides, exceptions, and cleanup;
- proof that no active consumer depends on removed request attributes or ordering;
- a bounded rollback path;
- explicit Product Owner disposition.

## Lane 2 completion boundary

This reconciliation completes the repository-documentation correction for tenant-enforcement implementation status.

It does not complete Lane 2. Full Lane 2 PASS still requires current executable and deployed evidence for the persona matrix, cross-tenant denial, object authorization, privilege-escalation denial, asynchronous tenant binding, and audit completeness on one immutable release identity.

Production remains **NOT APPROVED / NO-GO / HOLD**.
