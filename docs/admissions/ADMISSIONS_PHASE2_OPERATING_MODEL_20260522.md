# Admissions Phase 2 Operating Model (2026-05-22)

## Purpose
Turn the now-stable admissions submit flow into a repeatable operating system that improves conversion, response speed, and parent confidence.

## What Competitors Typically Do Next
1. Auto-triage each new application into counselor queues.
2. Start stage-based communication journeys immediately.
3. Expose a parent checklist and status tracker.
4. Run interview and assessment scheduling with SLA reminders.
5. Track conversion and cycle-time by stage, campus, and program.
6. Operationalize admit, waitlist, decline workflows with one-click transitions.

## Crown Phase 2 Goals
1. Make every successful submit produce deterministic next actions.
2. Reduce manual handoff delays between admissions stages.
3. Increase family transparency without creating staff overhead.
4. Measure and improve funnel movement week over week.

## Scope
In scope:
1. Post-submit orchestration.
2. Queue and SLA management.
3. Parent-facing status and checklist updates.
4. Admissions analytics and conversion instrumentation.

Out of scope:
1. New payment rails.
2. SIS-wide redesign.
3. Broad CRM replacement.

## Two-Week Execution Sequence

### Week 1: Operational Backbone
Day 1:
1. Define canonical admissions stages and stage entry criteria.
2. Define stage owner model (role-based, campus-aware).

Day 2:
1. Implement post-submit workflow trigger.
2. Create counselor queue records with due dates.

Day 3:
1. Add SLA policy config by stage (for example: initial review 24h, document review 48h).
2. Add overdue detector and alert rule.

Day 4:
1. Add parent status timeline payload to existing admissions API.
2. Add checklist item model for missing documents and required actions.

Day 5:
1. Add first communication journey templates:
   - Submission confirmation
   - Missing document reminder
   - Interview scheduling prompt
2. Add event logging for each communication send.

### Week 2: Conversion Operations
Day 6:
1. Add interview scheduling handoff status.
2. Add no-response and no-show escalation tasks.

Day 7:
1. Add admit, waitlist, decline transition actions with reason capture.
2. Add conversion timestamp tracking.

Day 8:
1. Build admissions operations dashboard widgets:
   - Stage aging
   - Applications by owner
   - Overdue SLA count
   - Conversion by stage

Day 9:
1. Add campus and program segmentation for all funnel analytics.
2. Add weekly cohort view for application velocity.

Day 10:
1. Execute dry-run in sandbox with seeded applications.
2. Validate expected triggers, queues, reminders, and stage transitions.
3. Freeze Phase 2 baseline and publish runbook update.

## Required Events
1. application_submitted
2. stage_entered
3. stage_exited
4. sla_due_soon
5. sla_missed
6. checklist_item_added
7. checklist_item_completed
8. communication_sent
9. decision_recorded
10. enrollment_converted

## Admission Queue Rules
1. New submission goes to queue status New with owner assignment.
2. If no owner action in SLA window, escalate to team lead queue.
3. Missing docs auto-create checklist tasks and family reminder sequence.
4. Interview pending beyond SLA escalates with next-best action guidance.

## Parent Experience Contract
1. Parent sees clear current stage and next required action.
2. Parent sees outstanding checklist items with due dates.
3. Parent sees latest communications and expected response time.
4. Parent can confirm completion state after upload and action acknowledgment.

## KPI Set (Weekly)
1. Time-to-first-review (median, p90).
2. Stage-to-stage conversion rate.
3. Average days in stage.
4. SLA breach rate.
5. Checklist completion rate within 72 hours.
6. Application-to-decision cycle time.
7. Decision-to-enrollment conversion.

## Acceptance Criteria
1. Every successful submit creates a queue item and stage record.
2. SLA timers fire and overdue alerts are visible to admissions ops.
3. Parent status timeline is accurate for seeded and live test records.
4. Communications are stage-aware and deduplicated.
5. Dashboard reflects same truth as queue and stage records.
6. Sandbox dry-run passes with no orphaned applications.

## Integrity Guardrails
1. No silent state transitions.
2. Every stage change must be evented and auditable.
3. Idempotency enforced on submit and stage transition triggers.
4. Correlation IDs preserved across submit to decision lifecycle.
5. No release to production without green gates and signed dry-run evidence.
6. Learn from competitor best practices only at the pattern level; do not copy proprietary flows, content, code, or protected implementation details.

## Suggested Ownership Model
1. Product owner: admissions operations policy and SLA definitions.
2. Backend owner: eventing, queue services, transition APIs.
3. Frontend owner: parent status and admissions operations dashboard.
4. QA owner: seeded scenario suite and SLA breach simulations.

## Immediate Next Step
Execute Day 1 and Day 2 items first, then run a mini proof with 10 seeded applications before broadening Phase 2 scope.
