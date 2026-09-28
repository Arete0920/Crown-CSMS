# Module Completion Matrix — CROWN

> Canonical notice (2026-03-15): For current-cycle completion governance, use docs/certification/MODULE_ACCEPTANCE_MATRIX_14.md and docs/certification/COMPLETION_CONTRACT.md.
> This file is historical baseline evidence and is not the primary definition of done.

**Generated:** 2026-02-24
**HEAD SHA:** d671749e94a605bb116da76b9f687dc33f143841
**Certification baseline:** `prod-deploy-certify-2026-02-24`

This matrix documents the production-readiness state of all 14 CROWN SIS
modules, capturing API endpoints, automated test coverage, and frontend UI
presence as of the certification date above.

---

## Status Key

| Symbol | Meaning |
|--------|---------|
| ✅ | Complete — proven in CI, fully integrated |
| 🔶 | Partial — exists and functional, limited breadth |
| ❌ | Not yet built or deferred |

---

## 14-Module Completion Matrix

| # | Module | Django App(s) | API | Tests | UI | Notes |
|---|--------|--------------|-----|-------|----|-------|
| 1 | **Academics — Roster & Sections** | `academics`, `academics_ro` | ✅ | ✅ | ✅ | 11 test files; AcademicsDashboard, roster endpoints, role-gated reads |
| 2 | **Gradebook** | `gradebook` | ✅ | ✅ | ✅ | 9 test files; GradebookRO.jsx, grade entry endpoints, category weights |
| 3 | **Attendance** | `academics` (AttendanceRecord) | ✅ | ✅ | ✅ | TeacherAttendancePage.jsx + ParentAttendancePage.jsx; lane-3 smoke tests |
| 4 | **Admissions** | `admissions`, `applications` | ✅ | 🔶 | 🔶 | 3 test files; AdmissionsPipelineList.jsx; full drilldown pending broader tests |
| 5 | **Financial Aid** | `financial_aid`, `aid` | ✅ | ✅ | ✅ | 2 test files + Director Actions API tests; FinancialAidDashboard.jsx; POST_ACCEPTED_AWARDS proven |
| 6 | **Billing & Finance** | `billing`, `finance`, `ledger` | ✅ | ✅ | ✅ | 6 billing + 10 ledger test files; BillingDashboard.jsx + FinanceDashboard.jsx + FinanceInvoicesList.jsx; ledger immutability proven |
| 7 | **Curriculum & Pacing** | `curriculum`, `curricula` | ✅ | 🔶 | 🔶 | 1 test file; CurriculumPacingCard.jsx; 4 courses + 16 units + 80 lessons seeded |
| 8 | **Student 360** | `student360` | ✅ | 🔶 | ✅ | 1 test file; Student360Page.jsx + ParentStudent360Page.jsx; aggregates across 5 modules |
| 9 | **Households & Guardians** | `households` | ✅ | 🔶 | 🔶 | 3 test files; 1,200 students + 180 families seeded; guardian read via Student360 |
| 10 | **Discipline** | `discipline` | ✅ | 🔶 | ✅ | DisciplinePage.jsx; 16 seeded incidents across 7 categories; seed_discipline_demo proven |
| 11 | **Service Hours** | `servicehours` | ✅ | 🔶 | ✅ | ServiceHoursPage.jsx; 60 seeded entries; approval workflow present |
| 12 | **Communications** | `comms` (integration wrap) | ✅ | 🔶 | ✅ | CommsInboxPage.jsx + CommsThreadPage.jsx + CommsComposePage.jsx; CommunicationsDirectorDashboard.jsx; 12 seeded threads |
| 13 | **Classroom Management** | `classroom` | ✅ | 🔶 | 🔶 | 1 test file; ClassroomsDashboard.jsx + ClassroomDetailDrawer.jsx; seating chart model present |
| 14 | **Director Actions API** | `crown_api` (director_views.py) | ✅ | ✅ | 🔶 | 24 test files in crown_api; POST /api/director/actions/ proven; POST_ACCEPTED_AWARDS end-to-end tested; no standalone UI page (consumed by Financial Aid flow) |

---

## Summary Counts

| Status | API | Tests | UI |
|--------|-----|-------|----|
| ✅ Complete | 14/14 | 6/14 | 8/14 |
| 🔶 Partial | 0/14 | 8/14 | 5/14 |
| ❌ Not built | 0/14 | 0/14 | 1/14 |

> **All 14 module APIs are production-present.**
> Test coverage is complete (≥2 test files) for 6 modules; partial but non-zero for all 14.
> UI presence: 8 modules have dedicated pages/dashboards; 5 have partial or read-only UI.

---

## Data Certification (Section 3)

Post-seed counts verified 2026-02-24 against `crown_api.models_academics_core.AttendanceRecord`
and related models:

| Model | Count | Minimum | Status |
|-------|-------|---------|--------|
| `core.models.Student` | 1,200 | ≥300 | ✅ |
| `core.models.Family` | 180 | ≥180 | ✅ |
| `crown_api.models_academics_core.AttendanceRecord` | 6,451 | ≥1,500 | ✅ |
| `crown_api.models.Section` | 4 | ≥4 | ✅ |
| `billing.models.Invoice` | 161 | ≥40 | ✅ |
| `curriculum.models.CurriculumCourse` | 4 | ≥4 | ✅ |

---

## CI Gate Coverage

| Gate | Workflow | Status |
|------|----------|--------|
| Full pytest suite | On push to main + PRs | ✅ 553 passed, 6 skipped |
| Proof test set (38 critical tests) | `ui-proof-gate.yml` subset | ✅ 38/38 |
| Playwright UI smoke (8 tests) | `ui-proof-gate.yml` | ✅ 8/8 |
| gitleaks secret scan | `security.yml` | ✅ 0 findings, 1,258 commits |
| Deploy guard (SHA verification) | `deploy-prod.yml` | ✅ BUILD_SHA verified post-deploy |

---

## Deferred Modules (Out of Scope — MVP Boundaries)

Per `ACTUAL_STATUS_TODAY.md` and `BASELINE_REALITY.md`:

- Food Services
- Athletics
- Daily Devotions / Spiritual Life (stub only)
- Advanced curriculum mapping
- Portrait of the Graduate builder (full)
- Marketplace
- Surveys / Sentiment engine
- Mobile app / PWA
- Advanced analytics dashboards
- Library, Transportation, Health (stub dashboards exist, no backend)

These are intentionally deferred, not abandoned. Stubs exist in the frontend
(`FoodDashboard.jsx`, `AthleticsDashboard.jsx`, etc.) to maintain scaffold
coherence.

---

*This document is part of the CROWN certification package for
`prod-certified-2026-02-24`.*
