# Phase 7.2 — Tenant Isolation Audit Certification

**Audit Phase:** 7.2  
**Branch:** `phase/7.2-tenant-isolation-audit`  
**Base SHA (main at branch point):** `869d64e3ca01d16cb3a29e885bbdc08f131a9bb0`  
**Test file:** `backend/tests/test_phase72_tenant_isolation.py`  
**Test result:** 13 tests, 0 failures, 0 errors  
**Status:** CERTIFIED ✓

---

## 1. Audit Scope

This audit covers Crown2026 backend modules for cross-tenant data isolation via the
`X-School-Id` request header. Every request must be scoped to the school identified
by this header; non-staff users must not be able to access or enumerate data belonging
to a different school.

Modules audited:

| Module | URL prefix | File(s) reviewed |
|---|---|---|
| Gradebook | `/api/v1/gradebook/` | `gradebook/views.py` |
| Billing (api) | `/api/v1/billing/runs/` | `billing/api.py` |
| Billing (billing_api) | `/api/v1/billing/` | `billing_api/views.py` |
| Academics | `/api/v1/academics/` | `academics/views.py` |
| Curricula | `/api/v1/curricula/` | `curricula/views.py` |
| Exports | `/api/v1/exports/` | `exports/views.py` |
| Financial Aid | `/api/v1/financial-aid/` | `financial_aid/views.py` |
| Discipline | `/api/v1/discipline/` | `discipline/api/views.py` |
| Admissions (dead code) | *(unregistered)* | `admissions/views_admissions_links.py`, `admissions/views_enroll.py` |

---

## 2. Scoping Mechanisms

### 2a. Canonical — `get_request_school_id`

Located in `households/scoping.py`. Behaviour:

- Missing header → raises `MissingSchoolContext` → HTTP 400
- Header present, user is `is_staff=True` → returns school regardless of user affiliation
- Header present, user is non-staff, user has no `UserRole` for that school → raises `NotFound` → HTTP 404
- Header present, user has valid `UserRole` for that school → returns `school.id`

This is the **gold-standard** enforcement mechanism.

### 2b. Non-canonical — `require_school_id` (financial_aid)

Located in `financial_aid/tenant.py`. Behaviour:

- Validates that the header is a well-formed UUID
- Sets `request.school` to the fetched `School` object
- Does **not** check whether the requesting user has a role at that school
- Permission enforcement happens separately via `user_has_permission(request.user, "...", school=request.school)`

Because `user_has_permission` runs before `require_school_id` in the view, a user without
any `UserRole` gets a 403 (permission denied) before reaching the school binding. This means
isolation is achieved via the permission layer rather than the scoping utility itself.
The isolation holds in practice but the mechanism is indirect.

### 2c. Non-canonical — Direct header read (discipline)

Located in `discipline/api/views.py`. Behaviour:

- Reads `school_id` directly from `request.headers.get("X-School-Id")`
- Filters ORM queryset: `DisciplineIncident.objects.filter(school=school_from_header)`
- No check that the requesting user has a role at that school
- A non-staff user supplying another school's ID receives HTTP 200 with an empty queryset (no data leaks, but no 404 enforcement)

---

## 3. Per-Module Findings

### Gradebook — CANONICAL ✓

- Uses `get_request_school_id(request, required=True)` via `_sections_for_gradebook()`
- Missing header → HTTP 400
- Non-staff user with wrong school header → HTTP 404 (NotFound raised)
- Additional gate: `_sections_for_gradebook()` raises `PermissionDenied` (403) when
  the user has no `UserRole` entry at all, preventing enumeration even with correct school

### Billing (`billing/api.py`) — CANONICAL ✓

- `billing_runs()` uses `get_request_school_id(request)` (required=True default)
- Missing header → HTTP 400 (MissingSchoolContext)
- Non-staff user with wrong school header → HTTP 404

### Billing (`billing_api/views.py`) — CANONICAL ✓

- Uses `get_request_school_id` throughout
- Same guarantees as above

### Academics — CANONICAL ✓

- Uses `get_request_school_id` in all affected viewsets

### Curricula — CANONICAL ✓

- Uses `get_request_school_id`

### Exports — CANONICAL ✓

- Uses `get_request_school_id`; confirmed in `exports/views.py`

### Financial Aid — NON-CANONICAL ⚠

- Uses `require_school_id` from `financial_aid/tenant.py`
- No direct user-school binding check in the scoping utility
- Isolation relies on `user_has_permission` (permission check executed first)
- **Risk:** If a view were added that calls `require_school_id` without a preceding
  permission check, cross-tenant access would be possible for any authenticated user.

### Discipline — NON-CANONICAL ⚠

- Direct header read; no cross-tenant user-role enforcement
- ORM `filter(school=...)` prevents data leakage (school-A incidents never returned
  under school-B scope), but a non-staff user with a wrong school header gets HTTP 200
  rather than HTTP 404
- **Risk:** Information disclosure via timing or response-shape differences is theoretically
  possible; the absence of 404 also violates the "you don't see what you can't access"
  principle.

### Admissions (dead code) — NOT REGISTERED

- `admissions/views_admissions_links.py` and `admissions/views_enroll.py` contain views
  that are **not registered** in any active URLconf. They are unreachable in production.
- These files lack canonical scoping. Their presence is a maintenance liability.

---

## 4. Global Model Note

`Term` in `crown_api/models_scheduling_core.py` has no `school` FK. This is an
**intentional design choice**: terms are global scheduling objects shared across the
instance. If multi-tenant scheduling isolation is required in the future, a `school`
FK will need to be added and a migration written.

---

## 5. Test Coverage

**File:** `backend/tests/test_phase72_tenant_isolation.py`  
**Total tests:** 13  
**Result:** All pass

| Class | Tests | Coverage |
|---|---|---|
| `Phase72GradebookTenantTests` | 4 | missing header (400), unauthenticated (401/403), wrong school non-staff (404), correct school staff (200) |
| `Phase72BillingRunsTenantTests` | 4 | missing header (400), unauthenticated (401/403), wrong school non-staff (404), correct school (200) |
| `Phase72DisciplineTenantTests` | 5 | missing header (400), unauthenticated (401/403), wrong school returns 200 (documents non-canonical), ORM isolation confirmation (school-A data absent under school-B scope), correct school (200) |

**Key assertions confirmed:**

- Canonical modules (gradebook, billing) → wrong tenant → HTTP 404 ✓
- Non-canonical discipline → wrong tenant → HTTP 200, **but** school-A data absent from response body ✓
- All modules → missing header → HTTP 400 ✓
- All modules → unauthenticated → HTTP 401 or 403 (DRF bearer-token auth behaviour) ✓

---

## 6. Risk Summary

| Risk | Severity | Module | Detail |
|---|---|---|---|
| Non-canonical discipline scoping | Medium | Discipline | Wrong-tenant requests return 200; no UserRole enforcement |
| Non-canonical financial aid scoping | Low-Medium | Financial Aid | Isolation via permission layer, not scoping utility; fragile if new views added without permission check |
| Dead admissions view files | Low | Admissions | Unrouted but unscoped; delete to reduce maintenance surface |
| Global Term model | Informational | Scheduling | No school FK; acceptable for current single-tenant-per-instance model |

---

## 7. Recommendations

> **Note:** These are observations, not implementation tasks for this PR.

1. Migrate `discipline/api/views.py` to use `get_request_school_id(request, required=True)`.
   This will make wrong-tenant requests return 404 consistently with all canonical modules.

2. Migrate `financial_aid/tenant.py` → deprecate `require_school_id`; switch to
   `get_request_school_id`. Ensure permission checks remain in place.

3. Delete `admissions/views_admissions_links.py` and `admissions/views_enroll.py`
   (or move to an archived branch). Unregistered, unscoped views are a maintenance hazard.

4. Consider adding a `school` FK to `Term` if multi-tenant scheduling is planned.

---

## 8. Certification Sign-off

All 13 Phase 7.2 tenant isolation tests pass as of this audit.

- **Canonical pattern confirmed in:** Gradebook, Billing, Billing API, Academics, Curricula, Exports
- **Non-canonical documented in:** Discipline, Financial Aid
- **Dead code flagged in:** Admissions
- **Test file:** `backend/tests/test_phase72_tenant_isolation.py`
- **Audit branch:** `phase/7.2-tenant-isolation-audit`
- **Main HEAD at branch point:** `869d64e3ca01d16cb3a29e885bbdc08f131a9bb0`
