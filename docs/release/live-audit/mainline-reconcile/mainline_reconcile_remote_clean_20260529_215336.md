# Mainline Reconcile Remote-Clean Evidence (2026-05-29 22:06:17)

Purpose: record completion of a fresh remote-clean `97_mainline_reconcile` run after first-blocker queue closure and environment bootstrap in the remote clone.

## Runner Context

- Runner location: `C:/Users/JMega/OneDrive/Desktop/Crown2026_remotecleanclone`
- Command: `powershell -ExecutionPolicy Bypass -File .\scripts\execution\97_mainline_reconcile.ps1`
- Terminal result: completed with `DONE` and emitted summary/latest paths.

## Packet Paths

- Summary packet:
  - `C:/Users/JMega/OneDrive/Desktop/Crown2026_remotecleanclone/audit-artifacts/mainline-reconcile/20260529_215336/00_SUMMARY.md`
- Latest mirror summary:
  - `C:/Users/JMega/OneDrive/Desktop/Crown2026_remotecleanclone/audit-artifacts/mainline-reconcile/latest/00_SUMMARY.md`
- Supporting packet files:
  - `C:/Users/JMega/OneDrive/Desktop/Crown2026_remotecleanclone/audit-artifacts/mainline-reconcile/20260529_215336/10_pr_status.json`
  - `C:/Users/JMega/OneDrive/Desktop/Crown2026_remotecleanclone/audit-artifacts/mainline-reconcile/20260529_215336/20_failed_runs_before.csv`
  - `C:/Users/JMega/OneDrive/Desktop/Crown2026_remotecleanclone/audit-artifacts/mainline-reconcile/20260529_215336/21_failed_runs_after.csv`
  - `C:/Users/JMega/OneDrive/Desktop/Crown2026_remotecleanclone/audit-artifacts/mainline-reconcile/20260529_215336/30_check_results.csv`

## Extracted Outcomes

From `00_SUMMARY.md`:

- Starting head: `f8549068891aa91b0a34b4bf52001ffa030fd3d7`
- Main head after sync: `d22fabb685f501928ecc39b8732e2b6ac86cea49`
- Target PR: `#733` (merged)
- Failed workflow groups before rerun: `8`
- Failed workflow groups after rerun not green: `0`
- Local check failures: `6`
- Dirty count after reconciliation: `0`
- Latest scorecard overall: `9 / 10`

From `30_check_results.csv`:

- Passed (`3`):
  - `95_live_scorecard_audit_baseline`
  - `95_live_scorecard_audit_deep`
  - `frontend_shell_contracts`
- Failed (`6`):
  - `frontend_unit`
  - `frontend_release_a11y`
  - `frontend_nav`
  - `frontend_release_routes`
  - `backend_reporting_exports_gate`
  - `backend_django_check`

From workflow rerun reconciliation files:

- `20_failed_runs_before.csv` contained `8` failed workflow groups.
- `21_failed_runs_after.csv` returned `Notice=none`.

## First Signatures from Failing Local Checks

- `frontend_unit`:
  - vitest suite ran, then terminated with `ERROR: System.Management.Automation.RemoteException`.
  - one test was marked failed in visible output before termination (`src/tests/sandboxCommandCenter.test.jsx`).
- Playwright suites (`frontend_release_a11y`, `frontend_nav`, `frontend_release_routes`):
  - each failed with WebServer bootstrap signature (`ERROR: [WebServer]` / `[WebServer]`).
- `backend_reporting_exports_gate`:
  - setup failed with `sqlite3.OperationalError: no such table: spiritual_life_portraitdomain`.
  - pytest summary: `8 errors in 91.48s`.
- `backend_django_check`:
  - failed with `SystemCheckError: System check identified some issues:`.
  - this packet's log does not include expanded issue detail lines after the headline.

## Integrity Notes

- This run is authoritative for remote-clean reconcile stamp `20260529_215336` and supersedes in-flight partial attempts.
- This evidence confirms packet generation success (`DONE`) with improved scorecard (`9/10`) but non-zero local check failures (`6`).
- This evidence does not change canonical release authority posture for the approved slice.
