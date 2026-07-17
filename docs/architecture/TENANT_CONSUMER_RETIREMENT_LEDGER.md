# CROWN Tenant Consumer Retirement Ledger

Status: execution inventory under #1352  
Authority: accepted ADR-0001 and merged canonical tenant-context implementation  
Runtime authority: `request.crown_tenant`

## Purpose

Track every remaining request, task, permission, queryset, audit, and integration consumer that still depends on legacy tenant aliases or duplicate resolution behavior. This ledger controls compatibility retirement and prevents premature middleware removal.

## Canonical contract

- `request.crown_tenant` is the immutable request-time authority.
- `request.school_id`, `request.school`, `request.tenant_school_id`, and `request.tenant_school` are compatibility aliases only.
- Protected routes fail closed when tenant identity is missing, malformed, unknown, or conflicts with an unauthorized principal.
- Staff or support override requires explicit authorization and an auditable override disposition.
- Background tasks must bind tenant context explicitly; request-local state cannot be reused.

## Consumer classes to inventory

| Consumer class | Required inventory | Retirement condition |
| --- | --- | --- |
| Middleware | every read/write of tenant request attributes; exemption lists; cleanup behavior | all enforcement delegated to canonical resolver and equivalence tests green |
| Permission classes | legacy attribute reads; cross-school object checks | canonical context used directly and denial matrix green |
| Queryset helpers | implicit school filters; fallback behavior | explicit canonical school ID required and cross-tenant tests green |
| Views and serializers | request alias reads; override behavior | canonical context used or documented compatibility adapter |
| Audit and observability | school ID, source, actor, override metadata | complete canonical context emitted for protected requests |
| Celery/background jobs | tenant arguments, task-local state, cleanup | immutable task tenant envelope and task isolation tests |
| Management commands/scripts | school selection and unrestricted defaults | explicit tenant parameter or privileged all-tenant control with audit |
| Integrations/webhooks | tenant lookup from payload, secrets, or account mapping | deterministic tenant mapping and rejection of ambiguity |
| Tests and fixtures | direct alias injection or middleware simulation | production binding helpers used consistently |

## Verified completed work

- ADR-0001 accepted the compatibility-first convergence strategy.
- PR #1364 introduced the frozen canonical tenant context and centralized ordinary-user conflicting-header denial.
- PR #1377 migrated the authenticated `whoami` proof endpoint to `request.crown_tenant` and added conflict tests.

## Remaining execution sequence

1. Generate a source-level inventory of all legacy alias reads and writes.
2. Classify each consumer as enforcement, compatibility, projection, audit, task, script, or test-only.
3. Migrate permission and queryset consumers before removing middleware aliases.
4. Introduce an immutable tenant envelope for background and scheduled jobs.
5. Expand override audit events with actor, principal tenant, selected tenant, reason, source, request ID, and outcome.
6. Consolidate public-route exemptions into one reviewed allowlist.
7. Prove request cleanup and task cleanup under concurrency.
8. Retire redundant middleware behavior only after source search, focused tests, broad CI, and same-SHA runtime proof.

## Required regression matrix

- unauthenticated protected request;
- authenticated single-school principal without header;
- matching explicit header;
- malformed header;
- unknown or inactive school;
- conflicting ordinary-user header;
- principal without school submitting a header;
- authorized staff/support override;
- unauthorized override attempt;
- cross-school object lookup;
- request context cleanup;
- concurrent request isolation;
- task tenant binding and cleanup;
- management command all-tenant safeguard;
- integration tenant ambiguity.

## Closure rule

Issue #1352 is not complete until every production consumer is classified, the enforcing path is singular, compatibility aliases have no untracked readers, task context is explicit, override events are auditable, redundant middleware is retired, and same-SHA browser/network evidence confirms tenant behavior without broadening access.
