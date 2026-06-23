# CROWN Live Evidence Authority

Date: 2026-06-22
Branch: cleanup/live-authority-rebaseline-20260622
Purpose: prevent stale scorecards, stale release notes, and historical audit packets from controlling current CROWN completion claims.

## Controlling current evidence

Use these files first for current completion/status work:

| Area | Current authority | Current verified status |
| --- | --- | --- |
| Modules | `audit-artifacts/module-completion/current/05_completion_scorecard.md` | 51 / 51 PROVEN |
| Dashboards | `audit-artifacts/dashboard-completion/state/dashboard-certification-state.json` | 40 / 40 certified for internal dashboard scope |
| Dashboard Batch 5 proof | `audit-artifacts/dashboard-completion/evidence-packets/batch5/remaining-six-final-proof.md` | Batch 5 internal proof packet present |
| Wizards | GitHub Actions Sandbox Ready Evidence run 428 job-level evidence on PR #981 head SHA `884ce9b3a742bdc61e8e0a3f28f996879e35e2d9` | Wizard parity and 50-wizard completion assertions passed |
| Release posture | `docs/CURRENT_RELEASE_STATUS.md` | NO-GO / RELEASE FREEZE until same-SHA final release authority is updated |

## Superseded material rule

Older scorecards, prior generated matrices, historical release packets, and partial audit outputs are not controlling truth when they conflict with the files above.

Use stale files only for provenance, not current status.

## Allowed current summary

- Modules: complete/proven by current module scorecard.
- Dashboards: certified for internal dashboard scope by current dashboard state register.
- Wizards: certified by connector-visible GitHub Actions wizard parity and 50-wizard assertion evidence.
- Production / unrestricted release: not approved by these completion artifacts alone.

## Not allowed

- Do not use pre-2026-06-22 dashboard counts as current if they conflict with `dashboard-certification-state.json`.
- Do not use old module scorecard dashboard/wizard subsections as controlling dashboard/wizard truth.
- Do not claim production GO unless `docs/CURRENT_RELEASE_STATUS.md` is explicitly updated with current same-SHA release evidence.
