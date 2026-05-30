# Protected Spine Auth Wrapper Divergence - 2026-05-29 20:00

Purpose: capture deterministic evidence that auth-security baseline product tests pass directly while wrapper execution intermittently remains indeterminate/stall-suspect.

## Direct command verification (product lane)

- Command:
  - `.venv/Scripts/python.exe -u -m pytest backend/core/tests/test_permission_engine.py backend/core/tests/test_rbac_contract.py backend/crown_api/tests/test_auth_jwt.py backend/crown_api/tests/test_gate1c_auth_tenant_proof.py backend/crown_api/tests/test_metrics_permissions_contract.py backend/crown_api/tests/test_middleware_api_exceptions.py backend/crown_api/tests/test_object_level_permissions.py backend/crown_api/tests/test_prod_flag_guards.py backend/crown_api/tests/test_rbac_matrix_readonly.py backend/crown_api/tests/test_rbac_matrix_writes.py backend/crown_api/tests/test_rbac_proof.py backend/crown_api/tests/test_renderer_policy.py backend/crown_api/tests/test_role_escalation.py backend/crown_api/tests/test_wave3_alias_auth_parity.py backend/tests/test_tenant_bulk_ops_guard.py backend/tests/test_tenant_context_guardrails.py backend/tests/test_tenant_write_guard.py -q -x --nomigrations`
- Result:
  - `268 passed, 1 skipped in 137.23s (0:02:17)`

Interpretation:
- auth-security baseline product tests are green under direct execution.

## Wrapper divergence observations

- Wrapper stamp `20260529_194740` remained in auth progress output without summary/footer emission at capture (`26%` then trailing dots).
- Wrapper stamp `20260529_195100` eventually emitted auth summary and moved to tenant stage before manual termination of overlapping runner instance.
- Wrapper stamp `20260529_195554` was started during a process-execution experiment and then terminated; this run is non-authoritative.

## Integrity correction

- A cmd.exe execution experiment was applied briefly to `72_run_protected_spine_subbatches.ps1` and then reverted in the same session after detecting malformed quoting risk.
- Canonical runner logic is restored to the prior known behavior (python Start-Process with stdout/stderr redirection).

## Status impact

- Auth baseline should be treated as product-green by direct evidence.
- Current blocker remains authoritative wrapper packet freshness/continuity (runtime orchestration stability), not auth product-test failure.
- P0-3 remains OPEN pending stable wrapper packet republish plus candidate-SHA policy linkage.
