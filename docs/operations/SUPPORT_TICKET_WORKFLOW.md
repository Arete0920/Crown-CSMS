# Operational support ticket foundation

Owner: CROWN product owner. Source implementation is distinct from deployed acceptance.

## Current source scope

Existing ticket intake/list, resolution and school escalation-check routes are retained.
Authenticated active school members can submit operational questions and list only their
own tickets. Explicit school-scoped support.view permits queue reads; support.manage
permits resolution and a school escalation check. The canonical active schoolless
platform operator retains global operator authority through an explicitly selected school.
Generic staff status, a school-bound superuser bit and the academic SUPPORT role do not
confer queue-management authority. HEAD_OF_SCHOOL, head_of_school and school_admin
receive these school-scoped permissions through the existing permission seed command.
No permission seeding or migration is automatically authorized on a hosted environment.

Each new ticket records the authenticated requester and a mandatory created event.
Resolution requires a nonblank summary, uses a database row lock and records a mandatory
resolved event. Event failure rolls back the associated write. Repeated resolution leaves
the original summary, timestamp and event intact. Historical tickets remain unowned;
only explicitly authorized queue viewers/managers see them. Do not infer ownership from
email, school membership or matching names. No historical actors/events are invented.

Ticket listing keeps the existing tickets key and adds total, page and per_page. Default
listing includes open/escalated records; status=closed or status=all permits authorized
history listing. Page size defaults to 50 and cannot exceed 100. Intake rejects client
identity, school, lifecycle and other unsupported fields. Title, description and resolution
summary have explicit size limits. Empty or non-text inputs are rejected.

## Handling procedure

1. Verify the requester and selected school; use synthetic or redacted diagnostics.
2. Triage impact and priority, appoint an accountable responder and record the next update
   in the approved restricted operational record until assignment/communication UI exists.
3. Investigate with the minimum permitted access. A ticket grants no access to grades,
   medical, pastoral, financial-aid, payment credentials or other school records.
4. Escalate suspected security incidents through the incident-response procedure; this
   general operational queue is not a confidential incident evidence repository.
5. Verify the affected behavior before resolving. Record the result in the resolution
   summary. A code merge, successful build or workaround proposal is not verified recovery.

Do not enter passwords, tokens, bank/card details or unnecessary personal records.
School isolation applies to both existing route mounts. Existing priority deadlines are
internal escalation thresholds, not approved contractual response/resolution guarantees.

## Delivery and acceptance limits

This foundation does not establish a staffed helpdesk, public service commitments,
assignment queues, internal/public conversation separation, attachments, outbound email,
notification delivery, temporary support-access grants, customer confirmation, reopening,
a leadership dashboard or complete ticket history coverage. The existing escalation
notifier remains a logging stub; do not describe it as an engineering alert delivery.
The event table covers new creation and authorized resolution, not every legacy/system
transition. There is no event edit/delete API, but database-level immutable/WORM storage
is not claimed. Protect user/ticket retention with the existing approval and legal process.

Validate the new additive migration against synthetic legacy tickets and a real PostgreSQL
database before hosted use. Existing deployment migration allowlists stay unchanged;
this migration must not be silently added to an unrelated DEV migration operation.
Source rollback is a governed revert; reverting source does not authorize deleting ticket
or audit data or reversing a live migration. Runtime acceptance requires the reviewed
migration, verified recovery point, role/tenant denials and actual school/operator flows.
