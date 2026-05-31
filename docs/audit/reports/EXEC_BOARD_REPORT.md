# Crown Executive Board Report

> Authority Scope Notice (2026-05-29)
>
> This file is a historical executive reporting snapshot and not a controlling repository-level release authority source.
>
> Current controlling sources:
> - docs/CURRENT_RELEASE_STATUS.md
> - docs/release/CURRENT_RELEASE_SCORECARD_20260528.md

## Overall Status
- Overall board status: **RED**
- Total inventoried assets: **106327**
- UI assets reviewed by inventory: **18924**
- API / route assets inventoried: **224**
- Model / service assets inventoried: **174**
- Test / CI / doc assets inventoried: **12081**
- Proof checks passed: **11**
- Proof checks failed: **0**
- Modules GREEN: **0**
- Modules YELLOW: **0**
- Modules RED: **23**

## Strategic Frame
- Crown is governed as **Core, Modules, and Add-ons**.
- Core owns truth. Modules run school operations. Add-ons integrate through approved contracts.
- No module should be treated as complete unless it is end-to-end proven.

## Top 25 Blockers

| Rank | Severity | Category | Title | Owner | Source | Count |
|---:|---|---|---|---|---|---:|
| 1 | CRITICAL | API / Routing | Route contract risk and duplicate-path risk | Dev 1 | ROUTE_RISK_SCAN.csv | 15472 |
| 2 | CRITICAL | Module Completion | Module not complete: Activities / Events | Dev 3 | MODULE_COMPLETION_MATRIX.csv | 1 |
| 3 | CRITICAL | Module Completion | Module not complete: Administrator Portal | Dev 4 | MODULE_COMPLETION_MATRIX.csv | 1 |
| 4 | CRITICAL | Module Completion | Module not complete: Admissions | Dev 3 | MODULE_COMPLETION_MATRIX.csv | 1 |
| 5 | CRITICAL | Module Completion | Module not complete: Advanced Board Reporting | Dev 3 | MODULE_COMPLETION_MATRIX.csv | 1 |
| 6 | CRITICAL | Module Completion | Module not complete: Attendance | Dev 2 | MODULE_COMPLETION_MATRIX.csv | 1 |
| 7 | CRITICAL | Module Completion | Module not complete: Billing / Payments | Dev 3 | MODULE_COMPLETION_MATRIX.csv | 1 |
| 8 | CRITICAL | Module Completion | Module not complete: Board Governance | Product | MODULE_COMPLETION_MATRIX.csv | 1 |
| 9 | CRITICAL | Module Completion | Module not complete: Communications | Dev 3 | MODULE_COMPLETION_MATRIX.csv | 1 |
| 10 | CRITICAL | Module Completion | Module not complete: Core Platform | Dev 1 / Dev 5 | MODULE_COMPLETION_MATRIX.csv | 1 |
| 11 | CRITICAL | Module Completion | Module not complete: Crown Compass | Product | MODULE_COMPLETION_MATRIX.csv | 1 |
| 12 | CRITICAL | Module Completion | Module not complete: Extended Discipline | Dev 3 | MODULE_COMPLETION_MATRIX.csv | 1 |
| 13 | CRITICAL | Module Completion | Module not complete: Food Services | Product | MODULE_COMPLETION_MATRIX.csv | 1 |
| 14 | CRITICAL | Module Completion | Module not complete: Nurse Office | Dev 3 | MODULE_COMPLETION_MATRIX.csv | 1 |
| 15 | CRITICAL | Module Completion | Module not complete: Parent Portal | Dev 4 | MODULE_COMPLETION_MATRIX.csv | 1 |
| 16 | CRITICAL | Module Completion | Module not complete: PD Hub | Product | MODULE_COMPLETION_MATRIX.csv | 1 |
| 17 | CRITICAL | Module Completion | Module not complete: Re-enrollment | Dev 3 | MODULE_COMPLETION_MATRIX.csv | 1 |
| 18 | CRITICAL | Module Completion | Module not complete: Scheduling / Gradebook | Dev 2 | MODULE_COMPLETION_MATRIX.csv | 1 |
| 19 | CRITICAL | Module Completion | Module not complete: Service & Outreach | Product | MODULE_COMPLETION_MATRIX.csv | 1 |
| 20 | CRITICAL | Module Completion | Module not complete: SIS Core | Dev 2 | MODULE_COMPLETION_MATRIX.csv | 1 |
| 21 | CRITICAL | Module Completion | Module not complete: Spiritual Life | Product | MODULE_COMPLETION_MATRIX.csv | 1 |
| 22 | CRITICAL | Module Completion | Module not complete: Teacher Portal | Dev 4 | MODULE_COMPLETION_MATRIX.csv | 1 |
| 23 | CRITICAL | Module Completion | Module not complete: Transportation | Dev 3 | MODULE_COMPLETION_MATRIX.csv | 1 |
| 24 | CRITICAL | Module Completion | Module not complete: Volunteer / Family Engagement | Dev 3 | MODULE_COMPLETION_MATRIX.csv | 1 |
| 25 | HIGH | API Inventory | API and route surface requires contract-level verification | Dev 1 / Dev 5 | API_ROUTE_CONTRACT_INVENTORY.csv | 224 |

## Immediate Actions
1. Fix all proof failures first.
2. Fill the module completion matrix completely.
3. Fill the dashboard / wizard status matrix completely.
4. Complete keep / rewrite / drop decisions.
5. Do not claim completion for any RED or YELLOW module.

## Owner Lanes
- Dev 1: platform, auth, RBAC, tenant, API contracts
- Dev 2: SIS/data truth
- Dev 3: admissions, reenrollment, billing, operational workflows
- Dev 4: shell, dashboards, wizards, pages, UI consistency
- Dev 5: integration, testing, regression, release readiness
- TC: final scope, canon approval, release truth, sign-off

## Generated Files
- reports/BOARD_TOP_25_BLOCKERS.csv
- reports/EXEC_BOARD_REPORT.md
- reports/MODULE_COMPLETION_MATRIX.csv
- reports/KEEP_REWRITE_DROP_MATRIX.csv
- reports/DASHBOARD_WIZARD_STATUS.csv
- evidence/PROOF_SUMMARY.csv
