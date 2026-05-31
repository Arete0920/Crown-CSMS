# Final 95+ Sprint First-Failure Isolation Results (2026-05-31)

Status: PARTIAL PASS (evidence pack completed with focused reruns)
Evidence root: `audit-artifacts/final-95-plus-sprint/20260531_000443`

## First Failures Observed

1. Frontend lint failed (`frontend_lint_exit=1`)
   - File: `12_frontend_lint.txt`
   - Root causes:
     - `frontend/dashboards/scripts/verify-dashboard-completeness.mjs`: Node globals undefined under flat ESLint config.
     - `frontend/dashboards/src/utils/dashboardOperationalModel.js`: unused parameter `value`.
   - Focused rerun proof:
     - `12b_frontend_lint_rerun.txt`
     - `frontend_lint_rerun_exit=0`

2. Frontend RC verify failed (`frontend_rc_verify_exit=1`)
   - File: `20_frontend_rc_verify.txt`
   - Root cause:
     - Missing required env var: `VITE_BUILD_SHA`.
   - Focused rerun proof:
     - `20b_frontend_rc_verify_rerun.txt`
     - `frontend_rc_verify_rerun_exit=0`

## Backend Focused Proof Results

- `07b_tenant_isolation_diagnostic.txt`: `tenant_isolation_diag_exit=0`
- `08b_admissions_endpoints_diagnostic.txt`: `admissions_endpoints_diag_exit=0`
- `09b_aftercare_diagnostic.txt`: `aftercare_diag_exit=0`
- `10b_later_tier_metrics_diagnostic.txt`: `later_tier_metrics_diag_exit=0`

Note:
- Canonical `07_tenant_isolation.txt` and `08_admissions_endpoints.txt` are header-only due shell/session variable and streaming behavior in the initial run path.
- Diagnostic reruns above are authoritative for pass/fail until the canonical block is re-run in a single stable terminal session.

## Remaining Execution Priority Queue

1. Keep command-pack hardening changes in place (PowerShell handling + env bootstrap) to prevent false negatives.
2. Optional: regenerate strict canonical `08` and `10` with a non-pipelined runner if exact non-diagnostic filenames are required.

## Block 3 Replay Delta (20260531_071710)

Evidence root: `audit-artifacts/final-95-plus-sprint/20260531_071710`

Observed blockers during replay:

1. `Tee-Object` pipeline capture could stall and leave sparse canonical files.
2. Initial aftercare retry used an incorrect test path (`backend/aftercare/tests/test_aftercare_endpoints.py`) and failed with exit 4.

Applied tactical fixes:

1. Re-ran with verbose streamed diagnostics (`-vv -s`) for deterministic evidence.
2. Corrected aftercare target to `backend/aftercare`.

Authoritative replay outputs in this evidence root:

- `07_tenant_isolation.txt`: `tenant_isolation_exit=0`
- `08c_admissions_endpoints_diagnostic.txt`: `admissions_endpoints_diag_exit=0`
- `09c_aftercare_diagnostic.txt`: `aftercare_diag_exit=0`
- `10c_later_tier_metrics_diagnostic.txt`: `later_tier_metrics_diag_exit=0`

Current canonical-file note:

- `08_admissions_endpoints.txt` and `10_later_tier_metrics.txt` remain sparse from pipeline-capture behavior in this shell environment.
- Diagnostic files above are the reliable pass/fail source for this replay root.

## Canonical Regeneration Attempt (No-Pipeline Script)

Attempted helper:

- `scripts/execution/174_block3_canonical_capture_nopipeline.ps1`

Result:

1. Script introduced a non-pipeline capture path using `Start-Process` output redirection.
2. In this shell environment, canonical `08` still remained sparse during repeated attempts; process-level behavior showed long-running pytest workers without deterministic completion output in terminal-captured execution.
3. To preserve truth discipline, diagnostic artifacts (`08c/09c/10c`) remain the authoritative replay proof for this evidence root.

## Canonical Regeneration Attempt (CMD Runner)

Attempted helper:

- `scripts/execution/174b_block3_canonical_capture.cmd`

Result:

1. Runner executes strict sequential order (`08` then `09` then `10`) with in-file exit marker writes and first-failure stop.
2. In this environment, execution repeatedly stalled on the first canonical target (`08_admissions_endpoints.txt`) after header write; downstream files were not advanced.
3. Process cleanup was performed after stall detection, and canonical strict regeneration remains unresolved.
4. Authoritative proof remains the diagnostic reruns (`08c/09c/10c`) in the same evidence root.
