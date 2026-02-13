# Gradebook B1 — Edit Mode Scope (Controlled)

## Goal
Enable editing of existing grade cells for a teacher in a single section, with strict tenant scoping and audit logging.

## Non-Goals
- No create/delete assignments
- No roster changes
- No grade scale edits
- No bulk import
- No parent/student views
- No mobile optimization

## UX (Minimum)
- Toggle: Read-only ↔ Edit
- Edit cell: numeric input (0..points_possible)
- Save on blur or explicit Save button (choose one; default: blur + debounce)
- Clear grade: set null
- Visual state: saving/spinner, saved, error

## API (Minimum)

### Existing
- GET /api/v1/gradebook/sections/{section_id}/grades/

### New
- PATCH /api/v1/gradebook/sections/{section_id}/grades/
  - body: `{ "changes": [ { "student_id": "...", "assignment_id": "...", "points_earned": 9.5 } ] }`
  - server validates:
    - school_id from X-School-Id required
    - section belongs to school_id
    - assignment belongs to section + school_id
    - student is on roster for section + school_id
    - points_earned is null or 0 <= points_earned <= points_possible
  - response: updated grade cells (echo)
  - all changes written to audit log

## Permissions
- Teacher role only (or staff with gradebook:write permission)
- Read remains for admin/head

## Data Integrity
- No floating drift: store Decimal in DB
- Round display to 2 decimals, store raw Decimal

## Audit Logging
- Record: who, when, school_id, section_id, assignment_id, student_id, old_value, new_value, request_id/correlation_id

## Test Plan (Required)
- API contract tests for PATCH:
  - happy path single cell
  - batch changes
  - invalid points > possible
  - wrong school_id rejected
  - student not in roster rejected
- Frontend smoke: edit cell, save success, error path

## Done Definition
- Teacher can edit a grade cell and see it persist on refresh
- All tests green
- No migrations that break demo seed (if migration required, seed updated and demo still boots)
