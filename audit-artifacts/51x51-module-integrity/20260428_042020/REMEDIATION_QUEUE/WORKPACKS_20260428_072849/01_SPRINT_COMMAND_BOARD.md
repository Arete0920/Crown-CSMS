# CROWN 51x51 Sprint Command Board

Generated: 2026-04-28T07:28:50.5925299-04:00

## Release Decision

**NO-GO / FIX REQUIRED**

## Open Work

- P1 FAIL rows: 215
- P2 REVIEW rows: 333
- Affected modules: 31

## Priority Module Order

| Rank | ModuleId | Layer | Module | Owner | FAIL | REVIEW |
|---:|---:|---|---|---|---:|---:|
| 1 | 4 | Platform Core | Audit Logging | Dev 1 | 8 | 31 |
| 2 | 43 | First-Wave Add-on | Christian PD Hub | Product + Dev 5 | 8 | 31 |
| 3 | 47 | Later Add-on | CRM / Marketing Suite | Product + Dev 3 | 8 | 31 |
| 4 | 49 | Later Add-on | Survey / Sentiment Engine | Product + Dev 5 | 8 | 31 |
| 5 | 11 | SIS Core | School Profile | Dev 2 | 7 | 21 |
| 6 | 13 | SIS Core | Student Master Record | Dev 2 | 7 | 21 |
| 7 | 23 | SIS Core | Emergency / Medical Essentials | Dev 2 | 7 | 21 |
| 8 | 5 | Platform Core | Notifications Framework | Dev 1 | 7 | 5 |
| 9 | 6 | Platform Core | Document / File Framework | Dev 1 | 7 | 5 |
| 10 | 8 | Platform Core | Shared Frontend Shell | Dev 4 | 7 | 5 |
| 11 | 9 | Platform Core | Shared Design System | Dev 4 | 7 | 5 |
| 12 | 10 | Platform Core | Reporting / Data Access Standards | Dev 5 | 7 | 5 |
| 13 | 12 | SIS Core | School Year / Term | Dev 2 | 7 | 5 |
| 14 | 15 | SIS Core | Staff / Faculty | Dev 2 | 7 | 5 |
| 15 | 17 | SIS Core | Grade Levels | Dev 2 | 7 | 5 |
| 16 | 20 | SIS Core | Grades / Report Cards | Dev 2 | 7 | 5 |
| 17 | 22 | SIS Core | Student Care / Discipline Summary | Dev 2 | 7 | 5 |
| 18 | 27 | First-Wave Module | Communications | Dev 3 | 7 | 5 |
| 19 | 28 | First-Wave Module | Parent Portal | Dev 4 | 7 | 5 |
| 20 | 33 | Second-Wave Module | Nurse Office / Health Office | Dev 3 | 7 | 5 |
| 21 | 34 | Second-Wave Module | Transportation | Dev 3 | 7 | 5 |
| 22 | 36 | Second-Wave Module | Volunteer / Family Engagement | Dev 3 | 7 | 5 |
| 23 | 38 | Second-Wave Module | Extended Discipline Workflows | Dev 3 | 7 | 5 |
| 24 | 40 | First-Wave Add-on | Service & Outreach | Product + Dev 3 | 7 | 5 |
| 25 | 41 | First-Wave Add-on | Crown Compass | Product + Dev 5 | 7 | 5 |
| 26 | 44 | Later Add-on | Chaplain / Pastoral Care | Product + Dev 3 | 7 | 5 |
| 27 | 45 | Later Add-on | Portrait of the Graduate | Product + Dev 3 | 7 | 5 |
| 28 | 46 | Later Add-on | Mission Metrics | Product + Dev 5 | 7 | 5 |
| 29 | 48 | Later Add-on | Mobile App / Family App | Product + Dev 4 | 7 | 5 |
| 30 | 51 | Later Add-on | Standalone Schedule Builder | Product + Dev 5 | 7 | 5 |
| 31 | 42 | First-Wave Add-on | Board Governance Suite | Product + Dev 5 | 1 | 31 |

## Category Attack Plan

1. Close Test-Coverage rows first.
2. Close Tenant-Isolation and Permission-Security rows before any sandbox expansion.
3. Close CI-Gate-Wiring rows so the fixes stay enforced.
4. Close Frontend-Operations rows for user-visible dashboard/module completion.
5. Close Backend-API and Data-Model rows for system integrity.

## Workpack Locations

- Owner workpacks: owners/
- Category workpacks: categories/
- Module workpacks: modules/
- Full open row CSV: 00_ALL_OPEN_REMEDIATION_ROWS.csv
