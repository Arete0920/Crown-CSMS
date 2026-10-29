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

## 2. Role-Based Row Scoping Matrix (target visibility doctrine)

The roles below express intended policy. They do **not** certify that all listed behavior has been implemented or deployed. Section 8 records the reviewed source behavior, with stricter fail-closed states where assignments or permissions are not yet supported.

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

_Source behavior reconciled on 2026-10-28 to protected main `2ae0c7a6283f566fa8918e43e61669dd2fa2d30a`; hosted privacy acceptance remains open under issue #441._

### 8.1 Authoritative identity versus compatibility read models

The accepted [ADR-001](architecture/ADR-001-CANONICAL-HOUSEHOLD-GUARDIAN-STUDENT.md) governs operational **writes**. Model naming and a protected read endpoint do not transfer that write authority.

| Model family | Current responsibility | Boundary |
|---|---|---|
| `core.Family`, `core.Guardian`, `core.Student` | Canonical operational family/guardian/student writes | School-scoped services and ADR-001; no implicit cross-model remapping |
| `households.Household`, `households.Guardian`, `households.Student` | Compatibility/read domain behind `/api/` and `/api/v1/` household, guardian and student views | Tenant, persisted school role, domain row and field scope before serialization |
| `crown_api` household/person/student models | Separate compatibility domain | No equivalence of identifiers without controlled reconciliation |

Do not substitute compatibility student identifiers for canonical `core.Student` records or the `/api/v1/student-records/` wizard identity route.

### 8.2 Current Layer C source behavior (not hosted certification)

Source authorities: `backend/core/scoping.py`, `backend/households/scoping.py`, `backend/households/views.py` and `backend/households/serializers.py`. The following describes the reviewed protected source, not a blanket claim that every endpoint in every module is wired or deployed.

| Domain and caller | Current row authorization | Current restriction |
|---|---|---|
| Compatibility household API, parent | Existing `households.Guardian.account` linked to this user in the selected school and matching household school | Email equality, unlinked guardians and cross-school selection alone confer no access |
| Compatibility guardian API, parent | Own linked `Guardian.account` row only | Co-guardian contact details are not inherited from residence; nested household `guardians` omitted |
| Compatibility student API, parent | Students of a verified linked household in the selected school | Legacy guardian-scope feature toggle does not bypass Layer C |
| Compatibility student API, teacher | Students in the teacher's linked section enrollments | Other students denied; current role must be verified in the selected school |
| Compatibility student API, student | Own record via `households.Student.account_id` when the required school role and link exist | Without the persisted linkage, deny |
| Compatibility household directory, staff | Persisted school role plus active staff status and explicit `households.view` grant | `is_staff` alone does not authorize directory access |
| Compatibility guardian directory, staff | Persisted school role plus active staff status and separate `guardians.view` grant | A household-directory grant does not confer contact-directory access |
| Student protected reads, unidentified/unauthorized actor | None | Unknown/no-role, other-school roles, and unsupported duties fail closed |
| Financial-aid row-scoping helper, parent | Selected-school household IDs resolved through linked `households.Guardian.account` | Email-only identity is not accepted |
| Legacy core LedgerEntry row-scoping helper, parent | `core.UserAccount.guardian.family` | Distinct legacy model and permission contract; not a cross-model household promotion |
| Discipline row-scoping helper, teacher/counselor | Denied pending reviewed assignment ownership | Section 2 expresses target doctrine, **not** a currently granted teacher/counselor permission |
| Formation and referral row-scoping helpers | Role-specific source rules; unsupported relationships deny | Presence of a helper is not proof of active protected endpoint coverage |

All public compatibility viewsets first resolve an active school via the canonical tenant contract, then apply domain rows and serializer fields. Inconsistent related household/guardian/student school IDs are excluded before direct or embedded serialization.

### 8.3 Current canonical compatibility endpoint wiring

| Endpoint / ViewSet | Centralized source contract | Verification status |
|---|---|---|
| `households.HouseholdViewSet` at `/api/households/` and `/api/v1/households/` | `DOMAIN_HOUSEHOLDS`, verified guardian ownership or granted staff duty, scoped nested children | Merged source and synthetic regression; hosted acceptance remains open |
| `households.GuardianViewSet` at `/api/guardians/` and `/api/v1/guardians/` | `DOMAIN_GUARDIANS`, own contact or separate contact-directory grant | Merged source and synthetic regression; hosted acceptance remains open |
| `households.StudentViewSet` at `/api/students/` and `/api/v1/students/` | `DOMAIN_STUDENTS`, role- and household-bound before field serialization | Merged source and synthetic regression; distinct from canonical operational `core.Student` |
| Other product APIs | Verify each actual route, scoping call and negative tests separately | Do not infer universal Layer C coverage from the three viewsets |

### 8.4 Security regression inventory and evidence boundaries

Existing source tests include:
- `backend/households/tests/test_privacy_role_boundaries.py`: both public aliases, unknown-role denial, linked versus email-only parent, wrong family, school mismatch and co-guardian negatives.
- `backend/households/tests/test_nested_privacy_fields.py`: direct/embedded parity, distinct staff directory grants and absence of denied nested record counts.
- `backend/households/tests/test_guardian_scoping.py`: verified parent, registrar grants and teacher household-denial behavior.
- `backend/households/tests/test_scoping_canonical_authority.py`: canonical tenant resolution and rejected unauthorized tenant overrides.

These cases are part of the governed backend suite. Source correction [PR #442](https://github.com/Arete0920/Crown-CSMS/pull/442) was merged with required CI. **Neither source checks nor synthetic tests establish live DEV permission seeding, guardian-link reconciliation, or deployed tenant/privacy acceptance.** Track those separately under [issue #441](https://github.com/Arete0920/Crown-CSMS/issues/441); keep it open until actual authorized hosted negatives are verified. No production compliance or assurance certification is asserted.

---

## Issue #441: canonical public privacy boundary

The accepted ADR-001 reserves canonical operational writes for `core.Family`, `core.Guardian`, and `core.Student`. The `households.*` models remain compatibility/read models, not canonical operational writers; section 8.1 now distinguishes the current authorities.

Canonical `/api/` and `/api/v1/` household, guardian and student endpoints require selected active school plus Layer C row/field scope. School-wide household access requires `households.view`; guardian directory access separately requires `guardians.view`. A Django staff bit, email match, unknown role, and a role belonging to another school do not authorize personal data. Parent household/student and financial aid reads require a persisted same-school `households.Guardian.account` link. The old guardian-scope toggle does not bypass protected viewsets. Permission seeding and hosted acceptance are distinct operational steps.

## 9. Historical Layer C implementation plan (archived)

The original phase/task examples below are preserved as historical design intent, not active implementation instructions. The current executable interfaces are `scope_queryset`, `scope_serializer_fields`, `scoped_serializer_context` and `apply_scope` in `backend/core/scoping.py`; the illustrative `scope_fields()` below is not the current interface.

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



### October 24, 2026 — #441 co-guardian and identity-source guard

A verified parent linked through `households.Guardian.account` may read
their own contact record but may not enumerate other adults' contacts
merely because those guardians share a household. Nested household
serialization omits `guardians` for parent consumers. Staff directory
grants remain distinct. A cross-school tenant-selector override alone
does not authorize private household reads.

Wizard E2E certification must use the canonical `core.Student` list
(`/api/v1/student-records/`) rather than compatibility
`households.Student` (`/api/v1/students/`); their UUIDs cannot be
substituted. The server-side student/school validation remains enforced.
