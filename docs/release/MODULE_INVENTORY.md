# Crown Module Inventory

> Authority Scope Notice (2026-05-29)
>
> This document is an operational module/status registry and not a controlling repository-level release authority source.
>
> Current controlling sources:
> - docs/CURRENT_RELEASE_STATUS.md
> - docs/release/CURRENT_RELEASE_SCORECARD_20260528.md

## Production Status Registry - Updated April 1, 2026

Status definitions:

- Production-ready: live in production, tested, proven in staging
- Evidence-backed release candidate: functional with proof artifacts present; full production claim requires all release gates green
- In-progress hardening: core workflow exists with remaining hardening or completion work tracked
- Out-of-scope: roadmap-only item outside the current release claim

## Core Operations

| Module | Status | Notes |
|---|---|---|
| Authentication / RBAC | Production-ready | JWT plus MSAL patterns present |
| School Admin Dashboard | Production-ready | Role dashboards available |
| Multi-tenant Isolation | Production-ready target | Header-based scoping and tenant tests |
| Admissions | Evidence-backed release candidate | Intake and review workflows available |
| Enrollment | Evidence-backed release candidate | Transition endpoint present |
| Student 360 View | Evidence-backed release candidate | Aggregated student view functional |

## Billing and Finance

| Module | Status | Notes |
|---|---|---|
| Parent Subscription | Evidence-backed release candidate | Billing APIs and invoice flows present |
| CompuWerx Integration | Evidence-backed release candidate | Integration wiring exists |
| Setup Fee | In-progress hardening | Manual process remains |
| Add-on Module Pricing | In-progress hardening | Pricing model defined |
| Financial Aid Processing | Evidence-backed release candidate | Intake and approval flows functional |
| Billing Dashboard | Evidence-backed release candidate | School-wide billing views present |

## Academics

| Module | Status | Notes |
|---|---|---|
| Attendance | Production-ready target | Submission and read APIs present |
| Gradebook | Evidence-backed release candidate | Assignment and grading surfaces present |
| Course Management | Evidence-backed release candidate | Courses and sections present |
| Transcripts / Report Cards | In-progress hardening | Partial automation |
| Academic Calendar | In-progress hardening | In progress |

## Faith Integration

| Module | Status | Notes |
|---|---|---|
| Chapel Attendance | Evidence-backed release candidate | Session tracking available |
| Bible Curriculum | Evidence-backed release candidate | Curriculum tracking available |
| Spiritual Development Milestones | Evidence-backed release candidate | Spiritual-life module present |
| Crown Compass Scoring | Out-of-scope | Roadmap item |

## Communications

| Module | Status | Notes |
|---|---|---|
| Announcements | Production-ready | Messaging surface present |
| Messaging | Evidence-backed release candidate | Core communications available |
| SMS Notifications | In-progress hardening | Twilio-based capability |
| Email Notifications | Evidence-backed release candidate | Outbox and messaging plumbing present |

## Family Portal

| Module | Status | Notes |
|---|---|---|
| Parent Portal | Evidence-backed release candidate | Parent 360 and household access patterns |
| Student Portal | Evidence-backed release candidate | Student views available |
| Family Financial View | Evidence-backed release candidate | Billing and household summaries available |

