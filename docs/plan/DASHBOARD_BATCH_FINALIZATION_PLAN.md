# Crown2026 Dashboard Finalization Plan (Batch and Role)

Purpose:
Finalize all dashboard work without random page-by-page churn.

Core rule:
Finalize shared roles first, then academic/finance workflows, then family-facing roles, then edge/admin specialist roles.

Execution rule:
Do not finalize dashboards one page at a time in random order. Execute in role batches, with proof after each batch.

## Standard Batch Workflow
Every batch must follow this order:
1. Lock the role list for the batch.
2. Verify routes and sidebar/nav visibility.
3. Wire and verify live data.
4. Verify loading, empty, and error states.
5. Verify permissions.
6. Verify visual polish.
7. Run smoke test.
8. Rerun fast gate.
9. Commit only that batch.

## Dashboard Completion Standard
A dashboard is complete only when all are true:
- route exists and loads
- menu/shortcut points to correct route
- data is live or explicitly documented as demo data
- widgets do not 500, crash, or spin forever
- empty state is human-readable
- error state is human-readable
- role cannot see dashboards they should not see
- layout works on desktop and tablet
- no obvious visual placeholders or broken cards
- no console errors
- no fake numbers unless explicitly labeled as demo

## Batch 0: Shared Spine and Cross-Role Shell
Scope:
- home dashboard shell
- layout container
- top nav, sidebar, breadcrumbs
- notifications area
- profile/account panel
- global filters if used
- error boundary behavior
- loading skeleton behavior
- empty state component consistency
- KPI card consistency
- chart card consistency

Roles affected:
- all roles

Exit criteria:
- one polished shell used everywhere
- one consistent state system for loading, empty, and error
- one consistent card/chart/table style
- no shared layout refactor needed later

## Batch 1: Executive and Platform Control Roles
Roles:
- Super Admin or Platform Admin
- Head of School or Executive Director
- Principal or Academic Dean
- Board Oversight or Board Viewer
- Master Control or System Oversight

Dashboards:
- Executive Summary
- School Health or Crown Compass
- Enrollment and retention summary
- Finance summary snapshot
- Mission, culture, attendance snapshot
- Strategic alerts and risk flags
- Board intelligence summary
- System status and audit summary

Exit criteria:
- executive dashboards are production-polished
- board role is read-only
- strategic alerts are meaningful
- numbers reconcile with source modules

## Batch 2: Admissions, Enrollment, Registrar
Roles:
- Admissions Director
- Admissions Counselor
- Enrollment Manager
- Registrar
- Re-enrollment Coordinator

Exit criteria:
- admissions can run daily from dashboard
- registrar can identify record issues quickly
- re-enrollment status is visible and trusted

## Batch 3: Finance, Billing, Financial Aid
Roles:
- Business Office
- Finance Director or CFO
- Billing Manager
- Accounts Receivable
- Financial Aid Director
- Payment or Ledger Reviewer

Exit criteria:
- totals match finance endpoints
- aid and billing do not conflict
- tenant boundaries proven
- operationally usable, not presentation-only

## Batch 4: Academic Operations
Roles:
- Academic Dean
- Registrar
- Department Chair
- Teacher Lead
- Scheduling Coordinator
- Attendance Officer

Exit criteria:
- gradebook summary trusted
- schedule, roster, attendance align
- no stale or phantom section behavior

## Batch 5: Teacher
Roles:
- Teacher
- Homeroom Teacher or Advisor
- Section Teacher
- Substitute-lite read-only view if designed

Exit criteria:
- teacher can start day from this screen
- quick actions are practical
- no admin data leakage

## Batch 6: Student Care, Discipline, Counselor, Chaplain
Roles:
- Dean of Students
- Discipline Officer
- Student Care Coordinator
- Counselor
- Chaplain
- Spiritual Life Director

Exit criteria:
- strict privacy boundaries
- actionable triage queues
- no sensitive data overexposure

## Batch 7: Parent and Family
Roles:
- Parent
- Guardian
- Family Account Holder

Exit criteria:
- family sees only own children
- balances are correct
- mobile and tablet behavior is clean

## Batch 8: Student
Roles:
- Student
- Dual Enrollment Student (if separate)
- Senior or graduation-track view (if specialized)

Exit criteria:
- student sees only own data
- dashboard is clear and actionable
- no admin clutter

## Batch 9: Advancement, Development, Outreach
Roles:
- Advancement Director
- Development Officer
- Donor or Campaign Manager
- Outreach or Community Relations

Exit criteria:
- fundraising metrics are real and scoped
- follow-up queues are actionable

## Batch 10: Activities, Athletics, Events
Roles:
- Athletics Director
- Coach
- Activities Coordinator
- Event Manager

Exit criteria:
- live team and event data
- efficient coach workflows

## Batch 11: Operations, Facilities, Transportation, Food, Health
Roles:
- Operations Manager
- Facilities Manager
- Transportation Coordinator
- Food Service Manager
- Nurse or Health Office
- Safety or Security Coordinator

Exit criteria:
- specialist queues are actionable
- health and safety permissions are strict

## Batch 12: Platform, Audit, DevOps, Internal Support
Roles:
- Internal Support Admin
- Audit Reviewer
- Compliance or QA Reviewer
- Technical Operations or Dev Admin

Exit criteria:
- support dashboards are useful and not noisy
- internal-only data remains internal

## Safe Execution Order
1. Batch 0
2. Batch 1
3. Batch 2
4. Batch 3
5. Batch 4
6. Batch 5
7. Batch 6
8. Batch 7
9. Batch 8
10. Batch 9
11. Batch 10
12. Batch 11
13. Batch 12

Why this order:
- protects leadership demo value
- prioritizes enrollment and finance readiness
- supports daily academic operations
- protects family-facing stability
- defers specialist and internal roles until core workflows are stable

## Per-Batch Proof Checklist
Before moving to next batch, confirm:
- route list verified
- sidebar/menu verified
- role access verified
- API/data verified
- loading/empty/error states verified
- responsive layout verified
- no console errors
- frontend audit rerun
- fast gate rerun
- manual click-through completed
- commit is batch-only scope
- no unrelated edits staged

## Role Completion Matrix (Certification View)
Executive and Admin:
- Super Admin: Batch 1 + 12
- Head of School: Batch 1
- Principal or Academic Dean: Batch 1 + 4
- Board Viewer: Batch 1 read-only
- Master Control or System Oversight: Batch 1 + 12

Enrollment:
- Admissions Director: Batch 2
- Admissions Counselor: Batch 2
- Enrollment Manager: Batch 2
- Registrar: Batch 2 + 4
- Re-enrollment Coordinator: Batch 2

Finance:
- Finance Director or CFO: Batch 3
- Billing Manager: Batch 3
- Accounts Receivable: Batch 3
- Financial Aid Director: Batch 3
- Ledger Reviewer: Batch 3

Academic:
- Academic Dean: Batch 4
- Department Chair: Batch 4
- Scheduling Coordinator: Batch 4
- Attendance Officer: Batch 4
- Teacher and Advisor: Batch 5

Student Support:
- Dean of Students: Batch 6
- Discipline Officer: Batch 6
- Counselor: Batch 6
- Chaplain: Batch 6
- Spiritual Life Director: Batch 6
- Student Care Coordinator: Batch 6

Family-facing:
- Parent or Guardian: Batch 7
- Student: Batch 8

Advancement and Community:
- Advancement Director: Batch 9
- Development Officer: Batch 9
- Outreach and Community Relations: Batch 9

Student Life:
- Athletics Director: Batch 10
- Coach: Batch 10
- Activities Coordinator: Batch 10
- Event Manager: Batch 10

Specialist Ops:
- Operations Manager: Batch 11
- Facilities Manager: Batch 11
- Transportation Coordinator: Batch 11
- Food Service Manager: Batch 11
- Nurse or Health Office: Batch 11
- Safety or Security Coordinator: Batch 11

Internal Technical:
- Internal Support Admin: Batch 12
- Audit Reviewer: Batch 12
- Compliance or QA Reviewer: Batch 12
- Dev or Technical Ops Admin: Batch 12

## Recommended Completion Definition
A dashboard is complete only when it is:
- visible to correct role
- hidden from wrong role
- live-data or explicitly documented demo-data
- visually polished
- actionable
- stable under empty/error/loading states
- signed off for production behavior
