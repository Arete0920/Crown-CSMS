# CROWN Architecture Documentation

**Status:** CANONICAL ARCHITECTURE GATEWAY  
**Owner:** CROWN Engineering  
**Effective date:** 2026-07-28

## Authority

Architecture documentation describes system structure, trust boundaries, canonical data ownership, integration boundaries, and accepted technical decisions. It does not certify production readiness or override `docs/CURRENT_RELEASE_STATUS.md`.

## Required reading order

1. `ARCHITECTURE_MAP.md` — canonical owner-facing architecture map.
2. `SYSTEM_OVERVIEW.md` — repository-visible implementation and convergence status.
3. `DECISION_INDEX.md` — authoritative list of accepted ADRs and decisions still required.
4. `decisions/ADR-0001-tenant-resolution-and-enforcement.md` — canonical tenant contract.
5. `ADR-001-CANONICAL-HOUSEHOLD-GUARDIAN-STUDENT.md` — canonical operational identity-write authority.
6. `CANONICAL_IDENTITY_CONSUMER_INVENTORY.md` — identity compatibility and convergence inventory.
7. `../engineering/DEV_SETUP.md` — supported development setup.
8. `../operations/README.md` — deployment, recovery, and operator navigation.
9. `../CURRENT_RELEASE_STATUS.md` — current release authority.

## Architecture domains

This directory governs durable descriptions of:

- platform and subsystem boundaries;
- frontend, backend, API, and persistence responsibilities;
- multi-tenant isolation and trusted school context;
- authentication, authorization, and role boundaries;
- domain ownership and shared service contracts;
- external integrations and payment-provider boundaries;
- asynchronous work and tenant propagation;
- deployment topology and runtime dependencies;
- architecture decisions, constraints, migrations, and supersession.

## Classification rules

- `ARCHITECTURE_MAP.md`, this gateway, and `DECISION_INDEX.md` are canonical architecture navigation.
- An ADR is authoritative only when accepted and listed in `DECISION_INDEX.md`.
- `SYSTEM_OVERVIEW.md` describes verified source behavior and implementation debt; it is not an ADR.
- Inventories describe observed consumers and compatibility obligations; they do not create authority by themselves.
- Completion matrices, test results, generated diagrams, and audit output are not architecture authority.
- New target architecture must be labeled as target or proposed until implemented and verified.

## Change control

A focused ADR is required when changing:

- tenant-resolution precedence or enforcement ownership;
- canonical identity or durable data-write authority;
- public API compatibility or transport contracts;
- cross-domain ownership or integration boundaries;
- asynchronous execution and idempotency contracts;
- deployment identity, rollback, restore, or secret authority;
- payment-provider activation and settlement boundaries.

Runtime implementation and documentation-only authority changes should normally use separate pull requests.
