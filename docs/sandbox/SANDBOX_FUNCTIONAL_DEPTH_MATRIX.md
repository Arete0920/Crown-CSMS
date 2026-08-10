# CROWN Sandbox Functional-Depth Certification Matrix

Control issue: #1960

## Certification rule

A dashboard rendering is not functional certification. A required row reaches PASS only when the sandbox persona can reach the workflow through normal role navigation, perform the representative action against fictional Heritage Christian Academy data, persist the expected state, observe the expected downstream result, and remain inside role and tenant boundaries.

Allowed status values: `PASS`, `FAIL`, `NOT VERIFIED`.

Runtime evidence must be exact-head and fail closed. Backend-only proof may certify only the specific backend behavior it exercises; it does not substitute for browser workflow proof.

| Priority | Persona | Required workflow | Transactional completion evidence | Status |
| --- | --- | --- | --- | --- |
| P0 | Parent | Start/resume application | Family can enter applicant workflow and save demo state | NOT VERIFIED |
| P0 | Parent | Submit application | Required application data can be completed and submitted | NOT VERIFIED |
| P0 | Parent | Application status | Submitted/accepted state and next action are visible | NOT VERIFIED |
| P0 | Parent | Enrollment/re-enrollment | Accepted demo applicant/family can complete enrollment workflow | NOT VERIFIED |
| P0 | Parent | Resulting family context | Student/family state is reflected after enrollment | NOT VERIFIED |
| P0 | Parent | Daily family work | Attendance, learning/progress, communications, billing available within parent scope | NOT VERIFIED |
| P0 | Teacher | Assigned classes/roster | Teacher can open only authorized instructional context | NOT VERIFIED |
| P0 | Teacher | Attendance | Teacher can record permitted attendance change and persist it | NOT VERIFIED |
| P0 | Teacher | Lesson planning | Teacher can create/edit/save/reopen lesson plan | NOT VERIFIED |
| P0 | Teacher | Curriculum/resource integration | Teacher can link/add an instructional resource to authorized context | NOT VERIFIED |
| P0 | Teacher | Assignment/class work | Teacher can create or manage assessable instructional work | NOT VERIFIED |
| P0 | Teacher | Grading | Exact-head backend proof confirms teacher sandbox JWT can enter/update an authorized student grade | PASS |
| P0 | Teacher | Grade downstream result | Exact-head backend proof confirms persisted grade is returned after reload through grade API | PASS |
| P0 | Admissions Director | Pipeline | Inquiry/applicant can be opened and legitimately advanced | NOT VERIFIED |
| P0 | Admissions Director | Checklist/documents | Application requirements can be reviewed/updated | NOT VERIFIED |
| P0 | Admissions Director | Decision | Authorized decision state can be recorded | NOT VERIFIED |
| P0 | Admissions Director | Enrollment conversion | Accepted applicant converts to SIS/enrollment state | NOT VERIFIED |
| P0 | Admissions Director | Metrics/queue update | Transaction changes live admissions operational state | NOT VERIFIED |
| P0 | Finance Director | Family account | Charges/payments/allocations and authoritative balance visible | NOT VERIFIED |
| P0 | Finance Director | Finance operation | Representative allowed finance update can be completed | NOT VERIFIED |
| P0 | Finance Director | Exception/reconciliation | Seeded exception can be worked through appropriate queue | NOT VERIFIED |
| P0 | Finance Director | Reversal/void integrity | Reversed/voided charges remain excluded from receivables correctly | NOT VERIFIED |
| P0 | School Administrator | Student/household operation | Authorized record can be opened and updated | NOT VERIFIED |
| P0 | School Administrator | Enrollment/roster operation | Enrollment/roster context can be reviewed or acted on | NOT VERIFIED |
| P0 | School Administrator | Attendance exception | Representative exception can be reviewed/resolved | NOT VERIFIED |
| P0 | School Administrator | Academic oversight | Appropriate grade/academic context is available | NOT VERIFIED |
| P0 | School Administrator | Communication operation | Representative school communication action is available | NOT VERIFIED |
| P0 | Student | Schedule/today | Student can open assigned schedule and next actions | NOT VERIFIED |
| P0 | Student | Assignments | Student can review assigned learning tasks | NOT VERIFIED |
| P0 | Student | Work/progress | Student can review appropriate submitted-work/progress state | NOT VERIFIED |
| P0 | Student | Communications | Student can review permitted school communications | NOT VERIFIED |
| P0 | Student | Denied admin surfaces | Admissions, finance admin, grading, staff and tenant admin controls remain unavailable | NOT VERIFIED |

## Cross-cutting P0 evidence

| Requirement | Status |
| --- | --- |
| Sandbox persona launches actual role-aware CROWN workspace | NOT VERIFIED |
| Fictional/demo data only | PASS |
| Cross-tenant isolation | PASS |
| Cross-role denial enforcement | PASS |
| Create/update/submit actions use real sandbox backend | PASS |
| Persistence after reload/navigation | PASS |
| Downstream state propagation | NOT VERIFIED |
| Deterministic reset/reseed | PASS |
| No required dead/placeholder action | NOT VERIFIED |
| No unexpected console/network errors on certified paths | NOT VERIFIED |
| Responsive parent/student/teacher paths | NOT VERIFIED |
| Accessibility/usability checks on transactional forms | NOT VERIFIED |

## Evidence boundary

The current exact-head transactional backend job proves sandbox-session JWT issuance for advertised personas, deterministic Heritage reset/reseed, teacher grade mutation and reload persistence, parent grade-write denial, and tenant-header isolation. Browser route/session proof must independently pass against the real seeded Django runtime before role-workspace launch or browser-only rows can be promoted.

## P1 expansion

After all P0 rows are PASS, add 2–4 representative transactional workflows for each buyer-advertised additional persona/module, including Registrar, Scheduling, Student Care, Communications, Activities/Athletics, Financial Aid, HR, Facilities, Health Office, Transportation, Food Service, IT Support, Fine Arts, Library/Media, Extended Care, Safety/Security, Curriculum/PD, Spiritual Life, Advancement Operations, Volunteer Management, Alumni, Network Benchmarking, and platform operations.

## Final gate

Sandbox release status remains **NO-GO** while any required P0 row is `FAIL` or `NOT VERIFIED`.

Final certification requires the exact main SHA, frontend/backend runtime identity, zero required FAIL rows, zero required NOT VERIFIED rows, deterministic reset proof, zero role/tenant violations, and an independent review path that does not require the product owner to self-approve.
