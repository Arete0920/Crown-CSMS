# Scheduling Final Disposition

Status: merge-gated completion record
Active repository: `tcmegahan/Crown-CSMS`

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

- `crown_api.views_scheduling`: bounded API compatibility reads while canonical Term/Section reads are preferred.
- `crown_api.serializers_scheduling`: response-contract compatibility for retained reads.
- regression/test fixtures that prove old authorized semantics and prevent accidental deletion before migration proof exists.

Prohibited after final consumer cutover:

- operational wizard writes to legacy Term/Section/SectionEnrollment;
- Django admin write registration for legacy Scheduling masters;
- local Scheduling seed writes to legacy Scheduling masters;
- sandbox student schedule creation in legacy Scheduling masters;
- demo reset/rehearsal proof that treats legacy Section as Scheduling authority.

## Final consumer cutover

The final cleanup:

1. removes legacy Scheduling Term/Section/SectionEnrollment from Django admin;
2. converts `backend/scripts/seed_scheduling.py` to canonical academics Term/Course/Section writes;
3. converts the student sandbox schedule fixture to canonical academics Enrollment plus canonical room/bell/placement data using an explicit sandbox-account compatibility identity;
4. converts local demo reset and rehearsal proofs to canonical Scheduling master/placement checks.

The local seed intentionally does not fabricate roster mappings across `core.Student` and `households.Student`.

## Completion gate

Scheduling may be marked **COMPLETED AND VERIFIED** only when:

- PR #22 (API/read adapter correction) is merged on its certified exact head;
- the final consumer-cutover PR is merged on its certified exact head;
- required exact-head CI, tenant isolation, full backend tests, governed coverage, sandbox evidence, runtime/full-surface proof, repository policy, and security/release gates are terminal green;
- zero unresolved actionable review threads remain;
- `main` is re-fetched and verified after both merges;
- a final repository consumer scan finds no unexplained production-capable legacy Scheduling writer.

Duplicate compatibility tables remain retained, not authoritative. Their future physical retirement is governed by the separate identity/data convergence program and must not be inferred from Scheduling module completion.
