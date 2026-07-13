# Production Deploy Failure Packet

- Run: 29202250977
- Job: 86675495870
- Workflow: Production Deploy
- SHA: cf19d31c3b6a3269f4196904dc46a2b2663b1421
- Disposition: COMPLETED / FAILURE

## First Failing Test Blocker

First pytest failure block begins at log line 4495 and first failed test entry is:

- crown_api/dashboards/tests/test_dashboard_auth_fallback.py::test_dev_open_does_not_bypass_tenant_in_production
- Assertion: expected 400, got 401

Additional key auth/tenant contract failures show endpoints returning 200 where 401/403 or 400 were expected.

## Failing Test IDs (12)

1. crown_api/dashboards/tests/test_dashboard_auth_fallback.py::test_dev_open_does_not_bypass_tenant_in_production
2. crown_api/dashboards/tests/test_dashboard_auth_fallback.py::test_production_mode_never_auto_creates_demo_school
3. crown_api/tests/test_dashboards_role_contract.py::test_unauthenticated_returns_401[/api/dashboards/me/]
4. crown_api/tests/test_dashboards_role_contract.py::test_unauthenticated_returns_401[/api/dashboards/summary/]
5. crown_api/tests/test_dashboards_role_contract.py::test_unauthenticated_returns_401[/api/dashboards/drilldown/?widget=alerts_flip]
6. crown_api/tests/test_dashboards_role_contract.py::test_unauthenticated_returns_401[/api/dashboards/alerts/]
7. crown_api/tests/test_dashboards_role_contract.py::test_missing_school_header_returns_400[/api/dashboards/me/]
8. crown_api/tests/test_dashboards_role_contract.py::test_missing_school_header_returns_400[/api/dashboards/summary/]
9. crown_api/tests/test_dashboards_role_contract.py::test_missing_school_header_returns_400[/api/dashboards/drilldown/?widget=alerts_flip]
10. crown_api/tests/test_dashboards_role_contract.py::test_missing_school_header_returns_400[/api/dashboards/alerts/]
11. crown_api/tests/test_wave3_alias_auth_parity.py::test_canonical_and_alias_dashboard_me_require_auth
12. crown_api/tests/test_wave3_alias_auth_parity.py::test_canonical_and_alias_dashboard_summary_missing_tenant_header

## Aggregate Pytest Result

- 12 failed, 3510 passed, 10 skipped, 2 warnings
- Test step exited with code 1

## Rollback Defect Evidence

Rollback step executed after test failure (before deployment), then forced failure via explicit `exit 1`.

- Step name: Rollback on failure
- Script behavior:
  - echo "ERROR: Deployment failed - rolling back"
  - exit 1

This confirms rollback logic is not bounded to "deployment actually occurred" and introduces a secondary failure signal.

## Workflow Defect Location

Workflow file contains unconditional rollback-fail body under `if: failure()`:

- .github/workflows/deploy-prod.yml
- Step: Rollback on failure
- Body includes explicit `exit 1`

## Notes

- Azure deployment step was skipped in this failed run.
- BUILD_SHA appsetting verification, health check, tenant-aware integrity check, and release identity verification were skipped.
- Production runtime parity against cf19d31... remains unproven and must not be certified from this run.
