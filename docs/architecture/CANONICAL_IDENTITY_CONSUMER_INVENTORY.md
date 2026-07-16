# Canonical Household, Guardian, and Student Consumer Inventory

**Status:** Verified inventory in progress; no canonical model decision yet  
**Related issue:** #1353  
**Base SHA:** `418802cc900fe319a7ba8dcdc60fe27deae96192`

## Purpose

This document records the verified dependency inventory required to resolve overlapping household, guardian, and student model families. It does not authorize a rename, destructive migration, table merge, silent identifier remap, or legacy-model removal.

## Executive finding

The live repository contains three distinct persisted identity families plus one stale wizard commit contract:

1. `core.Family`, `core.Guardian`, and `core.Student`;
2. `households.Household`, `households.Guardian`, and `households.Student`;
3. `crown_api.models_households.Person`, `Household`, `HouseholdMember`, and `Student`;
4. `guardian_household_wizard.views.commit_session`, which writes an older fourth shape that is not implemented by the current `households` models.

Canonicalization therefore cannot be treated as a two-model rename. It requires dependency mapping, compatibility design, representative reconciliation, and rollback proof.

## Verified model families

### `core` application

`backend/core/models.py` defines:

- `Family` with a direct `School` foreign key;
- `Guardian` linked to `Family`, with relationship, portal-access, and custody fields;
- `Student` linked to `Family`, `School`, and `GradeLevel`, with student number, date of birth, and lifecycle status.

The same file also proves that this family is embedded in operational records:

- `UserAccount.guardian`;
- `Enrollment.student`;
- `StudentTuition.student`;
- `LedgerEntry.family` and optional `LedgerEntry.student`.

This makes the `core` family financially and operationally significant.

### `households` application

`backend/households/models.py` defines:

- `Household`;
- `Guardian`;
- `Student`.

These models use UUID primary keys and bare indexed `school_id` UUID fields. `Guardian` and `Student` reference `Household`. The declared database tables are `household`, `guardian`, and `student`.

The current fields are materially narrower than the `core` family. For example, `households.Guardian` contains `first_name`, `last_name`, `email`, `phone`, and `is_primary`, while `core.Guardian` also owns relationship, portal-access, and custody semantics.

### `crown_api` identity spine

`backend/crown_api/models_households.py` defines:

- `Person`;
- `Household`;
- `HouseholdMember`;
- `Student`.

This family uses a normalized person-and-membership structure rather than separate guardian rows. It is exported from `backend/crown_api/models.py` and is therefore the `crown_api.Household` and `crown_api.Student` model family referenced by other apps.

`AdmissionsApplication` links both to `core.Family` / `core.Student` and optionally to `crown_api.Household` / `crown_api.Student`. This is an explicit compatibility bridge, not evidence that either side can be removed.

### Guardian-household wizard session domain

`backend/guardian_household_wizard/models.py` stores a tenant-bound workflow session with JSON household, guardian, and student-link payloads. The session itself uses `core.School` and the configured authentication user.

The wizard is therefore a workflow coordinator, not a fourth authoritative identity store.

## Verified wiring defect: wizard commit contract

`backend/guardian_household_wizard/views.py` currently imports:

```python
from households.models import Household, Guardian, HouseholdStudent
```

The current `households.models` contract contains no `HouseholdStudent` model.

The commit path also attempts to write fields that do not exist:

- `Household.address` does not exist; the model uses `address1`, `address2`, `city`, `state`, and `postal_code`;
- `Guardian.name` does not exist; the model uses `first_name` and `last_name`;
- `Guardian.custody_type`, `contact_priority`, and `receives_communications` do not exist;
- student linkage is modeled as `households.Student.household`, not a `HouseholdStudent` join table.

The existing wizard tests stop after session creation, configuration, guardian payload validation, and tenant isolation. They do not execute `link_students`, `commit_session`, or `verify_session`. The broken commit contract can therefore remain green in the general test suite.

This defect must be repaired and covered by a full-flow regression before the guardian-household wizard can be treated as functionally complete.

## Verified compatibility bridges

### Admissions

`backend/admissions/models.py` links each application to:

- required `core.Family`;
- optional `core.Student`;
- optional `crown_api.Household`;
- optional `crown_api.Student`.

### Household-family bridge

`core.HouseholdFamilyLink` stores a school-scoped UUID `household_id` linked to `core.Family`. Migration `0010_backfill_household_family_link.py` derives this bridge from admissions applications that already have both family and household references.

This bridge shows that the repository already expects coexistence and reconciliation between model families.

## Verified consumer surface

The current inventory includes:

- `backend/core/models.py`;
- `backend/core/admin.py`;
- `backend/core/migrations/0009_household_family_link.py`;
- `backend/core/migrations/0010_backfill_household_family_link.py`;
- `backend/households/models.py`;
- `backend/households/serializers.py`;
- `backend/households/views.py`;
- `backend/households/migrations/0008_households_guardians_students.py`;
- `backend/crown_api/models_households.py`;
- `backend/crown_api/models.py`;
- `backend/crown_api/views_students.py`;
- `backend/admissions/models.py`;
- `backend/admissions/serializers.py`;
- `backend/admissions/views_admissions_links.py`;
- `backend/guardian_household_wizard/models.py`;
- `backend/guardian_household_wizard/views.py`;
- `backend/guardian_household_wizard/tests/test_views.py`;
- `backend/guardian_household_wizard/migrations/0001_initial.py`;
- `backend/billing/migrations/0084_stage2_household_delinquency.py`;
- `frontend/dashboards/src/api/guardian_household_wizard.js`.

This remains a starting inventory, not a complete dependency graph.

## Required next inventory passes

Before selecting a canonical family, identify and classify every dependency in:

1. admissions and enrollment;
2. attendance and gradebook;
3. billing, financial aid, delinquency, ledger, and reporting;
4. guardian authentication and parent portal access;
5. dashboards, exports, migration tooling, and seed data;
6. serializers, viewsets, permissions, signals, tasks, and background jobs;
7. foreign keys, UUID references, compatibility links, and uniqueness rules;
8. frontend contracts and API response schemas.

Each consumer must record:

- source file and symbol;
- model family used;
- read, write, or migration behavior;
- tenant-scoping mechanism;
- identifier type and mapping assumptions;
- authoritative fields owned by the consumer;
- data-loss and rollback risk;
- proposed canonical or compatibility disposition.

## Current constraints

- No destructive migration.
- No table rename by inference.
- No silent ID remapping.
- No removal of compatibility bridges before reconciliation evidence.
- No legacy removal before representative rollback proof.
- Tenant isolation must remain fail-closed throughout compatibility work.
- Admissions, enrollment, guardian access, attendance, billing, financial aid, and reporting must be covered by regression evidence.

## Exit criteria for the inventory phase

The inventory phase passes only when:

- all model definitions and active consumers are enumerated;
- ownership of each data field is explicit;
- duplicate and non-equivalent fields are identified;
- cross-family identity mapping is documented;
- representative tenant reconciliation counts are defined;
- a non-destructive compatibility and migration sequence is proposed;
- rollback checkpoints and integrity assertions are specified;
- the guardian-household wizard full commit flow is repaired and tested separately.

Until those conditions are met, issue #1353 remains open and no model family is declared canonical.
