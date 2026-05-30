# Protected-Spine Authoritative Packet + Policy Delta (2026-05-29 20:09)

## Runtime command (authoritative wrapper)

`pwsh -NoProfile -File .\72_run_protected_spine_subbatches.ps1 -RepoRoot C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr -EvidenceRoot C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\audit-artifacts\runtime-release-closure\20260418_070051 -TimeoutSeconds 600`

Run stamp: `20260529_195922`

## Runtime packet outputs

- `audit-artifacts/runtime-release-closure/20260418_070051/BACKEND_PYTEST_PROTECTED_SPINE_SUBBATCH_PACKET_20260529_195922.json`
- `audit-artifacts/runtime-release-closure/20260418_070051/BACKEND_PYTEST_PROTECTED_SPINE_SUBBATCH_PACKET_20260529_195922.md`

## Runtime packet result

- `blocked=false`
- `proof_runner_failures=0`
- `product_test_failures=0`
- Sub-batch results:
  - `auth-security-baseline`: `268 passed, 1 skipped in 132.44s (0:02:12)`
  - `tenant-isolation-scoping`: `266 passed in 329.46s (0:05:29)`
  - `audit-security-baseline`: `17 passed in 95.79s (0:01:35)`
  - `admissions-applications`: `34 passed in 34.86s`

## Policy gate reruns

### Public surface policy

Command:

`.venv/Scripts/python.exe tools/verify_public_surface_policy.py`

Result:

- `Public surface policy gate PASSED`
- `AllowAny entries tracked: 16`
- `csrf_exempt entries tracked: 19`

### Workflow policy

Command:

`.venv/Scripts/python.exe tools/verify_workflow_policy.py`

Result:

- `Workflow policy violations detected` (14 findings), including missing top-level permissions/concurrency blocks, unpinned `uses` references, `continue-on-error: true`, and missing curl timeout guards in deployment workflows.

## Status interpretation

- Runtime protected-spine authoritative republish is GREEN for stamp `20260529_195922`.
- Policy is mixed: public-surface policy is GREEN; workflow policy remains RED.
- P0-3 remains OPEN until policy gate expectations are satisfied and linked in release authority.
