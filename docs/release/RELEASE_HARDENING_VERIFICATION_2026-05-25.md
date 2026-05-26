# Release Hardening Verification (2026-05-25)

## Scope
This document captures the release-hardening verification pass for:
- Production deployment identity parity
- Route boundary guards for teacher/parent aliases
- SARIF upload gating behavior in production workflows
- Contract test reliability after logo lockup migration

## Runtime Integration Status
- Backend production health endpoint: `https://crown-api-prod.azurewebsites.net/api/health/`
  - `ok=true`
  - `env=prod`
  - `build_sha=67178535a4bb6bf494d2aef90948f3c4fa5b47e4`
  - `deploy_workflow=Production Deploy`
- Frontend production build endpoint: `https://yellow-forest-0eecc8b0f.7.azurestaticapps.net/build.json`
  - `build_sha=67178535a4bb6bf494d2aef90948f3c4fa5b47e4`
- Cross-surface parity: matched (frontend SHA == backend SHA)

## CI Integration Status
- Proof Ceremony run for latest release branch commit:
  - Run: `26424856306`
  - Result: `success`
  - URL: `https://github.com/tcmegahan/Crown2026/actions/runs/26424856306`

## Tests Executed
### Frontend
- `npm run test:contracts`
- `npm run test -- src/tests/releaseHardeningContracts.test.jsx`
- Result: PASS

### Backend
- `pytest tests/test_release_hardening_workflow_contracts.py backend/crown_api/tests/test_health.py backend/crown_api/tests/test_rbac_proof.py backend/crown_api/tests/test_dashboards_role_contract.py -q`
- Result: PASS (`38 passed`)

## Edge Cases and Vulnerabilities Reviewed
1. Workflow SHA identity drift between dispatch and tag-push lanes
- Mitigation in place: release identity checks now use deploy SHA output.

2. SARIF upload hard-disable causing silent security signal loss
- Mitigation in place: conditional gate probes code-scanning availability and uploads when available.

3. Route boundary regressions for alias paths
- Mitigation in place: explicit RoleGuard coverage for:
  - `/teacher/attendance`
  - `/teacher`
  - `/teacher/dashboard`
  - `/parent/attendance`

4. Test fragility after brand logo migration (text-node assumptions)
- Mitigation in place: contract tests now assert logo alt text instead of brittle raw text nodes.

## Remaining Watch Items
1. Negative-path API tests intentionally generate warning logs (`Unauthorized`, `Bad Request`, `Not Found`).
- Expected in test context; monitor for unexpected increases in production logging noise.

2. One observed local test warning showed a slow `/health/` request (~1.3s) during pytest.
- Not a failure; monitor trend under production load and consider alert threshold tuning.

## Integrity Statement
- Code, tests, and CI verification are consistent with current release hardening objectives.
- No unresolved dirty working-tree noise should remain after commit/push.
