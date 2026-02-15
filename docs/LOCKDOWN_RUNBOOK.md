# Lockdown Runbook (Golden Path)

This runbook is the operator-only procedure for rehearsal/demo stability.
No architecture notes. No optional paths.

## Green Path (the only normal workflow)

1) Seed the lockdown minimum dataset (idempotent)
   - From DEMO_TAG backend:
     - `python manage.py seed_lockdown_minimal --count 10`

2) Boot + proof gate (must be green)
   - `tools/dev_scripts/demo_one_click.ps1`

3) Golden Path contract gate (must be green)
   - `tools/dev_scripts/golden_path_gate.ps1`

4) Discipline check
   - Run Golden Path gate **3 times**
   - Requirement: `GREEN_3X=YES`

5) Checkpoint tag (only after GREEN_3X)
   - Create + push: `lockdown-goldenpath-greenN`

## Red Path (what to do when gate fails)

When `golden_path_gate.ps1` fails:
- Do NOT “try random fixes”.
- Fix ONLY the failing `REASON=<TOKEN>`.

### Immediate triage rule
- If gate fails, the wrapper automatically runs `demo_snapshot.ps1`.
- Use the snapshot output to confirm:
  - Ports 8000/3000 owners
  - `/health/` JSON (demo_mode, build_sha)
  - current DEMO_TAG SHA

## Token-to-fix mapping (examples)

- `CTX_MISSING_SCHOOL_ID` / `CTX_MISSING_YEAR_ID`
  - Run `seed_lockdown_minimal` again.
  - Confirm env vars exist in User scope or pass explicit args.

- `HEALTH_HTTP_FAIL`
  - Backend not running on 8000 or wrong owner. Use snapshot.

- `HEALTH_BUILD_SHA_INVALID`
  - Backend started without a real SHA. Re-run `demo_one_click.ps1`.

- `ADM_*`
  - Admissions seed missing. Re-run `seed_lockdown_minimal`.

- `AID_*` / `REG_*` / `FIN_*`
  - Relevant demo seed missing OR regression in endpoint contract.
  - Fix only what the token indicates.

## Non-negotiables
- No feature work while Golden Path is red.
- No “pretty UI” changes until Golden Path is green 3x again.
