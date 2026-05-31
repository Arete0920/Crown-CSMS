# Mainline Reconcile Remote-Clean Delta (2026-05-29 22:39:55)

Purpose: capture a fresh authoritative `97_mainline_reconcile` run on a clean remote-clean worktree after first-blocker closure work.

## Command

- `powershell -ExecutionPolicy Bypass -File .\scripts\execution\97_mainline_reconcile.ps1`
- repo: `C:/Users/JMega/OneDrive/Desktop/Crown2026_remotecleanclone`
- run stamp: `20260529_222723`

## Packet outputs

- summary: `audit-artifacts/mainline-reconcile/20260529_222723/00_SUMMARY.md`
- checks: `audit-artifacts/mainline-reconcile/20260529_222723/30_check_results.csv`
- latest mirror: `audit-artifacts/mainline-reconcile/latest/00_SUMMARY.md`

## Summary highlights

- failed workflow groups before rerun: `8`
- failed workflow groups after rerun not green: `0`
- local check failures: `6`
- dirty count after reconciliation: `0`
- latest scorecard overall: `9 / 10`
- main head after sync: `d22fabb685f501928ecc39b8732e2b6ac86cea49`

## Local check truth table

- pass (`3`):
  - `95_live_scorecard_audit_baseline`
  - `95_live_scorecard_audit_deep`
  - `frontend_shell_contracts`
- fail (`6`):
  - `frontend_unit`
  - `frontend_release_a11y`
  - `frontend_nav`
  - `frontend_release_routes`
  - `backend_reporting_exports_gate`
  - `backend_django_check`

## First failure signatures captured

- `frontend_unit`: `ERROR: System.Management.Automation.RemoteException`
- `frontend_release_a11y`: `ERROR: [WebServer]`
- `frontend_nav`: `[WebServer]`
- `frontend_release_routes`: `ERROR: [WebServer]`
- `backend_reporting_exports_gate`: `EEEEEEEE` with setup trace selecting from `spiritual_life_portraitdomain`.
- `backend_django_check`: `ERROR: SystemCheckError: System check identified some issues:`

## Integrity note

- This clean reconcile run was executed with a clean worktree gate, which required temporary stashing of local blocker-fix edits in the remote-clean clone.
- Therefore this packet reflects the current clean mainline state at synced head, not the local patched closure lane.
- Local patched reruns remain recorded separately in:
  - `docs/release/live-audit/mainline-reconcile/mainline_reconcile_first_blocker_closure_20260529_2239.md`
