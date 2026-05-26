# Live Runtime Governance Commit-Ready Changelog (2026-05-26)

## Scope

- Public endpoint and CSRF governance automation.
- Release workflow hard-fail integration for unmanaged public surfaces.
- Shared dashboard truth-disclosure rollout.
- Finance bespoke live-data truth disclosure.
- Canonical release-authority signoff memo for current branch state.

## Code Changes

- `tools/verify_public_surface_policy.py`
  - Added scanner/enforcement gate for `AllowAny` and `csrf_exempt` usage.
  - Fails on unmanaged entries, stale policy rows, and malformed policy records.
- `tests/test_public_surface_policy_gate.py`
  - Added focused regression coverage for success, unmanaged-entry failure, stale-entry failure, and malformed-policy failure.
- `.github/workflows/contract-gate.yml`
  - Added policy-matrix files to workflow trigger paths.
  - Added public-surface policy verification step.
- `.github/workflows/release-verify.yml`
  - Added public-surface policy verification step.
- `docs/security/public_endpoint_policy_matrix.json`
  - Added authoritative inventory for current `AllowAny` surface.
- `docs/security/csrf_exception_policy_matrix.json`
  - Added authoritative inventory for current `csrf_exempt` surface.
- `docs/security/PUBLIC_ENDPOINT_POLICY_MATRIX.md`
  - Added human-readable public endpoint policy matrix.
- `docs/security/CSRF_EXCEPTION_POLICY_MATRIX.md`
  - Added human-readable CSRF exception policy matrix.
- `frontend/dashboards/src/components/crown-dashboard/CrownDashboardTemplate.jsx`
  - Added default `dataState` / `sourceLabel` injection for template-backed metrics and command modules.
  - Refactored shared template rendering to keep the new truth-disclosure behavior lint-clean.
- `frontend/dashboards/src/components/crown-dashboard/CrownDashboardTemplate.test.jsx`
  - Added focused unit coverage for default fallback disclosure and explicit top-level disclosure overrides.
- `frontend/dashboards/src/pages/FinanceDashboard.jsx`
  - Added explicit finance data-truth disclosure for `loading`, `live`, and `unavailable` states.
- `frontend/dashboards/src/pages/FinanceDashboard.test.jsx`
  - Added focused unit coverage for finance live and unavailable disclosure paths.
- `docs/release/LIVE_RELEASE_AUTHORITY_SIGNOFF_20260526.md`
  - Added canonical signoff memo with current truthful decision posture.

## Verified Behavior

- Protected-spine runtime packet remains green and authoritative.
- Auth/RBAC protected-spine rerun remains green.
- Public-surface governance gate passes locally and is wired into release workflows.
- Template-backed dashboards now disclose fallback/template data truth by default.
- Finance dashboard now discloses live/unavailable runtime truth explicitly.
- Admissions dashboard live/fallback truth disclosure remains intact.
- Board executive dashboard already discloses `LIVE` versus `DEMO` state.

## Validation

- `python tools/verify_public_surface_policy.py`
  - PASS
  - `AllowAny entries tracked: 14`
  - `csrf_exempt entries tracked: 19`
- `python -m pytest tests/test_public_surface_policy_gate.py -q`
  - PASS (`4 passed`)
- `npm run test:unit -- src/components/crown-dashboard/CrownDashboardTemplate.test.jsx src/pages/AdmissionsDashboard.test.jsx src/pages/FinanceDashboard.test.jsx`
  - PASS (`32 passed files / 125 passed tests`)

## Diff Metrics (tracked files)

Tracked diff summary captured this session for the currently modified tracked slice:

- `4 files changed, 264 insertions(+), 207 deletions(-)`

Tracked files included in that diff summary:

- `.github/workflows/contract-gate.yml`
- `.github/workflows/release-verify.yml`
- `frontend/dashboards/src/components/crown-dashboard/CrownDashboardTemplate.jsx`
- `frontend/dashboards/src/pages/FinanceDashboard.jsx`

## New Files To Stage Explicitly

- `tools/verify_public_surface_policy.py`
- `tests/test_public_surface_policy_gate.py`
- `docs/security/public_endpoint_policy_matrix.json`
- `docs/security/csrf_exception_policy_matrix.json`
- `docs/security/PUBLIC_ENDPOINT_POLICY_MATRIX.md`
- `docs/security/CSRF_EXCEPTION_POLICY_MATRIX.md`
- `frontend/dashboards/src/components/crown-dashboard/CrownDashboardTemplate.test.jsx`
- `frontend/dashboards/src/pages/AdmissionsDashboard.test.jsx`
- `frontend/dashboards/src/pages/FinanceDashboard.test.jsx`
- `docs/release/LIVE_RELEASE_AUTHORITY_SIGNOFF_20260526.md`
- `docs/release/LIVE_RUNTIME_GOVERNANCE_PR_SUMMARY_20260526.md`
- `docs/release/LIVE_HOSTED_CI_HANDOFF_20260526.md`

## Remaining External Blocker

- Hosted `contract-gate` and `release-verify` proof still requires commit + push because current local edits are not yet on the branch tip seen by GitHub Actions.

## Suggested Commit Message

- `feat(release): enforce public surface policy gate and complete dashboard truth disclosure`
