# PR: Runtime Governance Gate + Dashboard Truth Disclosure Closure

## Summary

This change set closes the main code-side release-governance gaps by enforcing policy-backed public endpoint review, blocking unmanaged `AllowAny` and `csrf_exempt` additions in CI, and completing truthful data-state disclosure across the current known dashboard surfaces.

## Why

- Prevent silent expansion of unauthenticated or CSRF-exempt backend surfaces.
- Convert security/governance recommendations into enforceable workflow checks.
- Make dashboard truth explicit so operators can distinguish live, fallback, loading, unavailable, demo, and template-backed data states.
- Consolidate current release authority into one canonical memo with a truthful decision posture.

## Key Changes

- Backend/release governance
  - Added `tools/verify_public_surface_policy.py` to inventory and enforce approved `AllowAny` and `csrf_exempt` usage.
  - Added authoritative policy matrices under `docs/security/`.
  - Added focused gate tests in `tests/test_public_surface_policy_gate.py`.
  - Wired the policy gate into `contract-gate` and `release-verify` workflows.
- Frontend dashboard truth disclosure
  - Added shared fallback/template disclosure defaults in `CrownDashboardTemplate.jsx`.
  - Preserved admissions explicit live/fallback disclosure.
  - Added finance explicit live/unavailable disclosure.
  - Kept board executive’s existing live/demo disclosure in the approved surface set.
  - Added focused frontend tests for template defaults and finance disclosure.
- Release authority
  - Added `docs/release/LIVE_RELEASE_AUTHORITY_SIGNOFF_20260526.md` as the canonical signoff memo for the current branch state.

## Validation

- `python tools/verify_public_surface_policy.py` -> PASS
- `python -m pytest tests/test_public_surface_policy_gate.py -q` -> PASS (`4 passed`)
- `npm run test:unit -- src/components/crown-dashboard/CrownDashboardTemplate.test.jsx src/pages/AdmissionsDashboard.test.jsx src/pages/FinanceDashboard.test.jsx` -> PASS (`32 passed files / 125 passed tests`)

## Evidence

- `docs/release/LIVE_RELEASE_AUTHORITY_SIGNOFF_20260526.md`
- `docs/security/public_endpoint_policy_matrix.json`
- `docs/security/csrf_exception_policy_matrix.json`
- `tests/test_public_surface_policy_gate.py`
- `frontend/dashboards/src/components/crown-dashboard/CrownDashboardTemplate.test.jsx`
- `frontend/dashboards/src/pages/AdmissionsDashboard.test.jsx`
- `frontend/dashboards/src/pages/FinanceDashboard.test.jsx`
- `audit-artifacts/runtime-release-closure/20260418_070051/BACKEND_PYTEST_PROTECTED_SPINE_SUBBATCH_PACKET_20260526_052724.md`
- `audit-artifacts/runtime-release-closure/20260418_070051/BACKEND_PYTEST_SUBBATCH_SUMMARY_auth_security_baseline_20260526_055509.md`

## Risk

- Low-to-moderate.
- The backend governance change is additive and guarded by explicit policy files.
- The dashboard truth rollout is narrow, tested, and does not change route ownership or business logic.

## Remaining Blocker

- Final GO is still conditional on hosted `contract-gate` and `release-verify` proof after this branch state is pushed.
