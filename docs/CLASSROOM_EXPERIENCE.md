# Classroom experience delivery register

All 60 requests are accepted requirements. Existing models or screens alone do not prove a completed workflow. Each batch requires authorized end-to-end behavior and exact-head tests within unchanged repository limits.

## Delivery sequence

1. Verified account/assigned-section access, shared classroom workspace, clear submission states and aggregate board evidence.
2. Assignment instructions, criteria, publishing, persisted drafts, submission receipts and revision history.
3. Help, formative checks, groups, goals, portfolios, accommodations, family conversations, digests and appointments.
4. Coaching, curriculum/resource coverage, workload, emergency/substitute preparation and accountable reporting.

## Acceptance register

| ID | Improvement | Verification state |
|---|---|---|
| T01 | Daily classroom workspace | Tracked requirement; verify authorized workflow before marking complete. |
| T02 | Fast audited attendance | Tracked requirement; verify authorized workflow before marking complete. |
| T03 | Curriculum-linked reusable planning | Tracked requirement; verify authorized workflow before marking complete. |
| T04 | Dependable gradebook and weighting | Tracked requirement; verify authorized workflow before marking complete. |
| T05 | Assignment publishing and reuse | Tracked requirement; verify authorized workflow before marking complete. |
| T06 | Actionable student support | Tracked requirement; verify authorized workflow before marking complete. |
| T07 | Accommodation implementation reminders | Tracked requirement; verify authorized workflow before marking complete. |
| T08 | Formative assessment checks | Tracked requirement; verify authorized workflow before marking complete. |
| T09 | Flexible instructional groups | Tracked requirement; verify authorized workflow before marking complete. |
| T10 | Feedback and reusable rubrics | Tracked requirement; verify authorized workflow before marking complete. |
| T11 | Contextual parent communication | Tracked requirement; verify authorized workflow before marking complete. |
| T12 | Behavior and restorative follow-through | Tracked requirement; verify authorized workflow before marking complete. |
| T13 | Expiring substitute access and packet | Tracked requirement; verify authorized workflow before marking complete. |
| T14 | Emergency roster accountability | Tracked requirement; verify authorized workflow before marking complete. |
| T15 | Observable Christian formation | Tracked requirement; verify authorized workflow before marking complete. |
| S01 | My classroom workspace | Tracked requirement; verify authorized workflow before marking complete. |
| S02 | Clear assignment directions and criteria | Tracked requirement; verify authorized workflow before marking complete. |
| S03 | Persisted drafts and submission receipts | Tracked requirement; verify authorized workflow before marking complete. |
| S04 | Cross-class workload and milestones | Tracked requirement; verify authorized workflow before marking complete. |
| S05 | Understandable progress and missing/zero distinction | Tracked requirement; verify authorized workflow before marking complete. |
| S06 | Private help requests | Tracked requirement; verify authorized workflow before marking complete. |
| S07 | Feedback response and preserved revisions | Tracked requirement; verify authorized workflow before marking complete. |
| S08 | Accessible learning materials | Tracked requirement; verify authorized workflow before marking complete. |
| S09 | Teacher-approved lesson practice | Tracked requirement; verify authorized workflow before marking complete. |
| S10 | Private understanding checks | Tracked requirement; verify authorized workflow before marking complete. |
| S11 | Group roles and contribution evidence | Tracked requirement; verify authorized workflow before marking complete. |
| S12 | Goals and reflection | Tracked requirement; verify authorized workflow before marking complete. |
| S13 | Work portfolios | Tracked requirement; verify authorized workflow before marking complete. |
| S14 | Absence recovery plans | Tracked requirement; verify authorized workflow before marking complete. |
| S15 | Worldview and service connections | Tracked requirement; verify authorized workflow before marking complete. |
| P01 | Verified children classroom overview | Tracked requirement; verify authorized workflow before marking complete. |
| P02 | Useful weekly classroom digest | Tracked requirement; verify authorized workflow before marking complete. |
| P03 | Published assignment visibility | Tracked requirement; verify authorized workflow before marking complete. |
| P04 | Accurate submission and grading status | Tracked requirement; verify authorized workflow before marking complete. |
| P05 | Understandable grades and next steps | Tracked requirement; verify authorized workflow before marking complete. |
| P06 | Contextual teacher conversations | Tracked requirement; verify authorized workflow before marking complete. |
| P07 | Notification preferences and deduplication | Tracked requirement; verify authorized workflow before marking complete. |
| P08 | Absence explanation and recovery | Tracked requirement; verify authorized workflow before marking complete. |
| P09 | Conference scheduling and follow-up | Tracked requirement; verify authorized workflow before marking complete. |
| P10 | Teacher-approved support at home | Tracked requirement; verify authorized workflow before marking complete. |
| P11 | Positive observations and balanced updates | Tracked requirement; verify authorized workflow before marking complete. |
| P12 | Authorized student support plans | Tracked requirement; verify authorized workflow before marking complete. |
| P13 | Classroom consent and permissions | Tracked requirement; verify authorized workflow before marking complete. |
| P14 | Shared portfolios | Tracked requirement; verify authorized workflow before marking complete. |
| P15 | Family mission and service partnership | Tracked requirement; verify authorized workflow before marking complete. |
| A01 | Classroom operational health | Tracked requirement; verify authorized workflow before marking complete. |
| A02 | Curriculum coverage and alignment | Tracked requirement; verify authorized workflow before marking complete. |
| A03 | Dated student growth evidence | Tracked requirement; verify authorized workflow before marking complete. |
| A04 | Intervention ownership and reviews | Tracked requirement; verify authorized workflow before marking complete. |
| A05 | Teacher workload visibility | Tracked requirement; verify authorized workflow before marking complete. |
| A06 | Confidential observation and coaching | Tracked requirement; verify authorized workflow before marking complete. |
| A07 | Grading consistency and policies | Tracked requirement; verify authorized workflow before marking complete. |
| A08 | Attendance and instructional time | Tracked requirement; verify authorized workflow before marking complete. |
| A09 | Support implementation oversight | Tracked requirement; verify authorized workflow before marking complete. |
| A10 | Class size and staffing planning | Tracked requirement; verify authorized workflow before marking complete. |
| A11 | Instructional resource use and cost | Tracked requirement; verify authorized workflow before marking complete. |
| A12 | Classroom climate and restorative outcomes | Tracked requirement; verify authorized workflow before marking complete. |
| A13 | Family concern resolution | Tracked requirement; verify authorized workflow before marking complete. |
| A14 | Mission and Portrait evidence | Tracked requirement; verify authorized workflow before marking complete. |
| A15 | Board aggregate reporting and provenance | Tracked requirement; verify authorized workflow before marking complete. |

## Workspace contract

GET `/api/v1/academics/classroom/workspace/?audience=teacher|student|parent|admin|board`. Optional term, section_id, student_id, from and to; maximum 32-day window. Authentication and canonical school context are mandatory. Matching emails and staff flags do not grant classroom relationships. Families see published work only. Board responses omit names, rosters, individual grades and confidential notes.

The workspace reads academics sections, enrollments, assignments, lesson plans and submissions, plus gradebook assignment points. Attendance remains owned by its existing verified identity bridge. No duplicate enrollment, grade or attendance store is created. Past-due work without evidence is unconfirmed, not automatically missing. Submitted work without recorded points awaits grading; zero is a real grade. Points are not weighted report-card totals. Plans do not establish a bell schedule. Limits and reporting dates are explicit.

## Delivery status

The shared relationship-scoped workspace is the first implementation batch. Later acceptance requirements remain open until their behavior and tests are complete. No deployment, external notification delivery, curriculum license, personal faith score or classroom quality score is implied. Guardian account linkage alone does not encode custody restrictions; an explicit disclosure control is required before claiming that capability.


## Assignment workflow batch

Canonical assignments now store purpose, instructions, success criteria and home support. Publication accepts actual booleans. Copies into authorized sections start as drafts, preserve teaching content and never copy student evidence. Assignments with student evidence cannot be deleted through the teacher API.

GET/POST `/api/v1/academics/assignments/<id>/work/?audience=student|parent|teacher|admin` supports save_draft, submit, feedback and return. Student account ownership is mandatory for save/submit. Teacher assignment or explicit leadership authority is mandatory for feedback/return. Parents cannot submit work for children. Each mutation uses a UUID request key and expected version; conflicts return 409. Submitted work needs a teacher return before editing. Revisions are append-only and drafts are not shared with families. UI keeps unsaved text on failures and reports submission success only after receiving a server timestamp. PostgreSQL row locking is implemented but concurrency certification still requires its runtime tests.

Legacy submission mutation routes cannot edit or delete submission evidence. Grade reads are relationship-scoped; a staff flag alone is not grading authority. Academic submission grades and gradebook points are explicitly sourced; disagreement shows a review requirement rather than silently selecting a preferred value. This is reconciliation of existing stores, not a new grade authority.
