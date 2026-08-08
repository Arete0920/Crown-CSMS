# ADR-0003 — Tenant-Aware Background Jobs and Scheduled Mutation

**Status:** Accepted  
**Date:** 2026-08-08  
**Owner:** CROWN Architecture Authority

## Context

CROWN is multi-tenant. HTTP requests are protected by canonical tenant resolution, but Celery workers, beat schedules, management commands, and other background execution have no request object from which to derive tenant context.

Final handoff review found a mixed background model: the communications outbox already bound each school through `tenant_context`, while several scheduled billing, support, and analytics jobs executed global cross-school mutation loops or called services that queried multiple schools in one context. Payment-dependent dunning and payout jobs were also scheduled even though external payment processing is intentionally disabled and fail closed.

## Decision

Every background operation that reads or mutates tenant-owned business data must be one of two explicit forms:

1. **Tenant task:** receives one tenant/school identifier, resolves that school, enters `core.tenant_models.tenant_context(school)`, and performs only that tenant's operation.
2. **Platform orchestrator:** may enumerate active school identifiers, but must dispatch or invoke the tenant operation separately for each school under explicit tenant context. It must not execute one unscoped cross-tenant mutation query.

Global maintenance is permitted only when the underlying data is genuinely platform-global or the operation is an explicitly authorized, audited, fail-closed platform control with its own guard contract.

## Service boundary

Tenant-mutating service functions must accept an explicit school/tenant identifier or operate under a required canonical tenant context. Querysets must include the tenant predicate when the model does not enforce tenant scoping through its manager.

A background service must not infer tenant from incidental data, the first matching row, process-local residue, or a client-supplied role/header concept.

## Context restoration

`tenant_context` must restore the prior context on exit. A worker must never leak one school's context into the next task or school iteration.

## Scheduled payment boundary

While external payment processing is `DEFERRED — NEW OWNER / DISABLED / FAIL CLOSED`:

- provider-dependent payment retry/dunning execution must perform no state mutation;
- processor payout audit/reconciliation tasks must perform no provider-dependent state mutation;
- no scheduled worker may create or use live processor credentials;
- payment-dependent jobs return an explicit `payment_integration_on_hold` result.

A future payment provider may replace this hold only through a separate provider-specific implementation, security, financial-control, and transaction-certification program.

## Current implementation aligned by this decision

- communications outbox: one outbox item/school under `tenant_context` with bounded retry/dead-letter handling;
- billing grace enforcement: one active school at a time under `tenant_context`, service explicitly filtered by `school_id`;
- support SLA escalation: one active school at a time under `tenant_context`, including manual platform-operator trigger;
- analytics customer-health refresh: one active school at a time under `tenant_context`;
- predictive analytics: one queued tenant identifier per school and tenant context during model execution;
- payment dunning and daily payout scheduled tasks: fail closed with `mutated=false` while provider integration is on hold;
- retention purge beat entry remains preview-only by default and retains its separate execution/confirmation/global-authorization safeguards.

## Retry and idempotency

- retries must be bounded;
- deterministic authorization/input failures must not be retried as transient failures;
- operations that may repeat must be idempotent or use locking/unique constraints/state transitions that make repeated execution safe;
- side effects must retain tenant identity in logs/audit evidence.

## Observability

Background execution should expose enough non-secret context to identify:

- task name;
- school/tenant identifier;
- execution outcome;
- retry/dead-letter state where applicable;
- correlation/job identity where available;
- failure class without leaking credentials or protected data.

## Enforcement

Regression tests must protect tenant-explicit service signatures and scheduled-task use of canonical tenant context. Payment-hold tests must prove payment-dependent scheduled tasks return hold status and perform no mutation.

## Consequences

### Positive

- eliminates ambiguous cross-tenant worker mutation;
- makes tenant identity explicit outside HTTP requests;
- prevents context leakage between schools;
- gives the new owner one background-processing rule across modules;
- preserves the payment fail-closed boundary.

### Tradeoff

Platform-wide jobs perform an explicit per-school orchestration step rather than one broad query. This is intentional isolation overhead.

## Reversal / replacement

Any future platform-global batch architecture must prove equivalent tenant isolation, auditability, failure containment, retry semantics, and rollback behavior through a new ADR and exact-head evidence before replacing this decision.
