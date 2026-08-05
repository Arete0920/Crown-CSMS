# CROWN Architecture Decision Index

**Status:** CANONICAL  
**Owner:** CROWN Engineering  
**Effective date:** 2026-08-04

## Purpose

This index is the authoritative list of accepted architecture decisions. Documents not listed here may describe implementation, analysis, inventory, or proposed direction, but they are not accepted architecture authority.

## Accepted decisions

| ID | Decision | Status | Implementation state |
|---|---|---|---|
| ADR-0001 | `decisions/ADR-0001-tenant-resolution-and-enforcement.md` | ACCEPTED | Canonical context, protected-route enforcement, explicit override authorization, compatibility binding, structured tenant-decision audit, cleanup, focused negative tests, tenant-boundary tripwires, tenant fixture regressions, and the supported-role matrix are present in source. Bounded deployed-runtime certification evidence is recorded in `docs/CURRENT_RELEASE_STATUS.md` and GitHub issue #1619. Complete consumer migration, exhaustive asynchronous-task proof, compatibility retirement, and redundant middleware removal remain post-release convergence work. See `TENANT_ENFORCEMENT_IMPLEMENTATION_STATUS.md`. |
| ADR-001 | `ADR-001-CANONICAL-HOUSEHOLD-GUARDIAN-STUDENT.md` | ACCEPTED FOR OPERATIONAL WRITES | `core.Family`, `core.Guardian`, and `core.Student` own canonical operational writes; compatibility-domain reconciliation remains incomplete. |

## Decisions still required before material boundary changes

The following topics do not yet have an accepted ADR in this index. Their absence does not invalidate the certified bounded release, but material changes in these areas require an accepted ADR first:

1. canonical frontend request client and transport contract;
2. domain ownership and cross-domain service boundaries;
3. asynchronous execution, tenant binding, retries, idempotency, and observability;
4. external integration authority and adapter boundaries;
5. deployment topology, release identity, rollback, and database restore;
6. reporting and analytics read-model boundaries;
7. document and file storage authority, retention, and access controls;
8. payment-provider adapter and fail-closed activation contract.

The certified release already demonstrated exact deployment identity, migration, production health, tenant integrity, and fail-closed payment containment. The missing ADRs govern future architectural evolution and completion of deferred operational maturity; they must not be misrepresented as completed decisions.

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
