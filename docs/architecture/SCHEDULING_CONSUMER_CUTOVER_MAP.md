# Scheduling Consumer Cutover Map

Status: P0 execution control
Active repository: `tcmegahan/Crown-CSMS`
Successor workstream: PR #18

## Canonical target

Scheduling master-data ownership must converge on:

- `academics.Term` -> `core.AcademicYear`
- `academics.Course`
- `academics.Section`
- `academics.Enrollment`
- `academics.TeacherAssignment` -> `core.Staff`
- `section_scheduler_wizard.SectionPlacement` for scheduling-owned room/day/period placement
- `room_setup_wizard.Room`
- `bell_schedule_wizard.BellSchedule` / `DayTemplate` / `PeriodBlock`

Legacy representations remain read-only compatibility sources until COPY -> COMPARE -> CUTOVER -> RETIRE LAST proof is complete.

## Duplicate scheduling representations

### Advanced scheduler legacy table

`section_scheduler_wizard.Section` currently duplicates section/course/staff/room/slot identity. PR #18 stops new advanced-scheduler writes to this model and preserves it for reconciliation only.

### crown_api scheduling stack

`crown_api.models_scheduling_core` defines its own `Term`, `Section`, and `SectionEnrollment`. Its `Section` also points to `crown_api.models_academics_core.Course`, `crown_api.models_households.Person`, string room/meeting fields, and its enrollment points to `core.Student`.

This stack must not be dropped directly because its student and teacher identity shapes differ from the canonical academics stack.

## Verified active consumers

| Consumer | Current dependency | Cutover requirement | Retirement gate |
|---|---|---|---|
| `backend/crown_api/views_scheduling.py` | crown_api Term/Section/SectionEnrollment | compatibility adapter or canonical query implementation with unchanged authorized response semantics | API parity + tenant/household tests |
| `backend/crown_api/serializers_scheduling.py` | crown_api scheduling models and Person | canonical serializer/adapter preserving response contract | serializer/API parity |
| `backend/crown_api/tests/test_scheduling_api.py` | crown_api scheduling fixtures | convert fixtures to canonical/crosswalk source and retain authorization assertions | all tests green on canonical path |
| `backend/scripts/seed_scheduling.py` | crown_api scheduling models | seed canonical Term/Course/Section/Enrollment/placement data | deterministic seed proof |
| `backend/sandbox_demo/student_self_service.py` | crown_api SectionEnrollment | read canonical enrollment/schedule adapter | sandbox persona proof |
| `scripts/ops/PRE_DEMO_RESET_AND_SEED.ps1` | crown_api scheduling reset/seed path | invoke canonical seed/reset path | demo reset proof |
| `scripts/demo/DEMO_PROOF_REHEARSAL.ps1` | crown_api scheduling path | update proof commands to canonical schedule | rehearsal proof |
| `backend/crown_api/admin.py` | crown_api scheduling registration | switch/remove only after data parity | admin smoke proof |
| `backend/crown_api/views_academics.py` | crown_api Section references | inspect and cut to canonical section authority where applicable | academics API parity |
| golden-path / tenant / academics tests referencing crown_api Section | duplicate fixture dependency | preserve test intent against canonical authority or explicit compatibility adapter | exact-head regression green |

Search verification also identified crown_api scheduling references in attendance/classwork tests. Those are test-consumer dependencies and must be examined before model retirement even if production code is already cut over.

## Required identity crosswalks

### Course

`crown_api.models_academics_core.Course.course_code` -> `academics.Course.code`, tenant scoped.

Mapping must be unique within school. Ambiguous or missing mappings are reconciliation failures, never guessed.

### Term

`crown_api.models_scheduling_core.Term.code` -> `academics.Term.code` within an explicit `AcademicYear`.

The crown_api Term model lacks tenant/AcademicYear authority, so a deterministic AcademicYear association must be proven before write/cutover.

### Section

`crown_api Section` -> `academics.Section` must use school + AcademicYear/term + course + canonical section identity. Course+term alone is insufficient because multiple sections of one course in one term are valid.

### Teacher

`crown_api Person` -> `core.Staff` -> `academics.TeacherAssignment`.

Email may be used only when unique, normalized, same-tenant identity is proven. No automatic cross-tenant or ambiguous matching.

### Student / roster

`crown_api SectionEnrollment.student` uses `core.Student`, while `academics.Enrollment.student` currently uses `households.Student`.

This is a hard compatibility boundary. Student schedule cutover requires the existing household/core student identity bridge or an explicit deterministic crosswalk. Do not delete crown_api SectionEnrollment before this proof exists.

## Cutover sequence

1. Freeze new writes to duplicate scheduling masters.
2. Repair canonical section identity/source writer so multiple same-course/same-term sections are representable and AcademicYear-bound.
3. Dry-run legacy advanced-scheduler reconciliation; require zero ambiguous/unmatched/conflicting rows before apply.
4. Build crown_api read adapter backed by canonical schedule data while preserving existing response/authorization contracts.
5. Run old-vs-new API output comparison on representative tenant/persona fixtures.
6. Cut seeds, demo/reset scripts, sandbox self-service, tests, and admin registrations to canonical authority.
7. Re-scan repository for crown_api scheduling model consumers.
8. Require zero production writes/read dependencies except explicitly documented compatibility paths.
9. Independent review and exact-head CI/browser proof.
10. Retire duplicate tables/models in a separate reversible change only after 100% parity evidence.

## Non-negotiable regression cases

- two sections of the same course in the same term remain distinct
- wrong-tenant section, student, room, teacher, and block rejected
- teacher collision rejected using canonical `TeacherAssignment`
- room collision rejected using canonical placement data
- unauthorized scheduling publish rejected
- parent/student schedule remains household/student scoped
- roster and staffing preserved during placement changes
- retry/idempotency does not duplicate sections or placements
- reconciliation ambiguity produces zero writes in strict/apply mode
- no implicit deletion of unrelated sections or placements

## Current retirement decision

`section_scheduler_wizard.Section`, `crown_api.models_scheduling_core.Term`, `Section`, and `SectionEnrollment`: **RETAIN** until the gates above are proven. No destructive retirement is authorized by PR #18.
