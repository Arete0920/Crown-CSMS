# CROWN Architecture Decision Index

**Status:** CANONICAL  
**Owner:** CROWN Engineering  
**Effective date:** 2026-07-28

## Purpose

This index is the authoritative list of accepted architecture decisions. Documents not listed here may describe implementation, analysis, inventory, or proposed direction, but they are not accepted architecture authority.

## Accepted decisions

| ID | Decision | Status | Implementation state |
|---|---|---|---|
| ADR-0001 | `decisions/ADR-0001-tenant-resolution-and-enforcement.md` | ACCEPTED | Canonical contract accepted; middleware, queryset, permission, task, and compatibility convergence remains incomplete. |
| ADR-001 | `ADR-001-CANONICAL-HOUSEHOLD-GUARDIAN-STUDENT.md` | ACCEPTED FOR OPERATIONAL WRITES | `core.Family`, `core.Guardian`, and `core.Student` own canonical operational writes; compatibility-domain reconciliation remains incomplete. |

## Decisions still required

The following topics do not yet have an accepted ADR in this index:

1. canonical frontend request client and transport contract;
2. domain ownership and cross-domain service boundaries;
3. asynchronous execution, tenant binding, retries, and idempotency;
4. external integration authority and adapter boundaries;
5. deployment topology, release identity, rollback, and database restore;
6. reporting and analytics read-model boundaries;
7. document and file storage authority, retention, and access controls;
8. payment-provider adapter and fail-closed activation contract.

## ADR admission rules

An ADR must include:

- context and decision drivers;
- options considered;
- the accepted decision;
- trust, tenant, security, and data implications;
- compatibility and migration impact;
- validation requirements;
- rollback or reversal strategy;
- named implementation status;
- explicit approval record.

An ADR is not accepted merely because it is committed. It becomes authoritative only when its status is accepted and it is listed in this index.

## Supersession

A replacement ADR must name the superseded decision, explain compatibility and migration consequences, update this index, and preserve the prior decision in Git history.
