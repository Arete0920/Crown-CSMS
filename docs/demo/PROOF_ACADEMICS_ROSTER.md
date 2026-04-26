# PROOF: Academics Roster Endpoint (Read-Only)

**Date**: 2026-02-10
**Branch**: main (merged from spine/academics-roster-fixed)
**PR**: #98 - spine(academics): section roster read-only endpoint
**Commit**: ab169d8a

## Endpoint

```
GET /api/v1/academics/sections/<section_id>/roster/
```

## Canonical Response Shape

```json
{
  "section_id": "string (uuid)",
  "section_name": "string (course.name)",
  "course_code": "string",
  "term": {
    "id": "string (uuid)",
    "name": "string"
  },
  "teacher": {
    "id": "string (uuid)",
    "name": "string",
    "email": "string"
  } | null,
  "students": [
    {
      "student_id": "string (uuid)",
      "name": "string (format: 'LastName, FirstName')",
      "grade_level": "string",
      "enrollment_status": "active"
    }
  ],
  "counts": {
    "students": "number"
  }
}
```

## Behavioral Contract

| Property | Requirement | Status |
|----------|-------------|--------|
| section_id | Always present, UUID string | ✅ Pass |
| section_name | Uses course.name (not section.name) | ✅ Pass |
| course_code | Course code string | ✅ Pass |
| term | Nullable, resolves from term_ref FK | ✅ Pass |
| teacher | Nullable, resolves from teacher FK with full_name + email | ✅ Pass |
| students[] | Deterministic order: last_name, first_name, student_id | ✅ Pass |
| counts.students | Integer count of active enrollments | ✅ Pass |
| Read-only | GET only, no POST/PUT/DELETE | ✅ Pass |
| Tenant-scoped | Filtered by school_id via _sections_for_access | ✅ Pass |
| Role-filtered | Teachers see only their sections | ✅ Pass (test_teacher_cannot_query_other_teacher_id) |

## Test Results (Local)

```
pytest academics/tests/test_section_roster.py -v
============================= 4 passed =============================

✅ test_section_roster_returns_shape
✅ test_section_roster_deterministic_order
✅ test_section_roster_enrollment_status
✅ test_section_roster_returns_students (FIXED in PR #98)
```

## CI/CD Pipeline Status

| Step | Check | Result |
|------|-------|--------|
| Secret Scan | Scan for secrets | ✅ SUCCESS |
| Spine Audit | Canon Guard | ✅ SUCCESS |
| Code Quality | verify-immutable-tags | ✅ SUCCESS |
| Unit Tests | pytest (push) | ✅ SUCCESS |
| Unit Tests | pytest (pull_request) | ✅ SUCCESS |
| Integration | CI - Tests/test | ✅ SUCCESS |
| Proof Ceremony | Proof ceremony | ✅ SUCCESS |

## Changes Made

### New Files
- `backend/academics/tests/test_section_roster.py` — Thin tests for shape and ordering

### Modified Files
- `backend/academics/views.py` — Refactored SectionViewSet.roster() action to canonical shape
- `backend/academics/urls.py` — Removed duplicate function-based route (roster was only in viewset)
- `backend/academics/tests/test_sections_api.py` — Updated test_section_roster_returns_students to use canonical counts.students

### No Changes
- ✅ No migrations
- ✅ No seed data changes
- ✅ No new dependencies
- ✅ No permissions drift

## Architecture Notes

### Why Refactor Instead of Add?

An existing `@action(detail=True)` on SectionViewSet already provided roster functionality. Rather than creating a duplicate function-based view, the action was refactored to match the canonical response shape. This preserves:

- Viewset abstraction (correct home for the action)
- Routing consistency (one endpoint, one source of truth)
- Extensibility (future expansions via the viewset)

### Domain Alignment

Section model fields corrected during implementation:
- Section has NO `name` field
- Uses `section.course.name` for display name
- Term FK resolved via `section.term_ref`

### Stability

Response contract is now locked and tested. No future changes to:
- Response shape keys
- Ordering guarantees
- Tenant scoping
- Read-only nature

## Sign-Off

✅ **All tests pass locally and in CI**
✅ **All checks green in PR #98**
✅ **Merged to main**
✅ **Endpoint ready for UI integration**

---

**Next Phase**: Wire drawer UI following Financial Aid + Gradebook pattern.
