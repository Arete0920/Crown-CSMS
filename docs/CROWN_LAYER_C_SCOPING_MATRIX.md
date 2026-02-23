# CROWN LAYER C SCOPING MATRIX

**Version:** 1.0
**Status:** Frozen Data Visibility Doctrine
**Authority:** Data Security & Privacy Standard

---

## 1. Purpose

Layer C governs:
- **Row-level visibility** — which records a user may access
- **Field-level visibility** — which fields within a record a user may view

Layer C applies **after**:
1. Authentication
2. Permission check
3. Tenant validation

**No endpoint may bypass Layer C logic.**

---

## 2. Role-Based Row Scoping Matrix

### 2.1 Students Domain

| Role | Row Scope |
|------|-----------|
| Director | All students in school |
| Registrar | All students |
| Teacher | Only students in assigned sections |
| Counselor | Only assigned students |
| Parent | Only their own children |
| Student | Only their own record |
| Finance | All students (financial context only) |
| Board | Aggregated data only (no individual student detail unless explicitly granted) |

### 2.2 Financial Records

| Role | Row Scope |
|------|-----------|
| Director | All |
| Finance | All |
| Registrar | View only if tuition-related |
| Parent | Only their household |
| Student | None |
| Teacher | None |
| Counselor | None |
| Board | Aggregated only |

### 2.3 Financial Aid

| Role | Row Scope |
|------|-----------|
| Director | All |
| Finance | All |
| Aid Officer | All |
| Parent | Only their household |
| Student | None |
| Teacher | None |
| Counselor | None |

### 2.4 Discipline & Counseling Notes

| Role | Row Scope |
|------|-----------|
| Director | All |
| Counselor | Assigned students |
| Teacher | Discipline entries for their students only |
| Parent | Limited view (non-confidential entries only) |
| Student | Limited view if allowed |
| Finance | None |
| Board | None |

### 2.5 Operation Andrew (Referrals)

| Role | Row Scope |
|------|-----------|
| Director | All |
| Admissions | All |
| Finance | Reward records only |
| Parent | Their own referrals only |
| Student | None |
| Teacher | None |

### 2.6 Barnabas (Mentoring & Devotions)

| Role | Row Scope |
|------|-----------|
| Director | All formation records |
| Spiritual Life Director | All |
| Counselor | Assigned students |
| Parent | Own child formation record |
| Student | Own formation record |
| Teacher | Reflection data only if part of classroom integration |
| Finance | None |
| Board | Aggregated only |

---

## 3. Field-Level Scoping Doctrine

Field restrictions must prevent sensitive leakage even when row access is granted.

### 3.1 Student Record Fields

**Restricted Fields:**
- Social security numbers
- Internal disciplinary notes
- Counseling notes
- Financial aid award details (non-finance roles)
- Staff-only comments

### 3.2 Financial Fields

**Restricted Fields:**
- Internal audit flags
- Collection notes
- Payment processor metadata
- Bank account details

### 3.3 Counseling & Formation

**Restricted Fields:**
- Confidential counseling notes
- Mentor private comments
- Risk assessments

**Parents may see:**
- General formation progress
- Approved milestone markers

---

## 4. Aggregation Rules

Board and analytics users must:
- Receive aggregated data only
- Never receive individual-level sensitive records unless explicitly authorized

Compass must:
- Operate on summarized data sets
- Not expose raw personal data

---

## 5. Implementation Doctrine

Layer C must be implemented:
- In a centralized scoping module
- Applied before serialization
- Covered by automated tests
- Enforced at queryset level
- Not duplicated across views

---

## 6. Test Requirements

Each domain must have:
- Role-based access tests
- Cross-tenant denial tests
- Field omission tests
- Attempted privilege escalation tests

**No domain may go live without coverage.**

---

## 7. Prohibited Practices

- Filtering rows in frontend
- Sending full object and hiding fields client-side
- Hardcoding role strings inside views
- Inline queryset hacks
- Skipping scoping for demo

---

## 8. Layer C: Current Implementation Status

_Last updated: 2026-02-22. Update this table with every scoping PR._

### 8.1 Canonical Student Model

`households.Student` is the **authoritative SIS identity model** for all row
scoping in the Students domain. `core.models.Student` is the legacy model and
must not be used for active scoping logic. `academics.Enrollment` links
`households.Student` to sections.

| Model | Status |
|-------|--------|
| `households.Student` | **Canonical — use this** |
| `core.models.Student` | Legacy — do not scope against |
| `crown_api.models_student_core.StudentProfile` | Feature supplement only |

### 8.2 Row Scoping Implementation Status

| Domain | Role | Pathway | Status |
|--------|------|---------|--------|
| Students | Director / Head / Registrar | All rows | ✅ Implemented |
| Students | Teacher | `enrollments__section__teacher=user` (via `academics.Section` + `academics.Enrollment`) | ✅ Implemented |
| Students | Parent | `household__guardians__email__iexact=user.email` (via `households.Guardian`) | ✅ Implemented |
| Students | Student (self) | `Student.user` FK not yet created | 🚫 Blocked — Phase 3 |
| Students | Counselor | Assignment model not yet defined | ⏳ Stub (deny) |
| Students | Board | Aggregate-only; raw endpoint not defined | ⏳ Stub (deny) |
| Financial Aid | Director / Finance / Aid Officer | All rows | ✅ Implemented |
| Financial Aid | Parent | `household_id__in` resolved from `households.Guardian.email` | ✅ Implemented |
| Financial Aid | Student | No student FK on application | ⏳ Stub (deny) |
| Financial (LedgerEntry) | Director / Finance | All rows | ✅ Implemented |
| Financial (LedgerEntry) | Parent | `family=user.guardian.family` (via `core.UserAccount.guardian → core.Guardian.family`) | ✅ Implemented |
| Discipline | All non-director roles | `Discipline` model not yet defined | ⏳ Stub (deny) |
| Formation (Barnabas) | All non-director roles | Formation model not yet defined | ⏳ Stub (deny) |
| Referrals (Op. Andrew) | All non-director roles | `Referral` model has no submitter FK | ⏳ Stub (deny) |

### 8.3 Endpoint Wiring Status

| Endpoint / ViewSet | Scoping Applied | Notes |
|--------------------|-----------------|-------|
| `households.StudentViewSet` | ✅ `scope_queryset(user, qs, DOMAIN_STUDENTS)` | Inline guardian filter removed from view |
| `households.HouseholdViewSet` | ⏳ Inline filter still in view | TODO: migrate to DOMAIN_FINANCIAL or new DOMAIN_HOUSEHOLDS |
| All other endpoints | ⏳ Not yet wired | Requires per-endpoint migration |

### 8.4 Test Coverage Status

| Test | Pathway | Status |
|------|---------|--------|
| `test_teacher_sees_only_enrolled_students` | Teacher → Section → Enrollment | ✅ Passing |
| `test_teacher_with_no_sections_sees_nothing` | Teacher (no sections) → deny | ✅ Passing |
| `test_parent_sees_only_own_household_students` | Parent email → guardian → household | ✅ Passing |
| `test_parent_email_match_is_case_insensitive` | Email case insensitivity | ✅ Passing |
| `test_parent_with_no_guardian_record_sees_nothing` | Orphan parent → deny | ✅ Passing |
| `test_parent_sees_only_own_household_applications` | Parent → FinancialAidApplication household_id | ✅ Passing |
| `test_parent_with_no_guardian_record_sees_nothing` (aid) | No guardian → deny | ✅ Passing |
| `test_parent_filter_targets_own_family` | Parent → LedgerEntry via guardian.family | ✅ Passing |
| `test_parent_without_guardian_db_record_sees_nothing` | No guardian FK → deny | ✅ Passing |
| `test_unknown_domain_returns_empty_queryset` | Unknown domain → deny | ✅ Passing |
| `test_empty_domain_string_returns_empty_queryset` | Empty string → deny | ✅ Passing |
| `test_teacher_student_fields_are_pruned` | Field: teacher cannot see ssn/counseling_notes | ✅ Passing |
| `test_director_student_fields_unchanged` | Field: director sees all fields | ✅ Passing |
| `test_missing_domain_in_context_clears_all_fields` | No crown_domain → deny all fields | ✅ Passing |

---

## 9. Layer C Implementation Plan

### Phase 1 — Infrastructure (Foundation Layer)

**Task 1: Create Central Scoping Module**

File: `backend/core/scoping.py`

Responsibilities:
- Row-level filtering engine
- Field-level filtering engine
- Role-to-domain mapping
- Centralized enforcement helpers

Core Interfaces:

```python
def scope_queryset(user, queryset, domain):
    """
    Applies row-level scoping rules.
    Returns filtered queryset.
    """

def scope_fields(user, serializer_class, domain):
    """
    Applies field-level scoping rules.
    Returns modified serializer class or filtered field set.
    """
```

No view-level filtering allowed after this.

---

**Task 2: Define Domain Constants**

File: `backend/core/scoping_domains.py`

```python
STUDENTS = "students"
FINANCIAL = "financial"
FINANCIAL_AID = "financial_aid"
DISCIPLINE = "discipline"
FORMATION = "formation"
REFERRALS = "referrals"
```

Views must declare which domain they belong to.

---

**Task 3: Implement Role → Row Scope Matrix**

Inside `scoping.py`:
- Map role to filtering logic
- Use centralized switch logic
- Never hardcode roles in views

---

**Task 4: Implement Field-Level Scoping**

Recommended strategy — Serializer Field Whitelisting:

```python
FIELD_SCOPE = {
    STUDENTS: {
        "teacher": ["id", "name", "grade", "attendance"],
        "finance": ["id", "name"],
        "director": "__all__"
    }
}
```

`scope_fields()` removes restricted fields dynamically.

---

### Phase 2 — Integrate Into Endpoints

**Task 5: Refactor All Sensitive Endpoints**

For each domain (Students, Billing, Aid, Discipline, Formation, Referrals):

```python
queryset = scope_queryset(request.user, queryset, STUDENTS)
serializer = scope_fields(request.user, StudentSerializer, STUDENTS)
```

This must happen **before** returning response.

**Task 6: Enforce No Frontend Filtering**

Search codebase and remove:
- `.filter()` logic in views tied to role strings
- Any conditional field hiding in frontend

Everything server-side.

---

### Phase 3 — Tests (Mandatory)

**Task 7: Create Row Scope Test Suite**

File: `backend/core/tests/test_layer_c_row_scope.py`

Test matrix:
- Teacher cannot see students outside assigned section
- Parent cannot see other families
- Finance cannot access counseling records
- Cross-tenant access denied

**Task 8: Create Field Scope Test Suite**

File: `backend/core/tests/test_layer_c_field_scope.py`

Tests must assert:

```python
assert "counseling_notes" not in response.json()
assert "internal_comments" not in response.json()
```

**Task 9: Add Cross-Tenant + Role Escalation Tests**

Simulate:
- User attempts to modify query params
- User attempts ID injection
- User attempts role header override

All must fail.

---

### Phase 4 — Refactor Existing Modules

| Task | Domain | Scope Action |
|------|--------|-------------|
| Task 10 | Students | Row + field scoping |
| Task 11 | Financial | Row scope for household; field restrictions for non-finance roles |
| Task 12 | Aid | Strict visibility — finance/aid officer/director only; parent sees household only |
| Task 13 | Discipline + Counseling | Strongest enforcement — confidential notes must never leak |
| Task 14 | Formation (Barnabas) | Student sees own; parent sees child; mentor sees assigned only |
| Task 15 | Referrals (Operation Andrew) | Parent sees own; admissions sees all; finance sees reward records only |

---

### Phase 5 — Audit & Validation

**Task 16: Full Test Suite Run**
- All existing tests must pass
- New Layer C tests must pass
- No ordering dependencies
- No conftest bypass issues

**Task 17: Manual Penetration Smoke**

Test manually:
- Change ID in URL
- Change tenant header
- Attempt cross-family lookup
- Attempt role override

All must fail cleanly.

---

### Phase 6 — Freeze Contract

After implementation:
1. Update this document with coverage percentages
2. Tag release: `phase7-layerc-contract-freeze-YYYY-MM-DD`

**Layer C becomes immutable contract.**

---

## 10. Risk Areas to Monitor

- Serializer inheritance leaks
- DRF `fields = "__all__"` misuse
- Nested serializers leaking child fields
- `prefetch_related` exposing unintended joins
- Aggregation endpoints returning raw objects

---

## 11. Canon Amendment

Any change to row or field visibility requires:
- Matrix update (this document)
- Test update
- Documentation revision
- Explicit code review

**No silent drift permitted.**

---

*Layer C Canon v1 Locked*
