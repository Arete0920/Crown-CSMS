# Crown Module Inventory

## Production Status Registry - Updated April 1, 2026

Status definitions:

- Production-ready: live in production, tested, proven in staging
- Demo-ready: functional and suitable for investor demos, not fully production-hardened
- MVP slice: core workflow works, polish and edge cases deferred
- Deferred: roadmap only, out of current release scope

## Core Operations

| Module | Status | Notes |
|---|---|---|
| Authentication / RBAC | Production-ready | JWT plus MSAL patterns present |
| School Admin Dashboard | Production-ready | Role dashboards available |
| Multi-tenant Isolation | Production-ready target | Header-based scoping and tenant tests |
| Admissions | Demo-ready | Intake and review workflows available |
| Enrollment | Demo-ready | Transition endpoint present |
| Student 360 View | Demo-ready | Aggregated student view functional |

## Billing and Finance

| Module | Status | Notes |
|---|---|---|
| Parent Subscription | Demo-ready | Billing APIs and invoice flows present |
| CompuWerx Integration | Demo-ready | Integration wiring exists |
| Setup Fee | MVP slice | Manual process remains |
| Add-on Module Pricing | MVP slice | Pricing model defined |
| Financial Aid Processing | Demo-ready | Intake and approval flows functional |
| Billing Dashboard | Demo-ready | School-wide billing views present |

## Academics

| Module | Status | Notes |
|---|---|---|
| Attendance | Production-ready target | Submission and read APIs present |
| Gradebook | Demo-ready | Assignment and grading surfaces present |
| Course Management | Demo-ready | Courses and sections present |
| Transcripts / Report Cards | MVP slice | Partial automation |
| Academic Calendar | MVP slice | In progress |

## Faith Integration

| Module | Status | Notes |
|---|---|---|
| Chapel Attendance | Demo-ready | Session tracking available |
| Bible Curriculum | Demo-ready | Curriculum tracking available |
| Spiritual Development Milestones | Demo-ready | Spiritual-life module present |
| Crown Compass Scoring | Deferred | Roadmap item |

## Communications

| Module | Status | Notes |
|---|---|---|
| Announcements | Production-ready | Messaging surface present |
| Messaging | Demo-ready | Core communications available |
| SMS Notifications | MVP slice | Twilio-based capability |
| Email Notifications | Demo-ready | Outbox and messaging plumbing present |

## Family Portal

| Module | Status | Notes |
|---|---|---|
| Parent Portal | Demo-ready | Parent 360 and household access patterns |
| Student Portal | Demo-ready | Student views available |
| Family Financial View | Demo-ready | Billing and household summaries available |