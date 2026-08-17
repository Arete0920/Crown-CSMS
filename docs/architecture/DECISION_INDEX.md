# CROWN Architecture Decision Index

**Status:** CANONICAL  
**Owner:** CROWN Engineering  
**Last verified:** 2026-08-17

## Purpose

This index is the authoritative list of accepted architecture decisions. Documents not listed here may describe implementation, analysis, inventory, or proposed direction, but they are not accepted architecture authority. Current release/runtime/turnover status is governed separately by `docs/CURRENT_RELEASE_STATUS.md` and Crown-CSMS issue #14.

## Accepted decisions

| ID | Decision | Status | Implementation state |
|---|---|---|---|
| ADR-0001 | `decisions/ADR-0001-tenant-resolution-and-enforcement.md` | ACCEPTED | Canonical request tenant context, protected-route enforcement, explicit override authorization, compatibility binding, structured tenant-decision audit, cleanup, focused negatives, and tenant-boundary tripwires are represented in source. Compatibility middleware retirement remains controlled convergence work. |
| ADR-0002 | `decisions/ADR-0002-canonical-frontend-api-transport.md` | ACCEPTED | `authClient.js` is the protected first-party transport authority. Shared wrappers converge on it; public/bootstrap/external/dev/test exceptions remain explicit and must not receive protected CROWN context. |
| ADR-0003 | `decisions/ADR-0003-tenant-aware-background-jobs.md` | ACCEPTED | Tenant-owned asynchronous mutation must execute under explicit school context. Provider-dependent payment jobs remain fail closed while payment processing is disabled. |
| ADR-001 | `ADR-001-CANONICAL-HOUSEHOLD-GUARDIAN-STUDENT.md` | ACCEPTED FOR OPERATIONAL WRITES | `core.Family`, `core.Guardian`, and `core.Student` own canonical operational writes; compatibility-domain reconciliation remains controlled convergence work. |

## Decisions still required before material boundary changes

The following topics do not yet have an accepted ADR in this index. Their absence does not erase current implemented controls, but material changes in these areas require an accepted ADR first:

1. complete domain ownership and cross-domain service boundaries;
2. external integration authority and adapter boundaries, including Microsoft 365 Education;
3. deployment topology, release identity, rollback, and database restore authority;
4. reporting and analytics read-model boundaries;
5. document/file storage authority, retention, and access controls;
6. payment-provider adapter and future activation contract;
7. HR/Core Staff ownership convergence;
8. report-card official-record authority where not already governed by accepted Gradebook/Transcript boundaries;
9. Little Lambs daycare-specific authority beyond the current Aftercare compatibility surface.

These are explicit architecture follow-ups, not permission to imply that an unimplemented target is already complete.

## Current evidence boundary

Repository source and CI evidence can prove implemented architecture and guardrails. They do not independently prove a deployed production identity, current operational rollback/restore execution, external-provider configuration, qualified legal/compliance review, or completed owner turnover.

Historical Crown2026 release evidence is provenance only and does not control Crown-CSMS architecture or release decisions.

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
- explicit approval record or the applicable approved solo-developer governance workaround.

An ADR is not accepted merely because it is committed. It becomes authoritative only when its status is accepted and it is listed in this index through the repository's governed review/merge path.

## Supersession

A replacement ADR must name the superseded decision, explain compatibility and migration consequences, update this index, and preserve the prior decision in Git history.
