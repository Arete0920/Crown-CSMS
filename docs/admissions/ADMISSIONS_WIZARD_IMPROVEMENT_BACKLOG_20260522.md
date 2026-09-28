# Admissions Wizard Improvement Backlog (P0/P1/P2)

Date: 2026-05-22
Scope: Crown admissions funnel operation, function, and appearance improvements derived from general admissions workflow research and school-user needs.

Companion planning artifact:
- docs/admissions/ADMISSIONS_WIZARD_SPRINT_BOARD_20260522.md

Process integration playbook:
- docs/admissions/ADMISSIONS_DELIVERY_PROCESS_PLAYBOOK_20260522.md

## Owner Lanes

- Product: requirements, priorities, SLA commitments, governance
- Frontend: parent and staff UX, timeline/status surfaces, wizard interactions
- Backend: workflow APIs, automation, alerts, integrity/idempotency, eventing
- Admissions Ops: templates, reviewer policy, stage ownership, quality controls
- Data/Analytics: KPIs, dashboards, forecasting, funnel reporting
- QA: E2E reliability, regression automation, acceptance test evidence

## P0 (0-30 days) - Reliability + Family Trust

### 1) Final submit idempotency and duplicate prevention
- Primary owners: Backend, QA
- Acceptance criteria:
  - Repeated final-submit requests with same token create one submission only.
  - Duplicate submits return safe success/duplicate response without 500.
  - E2E test proves no duplicate application creation under retries.

### 2) End-to-end submit smoke monitor
- Primary owners: Backend, QA, Data/Analytics
- Acceptance criteria:
  - Synthetic submit check runs every 5 minutes in non-prod and hourly in prod.
  - Alert triggers on >1 consecutive failures.
  - Dashboard shows rolling 7-day success rate.

### 3) Stage SLA clocks visible to families
- Primary owners: Product, Frontend, Admissions Ops
- Acceptance criteria:
  - Family sees first-response SLA and review SLA after submit.
  - SLA text configurable by campus/program.
  - SLA timestamps persist across sessions.

### 4) Post-submit status center for families
- Primary owners: Frontend, Backend
- Acceptance criteria:
  - New status panel shows current stage, next milestone, and owner contact.
  - Family can see last update timestamp.
  - Status data sourced from admissions events API.

### 5) No-follow-up aging alerts
- Primary owners: Backend, Admissions Ops, Data/Analytics
- Acceptance criteria:
  - Applications with no update beyond threshold auto-flag.
  - Owner and manager escalation route defined.
  - Alert resolution actions tracked.

### 6) Structured error payloads for admissions submit path
- Primary owners: Backend, Frontend
- Acceptance criteria:
  - Submit errors return consistent code/message/detail schema.
  - Family-facing error copy is actionable and non-technical.
  - Error telemetry includes route, status, and correlation id.

### 7) Re-check service + offline guidance hardening
- Primary owners: Frontend, QA
- Acceptance criteria:
  - Final step exposes service precheck state and retry action.
  - Submit button behavior is deterministic for checking/down/ready states.
  - E2E test validates all three states.

### 8) Stage-complete chips and persistent readiness summary
- Primary owners: Frontend
- Acceptance criteria:
  - Completion chips remain visible in steps 5-8 and review.
  - Household summary remains accurate as entries change.
  - Summary parity test covers guardian/child counts.

### 9) Admissions communication playbook v1
- Primary owners: Admissions Ops, Product
- Acceptance criteria:
  - Stage-based templates defined for inquiry, submit, review, decision.
  - Each template includes SLA, owner, and next step statement.
  - Playbook approved and versioned.

## P1 (31-90 days) - Reviewer Excellence + Operational Control

### 10) Reviewer packet auto-summary (household and child level)
- Primary owners: Backend, Frontend, Admissions Ops
- Acceptance criteria:
  - Staff view shows normalized summary with household context and per-child profile.
  - Mission narrative and support notes grouped consistently.
  - Exportable packet generated for decision meeting.

### 11) Decision reason templates and consistency checks
- Primary owners: Admissions Ops, Backend
- Acceptance criteria:
  - Decision action requires reason code + narrative.
  - Consistency guard warns when evidence fields are incomplete.
  - Audit log stores final rationale with actor and timestamp.

### 12) Funnel bottleneck heatmap dashboard
- Primary owners: Data/Analytics, Product
- Acceptance criteria:
  - Dashboard shows stage aging by campus and grade band.
  - Top bottleneck stage highlighted automatically.
  - Weekly report export available.

### 13) Counselor workload balancing view
- Primary owners: Frontend, Data/Analytics, Admissions Ops
- Acceptance criteria:
  - Work queue shows owner workload and aging risk.
  - Reassignment action available with reason capture.
  - SLA breach risk visible by owner.

### 14) Exception queue for incomplete/conflicting records
- Primary owners: Backend, Frontend, QA
- Acceptance criteria:
  - Validation exceptions routed to a dedicated queue.
  - Queue items include actionable remediation prompts.
  - Resolution state transitions are tracked.

### 15) Waitlist governance workflow
- Primary owners: Product, Admissions Ops, Backend
- Acceptance criteria:
  - Waitlist reason taxonomy implemented.
  - Review cadence and re-evaluation triggers enforced.
  - Waitlist communications use approved template set.

### 16) Forecast model for inquiry-to-enrollment
- Primary owners: Data/Analytics
- Acceptance criteria:
  - Weekly forecast published by campus and intake period.
  - Forecast compares planned vs actual conversion.
  - Variance thresholds trigger review tasks.

### 17) Mission conversation completion KPI instrumentation
- Primary owners: Data/Analytics, Admissions Ops
- Acceptance criteria:
  - Mission conversation completion captured per application.
  - KPI visible in admissions scorecard.
  - Month-over-month trend available.

### 18) First-term retention feedback loop (30/90 day)
- Primary owners: Product, Data/Analytics, Admissions Ops
- Acceptance criteria:
  - Cohort retention pulse collected at 30 and 90 days.
  - Admissions attributes can be correlated to retention outcome.
  - Findings included in quarterly admissions review.

## P2 (91-180 days) - Conversion Continuity + Premium Experience

### 19) Acceptance-to-enrollment checklist continuity
- Primary owners: Product, Backend, Frontend
- Acceptance criteria:
  - Accepted families receive enrollment task list in same portal thread.
  - Checklist includes contract, deposit, and onboarding tasks.
  - Task completion feeds enrollment status API.

### 20) Event scheduling integration (tour/interview/shadow)
- Primary owners: Backend, Frontend
- Acceptance criteria:
  - Families can schedule available slots in-portal.
  - Confirmations and reminders are automatic.
  - Event outcomes write back to funnel stage state.

### 21) Secure document upload and per-item verification
- Primary owners: Backend, Frontend, QA
- Acceptance criteria:
  - Families can upload required files with validation constraints.
  - Staff can mark document as accepted/rejected with reason.
  - Family receives clear remediation prompt for rejected items.

### 22) Conditional forms by program/grade/support needs
- Primary owners: Product, Frontend, Backend
- Acceptance criteria:
  - Dynamic fields render based on selected program and student profile.
  - Validation adjusts to conditional requirements.
  - Form schema remains versioned for auditability.

### 23) Notification preference center (email/SMS/channel consent)
- Primary owners: Frontend, Backend, Admissions Ops
- Acceptance criteria:
  - Family can manage communication channels and consent.
  - Changes are reflected immediately in notification routing.
  - Consent audit trail retained.

### 24) Multilingual parent-facing admissions surfaces
- Primary owners: Frontend, Product
- Acceptance criteria:
  - Core admissions wizard and status center support at least 2 languages.
  - Mission-critical copy is human-reviewed for translation quality.
  - Language selection persists across sessions.

### 25) Premium visual and trust design refresh
- Primary owners: Frontend, Product
- Acceptance criteria:
  - Updated visual hierarchy for milestones, timelines, and confidence blocks.
  - Accessibility score meets WCAG 2.1 AA for key wizard views.
  - Measured uplift in step completion and submit conversion.

## KPI Targets (Initial)

- Submit reliability: >= 99.9% successful final submits
- Inquiry -> started conversion: +10% from baseline
- Started -> submitted conversion: +12% from baseline
- Median submitted -> decision time: -20% from baseline
- Accepted -> enrolled conversion: +8% from baseline
- SLA breach rate: < 5%

## Competitor Pattern Traceability


## Implementation Order

1. P0 items 1-4, 6, 7 first (stability and trust)
2. P1 items 10-14 next (reviewer quality and control)
3. P2 items 19-21 then 25 (conversion continuity and premium experience)
