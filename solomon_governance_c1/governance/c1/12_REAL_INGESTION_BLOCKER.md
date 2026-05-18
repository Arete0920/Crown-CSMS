# C1 Real Ingestion Blocker

Status: enforced blocker.

This document defines the mandatory guardrail for any script named or behaving
as real ingestion execution.

## Canonical Entrypoint

`c1_dry_run_ingestion_executor.py`

This is the only canonical dry-run/blocker execution path.

## Deprecated Compatibility Guard

`execute_c1_real_ingestion.py`

This file is retained only to prevent accidental direct use.
Behavior:

- prints: `Use c1_dry_run_ingestion_executor.py`
- exits nonzero

## Mandatory Preconditions

Execution must refuse unless all conditions are true:

1. Activation gate decision is `ALLOW`.
2. Explicit `--execute-real-ingestion` flag is present.
3. Secondary confirmation token is valid.
4. Output target is isolated.
5. Rollback manifest is generated first.

## Current Policy State

Real ingestion is still disabled.

Even when all preconditions pass, execution remains blocked by policy.

This preserves fail-closed behavior while proving preflight guardrails are executable.
