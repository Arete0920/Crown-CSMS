# Canonical Household, Guardian, and Student Consumer Inventory

**Status:** Controlled architecture supporting record — operational write authority accepted; compatibility convergence remains open  
**Effective date:** 2026-08-08  
**Accepted decision:** `docs/architecture/ADR-001-CANONICAL-HOUSEHOLD-GUARDIAN-STUDENT.md`  
**Related architecture hardening:** #1925

## Purpose

This record defines the current identity-model authority and the safe boundary for compatibility convergence. It does not authorize destructive migration, table renaming, silent identifier remapping, compatibility-table removal, or movement of the certified production identity.

## Current write authority

`core.Family`, `core.Guardian`, and `core.Student` are the canonical operational write records for school-scoped family, guardian, and student identity.

That authority is supported by current dependency ownership:

- each canonical record belongs to `core.School`;
- `core.Student` participates in enrollment and tuition workflows;
- `core.Family`/`core.Student` participate in ledger relationships;
- `core.Guardian` participates in authenticated user relationships;
- admissions maintains explicit compatibility bridges to the separate `crown_api` household/person domain.

The accepted decision establishes write authority. It does not assert that compatibility tables are empty, semantically equivalent, or removable.

## Persisted identity families

### Canonical operational family

`backend/core/models.py` defines the authoritative operational `Family`, `Guardian`, and `Student` records, including direct school ownership and the lifecycle relationships used by core school operations.

### `households` compatibility domain

`backend/households/models.py` defines separate `Household`, `Guardian`, and `Student` persistence with its own UUID identities and school identifiers.

This domain remains compatibility/read infrastructure. It is not an approved canonical operational writer and must not be removed on model-name similarity.

### `crown_api` person/membership compatibility domain

`backend/crown_api/models_households.py` defines normalized `Person`, `Household`, `HouseholdMember`, and `Student` structures used by compatibility/API flows including admissions bridges.

This domain is not interchangeable with the canonical core family.

### Guardian-household wizard session domain

`backend/guardian_household_wizard/models.py` stores tenant-bound workflow session state and JSON payloads. It coordinates workflow; it is not an independent identity authority.

## Canonical wizard write contract

The guardian-household wizard writes to the canonical core identity spine under a transactional, tenant-bound contract. Current rules include:

1. selected students must exist in the active school;
2. students must not be silently moved between families;
3. family/guardian changes occur transactionally;
4. guardian identity follows the established school/email uniqueness boundary;
5. a guardian attached to another family is a conflict rather than an automatic merge;
6. repeated commit is idempotent through persisted wizard state/result;
7. validation/database failure rolls back writes;
8. the wizard does not write to legacy `households` or `crown_api` identity tables.

## Compatibility bridges

### Admissions

Admissions may retain simultaneous references to canonical core identities and compatibility household/student identities. These are explicit bridges, not evidence that either domain can be deleted.

### Household-family bridge

`core.HouseholdFamilyLink` stores a school-scoped compatibility household identifier linked to canonical `core.Family`. Its existence is an explicit translation boundary, not a second family write authority.

## Consumer classes that must be considered before convergence

Any future consolidation must inventory at least:

- core models, admin, permissions, serializers, services, migrations, tests, seeds and reports;
- households models, serializers, views, imports/exports and migrations;
- crown_api household/person/student models and API consumers;
- admissions models, serializers, links and enrollment handoff;
- guardian-household wizard backend/frontend contracts;
- enrollment, tuition, ledger, attendance, gradebook, financial aid, communications, portal, reporting and analytics consumers;
- asynchronous tasks and management commands;
- external IDs and integration mappings.

This list defines mandatory categories; it is not a claim that compatibility retirement has already been fully inventoried.

## Required convergence proof

Compatibility-domain retirement remains open and requires:

1. complete reader/writer/migration/report/import/export/task/signal/test/seed/frontend inventory;
2. table/field semantics, row counts, tenant distribution, nullability, uniqueness, external-ID, duplicate and orphan analysis;
3. deterministic cross-family mapping rules;
4. classification of every consumer as canonical, compatibility, bridge, migration-only, historical, or removable-after-proof;
5. expand-contract or equivalent non-destructive migration rehearsal on a production-shaped non-production copy;
6. tenant-by-tenant mapped/unmatched/duplicate/orphan/referential-integrity counts;
7. representative admissions, enrollment, attendance, billing, financial-aid, portal and reporting regression proof;
8. migration timing/locking assessment;
9. rollback or forward-fix rehearsal without losing canonical writes;
10. exact-head governed review before compatibility retirement.

## Constraints

- No destructive migration by inference.
- No table rename solely because models share names.
- No silent ID remapping or cross-tenant merge.
- No compatibility bridge removal before reconciliation evidence.
- No legacy-domain removal before representative rollback/forward-fix proof.
- Tenant isolation remains fail closed throughout migration work.
- New operational write paths must follow the canonical core authority unless a later accepted ADR explicitly replaces ADR-001.

## Certified-release/current-development boundary

The certified production release remains the exact source/tag recorded in `docs/CURRENT_RELEASE_STATUS.md` and #1619. The accepted identity authority applies architecturally, while this inventory does not claim that later development commits have inherited production certification.

## Current disposition

- Canonical operational family/guardian/student write authority: **ACCEPTED**.
- Guardian-household wizard canonical write contract: **IMPLEMENTED**.
- Compatibility bridges: **RETAIN / EXPLICIT**.
- Compatibility data convergence and retirement: **OPEN / NOT SAFE TO COLLAPSE WITHOUT FULL PROOF**.
- Destructive identity consolidation before handoff: **NOT AUTHORIZED**.
