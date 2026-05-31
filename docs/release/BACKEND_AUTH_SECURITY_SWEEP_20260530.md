# Backend Auth and Security Sweep - 2026-05-30

## Scope

- Priority 35: auth token-proof verification sweep
- Priority 36: backend settings posture and deploy-check sweep
- Priority 42 support: backend API contract surface verification linkage

## Commands and Results

- Backend auth proof tests

- Command: `python -m pytest crown_api/tests/test_auth_jwt.py crown_api/tests/test_gate1c_auth_tenant_proof.py -q --nomigrations`
- Artifact: `audit-artifacts/runtime-release-closure/20260418_070051/auth_token_proof_sweep_20260530.txt`
- Result: `11 passed in 13.55s`

- Backend deploy posture check

- Command: `python manage.py check --deploy`
- Artifact: `audit-artifacts/runtime-release-closure/20260418_070051/backend_deploy_check_20260530.txt`
- Result: command completed successfully; warnings observed were schema/documentation-type warnings from drf-spectacular, not permissive CORS/debug flag violations.

- Security posture extraction from settings

- Command: regex extraction on `backend/crown_api/settings.py`
- Artifact: `audit-artifacts/runtime-release-closure/20260418_070051/settings_security_posture_20260530.txt`
- Key findings:

  - `DEBUG` is environment-gated, not hard-enabled.
  - `CORS_ALLOW_ALL_ORIGINS` defaults to `False`.
  - Production guard `_assert_not_prod_true` blocks dangerous flags when `DEBUG=False`.

## Frontend-to-Backend Availability Verification

- Command: `npm run verify:api-contracts`
- Artifact: `audit-artifacts/runtime-release-closure/20260418_070051/frontend_api_contracts_verify_20260530.txt`
- Result: `API CONTRACT VERIFY PASS`

- Command: `npm run verify:navigation`
- Artifact: `audit-artifacts/runtime-release-closure/20260418_070051/frontend_navigation_verify_20260530.txt`
- Result: `NAV VERIFY PASS`

## Conclusion

- Priority 35: resolved with passing auth token-proof suite.
- Priority 36: resolved for current branch evidence lane; no permissive CORS/debug failure signal found.
- Priority 42: resolved with passing API contract and navigation verification.
