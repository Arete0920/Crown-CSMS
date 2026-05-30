# Protected-Spine Auth Nomigrations Discriminator (2026-05-29 06:11)

Purpose: document the discriminating check and runner adjustment that unblocked the auth-security subbatch for the current rerun stamp.

## Discriminating Check

- Baseline hanging node:
  - `backend/core/tests/test_permission_engine.py::TestUserHasPermission::test_returns_true_when_role_granted`
- Without `--nomigrations`:
  - repeated timeout (180s and 600s windows).
- With `--nomigrations`:
  - command: `.venv\Scripts\python.exe -u -m pytest backend/core/tests/test_permission_engine.py::TestUserHasPermission::test_returns_true_when_role_granted -q -x --nomigrations`
  - result: `1 passed in 4.51s`.

## Runner Adjustment

- Updated wrapper file:
  - `audit-artifacts/runtime-release-closure/20260418_070051/72_run_protected_spine_subbatches.ps1`
- Change:
  - `auth_security_baseline` now joins `tenant_isolation_scoping` and `admissions_applications` in automatic `--nomigrations` injection.

## Validation Outcome

- Fresh wrapper run stamp: `20260529_060848`.
- Auth-security summary emitted and GREEN:
  - `BACKEND_PYTEST_SUBBATCH_SUMMARY_auth_security_baseline_20260529_060848.md/.json`
  - footer: `268 passed, 1 skipped in 129.17s (0:02:09)`
  - command includes `--nomigrations`.

## Current State

- Auth-security no longer the active blocker on stamp `20260529_060848`.
- Full protected-spine packet for stamp `20260529_060848` is still pending while later subbatches continue.
