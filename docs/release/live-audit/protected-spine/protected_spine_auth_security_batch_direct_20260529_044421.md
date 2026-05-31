# Protected Spine Auth/Security Direct Batch - 2026-05-29 04:44:21

Purpose: authoritative rerun evidence for the protected-spine auth/security lane after earlier interrupted/ambiguous bisect attempts.

## Command

- `.venv\Scripts\python.exe -u -m pytest backend/core/tests/test_permission_engine.py backend/core/tests/test_rbac_contract.py backend/crown_api/tests/test_auth_jwt.py backend/crown_api/tests/test_gate1c_auth_tenant_proof.py backend/crown_api/tests/test_metrics_permissions_contract.py backend/crown_api/tests/test_middleware_api_exceptions.py backend/crown_api/tests/test_object_level_permissions.py backend/crown_api/tests/test_prod_flag_guards.py backend/crown_api/tests/test_rbac_matrix_readonly.py backend/crown_api/tests/test_rbac_matrix_writes.py backend/crown_api/tests/test_rbac_proof.py backend/crown_api/tests/test_renderer_policy.py backend/crown_api/tests/test_role_escalation.py backend/crown_api/tests/test_wave3_alias_auth_parity.py backend/tests/test_tenant_bulk_ops_guard.py backend/tests/test_tenant_context_guardrails.py backend/tests/test_tenant_write_guard.py -q -x`

## Result

- Exit code: `0`
- Summary: `268 passed, 1 skipped in 173.09s (0:02:53)`
- Skip detail: `backend/crown_api/tests/test_object_level_permissions.py:272` (documented test skip path)

## Evidence Artifact

- Captured stdout: `audit-artifacts/runtime-release-closure/20260418_070051/BACKEND_PYTEST_AUTH_SECURITY_BATCH_DIRECT_20260529_044421.txt`

## Interpretation

- Auth/security protected-spine subbatch is green on this rerun.
- This supersedes the earlier interrupted timeout-only interpretation from bisect attempts.
- P0-3 remains OPEN until full protected-spine packet and policy gate packet are re-published for the candidate SHA.
