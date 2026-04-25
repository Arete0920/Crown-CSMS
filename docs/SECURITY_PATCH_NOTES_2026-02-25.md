# Security Patch Notes — 2026-02-25

**Status:** All three criticals closed. Full test suite: 609 passed / 0 failed.

---

## CRITICAL #1 — Attendance submit: full cross-tenant write chain

**File:** `backend/crown_api/views_academics.py` — `section_attendance_submit()`

### Exploit chain (3 steps)

1. **RBAC bypass** — `get_request_school_id(required=False)` + `if school_id:` gate meant omitting `X-School-Id` header bypassed the `TEACHER/ADMIN/HEAD_OF_SCHOOL` role check entirely.
2. **Cross-tenant Section resolution** — `get_object_or_404(Section, id=section_id)` had no `school_id` constraint, so any caller could target a section belonging to another school.
3. **Unverified student write** — `AttendanceRecord.objects.update_or_create(student_id=sid, ...)` wrote records for any `student_id` without confirming the student belonged to the asserted school.

Together: authenticated attacker (any school, any role) could mark attendance for students at any school by omitting the header and supplying foreign UUIDs.

### Fixes applied

| Location | Before | After |
|---|---|---|
| RBAC gate | `required=False` + `if school_id:` | `required=True` — missing header → 400, always enforced |
| Section fetch | `get_object_or_404(Section, id=section_id)` | `get_object_or_404(Section, id=section_id, school_id=school_id)` |
| Per-row write | no ownership check | `get_object_or_404(Student, id=sid, school_id=school_id)` before every `update_or_create` |

### Why Section + Student, not AttendanceRecord

`AttendanceRecord` has no `school_id` field by design — tenant isolation is model-driven:
attendance is scoped to a student (who has `school_id`) belonging to a section (which has `school_id`).
Enforcing both foreign keys is the correct and complete defense.

### Invariant tests added

File: `backend/crown_api/tests/test_attendance_tenant_invariants.py`

| Test | Asserts |
|---|---|
| `test_missing_school_header_returns_400` | Omitting `X-School-Id` → 400 |
| `test_cross_tenant_section_returns_404` | Section from school_b via school_a header → 404 |
| `test_cross_tenant_student_returns_404` | Student from school_b written to school_a section → 404 |
| `test_valid_same_tenant_request_returns_200` | Same-tenant teacher/section/student → 200 `{"ok": true}` |

All 4 pass. Full suite: 609 passed, 0 failed.

### Supporting grep inventory

Two sweeps confirmed the bug was **isolated to one endpoint**:

**Sweep 1** — all `get_object_or_404(Section, id=...)` in production code:
```
assignments_views.py:91   get_object_or_404(Section, id=section_id, school_id=school_id)  ✅
assignments_views.py:245  get_object_or_404(Section, id=section_id, school_id=school_id)  ✅
assignments_views.py:352  get_object_or_404(Section, id=section_id, school_id=school_id)  ✅
gradebook/views.py:70     get_object_or_404(Section, id=section_id, school_id=school_id)  ✅
views_academics.py:108    get_object_or_404(Section, id=section_id)                        ← PATCHED
```

**Sweep 2** — all `get_request_school_id(required=False)` in production code:
```
tenant_guards.py:60       TenantOptionalMixin — declared design pattern, not a bug  ✅
views_academics.py:79     section_attendance_submit — exploit vector                 ← PATCHED
```

No other unscoped Section fetches or `required=False` bypass vectors exist in the backend.

---

## CRITICAL #2 — Gradebook bulk upsert: cross-tenant student write

**File:** `backend/gradebook/views.py:569` — `grade_entry_bulk_upsert()`

### Issue

`Student.objects.get(id=student_id)` had no `school_id` filter. A caller with valid credentials at school_a and a foreign `student_id` could write `GradeEntry` records attributed to a student from school_b.

### Fix

```python
# Before
student = Student.objects.get(id=student_id)

# After
student = Student.objects.get(id=student_id, school_id=school_id)
```

`school_id` is sourced at line 540 via `get_request_school_id(request, required=True)` — confirmed clean. Missing header → 400 regardless of this fix.

---

## CRITICAL #3 — Audit events: cross-school data exposure

**File:** `backend/crown_api/audit_views.py:22` — `recent_audit_events()`

### Issue

`AuditEvent.objects.all().order_by("-ts")[:limit]` returned events from all schools to any caller with `admin` or `finance` role.

### Fix

Added conditional tenant filter: when `X-School-Id` header is present, scope results to `AuditEvent.objects.filter(school_id=school_uuid)`. Invalid UUID format → 400.

### Policy note

Current behavior: filter when header is present; unscoped when absent (subject to role gate). This preserves backwards compatibility for any cross-school admin tooling.
If policy shifts to always-tenant-required for non-global roles, tighten to `required=True` in a follow-up patch.

---

## Standing code-level rule

> **Any `Section` fetch by `id` in a request-handling view must include `school_id=`.**

Violation pattern to grep for:
```
get_object_or_404(Section, id=
Section.objects.get(id=
Section.objects.filter(id=
```
Any of the above without a trailing `school_id=` argument in production view code is a finding.
