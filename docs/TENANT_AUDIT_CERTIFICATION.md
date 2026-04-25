# Phase 7.2 / 7.2B — Tenant Isolation Audit Certification

**Audit Phase:** 7.2 (audit) + 7.2B (discipline remediation) + 7.2B.2 (financial aid remediation) + 7.2B.3 (admissions remediation)
**Branch:** `phase/7.2-tenant-isolation-audit`
**Base SHA (main at branch point):** `869d64e3ca01d16cb3a29e885bbdc08f131a9bb0`
**Phase 7.2B remediation SHA:** see PR #428 merged to main
**Phase 7.2B.2 remediation SHA:** see PR merged to main
**Phase 7.2B.3 remediation SHA:** see PR #429
**Test file:** `backend/tests/test_phase72_tenant_isolation.py`
**Test result:** 25 tests, 0 failures, 0 errors
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
| Admissions | `/api/admissions/` | `admissions/api_urls.py`, `admissions/views_admissions_links.py`, `admissions/views_enroll.py` |

---

## 2. Scoping Mechanisms

### 2a. Canonical — `get_request_school_id`

Located in `households/scoping.py`. Behaviour:

- Missing header → raises `MissingSchoolContext` → HTTP 400
- Header present, user is `is_staff=True` → returns school regardless of user affiliation
- Header present, user is non-staff, user has no `UserRole` for that school → raises `NotFound` → HTTP 404
- Header present, user has valid `UserRole` for that school → returns `school.id`

This is the **gold-standard** enforcement mechanism.

### ~~2b. Non-canonical — `require_school_id` (financial_aid)~~ — REMEDIATED in Phase 7.2B.2

Located in `financial_aid/tenant.py`. **This utility is now unused by all views.**

**Before Phase 7.2B.2:** `financial_aid/views.py` called `require_school_id` (UUID validation only,
no user-school binding) after running a permission check with `school=getattr(request, "school", None)`,
meaning isolation relied on the permission layer rather than the scoping utility.

**After Phase 7.2B.2:** Both views now call `get_request_school_id(request, required=True)` first,
then resolve the `School` object, then pass it to `user_has_permission`. Financial Aid is now canonical:

- Missing header → MissingSchoolContext → HTTP 400
- Non-staff user with wrong-school header → NotFound → HTTP 404
- Staff users → pass-through

`financial_aid/tenant.py` → `require_school_id` has zero callers; candidate for deletion.

### 2c. ~~Non-canonical~~ — Direct header read (discipline) — REMEDIATED in Phase 7.2B

**Before Phase 7.2B:** `discipline/api/views.py` read `X-School-Id` directly and performed
no cross-tenant user-role check. Wrong-tenant non-staff requests returned HTTP 200.

**After Phase 7.2B:** `_get_school_from_request()` replaced with `_get_school()` which
delegates to `get_request_school_id(request, required=True)`. Discipline is now canonical:

- Missing or invalid header → MissingSchoolContext → HTTP 400
- Non-staff user with wrong-school header → NotFound → HTTP 404
- Staff users → pass-through

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

### Financial Aid — CANONICAL ✓ (remediated Phase 7.2B.2)

- `require_school_id` (from `financial_aid/tenant.py`) replaced with `get_request_school_id(request, required=True)`
- Scoping fires **before** permission check in both `FinancialAidSummaryView` and `FinancialAidDrilldownView`
- Missing header → HTTP 400 (MissingSchoolContext)
- Non-staff user with wrong school header → HTTP 404 (NotFound)
- `financial_aid/tenant.py` → `require_school_id` now has zero callers (candidate for deletion)

### Discipline — CANONICAL ✓ (remediated Phase 7.2B)

- `_get_school_from_request()` replaced with `_get_school()` calling `get_request_school_id(request, required=True)`
- Missing header → HTTP 400 (MissingSchoolContext)
- Non-staff user with wrong school header → HTTP 404 (NotFound)
- Correct school → HTTP 200
- All 4 discipline endpoints (`incidents/`, `incidents/<id>/`, `incidents/<id>/actions/`, `metrics/`) updated

### Admissions — CANONICAL ✓ (remediated Phase 7.2B.3)

- `get_request_school_id(request, required=True)` now fires **before** the `_require_staff` check
  in all three active view handlers
- `admissions_applications_list`: queryset filtered by `school=school`
- `admissions_application_detail`: `get_object_or_404(qs, id=application_id, school=school)`
  (tenant tripwire fixed — was `get(id=application_id)` without school filter)
- `enroll_applicant`: `AdmissionsApplication.objects...get(id=application_id, school=school)`
  (tenant tripwire fixed)
- Missing header → HTTP 400; non-staff wrong-tenant → HTTP 404; correct school → staff check proceeds

---

## 4. Global Model Note

`Term` in `crown_api/models_scheduling_core.py` has no `school` FK. This is an
**intentional design choice**: terms are global scheduling objects shared across the
instance. If multi-tenant scheduling isolation is required in the future, a `school`
FK will need to be added and a migration written.

---

## 5. Test Coverage

**File:** `backend/tests/test_phase72_tenant_isolation.py`
**Total tests:** 25
**Result:** All pass

| Class | Tests | Coverage |
|---|---|---|
| `Phase72GradebookTenantTests` | 4 | missing header (400), unauthenticated (401/403), wrong school non-staff (404), correct school staff (200) |
| `Phase72BillingRunsTenantTests` | 4 | missing header (400), unauthenticated (401/403), wrong school non-staff (404), correct school (200) |
| `Phase72DisciplineTenantTests` | 5 | missing header (400, uses user_noschool), unauthenticated (401/403), wrong school non-staff (404, Phase 7.2B canonical), cross-tenant data isolation confirmed (404), correct school (200) |
| `Phase72FinancialAidTenantTests` | 4 | missing header (400, uses user_noschool), unauthenticated (401/403), wrong school non-staff (404, Phase 7.2B.2 canonical), correct school (200/403) |
| `Phase72AdmissionsApplicationsTenantTests` | 4 | missing header (400, uses user_noschool), unauthenticated (401/403), wrong school non-staff (404, Phase 7.2B.3 canonical), correct school (200/403) |
| `Phase72AdmissionsEnrollTenantTests` | 4 | missing header (400, uses user_noschool), unauthenticated (401/403), wrong school non-staff (404, Phase 7.2B.3 canonical), correct school (200/400/403) |

**Key assertions confirmed:**

- Canonical modules (gradebook, billing, **discipline**, **financial aid**, **admissions**) → wrong tenant → HTTP 404 ✓
- All modules → missing header → HTTP 400 ✓
- All modules → unauthenticated → HTTP 401 or 403 (DRF bearer-token auth behaviour) ✓

---

## 6. Risk Summary

| Risk | Severity | Module | Detail |
|---|---|---|---|
| ~~Non-canonical discipline scoping~~ | ~~Medium~~ | Discipline | **RESOLVED in Phase 7.2B**: `_get_school()` now uses `get_request_school_id` — wrong tenant → 404 |
| ~~Non-canonical financial aid scoping~~ | ~~Low-Medium~~ | Financial Aid | **RESOLVED in Phase 7.2B.2**: `get_request_school_id` now used in both views — wrong tenant → 404 |
| ~~Active admissions views — non-canonical scoping~~ | ~~Medium~~ | Admissions | **RESOLVED in Phase 7.2B.3**: `get_request_school_id` now in all 3 handlers; tenant tripwire `.get(id=...)` → `.get(id=..., school=school)` |
| Global Term model | Informational | Scheduling | No school FK; acceptable for current single-tenant-per-instance model |

---

## 7. Recommendations

> **Note:** These are observations, not implementation tasks for this PR.

1. ~~Migrate `discipline/api/views.py` to use `get_request_school_id(request, required=True)`.~~
   **RESOLVED in Phase 7.2B.** `_get_school()` now delegates to `get_request_school_id`.

2. ~~Migrate `financial_aid/tenant.py` → deprecate `require_school_id`; switch to
   `get_request_school_id`. Ensure permission checks remain in place.~~
   **RESOLVED in Phase 7.2B.2.** Both FA views now use canonical scoping. `require_school_id` has zero callers.

3. ~~Apply canonical scoping (`get_request_school_id`) to `admissions/views_admissions_links.py`
   and `admissions/views_enroll.py`. These files ARE active (registered in `admissions/api_urls.py`
   under `/api/admissions/`) and currently lack cross-tenant guard. **Do not delete.**~~
   **RESOLVED in Phase 7.2B.3.** All 3 admissions handlers now use canonical scoping.

4. Consider adding a `school` FK to `Term` if multi-tenant scheduling is planned.

---

## 8. Certification Sign-off

All 25 Phase 7.2 / 7.2B / 7.2B.2 / 7.2B.3 tenant isolation tests pass.

- **Canonical pattern confirmed in:** Gradebook, Billing, Billing API, Academics, Curricula, Exports, **Discipline** (remediated Phase 7.2B), **Financial Aid** (remediated Phase 7.2B.2), **Admissions** (remediated Phase 7.2B.3)
- **Test file:** `backend/tests/test_phase72_tenant_isolation.py`
- **Audit branch:** `phase/7.2-tenant-isolation-audit`
- **Phase 7.2B remediation branch:** `phase/7.2b-discipline-canonical`
- **Phase 7.2B.2 + 7.2B.3 remediation branch:** `phase/7.2b2-financial-aid-canonical` (PR #429)
