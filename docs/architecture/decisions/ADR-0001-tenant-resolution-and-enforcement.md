# ADR-0001: Canonical tenant resolution and enforcement

- **Status:** Accepted
- **Date:** 2026-07-15
- **Owners:** Founder/Product Owner; backend architecture owner
- **Reviewers:** Repository architecture and security/data evidence review; independent human reviewer when available
- **Related issues:** #1287, #1352
- **Related pull requests:** #1360

## Context

CROWN is a multi-tenant school-management platform. Tenant context is a security boundary and must be resolved, authorized, propagated, audited, and cleared consistently.

Current source registers three tenant-related middleware layers:

1. `core.middleware.TenantIsolationMiddleware`
2. `core.tenant_header_middleware.TenantHeaderRequiredMiddleware`
3. `crown_api.tenant_middleware.TenantContextMiddleware`

Current behavior is distributed:

- `resolve_tenant_school_id()` resolves a canonical or legacy tenant header before authenticated-user fallback;
- `TenantHeaderRequiredMiddleware` validates and attaches `request.school` and `request.school_id` for protected API routes;
- `TenantContextMiddleware` stamps tenant-resolution metadata;
- `TenantIsolationMiddleware` populates an older `request.tenant_school` path from `request.user.profile.school`;
- permissions, views, queryset helpers, tests, background tasks, and audit code participate in enforcement.

Dashboard regression tests prove cross-school denial for tested dashboard endpoints. That does not establish universal coverage for all endpoints, tasks, scripts, integrations, and model access paths.

## Decision drivers

- Tenant isolation and least privilege
- Fail-closed behavior
- Centralized authorization
- Auditability of staff/support overrides
- Compatibility with session, JWT, Entra, and service identities
- Request and asynchronous-context cleanup
- Minimal migration risk
- Testability and operational clarity

## Considered options

### Option 1: Keep all three middleware layers unchanged

Benefits:

- no immediate code migration;
- preserves existing tested behavior.

Risks:

- duplicate request attributes and exemption lists;
- older user/profile assumptions may diverge from `core.UserAccount`;
- unclear ownership between resolution, enforcement, context stamping, and query scoping;
- difficult proof of universal coverage.

### Option 2: Replace all tenant middleware in one change

Benefits:

- immediate simplification.

Risks:

- high security and regression risk;
- difficult equivalence proof;
- unsafe rollback if hidden consumers rely on legacy request attributes.

### Option 3: Introduce one canonical contract, adapt current layers, then retire redundancy incrementally

Benefits:

- preserves behavior during migration;
- allows explicit compatibility attributes;
- supports endpoint-by-endpoint and task-by-task proof;
- enables safe rollback.

Risks:

- temporary compatibility code;
- requires a complete consumer inventory and staged cleanup.

## Decision

Adopt Option 3.

### Canonical resolution object

One resolver returns an immutable tenant context containing:

- `school_id`;
- resolved `School` object when required;
- resolution source;
- header-present flag;
- authenticated principal school ID;
- override-requested flag;
- override-authorized flag;
- actor type;
- audit reason or support context when required.

### Resolution precedence

1. Resolve and authenticate the principal.
2. Resolve any explicit tenant header.
3. If no header is present, use the authenticated principal's authorized school context where the route permits fallback.
4. If a header is present:
   - allow it when it matches the principal's authorized school;
   - allow a different school only for an explicitly authorized multi-school, support, service, staff, or superuser role;
   - otherwise reject before business logic executes.
5. Invalid, inactive, deleted, unknown, or unauthorized schools fail closed.

A valid UUID and existing school record are necessary but not sufficient authorization.

### Canonical request attributes

The authoritative attributes become:

- `request.crown_tenant` — immutable tenant context;
- `request.school_id` — compatibility scalar derived from `request.crown_tenant`;
- `request.school` — compatibility object derived from `request.crown_tenant`.

Legacy attributes may remain temporarily as read-only aliases during migration. New code must not introduce additional tenant attributes.

### Enforcement ownership

- Authentication middleware identifies the principal.
- One tenant-enforcement middleware resolves and authorizes tenant context for protected routes.
- Permission classes enforce domain permissions within the already-authorized tenant.
- Querysets and services require explicit tenant context and fail closed when absent.
- Public routes use a reviewed allowlist and may not silently inherit broad exemptions.
- Background tasks require explicit serialized tenant identity and establish/clear context around execution.

### Override policy

Cross-school override requires:

- explicit authorized role or permission;
- active target school;
- structured audit event including actor, source school, target school, request ID, route, and reason where applicable;
- no persistence of override context beyond the request or task.

### Cleanup

Tenant context must be cleared in a `finally` path after every request and task. Context storage should be request-local or context-local; thread-local compatibility may remain only until all consumers migrate.

## Consequences

### Positive

- one authoritative security contract;
- centralized cross-school denial;
- fewer exemption lists and request attributes;
- clearer audit and testing requirements;
- safer retirement of legacy middleware.

### Negative

- staged compatibility period;
- consumer inventory and migration effort;
- some tests and clients may require updates.

### Risks

- hidden reliance on `request.tenant_school` or profile-based school access;
- accidental exemption broadening during consolidation;
- staff/support workflows failing if authorization rules are incomplete;
- background tasks losing tenant context if migration is partial.

## Security, tenant, and data implications

This ADR changes the ownership and shape of tenant enforcement but must not weaken existing denials. It does not by itself prove runtime tenant safety or close #1287.

No implementation may merge unless tests cover:

- unauthenticated protected request;
- missing tenant;
- invalid header;
- unknown, inactive, or deleted tenant;
- authenticated fallback where explicitly permitted;
- matching header;
- conflicting header from ordinary user;
- authorized staff/support override;
- unauthorized staff-like actor;
- cross-tenant object lookup;
- public route behavior;
- context cleanup after success and exception;
- asynchronous task binding and cleanup;
- audit fields for override and denial.

## Migration and adoption plan

1. Inventory all tenant middleware, resolver calls, request attributes, exemption lists, permission classes, queryset helpers, tasks, scripts, tests, and frontend header senders.
2. Add the canonical tenant-context type and resolver behind regression tests.
3. Adapt existing enforcement middleware to populate the canonical context while preserving compatibility aliases.
4. Centralize header/user conflict authorization before views execute.
5. Move permissions, services, and queryset scoping to the canonical context.
6. Add task-context utilities and cleanup tests.
7. Compare old and new outcomes across the regression matrix.
8. Retire `TenantIsolationMiddleware` behavior only after no active consumer depends on it.
9. Retire redundant context middleware or convert it to a thin adapter only after exact-SHA evidence.
10. Capture same-SHA authenticated browser/network proof under #1287 and #1274.

## Validation

Required evidence:

- exact consumer and exemption inventory;
- before/after middleware sequence;
- passing tenant-isolation and permission suites;
- conflicting-header denial across representative modules;
- authorized override audit proof;
- task and request cleanup proof;
- no increase in public-route scope;
- same-SHA browser/network tenant proof;
- explicit Product Owner disposition.

## Rollback or reversal

During migration, retain compatibility aliases and the previous enforcement path behind a short-lived controlled feature flag or revertable commit boundary. Rollback must restore prior request attributes and denial behavior without broadening access. No legacy layer is removed in the same commit that first introduces its replacement.

## Follow-up work

- [ ] Complete tenant consumer and exemption inventory.
- [x] Review and accept, revise, or reject this ADR.
- [ ] Implement canonical context and conflict authorization.
- [ ] Migrate permissions, services, querysets, and tasks.
- [ ] Retire redundant middleware after equivalence proof.
- [ ] Complete #1287 and #1274 runtime evidence.

## Approval record

- Product Owner disposition: Accepted by John T. C. Megahan on 2026-07-15.
- Architecture review: Accepted through repository-source and contract review under the temporary solo-owner governance workaround.
- Security or data review: Accepted for the architecture decision boundary only; runtime proof remains mandatory before implementation closure.
- Independent review: Temporarily unavailable. The Founder/Product Owner authorization, exact-head CI, and no-unresolved-thread controls substitute for the missing review action and must not be represented as independent approval.
