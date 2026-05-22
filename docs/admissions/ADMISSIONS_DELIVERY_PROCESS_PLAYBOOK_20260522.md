# Admissions Delivery Process Playbook

Date: 2026-05-22
Purpose: operationalize the admissions funnel improvement roadmap into daily execution, governance, and measurable outcomes.

## Scope

This playbook governs execution of:

- docs/admissions/ADMISSIONS_WIZARD_IMPROVEMENT_BACKLOG_20260522.md
- docs/admissions/ADMISSIONS_WIZARD_SPRINT_BOARD_20260522.md

## Operating Model

### Work Item Standard

All work is tracked as ADM tickets (ADM-001 to ADM-025) with:

- owner lane
- sprint target
- dependencies
- acceptance criteria
- evidence checklist
- KPI impact mapping

### Board Columns

Use this exact flow in your tracker:

1. Intake
2. Ready
3. In Progress
4. In Review
5. QA Verification
6. Evidence Collected
7. Done

Rules:

- No item enters Ready without Definition of Ready satisfied.
- No item enters Done without Definition of Done and evidence complete.
- Any blocker older than 24 hours is escalated in daily standup.

## Ceremony Cadence

### Daily Admissions Delivery Standup (15 min)

Participants:

- Product lead
- Frontend lead
- Backend lead
- QA lead
- Admissions Ops lead

Agenda:

1. Yesterday completed tickets
2. Today committed tickets
3. Blockers older than 24h
4. SLA-risk items in funnel

Required output:

- updated board status
- top 3 risks list

### Twice-Weekly Reliability Review (30 min)

Participants:

- Backend
- QA
- Data/Analytics

Agenda:

1. submit success rate trend
2. precheck and monitor alert review
3. open production defects

Required output:

- reliability status line for exec update

### Weekly Admissions Ops Quality Review (45 min)

Participants:

- Admissions Ops
- Product
- Data/Analytics
- Reviewer representatives

Agenda:

1. stage aging and no-follow-up list
2. decision rationale quality check
3. communication template effectiveness

Required output:

- actions list with owners and due dates

### Sprint Planning (60 min)

Participants:

- all lanes

Agenda:

1. capacity check
2. dependency alignment
3. commit sprint scope
4. confirm acceptance and evidence plan per ticket

Required output:

- sprint commitment document

### Sprint Review and Gate (45 min)

Participants:

- product and lane leads

Gate decision:

- Go: all committed acceptance criteria and evidence complete
- Conditional Go: non-critical carryover with explicit owner and date
- No-Go: critical acceptance criteria missing or reliability regression detected

## Definition of Ready

A ticket is Ready only if all are true:

- acceptance criteria are explicit and testable
- dependency tickets are done or scheduled
- owner lane and backup owner assigned
- test approach is defined (unit, integration, E2E)
- evidence output location is defined

## Definition of Done

A ticket is Done only if all are true:

- acceptance criteria met
- tests pass in CI/local target
- QA verification complete
- evidence artifact captured
- user-facing copy and support paths updated if needed
- KPI instrumentation updated when applicable

## Evidence Requirements by Ticket Type

### Reliability tickets

Required evidence:

- failing scenario reproduced (before)
- passing scenario validated (after)
- monitor/alert screenshot or output

### UX tickets

Required evidence:

- before and after screen references
- accessibility check notes
- copy review confirmation

### Ops/analytics tickets

Required evidence:

- dashboard/report snapshot
- data source query or lineage note
- owner signoff from Admissions Ops

## KPI Reporting Cadence

### Weekly KPI pack

Publish each Friday:

- submit reliability percentage
- inquiry to started conversion
- started to submitted conversion
- median submitted to decision time
- accepted to enrolled conversion
- SLA breach rate

### Monthly KPI review

Include:

- trend analysis and root causes
- top 3 interventions for next month
- comparison to target bands

## First 10 Business Days Execution Plan

### Days 1-2

- activate ADM-001 and ADM-002
- define test matrix for retries and error schema
- finalize correlation id logging format

### Days 3-4

- deliver ADM-003 precheck regression coverage
- configure ADM-004 smoke monitor schedule and thresholds

### Days 5-6

- deploy ADM-005 status center skeleton
- begin ADM-006 SLA display wiring

### Days 7-8

- implement ADM-007 aging alert policy with ops escalation path
- validate ADM-008 completion chip persistence

### Days 9-10

- run end-to-end reliability and trust validation
- publish first weekly KPI pack
- gate decision for sprint closeout

## Escalation Policy

- P0 production issue: escalate immediately to Backend and Product leads
- Blocker >24h: escalate in daily standup and assign unblock owner
- Missed SLA on family communication: escalate to Admissions Ops lead same day

## Paste-Ready Daily Status Template

Admissions delivery status:

- Completed today:
- In progress:
- Blockers:
- SLA-risk cases:
- Reliability status:
- Next 24h commitments:

## Paste-Ready Weekly Executive Update

Admissions modernization weekly update:

- Sprint progress: X of Y committed tickets complete
- Reliability: submit success rate at X% (target >= 99.9%)
- Throughput: median submitted to decision at X days
- Conversion: started to submitted at X% (target delta +12%)
- Risks: [top 3]
- Decisions needed: [owners and dates]
