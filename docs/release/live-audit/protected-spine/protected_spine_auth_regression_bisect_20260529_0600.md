# Protected-Spine Auth Regression Bisect (2026-05-29 06:00)

Purpose: capture current first blocker after fresh wrapper reruns (`20260529_055342`, `20260529_055745`) failed to produce any new subbatch summaries.

## Context

- Prior completed wrapper packet stamp `20260529_045703` exists and is RED with admissions proof-runner failure.
- Two subsequent wrapper attempts were started (`055342`, `055745`) and both stalled in `auth-security-baseline` before any new summary/packet file emission.

## Deterministic Isolation Method

- Auth-security target files were run one-by-one with corrected timeout handling:
  - `Start-Process ... pytest <single-file> -q -x`
  - `Wait-Process -PassThru -Timeout 240`
  - classify timeout only when `Wait-Process` throws timeout and process remains live.

## Result

- First deterministic blocker in current rerun state:
  - `backend/core/tests/test_permission_engine.py`
  - outcome: `TIMEOUT` at 240s.

## Interpretation

- Current fresh rerun blocker is back in auth-security baseline at `test_permission_engine.py`.
- This supersedes any attempt to treat nav endpoint as deterministic first blocker for current rerun state.

## Release Impact

- P0-3 remains OPEN.
- No new authoritative wrapper packet beyond stamp `20260529_045703` has been produced.
- Next required action: stabilize/resolve `backend/core/tests/test_permission_engine.py` timeout path, then rerun full wrapper and republish packet with policy-gate linkage.
