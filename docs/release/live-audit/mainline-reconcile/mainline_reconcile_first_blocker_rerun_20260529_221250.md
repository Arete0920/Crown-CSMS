# Mainline Reconcile First-Blocker Rerun Evidence (2026-05-29 22:12:50)

Purpose: execute direct reruns for all six local-check failures from reconcile packet `20260529_215336` and capture current blocker truth.

## Runner Context

- Runner location: `C:/Users/JMega/OneDrive/Desktop/Crown2026_remotecleanclone`
- Source packet under reassessment:
  - `audit-artifacts/mainline-reconcile/20260529_215336/00_SUMMARY.md`
  - `audit-artifacts/mainline-reconcile/20260529_215336/30_check_results.csv`

## Commands and Outcomes

### Frontend checks

- `npm run test:unit` (from `frontend/dashboards`) -> **FAIL**
  - deterministic failure:
    - `src/tests/sandboxCommandCenter.test.jsx > renders guided context from URL params`
    - assertion expects `Program Director` but rendered value is `Head of School`.
- `npm run test:release:a11y` -> **PASS** (`5 passed`).
- `npm run ui:proof:nav` -> **PASS** (`11 passed`).
- `npm run test:release:routes` -> **PASS** (`1 passed`).
  - note: Vite proxy warning present (`ECONNREFUSED 127.0.0.1:8000`) but suite result is pass.

### Backend checks

- `python -m pytest backend/tests/test_reporting_exports_gate.py -q` -> **FAIL**
  - deterministic setup error across all tests:
    - `django.db.utils.OperationalError: no such table: spiritual_life_portraitdomain`
  - pytest summary: `8 errors in 88.82s`.
- `python manage.py check` (from `backend`) -> **FAIL**
  - deterministic system-check conflicts:
    - `auth.User.groups` vs `core.UserAccount.groups` reverse accessor clash (`fields.E304`)
    - `auth.User.user_permissions` vs `core.UserAccount.user_permissions` reverse accessor clash (`fields.E304`)
  - total: `System check identified 4 issues (0 silenced)`.

## Net Delta vs Packet `20260529_215336`

- Fresh direct rerun now shows **3/6 pass** and **3/6 fail**.
- Newly green from prior packet-fail state:
  - `frontend_release_a11y`
  - `frontend_nav`
  - `frontend_release_routes`
- Active blockers after rerun:
  - `frontend_unit` (stale assertion in `sandboxCommandCenter.test.jsx`)
  - `backend_reporting_exports_gate` (missing `spiritual_life_portraitdomain` table during DB setup)
  - `backend_django_check` (`fields.E304` user model reverse accessor conflicts)

## Integrity Notes

- This rerun evidence is a direct command-level reassessment and does not replace the authoritative reconcile packet.
- Canonical approved-slice authority posture remains unchanged.
- Next authoritative state change requires a fresh reconcile packet after resolving the three active blockers.
