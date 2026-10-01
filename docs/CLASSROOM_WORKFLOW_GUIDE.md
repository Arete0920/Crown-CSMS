# Classroom workflow guide

This guide describes the classroom improvement branches. A workflow becomes available only after its batch is merged, migrations are applied and the application is deployed. The delivery register remains the source for readiness and limitations.

## Teachers

1. Open Today's Classroom. Choose a term and section, review due work and the dated lesson plan, then open attendance when ready for roll call. Recorded sections are course rosters; they do not establish the bell schedule.
2. Publish an assignment with its purpose, directions, success criteria and home support. Choose points and a category. Reuse into another authorized section as a draft, then review and publish the copy.
3. Open a student's work to review the submission receipt and shared version. Record feedback or return submitted work with clear revision instructions. Student drafts remain private; refresh if another device changed the saved version.
4. Use instruction controls to attach a rubric, link curriculum objectives, reuse a lesson plan or provide accessible resources. Makeup deadlines and student-visible directions can be individualized; private staff reasons stay private.
5. Add practice or understanding checks and review each student's private response. Create enrolled instructional groups with roles and milestones. Follow through on help requests and close them with a next-step note.
6. Record positive observations. For confidential support, set an owner and review date; record the observed next step and outcome. Accommodations remain staff-only. Leadership can explicitly share an approved family support plan.
7. Use family conversations for assignment context, consent and conference follow-up. Record resolution with a note; messages remain in history.
8. Grant substitute packet access with a start, expiry and instructions; revoke it when the assignment ends. Substitute access provides the selected packet and attendance, without private plans, grades or family conversations.
9. For an emergency or drill, start roster accountability. Every student begins unknown. Confirm each student's status; unknown or missing students prevent completion. “Accounted elsewhere” is an accountability status, not pickup authorization.
10. Connect service opportunities to the school's Portrait domains, Biblical worldview priorities and Scripture references. Participation reflections provide observable evidence without scoring personal faith.

## Students

Review My Classroom for cross-class assignments, directions and deadlines. Open work, save a draft, then submit when ready. Treat the server timestamp as confirmation. If saving fails, retain your text and retry the same action. If the version changed, refresh the school version and review your text before saving.

Read feedback and revise work returned by the teacher. Unscored work is not a zero. A disagreement between grade sources requires teacher review. Weighted previews are provisional and may be withheld when weights, evidence or sources are incomplete.

Use private help requests, practice and understanding checks. Record group contributions, dated goals and reflection. Choose the audience for reflection and portfolio entries. Use teacher-provided alternative instructions and makeup deadlines after an absence. Respond to service opportunities with concrete participation evidence.

## Parents and guardians

Choose among verified children. Read published directions, submission receipts, feedback and shared portfolios. Draft assignments and private student drafts are withheld. A guardian cannot submit work for a student.

Review the live weekly digest and teacher-approved home support. Save notification preferences, timezone, digest weekday and quiet hours to receive in-app notices. Open an assignment-context conversation, provide an absence explanation, respond to a designated consent request or book an available conference. Booking confirmation comes from the school server; another family's booking can make a slot unavailable.

Read approved shared support plans and positive observations. Record family service participation for an enrolled child. Classroom disclosure restrictions can remove a guardian's access; the software does not infer a legal custody decision.

## Administrators and board members

Administrators can review operational facts, section rosters, primary/co-teacher workload, known curriculum objectives, scheduled lessons, confirmed teaching and dated mastery observations. Planned activity is distinct from completed evidence. Record a class-size target and rationale for planning; it does not change enrollment limits.

Assign or reassign an intervention to a verified authorized account and set its next review. Preserve legacy numeric identifiers without assuming which account they represent. Create confidential coaching for an assigned active teacher. The recipient can acknowledge; leadership records resolution.

Board reports provide aggregate facts, dates, definitions, sources and limitations. Individual rosters, grades, teacher workload rows, confidential notes and planning rationales are withheld. Counts do not establish classroom effectiveness or spiritual maturity. Unknown minutes and costs remain unknown; recorded zero remains zero.

## Deployment and operational verification

Apply the actual migrations through the repository's approved migration path. Run exact-head checks, including the PostgreSQL classroom proof lane, before completing the feature rollout. That lane requires PostgreSQL, applies actual migrations and tests simultaneous writes; SQLite focused tests are insufficient row-lock evidence.

Use the existing Celery worker and beat service for periodic in-app classroom notices. The task is `academics.tasks.prepare_classroom_notices`; the configured interval is fifteen minutes. `python backend/manage.py prepare_classroom_digests` is the recovery command. Verify an opted-in guardian's weekly notice, quiet-hour deferral and a conference reminder without creating duplicates. This workflow does not activate external email/SMS delivery.

Test one authorized teacher, student, guardian, administrator and board account against real enrolled sections after deployment. Check that unrelated accounts and restricted guardians cannot read the classroom records. Confirm a draft, submission, return and resubmission with preserved history; book and cancel a conference; correct attendance with a reason; revoke a substitute grant; complete an accountability session only after everyone is accounted for. Confirm live report dates and sources before using them for a board decision.
