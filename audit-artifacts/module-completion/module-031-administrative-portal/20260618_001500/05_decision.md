# Module 031 — Administrative Portal: Proof Decision

## Status: PROVEN (pending review and CI settlement)

## Evidence Summary

| Check | Result |
|---|---|
| Django system check | PASS — 0 issues in captured pre-review run |
| Focused pytest | PASS — 20/20 in captured pre-review run |
| Admin workspace importable | PASS |
| URL `admin-metrics` registered | PASS |
| Nav registry entry (`admin.view`) | PASS |
| Permission seed (`admin.view`) | PASS |
| Auth boundary — unauthenticated admin_metrics denied deterministically with 403 | PASS |
| Permission boundary — no-grant user denied deterministically with 403 | PASS |
| Happy path — admin.view user gets 200 | PASS |
| Oversight payload contract | PASS |
| Enrollment funnel shape | PASS |
| Operational alerts shape | PASS |
| ORM tenant isolation (`UserRole` scoped to school) | PASS |
| Executive360 view importable | PASS |
| Executive360 URL registered | PASS |
| Executive360 unauthenticated denied deterministically with 403 | PASS |

## Scope Boundary

- **IN SCOPE**: Backend proof — import, URL wiring, permission gate, payload contract, deterministic denial assertions, ORM/permission-layer isolation
- **OUT OF SCOPE**: Dashboard live-data readiness, full functional flow, release readiness
- **OUT OF SCOPE**: Canonical scorecard/matrix reconciliation (separate PR after merge)
- **OUT OF SCOPE**: HTTP middleware-attached tenant-header proof, because `backend/tests/conftest.py` disables `TENANT_HEADER_REQUIRED`

## Key Implementation Facts

- `admin_metrics` at `GET /api/admin/metrics/` is protected by `@require_permission("admin.view")`
- `require_permission()` returns `403` when unauthenticated or unpermitted access fails
- `admin.view` permission is defined in `seed_permissions.py`
- This evidence packet does **not** claim `PRINCIPAL` role mapping
- Nav registry entry: `Administration → /admin` gated on `admin.view`
- `ExecutiveSelfOverview` at `GET /api/executive360/me/overview/` requires `IsAuthenticated`
- Tenant isolation: `UserRole` is school-scoped; `user_has_permission(user, "admin.view", school=school_b)` returns false when the role exists only for `school_a`

## Review-fix disposition

This packet was corrected after review to:

1. Replace broad status-code ranges with deterministic `403` assertions for admin_metrics denial paths.
2. Remove HTTP tenant-header proof claims that are not supported while `TENANT_HEADER_REQUIRED` is disabled in test conftest.
3. Remove inaccurate `PRINCIPAL` role-mapping claims.

## Next Step (after merge)

Open a separate canonical reconciliation PR to update:
- `audit-artifacts/module-completion/current/01_module_matrix_expanded.csv` (row 031: NOT_PROVEN → PROVEN)
- `audit-artifacts/module-completion/current/05_completion_scorecard.md`

## Review

INDEPENDENT_REVIEW_REQUIRED or documented solo-maintainer workaround required before merge.
