# Protected Spine Wrapper Rerun - Auth Baseline Stall-Suspect - 2026-05-29 19:47

Purpose: capture authoritative wrapper rerun state after admissions direct-command remediation.

## Runner

- Command:
  - `pwsh -NoProfile -File .\72_run_protected_spine_subbatches.ps1 -RepoRoot C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr -EvidenceRoot C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\audit-artifacts\runtime-release-closure\20260418_070051 -TimeoutSeconds 2400`
- Working directory:
  - `audit-artifacts/runtime-release-closure/20260418_070051`
- Run stamp observed:
  - `20260529_194740`

## Emitted artifacts for this stamp

- `BACKEND_PYTEST_SUBBATCH_TARGETS_auth_security_baseline_20260529_194740.txt`
- `BACKEND_PYTEST_SUBBATCH_STDOUT_auth_security_baseline_20260529_194740.txt`
- `BACKEND_PYTEST_SUBBATCH_STDERR_auth_security_baseline_20260529_194740.txt`

No `BACKEND_PYTEST_SUBBATCH_SUMMARY_auth_security_baseline_20260529_194740.*` emitted at capture time.
No downstream subbatch summaries emitted at capture time.
No protected-spine packet emitted at capture time.

## Runtime signal

- Auth stdout contains diagnostics preamble plus progress output through `........................................................................ [ 26%]` and trailing dots.
- No terminal pytest summary/footer observed before runner termination.
- Process sample during run showed active Python CPU accumulation while summary artifacts remained absent.

## Operational decision

- Runner was terminated to preserve operator control and avoid indefinite background occupancy.
- Current state classification for this rerun: `auth-security-baseline stall-suspect` under wrapper path.

## Status impact

- Direct admissions subbatch command is green (separate artifact), but authoritative wrapper closure remains OPEN.
- P0-3 remains OPEN pending authoritative wrapper packet republish + candidate-SHA policy linkage.
