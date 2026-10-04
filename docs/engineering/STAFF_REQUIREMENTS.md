# Canonical staff requirements

## Ownership and workflow

HR owns requirement assignments, completion evidence references, due dates, optional
expiry dates and review events. Each requirement references canonical `core.Staff` and
the same school. No `hr.Employee` copy, staff identity writer, payroll or external
credential verification is introduced. The existing compatibility staff directory
remains separate; no name/email heuristic silently maps its records into this workflow.

The HR dashboard adds a live requirements workspace. Authorized HR users assign
training, certification, clearance and acknowledgment requirements to active canonical
staff. Completion requires an actual completion date and a reference to the school's
reviewed evidence. Expiry cannot precede completion, and completion cannot be in the
future. Source documents remain in the authorized document system; this workspace
stores references and decisions, not confidential background-report contents.

Statuses derive from the recorded dates: pending, overdue, complete, expired, and
expiring within 30 days. Expiry is inclusive through its date; a record expires on the
following day. Counts cover the full selected set; requirements and review histories use 100-row pages. Staff
choices are bounded to 200 with a search and full counts. Inactive staff retain their
historical requirements but cannot receive new assignments.

Reopening clears the current completion fields while retaining prior evidence in an
append-only event. Due-date changes require a reason and retain before/after states.
Every write uses optimistic version checks and an actor/school retry key. The mutation
and event commit together. Neither dates nor recorded completion imply a provider's
independent verification or legal clearance certification.

## Access and retained evidence

Persistent school-scoped `hr.view` and `hr.edit` govern reads and writes separately.
Inactive accounts, missing school context and foreign-school records fail closed.
School/staff validation also protects model writes. History cannot be overwritten or
deleted through the workflow. Requirements remain available for review after expiry.
Requirement school, staff, title and category remain fixed after assignment. Bulk
writes cannot bypass validation; a different definition requires a new assignment.
Dashboard template summaries retain their existing preview boundaries; the new
workspace labels and counts are sourced from its live canonical endpoint.

## Verification and rollback

Tests cover canonical identity, tenant and permission boundaries, retry conflicts,
stale versions, invalid dates/evidence, atomic writes, reopening, rescheduling,
expiry boundaries, full counts/pages, staff search and immutable history. Interface
tests cover recorded states, required evidence, read-only access, retry preservation,
canonical assignments, pagination, history and unavailable refreshes.

The schema is additive. A code revert stops new writes while retaining the requirement
tables and review evidence. Destructive database rollback must not erase those records.
Verification follows the approved solo-maintainer path; no independent human review
or hosted-runtime certification is represented. Existing release gates stay unchanged.
The existing PostgreSQL classroom verification job also exercises these canonical staff
regressions; its required context and verification thresholds are preserved.
