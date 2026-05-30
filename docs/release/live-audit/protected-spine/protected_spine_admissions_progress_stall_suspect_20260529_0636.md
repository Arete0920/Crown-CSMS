# Protected-Spine Admissions Progress Stall Suspect (2026-05-29 06:36)

Purpose: capture current rerun state for stamp `20260529_061936` where admissions remains process-active but has not emitted a summary or packet.

## Current Stage

- Wrapper process remains active:
  - PID `14980`
  - command: `pwsh -NoProfile -File .\72_run_protected_spine_subbatches.ps1 ... -TimeoutSeconds 2400`
- Admissions subbatch process tree remains active:
  - parent pytest PID `18304`
  - worker pytest PID `22108`
  - admissions command:
    - `python -u -m pytest backend/core/tests/test_nav_endpoint.py backend/crown_api/tests/test_health.py backend/tests/test_51x51_evidence_33_nurse_office___health_office.py backend/tests/test_health_demo_mode.py backend/tests/test_nurse_health_office_api.py backend/tests/test_nurse_health_office_negative.py backend/tests/test_nurse_health_office_unit.py -q -x --nomigrations`

## Observations

- Admissions stdout artifact exists:
  - `BACKEND_PYTEST_SUBBATCH_STDOUT_admissions_applications_20260529_061936.txt`
- Stdout content remains at diagnostics + progress dots with no pytest footer.
- Stdout file length remained flat across recent checks at `517` bytes.
- Worker CPU continued rising during same window (example snapshot progression):
  - `~402.19` -> `~404.09` -> `~415.30`

## Not Yet Emitted

- `BACKEND_PYTEST_SUBBATCH_SUMMARY_admissions_applications_20260529_061936.md/.json`
- `BACKEND_PYTEST_PROTECTED_SPINE_SUBBATCH_PACKET_20260529_061936.md/.json`

## Classification (Current)

- This is currently a `stall-suspect` state rather than proven hard failure:
  - process activity remains real,
  - output channel has not advanced to completion artifacts.

## Next Action

- Continue monitored polling for admissions summary/packet emission.
- If emission does not occur and process exits non-productively, publish superseding blocker artifact with final runner outcome classification.
