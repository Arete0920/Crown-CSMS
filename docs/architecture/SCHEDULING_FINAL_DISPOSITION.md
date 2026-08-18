# Scheduling Final Disposition

**Status:** Canonical supporting disposition record  
**Active repository:** `Arete-Advisory-Group/Crown-CSMS`  
**Last reconciled:** 2026-08-17

## Canonical Scheduling authority

Operational Scheduling writes are owned by:

- `academics.Term` bound to `core.AcademicYear`
- `academics.Course`
- `academics.Section`
- `academics.TeacherAssignment` -> `core.Staff`
- `section_scheduler_wizard.SectionPlacement`
- `room_setup_wizard.Room`
- `bell_schedule_wizard.BellSchedule`, `DayTemplate`, and `PeriodBlock`

The advanced and basic Scheduling wizards write canonical section/placement authority. Multiple sections for the same course/term are represented by durable section UUIDs, and one section may have multiple distinct recurring meeting placements.

## Student identity authority

`docs/architecture/ADR-001-CANONICAL-HOUSEHOLD-GUARDIAN-STUDENT.md` and `SYSTEM_OVERVIEW.md` remain authoritative:

- `core.Student` is the canonical operational student identity.
- `households.Student` remains a supported compatibility/read-domain identity pending separately governed convergence.
- No Scheduling path may guess, merge, or silently remap student identities by name, email, list position, or another heuristic.

`academics.Enrollment` currently references `households.Student`; that cross-domain convergence is a platform/Academics migration concern, not authorization to redefine student identity inside Scheduling.

## Compatibility disposition

The duplicate `crown_api.models_scheduling_core` tables are retained for reversible compatibility reads only. Destructive retirement is not part of Scheduling completion because the repository architecture requires explicit tenant-by-tenant identity/data reconciliation before table retirement.

Allowed retained consumers:

- `crown_api.views_scheduling`: bounded API compatibility reads while canonical Term/Section reads are preferred;
- `crown_api.serializers_scheduling`: response-contract compatibility for retained reads;
- regression/test fixtures that prove old authorized semantics and prevent accidental deletion before migration proof exists.

Prohibited:

- operational wizard writes to legacy Term/Section/SectionEnrollment;
- Django admin write registration for legacy Scheduling masters;
- local Scheduling seed writes to legacy Scheduling masters;
- sandbox student schedule creation in legacy Scheduling masters;
- demo reset/rehearsal proof that treats legacy Section as Scheduling authority.

## Consumer-cutover disposition

The completed cutover design removes legacy Scheduling Term/Section/SectionEnrollment from operational write ownership, moves local scheduling seed/demo paths to canonical academics/placement authority, and preserves explicit compatibility identity boundaries rather than fabricating roster mappings between `core.Student` and `households.Student`.

## Historical completion sequence

Earlier Scheduling PR numbers and exact-head checks are retained in Git/PR history as provenance. They are not current release authority and must not be treated as present turnover gates. Current Scheduling authority is determined by the implemented source on current Crown-CSMS `main`, current tests/evidence, `ARCHITECTURE_MAP.md`, and `docs/CURRENT_RELEASE_STATUS.md`.

Duplicate compatibility tables remain retained, not authoritative. Future physical retirement is governed by the separate identity/data convergence program and must not be inferred from Scheduling module completion.
