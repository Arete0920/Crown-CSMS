# Protected-Spine Policy Gate Workflow Remediation (2026-05-29 20:11)

## Objective

Clear workflow-policy violations that kept the policy portion of P0-3 in a mixed state after runtime packet stamp `20260529_195922` turned green.

## Targeted edits

- `.github/workflows/accounting-verification.yml`
  - added top-level `permissions` and `concurrency` blocks.
  - added `timeout-minutes` for job.
  - pinned `actions/checkout` and `actions/setup-python`.
- `.github/workflows/deploy-prod-dispatch.yml`
  - changed top-level `concurrency.group` to unique value (`crown-api-prod-dispatch`) to remove duplicate-group violation.
  - added curl timeout guards on code-scanning probe (`--connect-timeout 10 --max-time 30`).
  - removed `continue-on-error: true` from SARIF upload step.
- `.github/workflows/deploy-prod.yml`
  - added curl timeout guards on code-scanning probe (`--connect-timeout 10 --max-time 30`).
  - removed `continue-on-error: true` from SARIF upload step.
- `.github/workflows/full-surface-verification.yml`
  - added top-level `permissions` and `concurrency` blocks.
  - pinned `actions/checkout`, `actions/setup-node`, and `actions/upload-artifact`.

## Verification commands and results

1. Workflow policy gate

Command:

`.venv/Scripts/python.exe tools/verify_workflow_policy.py`

Result:

- `Workflow policy checks passed.`

1. Public surface policy gate (fresh paired rerun)

Command:

`.venv/Scripts/python.exe tools/verify_public_surface_policy.py`

Result:

- `Public surface policy gate PASSED`
- `AllowAny entries tracked: 16`
- `csrf_exempt entries tracked: 19`

## Status impact

- Runtime protected-spine packet for `20260529_195922` is already GREEN.
- Policy gates are now GREEN in fresh reruns (workflow + public surface).
- P0-3 is operationally green on runtime/policy checks, but remains OPEN until candidate-SHA linkage is finalized through deploy parity authority closure (P0-1/P0-2 dependency chain).
