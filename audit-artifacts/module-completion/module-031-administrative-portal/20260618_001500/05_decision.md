# Module 031 — Administrative Portal: Proof Decision

## Status: PROVEN (pending independent review)

## Evidence Summary

| Check | Result |
|---|---|
| Django system check | PASS — 0 issues |
| Focused pytest (20 tests) | PASS — 20/20 |
| Admin workspace importable | PASS |
| URL `admin-metrics` registered | PASS |
| Nav registry entry (admin.view) | PASS |
| Permission seed (admin.view) | PASS |
| Auth boundary — unauthenticated denied (403) | PASS |
| Permission boundary — no-grant user denied (403) | PASS |
| Happy path — admin.view user gets 200 | PASS |
| Oversight payload contract | PASS |
| Enrollment funnel shape | PASS |
| Operational alerts shape | PASS |
| ORM tenant isolation (UserRole scoped to school) | PASS |
| Executive360 view importable | PASS |
| Executive360 URL registered | PASS |
| Executive360 unauthenticated denied | PASS |

## Scope Boundary

- **IN SCOPE**: Backend proof — import, URL wiring, permission gate, payload contract, ORM isolation
- **OUT OF SCOPE**: Dashboard live-data readiness, full functional flow, release readiness
- **OUT OF SCOPE**: Canonical scorecard/matrix reconciliation (separate PR after merge)

## Key Implementation Facts

- `admin_metrics` at `GET /api/admin/metrics/` is protected by `@require_permission("admin.view")`
- `admin.view` permission is defined in `seed_permissions.py` and assigned to PRINCIPAL/school_admin/HEAD_OF_SCHOOL roles
- Nav registry entry: `Administration → /admin` gated on `admin.view`
- `ExecutiveSelfOverview` at `GET /api/executive360/me/overview/` requires `IsAuthenticated`
- Tenant isolation: `UserRole` is school-scoped; `user_has_permission` filters roles by school when middleware provides `request.school`
- Note: Test environment disables `TENANT_HEADER_REQUIRED` (via conftest.py); ORM-level isolation is proven directly via `user_has_permission(school=school_b)` → False

## Next Step (after merge)

Open a separate canonical reconciliation PR to update:
- `audit-artifacts/module-completion/current/01_module_matrix_expanded.csv` (row 031: NOT_PROVEN → PROVEN)
- `audit-artifacts/module-completion/current/05_completion_scorecard.md`

## Review

INDEPENDENT_REVIEW_REQUIRED
