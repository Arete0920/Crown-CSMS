# CrownMagus0 – Tier + Wizard Coverage Matrix

> **Legacy Positioning Note**
>
> This file contains older Crown Compass / Crown Solomon / Crown Discernment positioning language.
> The current authoritative definitions are:
> - `docs/canon/CROWN_COMPASS_CANON.md`
> - `docs/canon/CROWN_SOLOMON_CANON.md`
> - `docs/canon/CROWN_DISCERNMENT_PRINCIPLES.md`
> - `docs/canon/CROWN_DISCERNMENT_TECHNICAL_POSITION.md`
> - `docs/canon/CROWN_COMPASS_SOLOMON_DISCERNMENT_ARCHITECTURE.md`
>
> Until runtime implementation is explicitly approved, predictive analytics and scenario modeling remain conceptual and must not be treated as production-integrated features.

**Scope:** Gate 3–4 MVP (Core Ops + Academics Foundation)  
**Standard:** Tenant-safe, JWT protected, school-scoped, audited  
**Last verified:** 2026-02-28 (main `61e67163`)  
**Build evidence:** `django check` clean · no pending migrations · all gates green

---

## Tier Key

| Code | Meaning |
|------|---------|
| B | Smart Start (core SIS, Admissions, Billing, Aid, Comms, Dashboards) |
| M | Next Level (Smart Start + Attendance, Gradebook, Scheduling, Discipline, Activities) |
| C | All Access (full platform, board dashboards, premium integrations) |
| A | Add-On (optional per-school module) |

---

## 1. Admissions Module

| Component | Tier | Wizard | Backend App | Core Endpoints | Demo Status | Gaps |
|-----------|------|--------|------------|----------------|-------------|------|
| Application Intake | B/M/C | ✅ via `onboarding_wizard` | `admissions/` | `/api/v1/admissions/` | 🟢 Working | None |
| Document Tracking | B/M/C | Embedded | `admissions/` | `/api/v1/admissions/documents/` | 🟡 Partial | Validation hardening |
| Household/Guardian Link | B/M/C | ✅ `guardian_household_wizard` | `admissions/` | `/api/v1/admissions/links/` | 🟢 Working | None |
| Re-Enrollment | B/M/C | ✅ `reenrollment` wizard | `reenrollment/` | `/api/v1/reenrollment/sessions/` | 🟢 Working | Edge-case audit |
| Enrollment Conversion | M/C | ✅ `enrollment_conversion_wizard` | `enrollment/` | `/api/v1/enrollment-conversion-wizard/sessions/` | 🟢 Working | None |
| Enrollment Period Config | M/C | ✅ `enrollment_period_wizard` | `enrollment/` | `/api/v1/enrollment-period-wizard/sessions/` | 🟢 Working | None |
| POG / Mission Fit Score | C | ⚠️ No wizard | `admissions/` | — | 🟡 Partial | Weight engine logic not formalized |
| Funnel Dashboard Metrics | M/C | N/A | `admissions/` | `/api/v1/admissions/metrics/` | 🟡 Stub | Needs live DB aggregation |

**↳ App reality:** `admissions/` has models, services, api_views, 3 migration steps, seed command. Solid transactional layer; metrics surface is stub.

---

## 2. Financial Aid Module

> ⚠️ **Two separate apps exist:** `aid/` (application/award engine, wizard-facing) and `financial_aid/` (ledger-integrated distribution, 5 test files). Matrix must distinguish them.

| Component | Tier | Wizard | Backend App | Core Endpoints | Demo Status | Gaps |
|-----------|------|--------|------------|----------------|-------------|------|
| Aid Application | B/M/C | ✅ `financial_aid_wizard` | `aid/` | `/api/v1/aid-wizard/sessions/` | 🟢 Working | None |
| Award Engine | M/C | Embedded | `aid/services/award_engine.py` | `/api/v1/aid/awards/` | 🟢 Tested | `test_aid_engine.py` · `test_aid_award_invariants.py` |
| Ledger Bridge | M/C | N/A | `aid/services/ledger_bridge.py` | `/api/v1/ledger/allocations/` | 🟡 Partial | Reversal invariants under test |
| Aid Buckets (Need/Merit/Marketing/Hardship) | C | ⚠️ Backend only | `aid/models.py` | `/api/v1/aid/buckets/` | 🟡 Partial | Admin/wizard UI missing |
| Aid Metrics Dashboard | M/C | N/A | `financial_aid/` | `/api/v1/financial-aid/metrics/` | 🟢 Live charts | Drilldown API finishing |
| Phase 4b Ledger Integration | M/C | N/A | `financial_aid/` | `/api/v1/financial-aid/award/` | 🟡 Partial | `test_phase4b_ledger_integration.py` — invariants still hardening |
| Finance Policy Wizard *(NEW)* | B/M/C | ✅ `finance_setup` | `finance_setup/` | `/api/v1/finance-setup/wizard/` | 🟢 Working | Year-locked; 11 tests green |

**↳ App reality:** `aid/` has `award_engine.py`, `ledger_bridge.py`, 3 test files. `financial_aid/` has 5 test files including ledger integration. Both seeded.

---

## 3. Billing / Ledger Module

| Component | Tier | Wizard | Backend App | Core Endpoints | Demo Status | Gaps |
|-----------|------|--------|------------|----------------|-------------|------|
| Charge Creation | B/M/C | Embedded | `billing/` | `/api/v1/billing/` | 🟢 Working | None |
| Billing Setup Wizard | B/M/C | ✅ `billing_wizard` | `billing_wizard/` | `/api/v1/billing-wizard/sessions/` | 🟢 Working | None |
| Payment Allocation (FIFO) | B/M/C | N/A | `ledger/` | `/api/v1/ledger/allocate/` | 🟢 Working | `test_ledger_allocations_api.py` passing |
| Void / Reversal | M/C | N/A | `ledger/` | `/api/v1/ledger/void/` | 🟢 Tested | `test_gate2b_charge_void_reversal.py` · `test_ledger_void_endpoints_api.py` |
| Ledger Immutability | M/C | N/A | `ledger/` | — | 🟢 Certified | `test_ledger_immutability.py` · `test_ledger_invariants.py` |
| AR → Journal | M/C | N/A | `ledger/` | — | 🟢 Tested | `test_ar_posts_to_journal.py` |
| Invoice Run | M/C | ✅ `invoice_run_wizard` | Invoice wizard | `/api/v1/invoice-run-wizard/sessions/` | 🟢 Working | None |
| Fee Schedule Setup | M/C | ✅ `fee_schedule_wizard` | Fee wizard | `/api/v1/fee-schedule-wizard/sessions/` | 🟢 Working | None |
| Finance Policy (Tuition/Discounts/Plans) | B/M/C | ✅ `finance_setup` | `finance_setup/` | `/api/v1/finance-setup/wizard/configure/` | 🟢 Working | Year-lock enforced |
| Parent Financial View | B/M/C | N/A | `ledger/` | `/api/v1/ledger/statements/` | 🟡 Partial | `test_ledger_statements_api.py` — UI polish needed |

**↳ Ledger reality:** 12 test files, covering allocations, immutability, invariants, void/reversal, write safety, statements, payments correctness. **This is the strongest module in the platform.**

---

## 4. Finance Setup Wizard *(New — merged 2026-02-28)*

| Component | Tier | Wizard | Endpoints | Status |
|-----------|------|--------|-----------|--------|
| Tuition Structure (mode, currency, flat rate) | B/M/C | ✅ Step 1 | `wizard/configure/` | 🟢 Working |
| Discount Policy (sibling/staff/ministry, stacking) | B/M/C | ✅ Step 2 | `wizard/configure/` | 🟢 Working |
| Financial Aid Policy (app fee, distribution, caps) | B/M/C | ✅ Step 3 | `wizard/configure/` | 🟢 Working |
| Payment Plans (PIF/semi/quarterly/10mo/12mo, ACH) | B/M/C | ✅ Step 4 | `wizard/configure/` | 🟢 Working |
| Extended Care / Before-After School Policy | A | ✅ Step 5 | `wizard/configure/` | 🟢 Working |
| Year Lock | B/M/C | ✅ `wizard/lock/` | `wizard/lock/` | 🟢 Enforced · 409 on edit |
| Policy Snapshot | B/M/C | ✅ `wizard/snapshot/` | `wizard/snapshot/` | 🟢 Working |

**↳ Covers what the original matrix called "TuitionPlanWizard 🔴 Missing."** Now ✅ stable with 11 passing tests and 5-school demo seeded.

---

## 5. Extended Care / Aftercare Module *(not in original matrix)*

| Component | Tier | Wizard | Backend App | Core Endpoints | Demo Status | Gaps |
|-----------|------|--------|------------|----------------|-------------|------|
| Aftercare Roster | A | ✅ `aftercare_wizard` | `aftercare/` | `/api/aftercare/wizard/status/` | 🟢 Working | None |
| Program Configuration | A | ✅ Wizard | `aftercare/` | `/api/aftercare/wizard/configure/` | 🟢 Working | None |
| Late Pickup Fees | A | Embedded | `aftercare/` | `/api/aftercare/late-fees/` | 🟢 Tested | `test_aftercare_late_fee.py` |
| Tenant Scoping | A | N/A | `aftercare/` | — | 🟢 Tested | `test_aftercare_tenant_scoping.py` |
| Finance Policy Integration | A | Via `finance_setup` | `finance_setup/extended_care` | wizard snapshot | 🟢 Working | Policy reads from finance_setup |

---

## 6. Attendance Module

| Component | Tier | Wizard | Backend App | Core Endpoints | Demo Status | Gaps |
|-----------|------|--------|------------|----------------|-------------|------|
| Attendance Rules Config | M/C | ✅ `attendance_rules_wizard` | Wizard | `/api/v1/attendance-rules-wizard/sessions/` | 🟢 Working | None |
| Attendance Codes Config | M/C | ✅ `attendance_codes_wizard` | Wizard | `/api/v1/attendance-codes-wizard/sessions/` | 🟢 Working | None |
| Daily Attendance Entry | M/C | N/A | `academics/` | `/api/v1/academics/attendance/` | 🟢 Working | None |
| Attendance Alerts | M/C | N/A | — | — | 🟡 Basic | Smart threshold engine missing |
| Attendance Dashboard Metrics | M/C | N/A | — | — | 🟡 Stub | Needs live aggregation |

---

## 7. Discipline Module

| Component | Tier | Wizard | Backend App | Core Endpoints | Demo Status | Gaps |
|-----------|------|--------|------------|----------------|-------------|------|
| Incident Logging | M/C | Embedded | `discipline/api/` | `/api/v1/discipline/incidents/` | 🟢 Working | None |
| Seed / Demo Data | M/C | N/A | `discipline/management/` | `seed_discipline_demo` | 🟢 Ready | None |
| Disciplinary Dashboard | C | N/A | — | `/api/v1/discipline/metrics/` | 🔴 Not built | Needs aggregation layer |
| Escalation Flow | C | 🔴 No wizard | — | `/api/v1/discipline/escalations/` | 🔴 Not implemented | Requires policy rule engine |

**↳ App reality:** `discipline/api/views.py`, `api/urls.py`, `api/serializers.py` exist with seed. Core incident logging works; escalation/dashboard layer not built.

---

## 8. Academics / Gradebook

| Component | Tier | Wizard | Backend App | Core Endpoints | Demo Status | Gaps |
|-----------|------|--------|------------|----------------|-------------|------|
| Course Catalog | B/M/C | ✅ `course_catalog_wizard` | `academics/` | `/api/v1/course-catalog-wizard/sessions/` | 🟢 Working | None |
| Section Scheduler | M/C | ✅ `section_scheduler_wizard` | Wizard | `/api/v1/section-scheduler-wizard/sessions/` | 🟢 Working | Edge-case validation |
| Section Assign | M/C | ✅ `section_assign_wizard` | Wizard | `/api/v1/section-assign-wizard/sessions/` | 🟢 Working | None |
| Section Staffing | M/C | ✅ `section_staffing_wizard` | Wizard | `/api/v1/section-staffing-wizard/sessions/` | 🟢 Working | None |
| Gradebook Entry | M/C | N/A | `gradebook/` | `/api/v1/gradebook/` | 🟢 Working | `9 test files` · bulk entry UI polish |
| Gradebook Setup | M/C | ✅ `gradebook_setup_wizard` | Wizard | `/api/v1/gradebook-setup-wizard/sessions/` | 🟢 Working | None |
| Grade Scale Config | M/C | ✅ `grade_scale_wizard` | Wizard | `/api/v1/grade-scale-wizard/sessions/` | 🟢 Working | None |
| Grade Weights/Categories | M/C | ✅ `grade_weights_wizard` | Wizard | `/api/v1/grade-weights-wizard/sessions/` | 🟢 Working | None |
| Term Structure | M/C | ✅ `term_structure_wizard` | Wizard | `/api/v1/term-structure-wizard/sessions/` | 🟢 Working | None |
| Bell Schedule | M/C | ✅ `bell_schedule_wizard` | Wizard | `/api/v1/bell-schedule-wizard/sessions/` | 🟢 Working | None |
| Promotion Engine | M/C | ✅ `promotion_wizard` | Wizard | `/api/v1/promotion-wizard/sessions/` | 🟡 Functional | Rule enforcement light |
| Academic Year Rollover | M/C | ✅ `academic_year_wizard` | Wizard | `/api/v1/academic-year-wizard/sessions/` | 🟢 Working | None |
| Transcript / Graduation | C | ⚠️ No wizard | `graduation/` | `/api/v1/graduation/` | 🟡 Partial | `services.py` + `views_breakdown.py` exist; no PDF engine |
| Read-Only Gradebook | B/M/C | N/A | `academics_ro/` | `/api/v1/academics-ro/` | 🟢 Working | None |

**↳ Academics is the largest wizard-covered surface in the platform — 10 stable wizards.**

---

## 9. Board & Governance Module

| Component | Tier | Wizard | Backend App | Core Endpoints | Demo Status | Gaps |
|-----------|------|--------|------------|----------------|-------------|------|
| Board Metrics (Read) | C | N/A | `board_oversight/` | `/api/v1/board/` | 🟡 Partial | `views.py + services.py` exist, role-gated; aggregation sparse |
| RBAC Enforcement | C | N/A | `board_oversight/` | — | 🟢 Tested | `test_board_rbac.py` · `test_board_tenant_required.py` |
| URL Coverage | C | N/A | `board_oversight/` | — | 🟢 Tested | `test_board_urls.py` |
| Board Pack Generator | C | 🔴 No wizard | — | `/api/v1/board/reports/` | 🔴 No PDF engine | Requires PDF generation layer |
| Crown Compass / Discernment (canon alignment) | A | N/A | documentation / later-phase review | — | ⚪ Canon-gated | Leadership add-on canon is authoritative; predictive analytics remain conceptual and are not approved for production integration |

**↳ Canon update:** `board_oversight/` is still NOT 🔴 Missing — it has models, serializers, services, views, urls, and 4 test files. It remains 🟡 Partial (data aggregation thin, PDF missing). Crown Compass is now positioned as a leadership add-on, and Discernment-style predictive analytics remain conceptual / later-phase until separately approved.

---

## 10. Spiritual Life Module

| Component | Tier | Wizard | Backend App | Core Endpoints | Demo Status | Gaps |
|-----------|------|--------|------------|----------------|-------------|------|
| Devotional Content | B/M/C | N/A | `spiritual_life/` | `/api/v1/spiritual-life/devotionals/` | 🟡 Partial | Content scheduling missing |
| Service Hour Tracking | M/C | N/A | `servicehours/` | `/api/v1/service-hours/` | 🟢 Working | Approval workflow light |
| Spiritual Dashboard | C | N/A | — | — | 🔴 Not built | Needs aggregation layer |

**↳ App reality:** `spiritual_life/` has models, api/views.py, api/urls.py, and test file. `servicehours/` is a separate app. No dashboard aggregation.

---

## 11. Student Record Surface

| Component | Tier | Wizard | Backend App | Core Endpoints | Demo Status | Gaps |
|-----------|------|--------|------------|----------------|-------------|------|
| Student 360 | M/C | N/A | `student360/` | `/api/v1/student360/` | 🟢 Working | None |
| Parent 360 | B/M/C | N/A | `parent360/` | `/api/v1/parent360/` | 🟢 Working | None |
| Student Import | B/M/C | ✅ `student_import_wizard` | Wizard | `/api/v1/student-import-wizard/sessions/` | 🟢 Working | None |
| Guardian Household Wizard | B/M/C | ✅ `guardian_household_wizard` | Wizard | `/api/v1/guardian-household-wizard/sessions/` | 🟢 Working | None |
| HR / Staff Setup | M/C | ✅ `staff_setup_wizard` | `hr/` | `/api/v1/staff-setup-wizard/sessions/` | 🟢 Working | None |

---

## Wizard Registry — Complete Coverage

> Source of truth: `backend/crown_api/wizard_registry.py`

| # | Wizard | App | URL Prefix | Status |
|---|--------|-----|-----------|--------|
| 1 | Student Onboarding | `onboarding` | `/api/v1/onboarding/imports/` | ✅ Stable |
| 2 | Re-enrollment | `reenrollment` | `/api/v1/reenrollment/sessions/` | ✅ Stable |
| 3 | Billing Setup | `billing_wizard` | `/api/v1/billing-wizard/sessions/` | ✅ Stable |
| 4 | Financial Aid Setup | `financial_aid_wizard` | `/api/v1/aid-wizard/sessions/` | ✅ Stable |
| 5 | Scheduling Setup | `scheduling_wizard` | `/api/v1/scheduling-wizard/sessions/` | ✅ Stable |
| 6 | Communications Campaign | `comms_wizard` | `/api/v1/comms-wizard/sessions/` | ✅ Stable |
| 7 | Section Assignments | `section_assign_wizard` | `/api/v1/section-assign-wizard/sessions/` | ✅ Stable |
| 8 | Bell Schedule | `bell_schedule_wizard` | `/api/v1/bell-schedule-wizard/sessions/` | ✅ Stable |
| 9 | Gradebook Setup | `gradebook_setup_wizard` | `/api/v1/gradebook-setup-wizard/sessions/` | ✅ Stable |
| 10 | Attendance Rules | `attendance_rules_wizard` | `/api/v1/attendance-rules-wizard/sessions/` | ✅ Stable |
| 11 | Enrollment Conversion | `enrollment_conversion_wizard` | `/api/v1/enrollment-conversion-wizard/sessions/` | ✅ Stable |
| 12 | Invoice Run | `invoice_run_wizard` | `/api/v1/invoice-run-wizard/sessions/` | ✅ Stable |
| 13 | Staff Onboarding | `staff_onboarding_wizard` | `/api/v1/staff-onboarding-wizard/sessions/` | ✅ Stable |
| 14 | Fee Schedule Setup | `fee_schedule_wizard` | `/api/v1/fee-schedule-wizard/sessions/` | ✅ Stable |
| 15 | Academic Year Rollover | `academic_year_wizard` | `/api/v1/academic-year-wizard/sessions/` | ✅ Stable |
| 16 | Enrollment Period Setup | `enrollment_period_wizard` | `/api/v1/enrollment-period-wizard/sessions/` | ✅ Stable |
| 17 | Grade Scale Setup | `grade_scale_wizard` | `/api/v1/grade-scale-wizard/sessions/` | ✅ Stable |
| 18 | Term Structure Setup | `term_structure_wizard` | `/api/v1/term-structure-wizard/sessions/` | ✅ Stable |
| 20 | Section Scheduler Seed | `section_scheduler_wizard` | `/api/v1/section-scheduler-wizard/sessions/` | ✅ Stable |
| 21 | Staff & Roles Setup | `staff_setup_wizard` | `/api/v1/staff-setup-wizard/sessions/` | ✅ Stable |
| 22 | Course Catalog Setup | `course_catalog_wizard` | `/api/v1/course-catalog-wizard/sessions/` | ✅ Stable |
| 23 | Rooms Setup | `room_setup_wizard` | `/api/v1/room-setup-wizard/sessions/` | ✅ Stable |
| 24 | Promotion Map Setup | `promotion_wizard` | `/api/v1/promotion-wizard/sessions/` | 🟡 Functional / light |
| 25 | Student Import | `student_import_wizard` | `/api/v1/student-import-wizard/sessions/` | ✅ Stable |
| 26 | Guardian & Household | `guardian_household_wizard` | `/api/v1/guardian-household-wizard/sessions/` | ✅ Stable |
| 27 | Section Staffing | `section_staffing_wizard` | `/api/v1/section-staffing-wizard/sessions/` | ✅ Stable |
| 28 | Attendance Codes Setup | `attendance_codes_wizard` | `/api/v1/attendance-codes-wizard/sessions/` | ✅ Stable |
| 29 | Grade Weights & Categories | `grade_weights_wizard` | `/api/v1/grade-weights-wizard/sessions/` | ✅ Stable |
| — | Finance Setup (Policy Lock) | `finance_setup` *(direct app)* | `/api/v1/finance-setup/wizard/` | ✅ Stable — *merged 2026-02-28* |
| — | Aftercare Setup | `aftercare` *(direct app)* | `/api/aftercare/wizard/` | ✅ Stable |

**Missing wizards (explicitly deferred):**

| Wizard | Risk | Deferred Reason |
|--------|------|-----------------|
| Discipline Escalation Wizard | 🔴 High | Requires policy rule engine not yet designed |
| Transcript / Graduation Wizard | 🟡 Medium | `graduation/` partial; PDF engine missing |
| Board Setup / Pack Generator | 🟡 Medium | Data aggregation thin; PDF layer missing |
| Spiritual Dashboard Aggregator | 🟡 Low | Data exists; no rollup endpoint |

---

## Demo Readiness Summary

| Category | Status | Evidence |
|----------|--------|---------|
| Tenant Isolation | 🟢 Strong | Per-app tenant tests across all core modules |
| Auth (JWT / RBAC) | 🟢 Working | `identity.rbac` · board RBAC tests |
| Core Ops (Admissions / Aid / Ledger) | 🟢 Demo Ready | 12 ledger tests · 5 aid tests · seed commands |
| Finance Policy (Tuition/Plans/Lock) | 🟢 Demo Ready | `finance_setup` — 11 tests green · 5 schools seeded |
| Aftercare / Extended Care | 🟢 Demo Ready | Late fee tests · tenant scoping · seeded |
| Academics (Gradebook / Scheduling) | 🟢 Demo Ready | 10 wizards · 9 gradebook tests |
| Student Lifecycle (360 / Import) | 🟢 Demo Ready | student360, parent360, import wizard |
| Analytics Aggregation | 🟡 Partial | Metrics stubs exist; most need live DB rollup |
| Governance / Board | 🟡 Partial | `board_oversight` exists + tests; PDF missing |
| Crown Compass (Signals) | 🟡 Functional | engine.py + compute_signals command exist |
| Discipline (Incidents) | 🟡 Functional | API + seed working; escalation/dashboard 🔴 |
| Transcript / Graduation | 🟡 Partial | `graduation/services.py` + breakdown views; no PDF |
| Reporting / PDF Export | 🔴 Missing | No PDF generation layer anywhere |
| Spiritual Dashboard | 🔴 Missing | Data exists; no rollup endpoint |
| Discipline Dashboard | 🔴 Missing | No aggregation layer |

---

## Risk Register

| Risk | Severity | Evidence | Impact | Confidence |
|------|----------|---------|--------|-----------|
| PDF / export layer entirely absent | High | No PDF app in backend dir listing | Board pack, transcripts, reports blocked | High |
| Discipline escalation not implemented | High | No escalation model/views | Compliance gap for school policies | High |
| Metrics endpoints are stubs not real aggregations | Medium | Views return mock data | Dashboard demo requires seed data only | High |
| Award bucket admin UI missing | Medium | `aid/models.py` has buckets; no wizard step | Aid administrators can't self-serve bucket config | High |
| `promotion_wizard` rule enforcement light | Medium | Wizard exists; engine light | Grade promotion logic not fully enforced | Medium |
| Ledger reversal invariants still hardening | Low | `test_phase4b_ledger_integration.py` in progress | Edge-case financial data integrity | Medium |
| `graduation/` has no wizard | Low | `graduation/` is a direct app with services/views | Transcript UX requires manual API calls | High |

---

## Corrections vs Original Matrix

| Original Claim | Corrected State | Evidence |
|----------------|-----------------|---------|
| "TuitionPlanWizard 🔴 Missing" | ✅ `finance_setup` merged 2026-02-28 | 11 tests green, year-lock enforced, 5 schools seeded |
| "Board Dashboard 🔴 Not built" | 🟡 Partial — `board_oversight/` has models/services/views/4 test files | `test_board_rbac.py`, `test_board_urls.py` passing |
| "KPI Health (Crown Compass) 🟡 Conceptual" | 🟡 Functional — `signals/engine.py` + `compute_signals` command | Engine + seeder exist; trigger not automated |
| "Aftercare" not in matrix at all | ✅ Module exists and is stable | `test_aftercare_late_fee.py` · `test_aftercare_tenant_scoping.py` |
| "Void/Reversal 🟡 Partial" | 🟢 Tested | `test_gate2b_charge_void_reversal.py` · `test_ledger_void_endpoints_api.py` |
| "Financial Aid one app" | Two separate apps: `aid/` + `financial_aid/` | Different concerns: award engine vs ledger bridge |
