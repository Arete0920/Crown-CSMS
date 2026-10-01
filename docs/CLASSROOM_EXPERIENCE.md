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
| T01 | Daily classroom workspace | Implemented: assigned-section workspace; relationship and private-note tests. |
| T02 | Fast audited attendance | Implemented: canonical roll call, mandatory new-workflow reasons, versions and immutable correction evidence; legacy writer also audited. |
| T03 | Curriculum-linked reusable planning | Implemented: curriculum objective links and authorized plan reuse with fresh delivery evidence; private notes not copied. |
| T04 | Dependable gradebook and weighting | Strengthened: explicit grade-source conflicts and provisional weighted previews; authoritative report-card policies remain existing. |
| T05 | Assignment publishing and reuse | Implemented: explicit publication and authorized draft copies; retry-safe student workflow. |
| T06 | Actionable student support | Implemented: canonical instructional intervention cases with account-linked owner, required review and versioned outcomes. |
| T07 | Accommodation implementation reminders | Implemented: staff-only accommodation instructions, required review date and follow-through; deadline overrides pending. |
| T08 | Formative assessment checks | Implemented: teacher understanding checks, private responses and feedback. |
| T09 | Flexible instructional groups | Implemented: enrolled groups, roles and milestone records. |
| T10 | Feedback and reusable rubrics | Implemented: immutable reusable rubric criteria and rubric-based feedback templates with revision history. |
| T11 | Contextual parent communication | Implemented: contextual designated-guardian conversations, concern state and resolution notes. |
| T12 | Behavior and restorative follow-through | Implemented: verified-identity restorative plans use canonical discipline incidents and immutable action evidence. |
| T13 | Expiring substitute access and packet | Implemented: staff-issued grant, maximum seven days, immediate revocation, per-request expiry and public lesson packet. |
| T14 | Emergency roster accountability | Implemented: printable roster and unknown-first drill/incident checks; unaccounted students prevent completion. |
| T15 | Observable Christian formation | Tracked requirement; verify authorized workflow before marking complete. |
| S01 | My classroom workspace | Implemented: enrolled student workspace with live source and reporting window. |
| S02 | Clear assignment directions and criteria | Implemented: assignment purpose, directions and success criteria. |
| S03 | Persisted drafts and submission receipts | Implemented: versioned saved drafts and server-timestamped receipts. |
| S04 | Cross-class workload and milestones | Implemented: cross-class dated assignments and group milestones; individualized deadlines are explicit. |
| S05 | Understandable progress and missing/zero distinction | Implemented: recorded points, missing/awaiting grading states and explicit grade-source conflict. |
| S06 | Private help requests | Implemented: staff-only help requests with acknowledgement, owner and closure history. |
| S07 | Feedback response and preserved revisions | Implemented: teacher returns, student revisions and append-only evidence. |
| S08 | Accessible learning materials | Implemented: HTTPS resource references with accessible descriptions and alternative instructions. |
| S09 | Teacher-approved lesson practice | Implemented: teacher-created practice with private student responses and feedback. |
| S10 | Private understanding checks | Implemented: private understanding-check responses; peer-answer isolation tests. |
| S11 | Group roles and contribution evidence | Implemented: roster-validated groups, roles, milestones and private contributions. |
| S12 | Goals and reflection | Implemented: dated goals and private/shared reflections with explicit audience. |
| S13 | Work portfolios | Implemented: portfolio reflections reference canonical published assignments. |
| S14 | Absence recovery plans | Implemented: public dated recovery lessons and student-specific makeup instructions/deadlines. |
| S15 | Worldview and service connections | Tracked requirement; verify authorized workflow before marking complete. |
| P01 | Verified children classroom overview | Implemented: canonical guardian accounts and active household scope; custody control pending. |
| P02 | Useful weekly classroom digest | Implemented: live seven-day digest and deduplicated weekly notices; deployment scheduler required. |
| P03 | Published assignment visibility | Implemented: published assignment directions and criteria; drafts withheld. |
| P04 | Accurate submission and grading status | Implemented: submission receipts and grading status, no inferred missing or zero. |
| P05 | Understandable grades and next steps | Implemented: source-aware provisional category-weighted previews and explicit withheld states. |
| P06 | Contextual teacher conversations | Implemented: designated-guardian conversations with assignment context and immutable message history. |
| P07 | Notification preferences and deduplication | Implemented: validated preferences, quiet hours, source-key deduplication and in-app notices; recurring command needs deployment scheduling. |
| P08 | Absence explanation and recovery | Implemented: guardian absence explanations, dated recovery lessons and teacher-set makeup deadlines. |
| P09 | Conference scheduling and follow-up | Implemented: conflict-checked availability, locked bookings, cancellations and follow-up; deployment scheduler required for reminders. |
| P10 | Teacher-approved support at home | Implemented: assignment home support and classroom home-support records. |
| P11 | Positive observations and balanced updates | Implemented: individual positive observations with family visibility. |
| P12 | Authorized student support plans | Tracked requirement; verify authorized workflow before marking complete. |
| P13 | Classroom consent and permissions | Implemented: staff-issued permission requests and designated-guardian consent/decline evidence. |
| P14 | Shared portfolios | Implemented: student-selected family portfolio visibility. |
| P15 | Family mission and service partnership | Tracked requirement; verify authorized workflow before marking complete. |
| A01 | Classroom operational health | Tracked requirement; verify authorized workflow before marking complete. |
| A02 | Curriculum coverage and alignment | Tracked requirement; verify authorized workflow before marking complete. |
| A03 | Dated student growth evidence | Implemented: dated mastery evidence preserves earlier levels and teacher observations; no inferred growth score. |
| A04 | Intervention ownership and reviews | Implemented: account-linked canonical case ownership, scheduled reviews and preserved follow-through; legacy integer owners remain explicitly unmapped. |
| A05 | Teacher workload visibility | Tracked requirement; verify authorized workflow before marking complete. |
| A06 | Confidential observation and coaching | Partial: leadership-only coaching records with review dates; observation framework pending. |
| A07 | Grading consistency and policies | Strengthened: immutable rubrics, weight-total checks and explicit evidence coverage/conflicts. |
| A08 | Attendance and instructional time | Partial: dated canonical attendance audit and interruption evidence; leadership instructional-time aggregation follows. |
| A09 | Support implementation oversight | Tracked requirement; verify authorized workflow before marking complete. |
| A10 | Class size and staffing planning | Tracked requirement; verify authorized workflow before marking complete. |
| A11 | Instructional resource use and cost | Partial: resource references and recorded cost; usage reporting pending. |
| A12 | Classroom climate and restorative outcomes | Implemented: canonical restorative incidents, review dates and outcome notes; aggregate climate reporting follows. |
| A13 | Family concern resolution | Implemented: school-authorized concern resolution, preserved messages and disclosure restrictions. |
| A14 | Mission and Portrait evidence | Tracked requirement; verify authorized workflow before marking complete. |
| A15 | Board aggregate reporting and provenance | Implemented: dated aggregate section facts and definitions; expanded oversight reports pending. |

## Workspace contract

GET `/api/v1/academics/classroom/workspace/?audience=teacher|student|parent|admin|board`. Optional term, section_id, student_id, from and to; maximum 32-day window. Authentication and canonical school context are mandatory. Matching emails and staff flags do not grant classroom relationships. Families see published work only. Board responses omit names, rosters, individual grades and confidential notes.

The workspace reads academics sections, enrollments, assignments, lesson plans and submissions, plus gradebook assignment points. Attendance remains owned by its existing verified identity bridge. No duplicate enrollment, grade or attendance store is created. Past-due work without evidence is unconfirmed, not automatically missing. Submitted work without recorded points awaits grading; zero is a real grade. Points are not weighted report-card totals. Plans do not establish a bell schedule. Limits and reporting dates are explicit.

## Delivery status

The shared relationship-scoped workspace is the first implementation batch. Later acceptance requirements remain open until their behavior and tests are complete. No deployment, external notification delivery, curriculum license, personal faith score or classroom quality score is implied. Guardian account linkage alone does not encode custody restrictions; an explicit disclosure control is required before claiming that capability.


## Assignment workflow batch

Canonical assignments now store purpose, instructions, success criteria and home support. Publication accepts actual booleans. Copies into authorized sections start as drafts, preserve teaching content and never copy student evidence. Assignments with student evidence cannot be deleted through the teacher API.

GET/POST `/api/v1/academics/assignments/<id>/work/?audience=student|parent|teacher|admin` supports save_draft, submit, feedback and return. Student account ownership is mandatory for save/submit. Teacher assignment or explicit leadership authority is mandatory for feedback/return. Parents cannot submit work for children. Each mutation uses a UUID request key and expected version; conflicts return 409. Submitted work needs a teacher return before editing. Revisions are append-only and drafts are not shared with families. UI keeps unsaved text on failures and reports submission success only after receiving a server timestamp. PostgreSQL row locking is implemented but concurrency certification still requires its runtime tests.

Legacy submission mutation routes cannot edit or delete submission evidence. Grade reads are relationship-scoped; a staff flag alone is not grading authority. Academic submission grades and gradebook points are explicitly sourced; disagreement shows a review requirement rather than silently selecting a preferred value. This is reconciliation of existing stores, not a new grade authority.

## Collaboration batch

Classroom records support teaching updates, home support, practice, private understanding checks, enrolled groups with roles and milestones, positive observations, accommodations, dated support reviews, help requests, goals, reflections and portfolio links. Staff actions require follow-through notes. Creation and actions use retry keys; actions require expected versions. Answers and answer-history are scoped to the responding student and their authorized guardian; peers cannot read them. Private reflections remain private even from assigned teachers. School leaders alone may share support plans with families. Absence explanations are communication records, not attendance corrections. Coaching is leadership-only. Resource costs and interruption minutes are recorded evidence, not measures of effectiveness.

POST/GET `/api/v1/academics/classroom/records/` and POST `records/<id>/actions/` enforce the same canonical classroom relationships. Events cannot be edited or deleted through model interfaces. Existing academic work remains the portfolio authority. Classroom support records describe instructional implementation and do not replace clinical records or the existing signals intervention case system. No external delivery is implied by a saved record.

## Family partnership batch

Designated-guardian conversations preserve message history and published assignment context. Staff record resolution notes; guardians can reply but cannot close concerns on behalf of staff. Staff issue consent requests and only the designated guardian can agree or decline, with timestamped immutable responses. Conferences use staff availability, collision checks, locked booking, retry-safe confirmation, cancellation notes and follow-up messages.

Leadership can record a verified classroom disclosure restriction or restoration per student/guardian. Restricted guardians are excluded from the canonical classroom relationship helper, workspace, collaboration records, assignment work and family threads. This is an explicit classroom disclosure control, not a determination of legal custody and not a claim that every legacy school module enforces it.

Notification preferences validate timezone, digest weekday and quiet hours. In-app thread notices use unique source keys; disabled preferences suppress notices and quiet hours defer availability. The management command `prepare_classroom_digests` prepares deduplicated weekly digest notices and upcoming conference reminders. Deployment must schedule this command periodically before recurring notices are operational. No email/SMS provider is activated. The on-demand seven-day digest always remains readable independently of notification preference.

## Classroom operations batch

The operations workspace uses existing canonical AttendanceRecord entries and verified StudentIdentityLink mappings. Unknown identities remain unmarked. New attendance writes require an expected session version and a reason. The legacy section attendance writer also appends before/after evidence under the same section lock, so later classroom writes detect those changes. Attendance history is append-only.

School-authorized teachers/substitutes may receive section-specific access for 5 minutes–7 days. Active grants authorize only the operations packet, roster and roll call, not grades, private lesson notes or family conversations. Expiry and revocation are rechecked on each mutation. Packets show public dated lessons, student names, recorded attendance and intentionally supplied substitute instructions.

Drill/incident rosters begin with every student unknown. Individual checks require verification notes. Sessions cannot complete while any student is missing or unknown. 'Accounted elsewhere' is roster evidence, not authorization for custody release. No emergency dispatch, medical record or external contact action is created.

## Instruction and evidence batch

Immutable reusable rubrics describe academic criteria and performance levels. Existing submitted evidence prevents replacing an assignment rubric. Teacher feedback can begin from the attached criteria without generating a grade. Plan reuse requires source and target authority, validates course links, omits private notes and resets actual delivery evidence. Curriculum tags reference existing PublisherObjective and Lesson records.

Student-specific deadline adjustments require teacher authority, private reasons, student-visible makeup instructions, retry keys and expected versions. The student work endpoint applies the effective deadline when classifying submission timing. Shared workspace tasks use the adjusted date; private reasons are withheld. Resource references require HTTPS and include accessible descriptions and alternative instructions.

Progress previews use the existing grade sources, active category weights and scored evidence only. Invalid weights, unscored categories or source conflicts withhold the weighted preview. Unscored work is not zero, and the preview does not replace report-card authority. Mastery writes update existing MasteryRecord rows and append dated evidence, preserving prior levels. Academic mastery evidence is not a personal faith or classroom quality score.

## Support and restorative batch

Instructional support references canonical signals InterventionCase/InterventionAction records. Verified account owner and actor foreign keys, review dates and versions support UUID accounts; legacy integer evidence remains intact without guessed conversions. Existing owned cases can be linked to a classroom. New support and outcome actions preserve retry and version evidence. Raw signal drivers require leadership; legacy intervention reads require explicit leadership or current assigned ownership, and client-supplied actor IDs cannot spoof authorship.

Restorative plans resolve the verified student identity before creating canonical discipline incidents. Teacher notes, review dates and closed outcome evidence are preserved through canonical actions and append-only classroom audit events. No saved plan claims a parent was notified. Families receive only explicitly approved shared support records through the separate classroom disclosure controls.
