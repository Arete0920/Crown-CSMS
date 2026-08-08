# CROWN Module Completion Matrix

**Status:** ACTIVE CONTROL MATRIX — EVIDENCE BASELINE  
**Baseline inspected:** `main` at `57c14f789a05f1d61e8b63b95f846f7ba546d55d` on 2026-08-07  
**Parent canon:** `docs/product/CROWN_MODULES_AND_DASHBOARDS_CANON.md`  
**Release authority:** `docs/CURRENT_RELEASE_STATUS.md` and GitHub issue `#1619`

## Purpose

This is the required row-level completion control for CROWN modules. It does not replace the bounded production-release certification in issue `#1619`. It governs the separate full-module completion program.

Only the canon statuses are allowed: `Inventory`, `Schema-visible`, `Wired`, `Runtime-visible`, `Evidence-backed`, and `Certified`. Only `Certified` means complete.

No row may be promoted from this baseline because a route renders, a dashboard registry row exists, sample data exists, or a repository-wide test is green. Promotion requires current row-specific evidence for the complete module flow and an independent human review retained under `CROWN_MODULE_REVIEW_RACI.md`.

## Baseline disposition

The current audit proves broad repository inventory and several cross-layer structural contracts, but it does not yet provide a current, independent, row-complete evidence packet for every module. Therefore every row below is conservatively baselined at `Inventory` until its complete evidence packet is assembled and reviewed.

The August 4 production release remains separately certified for its bounded supported scope. This matrix does not downgrade that release and does not broaden its claims.

## Required evidence columns

For each row, promotion requires evidence for: domain ownership; models/schema; service/query layer; API; tenant enforcement; entitlement; action permission; validation/error behavior; audit events; frontend workflow; dashboard source/provenance where applicable; performance limits; backend/frontend/runtime tests; and independent review.

`NOT VERIFIED` means the full row-specific requirement has not yet been proven in the current full-module audit. It does not mean no implementation exists.

## Phase 0 — Control layer

| Order | Module Key | Module / Control Area | Status | Current evidence boundary | Blocking proof |
|---:|---|---|---|---|---|
| 0.1 | `tenant-school-context` | Tenant / School Context | Inventory | Bounded release tenant evidence exists | Full module/API tenant matrix, cross-tenant negative proof, current independent review NOT VERIFIED |
| 0.2 | `identity-users-roles` | Identity / Users / Roles | Inventory | Authentication and role infrastructure exists | Full identity lifecycle, role assignment, recovery, and module-scope proof NOT VERIFIED |
| 0.3 | `rbac-permissions` | RBAC / Permissions | Inventory | Central permission engine exists | Action-level matrix coverage and direct-URL/API negative proof for every module NOT VERIFIED |
| 0.4 | `audit-logging` | Audit Logging | Inventory | Audit facilities exist in repository | Required-event coverage for every sensitive/write action NOT VERIFIED |
| 0.5 | `entitlements-subscriptions` | Entitlements / Subscriptions | Inventory | Subscription/entitlement surfaces exist | Navigation + API + dashboard entitlement parity for every module NOT VERIFIED |
| 0.6 | `retention-rollover` | Retention / Rollover | Inventory | Governance requirements documented | Module-specific retention, purge, archive, rollover and recovery proof NOT VERIFIED |
| 0.7 | `dashboard-certification-contract` | Dashboard Certification Contract | Inventory | 40-key registry/data/backend structural audit exists | Full provenance, freshness, sensitivity, payload, performance and review contract NOT VERIFIED |

## Phase 1 — Core SIS truth

| Order | Module Key | Module | Status | Current evidence boundary | Blocking proof |
|---:|---|---|---|---|---|
| 1 | `school-year-grade` | School / Academic Year / Grade Level | Inventory | Repository surface documented | Lifecycle, rollover, API, permission, tenant and runtime evidence packet NOT VERIFIED |
| 2 | `staff-user-role` | Staff / Identity / Roles | Inventory | Repository surface documented | Staff lifecycle, role alignment, permission and audit evidence packet NOT VERIFIED |
| 3 | `family-guardian-household` | Family / Guardian / Household | Inventory | Repository surface documented | Custody, portal visibility, redaction and lifecycle evidence packet NOT VERIFIED |
| 4 | `student-master` | Student Master Record | Inventory | Repository surface documented | Status lifecycle, validation, audit and cross-module write rules NOT VERIFIED |
| 5 | `enrollment-registrar` | Enrollment / Registrar | Inventory | Registrar/dashboard/wizard surfaces exist | Enrollment state machine, side effects, audit and runtime proof NOT VERIFIED |
| 6 | `courses-sections-rosters` | Courses / Sections / Rosters | Inventory | Academic surfaces exist | Canonical roster ownership and teacher/student scope proof NOT VERIFIED |
| 7 | `attendance` | Attendance | Inventory | Dashboard is structurally registered; bounded supported-role evidence exists | Correction audit, freshness, row-level RBAC, live provenance and full module evidence NOT VERIFIED |
| 8 | `gradebook` | Gradebook | Inventory | UI/API proof workflows exist | Lock/finalization, roster scope, parent visibility and complete module evidence NOT VERIFIED |
| 9 | `transcripts-reportcards` | Transcript / Report Card / Graduation | Inventory | Repository surface documented | Official-record lock/reopen, graduation lifecycle, export/redaction proof NOT VERIFIED |
| 10 | `student-care-discipline` | Student Care / Discipline | Inventory | Dashboard and care surfaces exist | Highly-sensitive redaction, small-cell, audit and access proof NOT VERIFIED |

## Phase 2 — Commercial operating modules

| Order | Module Key | Module | Status | Current evidence boundary | Blocking proof |
|---:|---|---|---|---|---|
| 11 | `admissions` | Admissions | Inventory | Routes, wizard/API and dashboard surfaces exist | Applicant-to-enrollment conversion, permission, tenant and runtime evidence packet NOT VERIFIED |
| 12 | `re-enrollment` | Re-enrollment | Inventory | Wizard/API surface exists | Year rollover, contract states and downstream side-effect proof NOT VERIFIED |
| 13 | `billing-tuition-ledger` | Billing / Tuition / Ledger | Inventory | Billing/finance surfaces exist; external payment processing remains fail closed | Ledger immutability, reversal/export rules and full module proof NOT VERIFIED |
| 14 | `financial-aid` | Financial Aid | Inventory | Wizard/dashboard surfaces exist | Confidential award lifecycle, billing impact and access proof NOT VERIFIED |
| 15 | `communications` | Communications | Inventory | Permission-protected metrics route and frontend surfaces exist | Live tenant-derived metrics, delivery/audit/opt-out/emergency behavior NOT VERIFIED |
| 16 | `parent-family-portal` | Parent / Family Portal | Inventory | Portal routes exist | Custody redaction, child/household scope, write boundaries and full role proof NOT VERIFIED |
| 17 | `teacher-portal` | Teacher Portal | Inventory | Supported-role release evidence exists | Section/roster action scope and complete module evidence packet NOT VERIFIED |
| 18 | `administrator-portal` | Administrator Portal | Inventory | Supported-role release evidence and dashboard surface exist | Aggregate redaction, drilldown authority and module-complete evidence NOT VERIFIED |

## Phase 3 — Operational expansion modules

| Order | Module Key | Module | Status | Current evidence boundary | Blocking proof |
|---:|---|---|---|---|---|
| 19 | `scheduling` | Scheduling | Inventory | Routes/dashboard/wizard surfaces exist | Conflict engine, room/location ownership, publish lifecycle and runtime proof NOT VERIFIED |
| 20 | `activities-athletics` | Activities / Athletics | Inventory | Dashboard surfaces exist | Eligibility source, roster ownership and family visibility proof NOT VERIFIED |
| 21 | `health-office` | Health Office | Inventory | Module/dashboard surfaces exist | Highly-sensitive access, health redaction, audit and stale-data proof NOT VERIFIED |
| 22 | `transportation` | Transportation | Inventory | Module/dashboard surfaces exist | Address source, rider/emergency scope and lifecycle proof NOT VERIFIED |
| 23 | `food-service` | Food Service | Inventory | Module/dashboard surfaces exist | Billing boundary, meal-account privacy and operational workflow proof NOT VERIFIED |
| 24 | `facilities` | Facilities | Inventory | Module/dashboard surfaces exist | Asset/location ownership and work-order lifecycle proof NOT VERIFIED |
| 25 | `safety-security` | Safety / Security | Inventory | Module/dashboard surfaces exist | Incident access, notification, redaction and audit proof NOT VERIFIED |
| 26 | `hr` | HR | Inventory | Module/dashboard surfaces exist | Sensitive staff-data separation, manager scope and lifecycle proof NOT VERIFIED |
| 27 | `it-support` | IT Support | Inventory | Module/dashboard surfaces exist | Access-change boundary, escalation and audit proof NOT VERIFIED |

## Phase 4 — Enrichment, mission, and advancement

| Order | Module Key | Module | Status | Current evidence boundary | Blocking proof |
|---:|---|---|---|---|---|
| 28 | `fine-arts` | Fine Arts | Inventory | Dashboard surface exists | Roster/event service, permissions and runtime proof NOT VERIFIED |
| 29 | `library-media` | Library / Media | Inventory | Dashboard surface exists | Circulation model, privacy, overdue lifecycle and runtime proof NOT VERIFIED |
| 30 | `extended-care` | Extended Care | Inventory | Dashboard and aftercare surfaces exist | Check-in/out, custody, billing linkage and role alignment proof NOT VERIFIED |
| 31 | `summer-camp` | Summer Camp | Inventory | Dashboard surface exists | Seasonal lifecycle, roster/session API and runtime proof NOT VERIFIED |
| 32 | `spiritual-life` | Spiritual Life / Chaplaincy | Inventory | Mission surfaces exist | Pastoral confidentiality, redaction, audit and role proof NOT VERIFIED |
| 33 | `service-outreach-portrait` | Service / Outreach / Portrait | Inventory | Dashboard surface exists | Approval workflow, graduation linkage and permission proof NOT VERIFIED |
| 34 | `volunteer-management` | Volunteer Management | Inventory | Dashboard surface exists | Background-check privacy, approval workflow and restricted access proof NOT VERIFIED |
| 35 | `advancement-operations` | Advancement Operations | Inventory | Dashboard surfaces exist | Donor privacy, gift/finance boundary and runtime proof NOT VERIFIED |
| 36 | `alumni-relations` | Alumni Relations | Inventory | Dashboard surface exists | Alumni conversion, contact rules and access proof NOT VERIFIED |
| 37 | `board-governance` | Board Governance | Inventory | Board/dashboard surfaces exist | Board access boundary, exports and governance-record lifecycle proof NOT VERIFIED |
| 38 | `curriculum-pd` | Curriculum / PD | Inventory | Dashboard surface exists | Curriculum ownership/versioning, PD approval and runtime proof NOT VERIFIED |
| 39 | `network-benchmarking` | Network Benchmarking / Analytics | Inventory | Dashboard surface exists | Anonymization, small-cell suppression and multi-school isolation proof NOT VERIFIED |

## Phase 5 — Platform operations

| Order | Module Key | Module | Status | Current evidence boundary | Blocking proof |
|---:|---|---|---|---|---|
| 40 | `implementation-success` | Implementation Success | Inventory | Dashboard surface exists | Customer-readiness source, tenant/customer separation and runtime proof NOT VERIFIED |
| 41 | `data-migration` | Data Migration | Inventory | Dashboard/import surfaces exist | Rollback/backfill, validation, audit and sensitive-data proof NOT VERIFIED |
| 42 | `integrations-automation` | Integrations / Automation | Inventory | Dashboard/integration surfaces exist | Retry/dedupe, secret redaction, ownership and failure-recovery proof NOT VERIFIED |
| 43 | `compliance-audit` | Compliance Audit | Inventory | Dashboard/evidence surfaces exist | Exception workflow, retention and evidence-chain proof NOT VERIFIED |
| 44 | `revenue-operations` | Revenue Operations | Inventory | Dashboard surface exists | Customer/school-data separation and source-of-truth proof NOT VERIFIED |
| 45 | `release-reliability` | Release Reliability | Inventory | Registry marks dashboard ready; exact-head release workflows exist | Current-head service provenance, no sample fallback, performance and independent module review NOT VERIFIED |
| 46 | `dashboard-certification-center` | Dashboard Certification Center | Inventory | Registry-derived certification surface exists | Strict payload contract, evidence linkage, freshness/performance and independent review NOT VERIFIED |

## Promotion checklist

A row may move above `Inventory` only when the evidence packet names the exact source SHA and proves the relevant stages. A row may move to `Certified` only when all required evidence is current, zero required evidence items are pending/failed, the independent reviewer is identified and did not author the work, review findings are resolved, and the retained signoff references the exact evidence packet.

## Current baseline summary

- Control/module rows: **53** (7 control areas + 46 ordered module/platform areas).
- Rows marked `Certified` by this matrix: **0**.
- Independent full-module review assignments: **UNVERIFIED until recorded in the RACI**.
- Existing bounded production release status: **unchanged; governed by issue #1619**.
- Full-module completion claim: **NOT VERIFIED**.
