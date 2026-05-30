# Mainline Reconcile First-Blocker Closure Delta (2026-05-29 22:39)

Purpose: record authoritative closure evidence for the three active blockers from the direct-rerun delta tied to reconcile packet `20260529_215336`.

## Starting active blockers

- `frontend_unit`
- `backend_django_check`
- `backend_reporting_exports_gate`

## Surgical fixes applied in remote-clean lane

- `frontend/dashboards/src/tests/sandboxCommandCenter.test.jsx`
  - updated stale role expectation from `Program Director` to `Head of School`.
  - changed duplicate-text assertions to `getAllByText(...).length > 0` for role and organization labels.
- `backend/crown_api/settings.py`
  - restored canonical custom-user wiring: `AUTH_USER_MODEL = 'core.UserAccount'`.
- `backend/spiritual_life/migrations/0002_alter_prayerrequest_visibility_and_more.py`
  - generated missing formation-schema migration including `PortraitDomain` and related models/indexes required during test DB setup.

## Verification reruns

- Frontend unit suite:
  - command: `npm run test:unit`
  - result: `Test Files 35 passed (35); Tests 140 passed (140)`.
- Django system check:
  - command: `python manage.py check`
  - result: `System check identified no issues (0 silenced)`.
- Reporting exports gate (authoritative migration path):
  - command: `python -m pytest backend/tests/test_reporting_exports_gate.py -q`
  - result: `8 passed in 108.90s (0:01:48)`.
- Reporting exports gate (sanity discriminator):
  - command: `python -m pytest backend/tests/test_reporting_exports_gate.py -q --nomigrations`
  - result: `8 passed in 6.16s`.

## Outcome

- Active blockers reduced: `3 -> 0`.
- Local-check first-blocker queue is fully closed for this reconcile lane (`7/7`).
- Canonical release posture unchanged; this is a closure-evidence delta only.
