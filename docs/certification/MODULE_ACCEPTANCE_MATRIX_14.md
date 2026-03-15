# Crown2026 14-Module Acceptance Matrix

Status date: 2026-03-15
Head sha for this snapshot: 34ca98d3

Status legend:
- Complete: all required acceptance fields have current-cycle evidence and signoff
- Incomplete: module exists but one or more required fields are missing
- Blocked: required blocker open in BLOCKER_LEDGER.md
- Unproven: evidence exists but is stale or not tied to current-cycle certification

## Required acceptance fields per module

- Owner
- Required APIs
- Required pages/routes
- Required roles
- Required reports
- Required proof tests
- Required demo data
- Open defects
- Signoff evidence

## Matrix

| # | Module | Owner | Required APIs | Required pages/routes | Required roles | Required reports | Required proof tests | Required demo data | Open defects | Signoff status |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Academics - Roster and Sections | TBD | Defined | Defined | Defined | Partial | Present | Present | None recorded in this cycle | Unproven |
| 2 | Gradebook | TBD | Defined | Defined | Defined | Partial | Present | Present | B1-001, B1-002 | Blocked |
| 3 | Attendance | TBD | Defined | Defined | Defined | Partial | Present | Present | None recorded in this cycle | Unproven |
| 4 | Admissions | TBD | Defined | Defined | Defined | Partial | Partial | Present | None recorded in this cycle | Incomplete |
| 5 | Financial Aid | TBD | Defined | Defined | Defined | Present | Present | Present | None recorded in this cycle | Unproven |
| 6 | Billing and Finance | TBD | Defined | Defined | Defined | Present | Present | Present | None recorded in this cycle | Unproven |
| 7 | Curriculum and Pacing | TBD | Defined | Defined | Defined | Partial | Partial | Present | None recorded in this cycle | Incomplete |
| 8 | Student 360 | TBD | Defined | Defined | Defined | Partial | Partial | Present | None recorded in this cycle | Incomplete |
| 9 | Households and Guardians | TBD | Defined | Partial | Defined | Partial | Partial | Present | None recorded in this cycle | Incomplete |
| 10 | Discipline | TBD | Defined | Defined | Defined | Partial | Partial | Present | None recorded in this cycle | Incomplete |
| 11 | Service Hours | TBD | Defined | Defined | Defined | Partial | Partial | Present | None recorded in this cycle | Incomplete |
| 12 | Communications | TBD | Defined | Defined | Defined | Partial | Partial | Present | None recorded in this cycle | Incomplete |
| 13 | Classroom Management | TBD | Defined | Partial | Defined | Partial | Partial | Present | None recorded in this cycle | Incomplete |
| 14 | Director Actions API | TBD | Defined | Integration surface only | Defined | Present | Present | Present | None recorded in this cycle | Unproven |

## Notes

- This matrix intentionally avoids optimistic completion claims from prior baselines.
- Modules marked Unproven require fresh signoff evidence tied to a certified release SHA.
- Modules marked Incomplete require missing acceptance fields to be explicitly closed.
- Bucket 1 branch blockers can block a module even if module acceptance appears otherwise strong.
