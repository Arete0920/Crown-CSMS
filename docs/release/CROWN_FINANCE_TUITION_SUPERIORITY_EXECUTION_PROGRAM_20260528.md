# CROWN Finance and Tuition Superiority Execution Program (2026-05-28)

## Purpose
This program converts strategy into an implementation sequence that can be executed with high integrity, minimal rework, and production-grade evidence.

Target outcomes:
- Sandbox-ready finance and tuition core by 2026-06-01.
- Production-ready release posture by 2026-07-01.
- Functional superiority in Christian-school mission fit, Microsoft-native execution, and operator usability.

## Non-Negotiable Commitments
1. No guessing, no imagined behavior, no undocumented assumptions.
2. Backend truth first, then API contracts, then UI.
3. Every material change has test evidence and runtime verification.
4. Preserve source hygiene and tenant/privacy controls.
5. Keep one CROWN visual language across all personas and pages.
6. Keep prayer, devotion, announcements, celebrations, and communications available on all persona experiences.

## Current State Baseline
This plan is based on:
- Competitive synthesis and role model in docs/product/CROWN_PERSONA_DASHBOARD_COMPETITIVE_DESIGN_ASSESSMENT.md.
- Release authority posture in docs/CURRENT_RELEASE_STATUS.md.
- Admissions complexity boundaries in docs/release/ADMISSIONS_ORCHESTRATION_COMPLEXITY_REDUCTION_PLAN_20260527.md.
- Current long-running backend suite execution evidence in audit-artifacts/runtime-release-closure/20260418_070051/ARCHITECT_DESIGNER_PUNCHLIST_STATUS_20260528.md.

Observed finance/aid/billing API surfaces in active verification runs include:
- /api/finance/obligations/
- /api/finance/invoices/create-from-obligations/
- /api/finance/payments/intent/
- /api/finance/payments/{id}/settle/
- /api/finance/payments/{id}/refund/
- /api/billing/households/{id}/open-invoices/
- /api/exports/accounting/payments-qb.csv
- /api/v1/aid-wizard/sessions/*
- /api/v1/billing-wizard/sessions/*
- /api/v1/financial-aid/summary
- /api/v1/financial-aid/drilldown

## Strategy Positioning
CROWN winning lane:
- Microsoft-native Christian school finance operating system.

Not the target:
- Generic ERP clone.

Functional parity baseline to meet quickly:
- Tuition configuration and schedules.
- Payment plans.
- Financial aid workflow from intake to billing handoff.
- Family billing portal clarity.
- A/R aging and collections workflow.
- Reconciliation and close support.
- Export/report integrity (including QuickBooks/Sage style pathways).

## Delivery Model (Backend-First)
Every capability must pass this sequence:
1. Data model and migration.
2. Service layer with deterministic business rules.
3. API contract with validation and permission checks.
4. Audit/event logging and idempotency behavior.
5. UI wiring and persona UX.
6. Export/report output.
7. Automated tests + focused runtime evidence.

## Workstreams
- WS1: Parent Financial Home.
- WS2: Finance Command Center.
- WS3: Tuition Builder Wizard.
- WS4: Financial Aid Workspace.
- WS5: A/R Aging Dashboard.
- WS6: Reconciliation Workspace.
- WS7: Family Statement Page.
- WS8: Board Finance Dashboard.

## Milestones
### M0 - Governance and Integrity (Immediate)
- Freeze acceptance criteria per workstream.
- Confirm API ownership and evidence packet template.
- Ensure every task references tests before merge.

### M1 - Sandbox Core (by 2026-06-01)
Required for sandbox-ready:
- Parent Financial Home core read model (balance due, next payment, autopay status, aid applied, open tasks).
- Finance Command Center core queues (cash today, A/R aging buckets, failed payments, pending refunds, pending aid).
- Tuition Builder Wizard publish flow with schedule and discount rules.
- Financial Aid Workspace basic lifecycle (application, checklist, recommendation, approval, family acceptance, billing handoff).
- Family Statement page generation from ledger truth.

### M2 - Production Operations (by 2026-06-15)
- Reconciliation workspace (processor payout match, unmatched queue, approval/lock actions).
- A/R aging drilldown and action queue.
- Batch posting/refund control hardening.
- QuickBooks/Sage export center with integrity checks.
- Board finance summary mode v1.

### M3 - Production Hardening (by 2026-07-01)
- Coverage closure on critical finance and aid flows.
- Performance and reliability guardrails for high-use payment paths.
- Accessibility/mobile consistency closure.
- Final runtime proof packet with pass/fail totals and go/no-go authority alignment.

## Persona-Specific Truth Priorities
### Parent/Guardian
- One amount due now.
- One next due date.
- One payment action.
- Statements, receipts, and task list with plain language.

### CFO/Business Manager
- Exception-first control plane.
- A/R aging, reconciliation delta, refund approvals, failed payments.
- Board-safe trend summaries.

### Finance Clerk
- Queue-based work execution.
- Posting/reversal guidance.
- Minimal executive noise.

### Admissions Director
- Fee/deposit/aid readiness and enrollment billing handoff.

### Financial Aid Officer
- Intake to award to billing, budget visibility, and full decision trace.

### Head of School and Board
- Tuition risk, aid exposure, affordability, and revenue impact.

### IT/Systems
- Integration health, failed syncs, provider status, and audit diagnostics.

## Architecture Slices and Expected Artifacts
For each workstream, deliver:
- One service module or enhancement.
- One API contract (request/response + validation).
- One route/page integration.
- One migration if required.
- One test packet (unit + API + role/rbac + regression).
- One runtime evidence markdown update in audit-artifacts.

## Quality Gates
1. No merge without test evidence.
2. No API exposure without permission and tenant validation tests.
3. No finance UI merge without data-truth mapping.
4. No export/report without deterministic fixture tests.
5. No persona page release without consistency checks for:
   - faith/community strip,
   - communications strip,
   - KPI row,
   - needs-attention panel,
   - data-truth footer.

## Risk Register and Controls
- Risk: Frontend-first drift.
  - Control: Enforce backend-first gate and API contract review.
- Risk: Reconciliation trust gap.
  - Control: Prioritize WS6 before release closeout.
- Risk: Aid workflow incompleteness.
  - Control: Require end-to-end aid-to-billing test before production signoff.
- Risk: Visual inconsistency by persona.
  - Control: Shared shell checklist and persona contract tests.
- Risk: Scope sprawl.
  - Control: Execute by workstream slices with strict acceptance criteria.

## Definition of Done (Program)
Program is complete only when all are true:
1. All 8 workstreams are implemented and verified.
2. Role-based workflows match persona expectations.
3. Sandbox and production milestones are met with evidence.
4. Release authority files and runtime artifacts are synchronized.
5. No unresolved critical finance or aid blockers remain.

## Execution Order (No Pause Sequence)
1. Parent Financial Home.
2. Finance Command Center.
3. Tuition Builder Wizard.
4. Financial Aid Workspace.
5. A/R Aging Dashboard.
6. Reconciliation Workspace.
7. Family Statement Page.
8. Board Finance Dashboard.
9. Cross-persona visual and accessibility hardening.
10. Final authority packet and go/no-go decision.
