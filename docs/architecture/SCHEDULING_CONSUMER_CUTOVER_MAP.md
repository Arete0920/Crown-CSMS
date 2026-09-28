# Scheduling Consumer Cutover Map

**Status:** Controlled compatibility/convergence map
**Active repository:** `Arete0920/Crown-CSMS`
**Last reconciled:** 2026-08-17

## Canonical target

Scheduling master-data ownership converges on:

- `academics.Term` -> `core.AcademicYear`
- `academics.Course`
- `academics.Section`
- `academics.Enrollment`
- `academics.TeacherAssignment` -> `core.Staff`
- `section_scheduler_wizard.SectionPlacement` for scheduling-owned room/day/period placement
- `room_setup_wizard.Room`
- `bell_schedule_wizard.BellSchedule` / `DayTemplate` / `PeriodBlock`

Legacy representations remain compatibility sources until COPY -> COMPARE -> CUTOVER -> RETIRE LAST proof is complete. Earlier PR numbers are historical implementation provenance, not current turnover authority.

## Duplicate scheduling representations

### Advanced scheduler compatibility table

`section_scheduler_wizard.Section` duplicates section/course/staff/room/slot identity. New operational writes must use canonical scheduling authority; the compatibility table is retained only where current source still requires bounded read/reconciliation behavior.

### crown_api scheduling stack

`crown_api.models_scheduling_core` defines its own `Term`, `Section`, and `SectionEnrollment`, with identity shapes that differ from the canonical academics stack. These tables must not be dropped by assumption because student and teacher identity mappings require deterministic reconciliation.

## Compatibility consumers requiring explicit disposition before physical retirement

| Consumer category | Retirement requirement |
|---|---|
| `backend/crown_api/views_scheduling.py` and serializers | Canonical adapter/query parity with unchanged authorization semantics |
| Scheduling/academics regression fixtures | Preserve behavioral intent against canonical authority or explicit compatibility adapter |
| Seeds, demo/reset, and sandbox schedule paths | Canonical authority only for operational writes; deterministic proof |
| Admin registrations | Remove legacy write authority; retain only if a bounded compatibility need is proven |
| Cross-domain attendance/classwork consumers | Explicit consumer/equivalence proof before model retirement |

The current repository must be rescanned before any destructive retirement because a historical consumer list is not sufficient authority for deletion.

## Required identity crosswalks

### Course

`crown_api.models_academics_core.Course.course_code` -> `academics.Course.code`, tenant scoped. Mapping must be unique within school; ambiguous or missing mappings fail closed.

### Term

`crown_api.models_scheduling_core.Term.code` -> `academics.Term.code` within an explicit `AcademicYear`. A deterministic AcademicYear association must be proven before migration/retirement.

### Section

Legacy/crown_api Section -> `academics.Section` must use school + AcademicYear/term + course + durable section identity. Course+term alone is insufficient because multiple sections of one course in one term are valid.

### Teacher

Legacy/crown_api Person -> `core.Staff` -> `academics.TeacherAssignment`. Email may be used only when unique, normalized, same-tenant identity is proven. Ambiguous or cross-tenant matching is prohibited.

### Student / roster

`crown_api SectionEnrollment.student` and `academics.Enrollment.student` may traverse different compatibility identity domains. Student schedule cutover/retirement therefore requires an existing accepted bridge or an explicit deterministic crosswalk. Do not delete compatibility enrollment data before this proof exists.

## Retirement sequence

1. Confirm no new operational writes target duplicate scheduling masters.
2. Inventory every current production/test/demo/admin consumer against current `main`.
3. Prove canonical section identity supports multiple same-course/same-term sections and explicit AcademicYear context.
4. Dry-run reconciliation and require zero ambiguous/unmatched/conflicting rows before any destructive action.
5. Compare retained compatibility responses against canonical adapters on representative tenant/persona fixtures.
6. Verify seeds, demo/reset, sandbox, admin, and tests use the intended authority.
7. Re-scan the repository for compatibility-model consumers.
8. Require zero unexplained production write/read dependencies outside explicitly documented compatibility paths.
9. Require governed exact-head validation and the applicable solo-developer governance workaround.
10. Retire duplicate tables/models only in a separate reversible change after parity and recovery evidence are complete.

## Non-negotiable regression cases

- two sections of the same course in the same term remain distinct;
- wrong-tenant section, student, room, teacher, and block are rejected;
- teacher and room collision policy is enforced by canonical authority;
- unauthorized scheduling publication is rejected;
- parent/student schedule remains household/student scoped;
- roster and staffing are preserved during placement changes;
- retry/idempotency does not duplicate sections or placements;
- reconciliation ambiguity produces zero writes in strict/apply mode;
- no implicit deletion of unrelated sections or placements.

## Current retirement decision

Compatibility scheduling tables/models: **RETAIN UNTIL CURRENT CONSUMER/PARITY/RECOVERY PROOF AUTHORIZES RETIREMENT.** This document is a convergence map, not a present P0 release blocker and not authorization for destructive cleanup.
