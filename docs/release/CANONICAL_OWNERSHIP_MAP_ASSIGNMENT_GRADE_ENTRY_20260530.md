# Canonical Ownership Map - Assignment/Grade Entry (2026-05-30)

Purpose: define canonical write boundaries between assignment definition and grade evidence.

## Canonical Owners

| Domain Entity | Canonical Owner | Write Authority | Read Compatibility | Notes |
| --- | --- | --- | --- | --- |
| Assignment Definition | academics.Assignment | academics app only | gradebook reads via FK | Canonical assignment metadata and points_possible baseline. |
| Assignment Categorization | academics.AssignmentCategory | academics app only | gradebook reads | Canonical weighting/category structure. |
| Grade Evidence Entry | gradebook.GradeEntry | gradebook app only | academics analytics reads | Canonical student earned-points event per assignment context. |

## Controlled Overlaps

- gradebook.assignment_name (legacy string shadow of assignment identity; transitional)
- gradebook.points_possible (legacy snapshot; assignment canonical points live in academics.Assignment)

## Guardrail

- Assignment identity and configuration writes are owned by academics.
- Grade evidence writes are owned by gradebook.
- Legacy `assignment_name` and duplicated points fields remain compatibility-only until backfill removal window.
