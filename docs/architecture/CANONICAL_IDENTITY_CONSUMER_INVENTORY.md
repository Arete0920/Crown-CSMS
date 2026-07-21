# Canonical Household, Guardian, and Student Consumer Inventory

**Status:** Operational write authority accepted; compatibility convergence remains open  
**Related issue:** #1353  
**Observed main SHA:** `dc48cd4c508a5a831ebc2e3c0e0de3ee7116e946`  
**Accepted decision:** `docs/architecture/ADR-001-CANONICAL-HOUSEHOLD-GUARDIAN-STUDENT.md`

## Purpose

This document records the current identity-model authority and the remaining dependency, reconciliation, migration, and rollback work. It does not authorize destructive migration, table renaming, silent identifier remapping, compatibility-table removal, or production release.

## Current decision

`core.Family`, `core.Guardian`, and `core.Student` are the canonical operational write records for school-scoped family, guardian, and student identity.

This decision is based on verified dependency ownership:

- each record has a real `core.School` foreign key;
- `core.Student` is referenced by enrollment and tuition;
- `core.Family` and `core.Student` are referenced by the ledger;
- `core.Guardian` is referenced by authenticated user accounts;
- admissions already bridges core identity records to the separate `crown_api` household/person domain.

The decision establishes write authority. It does not prove that the other persisted model families are empty, equivalent, safely removable, or fully reconciled.

## Persisted identity families

### Canonical operational family

`backend/core/models.py` defines:

- `Family` with a direct `School` foreign key;
- `Guardian` linked to `Family`, with relationship, portal-access, and custody semantics;
- `Student` linked to `Family`, `School`, and `GradeLevel`, with student number, date of birth, and lifecycle status.

Verified operational dependencies include:

- `UserAccount.guardian`;
- `Enrollment.student`;
- `StudentTuition.student`;
- `LedgerEntry.family` and optional `LedgerEntry.student`.

### `households` compatibility domain

`backend/households/models.py` defines separate `Household`, `Guardian`, and `Student` tables using UUID primary keys and bare indexed `school_id` UUID fields.

This domain remains supported for compatibility and read behavior. It is not an approved canonical writer and must not be deleted or renamed without tenant-by-tenant reconciliation and rollback proof.

### `crown_api` person and membership domain

`backend/crown_api/models_households.py` defines `Person`, `Household`, `HouseholdMember`, and `Student` using a normalized person-and-membership structure.

This family remains a compatibility domain referenced by admissions. It is not interchangeable with the canonical core family and cannot be removed by model-name similarity.

### Guardian-household wizard session domain

`backend/guardian_household_wizard/models.py` stores a tenant-bound workflow session with JSON household, guardian, and student-link payloads. It is a workflow coordinator, not an independent authoritative identity store.

## Repaired wizard write contract

The previously documented wizard commit mismatch is no longer an active defect.

Merged implementation `452d37e3aab6e8ed3100690cbbb2f349209186ac` established a transactionally safe, tenant-bound writer to the canonical core identity spine.

The current contract requires:

1. every selected student exists in the active school;
2. all selected students already belong to one `core.Family`;
3. students are never silently reassigned between families;
4. family and guardian updates occur in one transaction;
5. guardian identity follows the existing `(school, email)` uniqueness rule;
6. a guardian email attached to another family is a conflict, not an automatic merge;
7. repeated commit is idempotent through the locked wizard session and persisted result;
8. validation or database failure rolls back all writes;
9. legacy `households` and `crown_api` identity tables receive no writes from this wizard.

Focused regression proof covers same-school commit, repeated commit, no legacy writes, cross-school denial, mixed-family rejection, guardian conflict rollback, and verify transition.

## Verified compatibility bridges

### Admissions

`AdmissionsApplication` links to required `core.Family`, optional `core.Student`, optional `crown_api.Household`, and optional `crown_api.Student`.

These references are an explicit compatibility bridge, not proof that either domain can be removed.

### Household-family bridge

`core.HouseholdFamilyLink` stores a school-scoped household UUID linked to `core.Family`. Migration `0010_backfill_household_family_link.py` derives this bridge from admissions applications that already contain both family and household references.

## Verified consumer starting set

The current inventory includes:

- `backend/core/models.py` and `backend/core/admin.py`;
- core household-family-link migrations;
- `backend/households/models.py`, serializers, views, and migrations;
- `backend/crown_api/models_households.py`, models exports, and student views;
- admissions models, serializers, and household/student link views;
- guardian-household wizard models, views, tests, migrations, and frontend client;
- billing household-delinquency migration.

This is a verified starting set, not a complete dependency graph.

## Remaining convergence work

Issue #1353 remains open for compatibility-domain convergence. Required work includes:

1. enumerate all readers, writers, migrations, reports, imports, exports, tasks, signals, tests, seeds, and frontend contracts;
2. record table names, row counts, tenant distribution, nullability, uniqueness, external IDs, duplicate risk, and orphan risk;
3. define deterministic cross-family identity mapping;
4. classify every consumer as canonical, compatibility, bridge, migration-only, historical, or removable-after-proof;
5. rehearse expand-contract migration on a production-shaped non-production copy;
6. capture mapped, unmatched, duplicate, orphan, and referential-integrity counts by tenant;
7. prove cross-tenant isolation, API compatibility, reporting, admissions, enrollment, attendance, billing, financial aid, and portal behavior;
8. measure migration timing and lock impact;
9. rehearse rollback or forward-fix without losing canonical writes;
10. obtain exact-SHA review and Product Owner acceptance before any compatibility-domain retirement.

## Constraints

- No destructive migration.
- No table rename by inference.
- No silent ID remapping or cross-tenant merge.
- No removal of compatibility bridges before reconciliation evidence.
- No legacy removal before representative rollback proof.
- Tenant isolation remains fail-closed throughout migration work.
- The accepted write authority and repaired wizard do not establish complete data convergence, deployed runtime proof, compliance completion, or production authorization.

## Exit criteria

The convergence inventory and planning phase passes only when:

- every active model and consumer is enumerated;
- field ownership and non-equivalent semantics are explicit;
- deterministic cross-family mapping is documented;
- representative reconciliation counts are defined and reproducible;
- a non-destructive migration sequence is approved;
- rollback checkpoints and integrity assertions are specified;
- no unmatched record is left without an explicit disposition.

Until those conditions are met, compatibility convergence remains open under #1353 and production remains not approved.
