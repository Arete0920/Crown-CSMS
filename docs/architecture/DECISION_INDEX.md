# CROWN Architecture Decision Index

**Status:** CANONICAL  
**Owner:** CROWN Engineering  
**Effective date:** 2026-08-08

## Purpose

This index is the authoritative list of accepted architecture decisions. Documents not listed here may describe implementation, analysis, inventory, or proposed direction, but they are not accepted architecture authority.

## Accepted decisions

| ID | Decision | Status | Implementation state |
|---|---|---|---|
| ADR-0001 | `decisions/ADR-0001-tenant-resolution-and-enforcement.md` | ACCEPTED | Canonical context, protected-route enforcement, explicit override authorization, compatibility binding, structured tenant-decision audit, cleanup, focused negative tests, tenant-boundary tripwires, tenant fixture regressions, and the supported-role matrix are present in source. Bounded deployed-runtime certification evidence is recorded in `docs/CURRENT_RELEASE_STATUS.md` and GitHub issue #1619. Compatibility middleware retirement remains controlled convergence work. See `TENANT_ENFORCEMENT_IMPLEMENTATION_STATUS.md`. |
| ADR-0002 | `decisions/ADR-0002-canonical-frontend-api-transport.md` | ACCEPTED | `authClient.js` is the protected first-party transport authority. Shared wrappers converge on it; Board Executive, Learning Continuity, and shared CROWN dashboard metrics are migrated in the final architecture hardening lane; public/bootstrap/external/dev/test exceptions remain explicit. |
| ADR-0003 | `decisions/ADR-0003-tenant-aware-background-jobs.md` | ACCEPTED | Communications already binds tenant context. Billing grace enforcement, support SLA escalation, customer-health refresh, and predictive analytics are tenant-explicit in the final architecture hardening lane. Provider-dependent dunning and payout scheduled tasks fail closed with no mutation while payments are deferred. |
| ADR-001 | `ADR-001-CANONICAL-HOUSEHOLD-GUARDIAN-STUDENT.md` | ACCEPTED FOR OPERATIONAL WRITES | `core.Family`, `core.Guardian`, and `core.Student` own canonical operational writes; compatibility-domain reconciliation remains incomplete. |

## Decisions still required before material boundary changes

The following topics do not yet have an accepted ADR in this index. Their absence does not invalidate the certified bounded release. Material changes in these areas require an accepted ADR first:

1. domain ownership and cross-domain service boundaries;
2. external integration authority and adapter boundaries;
3. deployment topology, release identity, rollback, and database restore;
4. reporting and analytics read-model boundaries;
5. document and file storage authority, retention, and access controls;
6. payment-provider adapter and future activation contract.

The certified release already demonstrated exact deployment identity, migration, production health, tenant integrity, and fail-closed payment containment. The remaining ADRs govern future architectural evolution, compatibility convergence, or future-owner implementation choices; they must not be represented as already implemented decisions.

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

An ADR is not accepted merely because it is committed. It becomes authoritative only when its status is accepted and it is listed in this index through the repository's governed review/merge path.

## Supersession

A replacement ADR must name the superseded decision, explain compatibility and migration consequences, update this index, and preserve the prior decision in Git history.
