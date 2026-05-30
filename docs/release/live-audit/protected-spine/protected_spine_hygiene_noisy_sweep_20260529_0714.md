# Protected Spine Hygiene + Noisy Sweep - 2026-05-29 07:14

Purpose: perform an evidence-first hygiene/noise sweep to confirm runtime cleanliness and isolate noisy integrity failures without broad refactor.

## Scope

- Working-tree hygiene snapshot (non-destructive).
- Process hygiene verification (no stale protected-spine runners left active).
- Admissions noisy-path isolation by deterministic chunk and file-level reruns.
- Cleanup of hung pytest processes after isolation.

## Findings

1. Repository hygiene baseline is mixed (expected for in-flight release closure): multiple tracked docs/code modifications and untracked evidence docs are present; no destructive cleanup was performed.
2. Merge-conflict marker sweep found no unresolved conflict markers in code/document source files.
3. Admissions subbatch noise is reproducible outside wrapper context:
   - Combined admissions command (`nav + health + 51x51 + health_demo + nurse_api + nurse_negative + nurse_unit`) enters long-running state with no completion footer while Python child CPU rises.
4. Deterministic narrowing:
   - Chunk A (`test_nav_endpoint.py`, `test_health.py`, `test_51x51_evidence_33_nurse_office___health_office.py`, `test_health_demo_mode.py`) is clean: `18 passed in 8.77s`.
   - `test_nurse_health_office_api.py` is clean: `6 passed in 10.81s`.
   - `test_nurse_health_office_negative.py` is clean: `6 passed in 7.88s`.
   - `test_nurse_health_office_unit.py` is stall-suspect in isolation: process remains alive, CPU rises, no terminal pytest summary emitted during observation window.
5. A prior script-level noise source was reconfirmed: `Start-Process` + timeout probes can produce false timeout classification when the parent shim process persists after pytest output indicates pass.

## What Was Addressed

1. Process cleanup performed after each noisy stall reproduction:
   - terminated stale combined admissions run PIDs.
   - terminated isolated `test_nurse_health_office_unit.py` stall PIDs.
2. Runtime state returned to clean operational posture (no intentionally left hung admissions/wrapper process from this sweep).
3. Blocker precision improved from broad admissions stall to file-level suspect:
   - current deterministic suspect module: `backend/tests/test_nurse_health_office_unit.py`.
4. Canonical release status and P0 execution board were updated to reflect this hygiene sweep delta and narrowed first-blocker evidence.

## Commands Executed (Representative)

- `git status --short`
- `Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match '72_run_protected_spine_subbatches\.ps1|...admissions...' }`
- `rg -n "^<<<<<<<|^=======|^>>>>>>>" **/*.{py,ps1,md,json,yml,yaml,ts,tsx,js,jsx}`
- `python -u -m pytest backend/core/tests/test_nav_endpoint.py backend/crown_api/tests/test_health.py backend/tests/test_51x51_evidence_33_nurse_office___health_office.py backend/tests/test_health_demo_mode.py -q -x --nomigrations`
- `python -u -m pytest backend/tests/test_nurse_health_office_api.py -q -x --nomigrations`
- `python -u -m pytest backend/tests/test_nurse_health_office_negative.py -q -x --nomigrations`
- `python -u -m pytest backend/tests/test_nurse_health_office_unit.py -q -x --nomigrations`
- targeted `Stop-Process -Id <pid> -Force` cleanup for hung runs.

## Current Classification After Sweep

- P0-3 remains OPEN.
- Admissions first-blocker is now narrowed to a deterministic file-level stall-suspect (`test_nurse_health_office_unit.py`) pending root-cause fix and green rerun packet.
