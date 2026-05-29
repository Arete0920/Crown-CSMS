# Protected Spine Hang Triage - 2026-05-29 04:27:53

Purpose: deterministic first-blocker evidence for P0-3 protected-spine rerun.

> Superseded Evidence Note (2026-05-29)
>
> This triage snapshot captured an interrupted/hung attempt and is retained for audit history only.
> Current auth/security lane truth is in:
> `docs/release/live-audit/protected-spine/protected_spine_auth_security_batch_direct_20260529_044421.md`.

## Runner

- Wrapper attempt:
  - `pwsh -File audit-artifacts/runtime-release-closure/20260418_070051/72_run_protected_spine_subbatches.ps1 -RepoRoot C:/Users/JMega/OneDrive/Desktop/Crown2026_deploypr -EvidenceRoot C:/Users/JMega/OneDrive/Desktop/Crown2026_deploypr/audit-artifacts/runtime-release-closure/20260418_070051 -TimeoutSeconds 1200`
- Direct auth/security batch attempt:
  - `.venv\Scripts\python.exe -u -m pytest backend/core/tests/test_permission_engine.py backend/core/tests/test_rbac_contract.py backend/crown_api/tests/test_auth_jwt.py backend/crown_api/tests/test_gate1c_auth_tenant_proof.py backend/crown_api/tests/test_metrics_permissions_contract.py backend/crown_api/tests/test_middleware_api_exceptions.py backend/crown_api/tests/test_object_level_permissions.py backend/crown_api/tests/test_prod_flag_guards.py backend/crown_api/tests/test_rbac_matrix_readonly.py backend/crown_api/tests/test_rbac_matrix_writes.py backend/crown_api/tests/test_rbac_proof.py backend/crown_api/tests/test_renderer_policy.py backend/crown_api/tests/test_role_escalation.py backend/crown_api/tests/test_wave3_alias_auth_parity.py backend/tests/test_tenant_bulk_ops_guard.py backend/tests/test_tenant_context_guardrails.py backend/tests/test_tenant_write_guard.py -q -x`

## Observed Behavior

- Output emitted only Django early diagnostics.
- No further per-test progress or completion lines were emitted.
- No fresh protected-spine packet was produced for run stamp `20260529_042439`.

## Evidence Pointers

- Stalled stdout capture:
  - `audit-artifacts/runtime-release-closure/20260418_070051/BACKEND_PYTEST_AUTH_SECURITY_MANUAL_20260529_042753.txt`
- Auth/security target list used:
  - `audit-artifacts/runtime-release-closure/20260418_070051/BACKEND_PYTEST_SUBBATCH_TARGETS_auth_security_baseline_20260529_042439.txt`
- Runtime triage copy in artifact folder:
  - `audit-artifacts/runtime-release-closure/20260418_070051/PROTECTED_SPINE_HANG_TRIAGE_20260529_042753.md`
- Single-test bisect summary:
  - `audit-artifacts/runtime-release-closure/20260418_070051/BACKEND_PYTEST_AUTH_SECURITY_BISECT_20260529_043903.md`

## First Blocker

- Blocker class: runtime hang/stall in auth/security baseline lane.
- First timed-out test from deterministic bisect: `backend/core/tests/test_permission_engine.py` (240s timeout).
- Gate impact: P0-3 remains OPEN and blocked until hang isolation plus fresh packet proof.

## Required Follow-up

1. Isolate root cause inside `backend/core/tests/test_permission_engine.py` with bounded fixtures/dependency checks.
2. Re-run auth/security baseline after fix and confirm completion beyond first test.
3. Re-run full protected-spine wrapper and publish fresh packet artifacts.
