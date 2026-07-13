# Minimal Patch Proposal (Not Applied)

Run: 29202250977
Scope: fix first real blocker (dashboard auth/tenant contract) and bound rollback failure behavior.
Policy: smallest safe diff, no deployment rerun in this step.

## 1) First-blocker fix lane (dashboard auth and tenant contract)

### Observed failure pattern
- Unauthenticated dashboard endpoints returned 200 where tests require 401/403.
- Authenticated requests missing X-School-Id returned 200 where tests require 400.
- Summary from failed run:
  - 12 failed, 3510 passed, 10 skipped.

### Minimal implementation target
Primary file:
- backend/crown_api/dashboards/views.py

Supporting context:
- backend/crown_api/dashboards/tenant.py
- backend/crown_api/tests/test_dashboards_role_contract.py
- backend/crown_api/tests/test_wave3_alias_auth_parity.py
- backend/crown_api/dashboards/tests/test_dashboard_auth_fallback.py

### Proposed code changes (minimal)
1. Dev-open default should fail-closed unless explicitly enabled:
- In backend/crown_api/settings.py, change CROWN_DEV_OPEN_API default from open-by-default on non-Azure to default false.
- Keep explicit env override behavior intact.

2. Keep role-contract endpoints auth-first in production-like/runtime CI lanes:
- Continue requiring authentication for:
  - /api/dashboards/me/
  - /api/dashboards/summary/
  - /api/dashboards/drilldown/
  - /api/dashboards/alerts/
- Ensure missing X-School-Id on authenticated calls returns 400 via strict tenant resolver.

3. Eliminate fallback behavior that can return 200 without explicit tenant in contract paths:
- For contract endpoints above, do not allow dev-open tenant fallback to auto demo school when header is missing.

### Expected result after patch
- Unauthenticated + header: 401/403 (never 200)
- Authenticated + missing header: 400
- Authenticated + invalid UUID: 400
- Authenticated + nonexistent school: 404
- Valid authenticated + correct tenant: 200

## 2) Rollback guard defect lane (workflow behavior)

Primary file:
- .github/workflows/deploy-prod.yml

Current defect
- Rollback step is triggered by generic failure() and then forces exit 1.
- This creates a secondary failure even when deployment step never ran.

### Proposed workflow changes (minimal)
1. Add id to deploy step:
- Step: Deploy to Azure Web App
- Add id: deploy_webapp

2. Bound rollback step to actual deploy-step failure only:
- Change condition from:
  - if: failure()
- To:
  - if: ${{ failure() && steps.deploy_webapp.outcome == 'failure' }}

3. Remove unconditional forced failure in rollback body:
- Replace explicit exit 1 with bounded rollback logging/actions.
- If no concrete rollback action exists, log and exit 0 to avoid false secondary failure signal.

## 3) Test/validation order after applying patch (future lane)

Run only focused contract tests first:
1. backend/crown_api/tests/test_dashboards_role_contract.py
2. backend/crown_api/tests/test_wave3_alias_auth_parity.py
3. backend/crown_api/dashboards/tests/test_dashboard_auth_fallback.py

Then execute production deploy workflow again only after focused tests pass and rollback guard patch is in place.

## 4) Decision gate

Do not recapture parity or run production certification until:
- Focused dashboard auth/tenant contract tests are green.
- Rollback guard is bounded to deploy-step failure.
- A new deploy run reaches deployment and post-deploy identity checks.
