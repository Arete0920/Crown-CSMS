# Mainline Reconcile Remote-Clean Evidence (2026-05-29 21:22:50)

Purpose: record successful execution of `scripts/execution/97_mainline_reconcile.ps1` from a remote-clean clone after repeated local/worktree cleanliness drift.

## Runner Context

- Runner location: `C:/Users/JMega/OneDrive/Desktop/Crown2026_remotecleanclone`
- Command: `powershell -ExecutionPolicy Bypass -File .\scripts\execution\97_mainline_reconcile.ps1`
- Terminal result: completed with `DONE` and emitted summary/latest paths.

## Packet Paths

- Summary packet:
  - `C:/Users/JMega/OneDrive/Desktop/Crown2026_remotecleanclone/audit-artifacts/mainline-reconcile/20260529_212250/00_SUMMARY.md`
- Latest mirror summary:
  - `C:/Users/JMega/OneDrive/Desktop/Crown2026_remotecleanclone/audit-artifacts/mainline-reconcile/latest/00_SUMMARY.md`
- Supporting packet files:
  - `C:/Users/JMega/OneDrive/Desktop/Crown2026_remotecleanclone/audit-artifacts/mainline-reconcile/20260529_212250/10_pr_status.json`
  - `C:/Users/JMega/OneDrive/Desktop/Crown2026_remotecleanclone/audit-artifacts/mainline-reconcile/20260529_212250/20_failed_runs_before.csv`
  - `C:/Users/JMega/OneDrive/Desktop/Crown2026_remotecleanclone/audit-artifacts/mainline-reconcile/20260529_212250/21_failed_runs_after.csv`
  - `C:/Users/JMega/OneDrive/Desktop/Crown2026_remotecleanclone/audit-artifacts/mainline-reconcile/20260529_212250/30_check_results.csv`

## Extracted Outcomes

From `00_SUMMARY.md`:

- Starting head: `f8549068891aa91b0a34b4bf52001ffa030fd3d7`
- Main head after sync: `d22fabb685f501928ecc39b8732e2b6ac86cea49`
- Target PR: `#733` (merged)
- Failed workflow groups before rerun: `8`
- Failed workflow groups after rerun not green: `0`
- Local check failures: `7`
- Dirty count after reconciliation: `0`
- Latest scorecard overall: `8 / 10`

From `30_check_results.csv`:

- Passed (`2`):
  - `95_live_scorecard_audit_baseline`
  - `95_live_scorecard_audit_deep`
- Failed (`7`):
  - `frontend_shell_contracts`
  - `frontend_unit`
  - `frontend_release_a11y`
  - `frontend_nav`
  - `frontend_release_routes`
  - `backend_reporting_exports_gate`
  - `backend_django_check`

From workflow rerun reconciliation files:

- `20_failed_runs_before.csv` contained `8` failed workflow groups.
- `21_failed_runs_after.csv` returned `Notice=none`.

## Integrity Notes

- This evidence is authoritative for reconcile packet generation success in the remote-clean clone context.
- This evidence does **not** supersede canonical release authority documents.
- Repeated cleanliness drift in local/worktree surfaces was observed separately and remains a hygiene risk for future reruns; this packet is logged to preserve a clean execution trail.
