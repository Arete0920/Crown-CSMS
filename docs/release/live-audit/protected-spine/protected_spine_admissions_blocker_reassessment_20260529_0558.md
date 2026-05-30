# Protected-Spine Admissions Blocker Reassessment (2026-05-29 05:58)

Purpose: supersede the earlier deterministic timeout claim for `backend/core/tests/test_nav_endpoint.py` and record corrected evidence.

## What Changed

An earlier isolation harness used this pattern:

- `if (-not ($p | Wait-Process -Timeout ... -ErrorAction SilentlyContinue)) { ... timeout ... }`

`Wait-Process` without `-PassThru` does not return the process object, so that expression can misclassify completion state.

## Corrected Probe (Clean State)

Command:

- `.venv\Scripts\python.exe -u -m pytest backend/core/tests/test_nav_endpoint.py -q -x --nomigrations`

Observed result (clean state after killing overlapping wrapper/pytest workers):

- `11 passed in 10.08s`
- process exited normally
- `EXIT_CODE=0`

## Current Interpretation

- The prior claim that `test_nav_endpoint.py` deterministically "passes then hangs" is superseded.
- Protected-spine packet stamp `20260529_045703` still reports first blocker `admissions-applications` with `proof_runner_error`, but this reassessment does not confirm nav endpoint as root cause.
- Root cause for admissions `proof_runner_error` is currently unresolved and requires a fresh clean wrapper-complete packet for authoritative classification.

## Release Impact

- P0-3 remains OPEN.
- Runtime packet for stamp `20260529_045703` remains RED.
- Continue with clean authoritative rerun and use only corrected timeout instrumentation (`Wait-Process -PassThru` or explicit post-wait exit checks) for any further isolation artifacts.
