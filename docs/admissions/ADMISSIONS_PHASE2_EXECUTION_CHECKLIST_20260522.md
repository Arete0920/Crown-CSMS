# Admissions Phase 2 Execution Checklist (2026-05-22)

Source plan:
- docs/admissions/ADMISSIONS_PHASE2_OPERATING_MODEL_20260522.md

## Usage Rules
1. Do not mark an item complete without evidence.
2. Link each completed item to proof (log, screenshot, query result, or test output).
3. If any item is blocked, record blocker and owner on the same day.

## Day 1: Stage Canon and Ownership
- [ ] Finalize canonical admissions stage list.
- [ ] Define stage entry and exit criteria for each stage.
- [ ] Define owner resolution rules (role + campus).
- [ ] Publish stage dictionary in admissions docs.

Done criteria:
1. Stage dictionary committed.
2. Owner rules documented with at least 3 example assignments.

Evidence:
- [ ] Link to committed doc(s)
- [ ] Link to owner-rule examples

## Day 2: Post-Submit Queue Creation
- [ ] Create post-submit trigger contract.
- [ ] Create queue record on every successful submit.
- [ ] Attach initial due date using stage SLA defaults.
- [ ] Add correlation ID propagation into queue metadata.

Done criteria:
1. 10/10 seeded submits create queue records.
2. No duplicate queue records on idempotent replay.

Evidence:
- [ ] Seed run output
- [ ] Queue query proof

## Day 3: SLA Timers and Escalation
- [ ] Configure SLA policy by stage.
- [ ] Implement due-soon event emission.
- [ ] Implement overdue escalation to lead queue.
- [ ] Add breach counter metric.

Done criteria:
1. Simulated overdue cases escalate correctly.
2. SLA breach metric increments and is queryable.

Evidence:
- [ ] Escalation log proof
- [ ] Metric/query output

## Day 4: Parent Status Timeline and Checklist Model
- [ ] Add parent status timeline payload.
- [ ] Add checklist item model (required docs/actions).
- [ ] Add due-date and completion-state fields.
- [ ] Verify API contract in sandbox.

Done criteria:
1. Parent timeline reflects real stage transitions.
2. Checklist state persists accurately across refresh/reload.

Evidence:
- [ ] API response snapshots
- [ ] UI screenshot proof

## Day 5: Communication Journeys v1
- [ ] Build submission confirmation template.
- [ ] Build missing document reminder template.
- [ ] Build interview scheduling prompt template.
- [ ] Add communication event log records.

Done criteria:
1. Each journey fires exactly once per qualifying event.
2. Duplicate sends prevented on retries.

Evidence:
- [ ] Event log excerpts
- [ ] Deduplication test output

## Day 6: Interview Handoff and Escalations
- [ ] Add interview pending status state.
- [ ] Add no-response escalation policy.
- [ ] Add no-show escalation policy.
- [ ] Add next-best-action suggestions for counselors.

Done criteria:
1. All seeded no-response/no-show scenarios escalate as defined.

Evidence:
- [ ] Scenario matrix output

## Day 7: Decision Transitions
- [ ] Implement admit transition action.
- [ ] Implement waitlist transition action.
- [ ] Implement decline transition action.
- [ ] Capture transition reason and timestamp.

Done criteria:
1. Decision transitions are auditable and immutable in logs.
2. Parent-facing status reflects decision state.

Evidence:
- [ ] Audit trail proof
- [ ] Parent-view proof

## Day 8: Admissions Ops Dashboard v1
- [ ] Add stage aging widget.
- [ ] Add applications-by-owner widget.
- [ ] Add overdue SLA count widget.
- [ ] Add stage conversion widget.

Done criteria:
1. Dashboard values match source query outputs.

Evidence:
- [ ] Dashboard screenshot
- [ ] Source query snapshots

## Day 9: Segmentation and Cohort Velocity
- [ ] Add campus segmentation for funnel metrics.
- [ ] Add program segmentation for funnel metrics.
- [ ] Add weekly cohort velocity chart.
- [ ] Validate cohort boundaries and timestamp logic.

Done criteria:
1. Segmented metrics reconcile with unsegmented totals.

Evidence:
- [ ] Reconciliation output

## Day 10: Sandbox Dry Run and Baseline Freeze
- [ ] Execute 10-application dry run in sandbox.
- [ ] Validate all trigger-to-task-to-comms paths.
- [ ] Validate decision and conversion flows.
- [ ] Publish runbook update and freeze baseline.

Done criteria:
1. No orphaned applications.
2. No unowned queue records.
3. No silent stage transitions.
4. Final signoff artifact committed.

Evidence:
- [ ] Dry-run report
- [ ] Final signoff artifact

## Daily Integrity Checklist
- [ ] All completed items have linked evidence.
- [ ] Any partial implementation is labeled explicitly.
- [ ] No unresolved blocker is hidden or deferred without owner/date.
- [ ] CI and validation gates are reviewed before end-of-day closure.

## Owner and Timing Sheet
- Product owner initials: ______
- Backend owner initials: ______
- Frontend owner initials: ______
- QA owner initials: ______
- Start date: ______
- Target end date: ______
