# CROWN Current Release Status

Date: 2026-06-28
Purpose: Single canonical repository-level release posture for CROWN.

## Canonical Authority

1. This file is the canonical repository-level release authority.
2. Current controlling posture is **SANDBOX RELEASE CANDIDATE / PRODUCTION NOT APPROVED**.
3. Historical GO, SHIP, PASS, RELEASE_READY, PARTIAL, prior candidate-SHA documents, local transcript notes, and superseded audit packets are non-authoritative unless this file explicitly promotes them.
4. Product, sandbox, pilot, and production claims must be based on current repository evidence and same-SHA gate settlement, not stale packets or memory.
5. This file does not approve unrestricted production release.

## Current Decision

Repository-wide decision: **SANDBOX_RELEASE_CANDIDATE**.
Production release decision: **NOT APPROVED**.
Current controlling posture: **CONTROLLED SANDBOX / TIER 0 ELIGIBLE PENDING AUTHORITY APPROVAL AND LIVE PROOF REFRESH**.

Decision meaning:

- CROWN is no longer accurately described by the older June 24-only release-freeze posture without acknowledging later merged sandbox and CI fixes.
- The repository has current evidence supporting controlled sandbox/investor-preview candidate posture.
- Production release remains blocked pending independent governance review, release notes/changelog, production deployment runbook confirmation, and explicit owner production authorization.
- Completion evidence remains controlled by `docs/LIVE_EVIDENCE_AUTHORITY_20260622.md` plus the current follow-up PR evidence listed below.
- If main receives additional commits, same-SHA release/sandbox evidence must be re-run before any broader cohort or production claim.

## Current GitHub Evidence Snapshot

- Prior sandbox candidate SHA: `143308707333761c46a7bd7a45b3b939b7c20d28` from PR #1173.
- PR #1173, merged 2026-06-24: fixed dashboard SWA sandbox/prod env flag handling and release-authority wording.
- PR #1176, merged 2026-06-24: removed dashboard deploy workflow UTF-8 BOM hygiene risk.
- PR #1180, merged 2026-06-27/2026-06-28 window: synced batch0 certification-center connector intake to current main and preserved draft gating state metadata.
- PR #1184, merged 2026-06-28: fixed CI `dashboards-build-gate` rolldown native binding blocker by regenerating `frontend/dashboards/package-lock.json` from a clean install.
- PR #1185, merged 2026-06-28: fixed `sandbox_seed_flagship --reset` protected aid cleanup failure and added focused regression coverage.
- Follow-up PR #1181 was closed unmerged and must not be treated as part of current shipped authority.
- Follow-up PR #1178 was closed unmerged as draft and must not be treated as part of current shipped authority.
- Open PR count is not controlled by this static file; verify current PR state live through the GitHub connector when making current-status decisions.

## Current Product Completion Evidence

Use `docs/LIVE_EVIDENCE_AUTHORITY_20260622.md` first for current completion/status work.

| Area | Current verified status | Current authority |
| --- | --- | --- |
| Modules | 51 / 51 PROVEN | `audit-artifacts/module-completion/current/05_completion_scorecard.md` |
| Dashboards | 40 / 40 certified for internal dashboard scope | `audit-artifacts/dashboard-completion/state/dashboard-certification-state.json` plus follow-up PR evidence |
| Wizards | CERTIFIED | `audit-artifacts/wizard-certification/current/FINAL_WIZARD_CERTIFICATION_20260622.md` |
| Components | CERTIFIED BY PARENT SURFACE COVERAGE | `audit-artifacts/component-widget-certification/current/COMPONENT_CERTIFICATION_MATRIX_20260622.csv` |
| Widgets | CERTIFIED BY PARENT SURFACE COVERAGE | `audit-artifacts/component-widget-certification/current/WIDGET_CERTIFICATION_MATRIX_20260622.csv` |
| Sandbox / investor preview | CANDIDATE | This file plus #1173, #1184, #1185 evidence; live deployed proof refresh required |
| Production release | NOT APPROVED | Independent governance review, release notes/changelog, production runbook, and explicit owner production authorization required |

## Gate Settlement Status

### Settled as of 2026-06-24

| Step | Status | Evidence | Time |
| --- | --- | --- | --- |
| Local Repo Hygiene | PASS | 0 modified, 0 staged, 0 deleted | 2026-06-24 |
| Release Verify Gate | PASS | GitHub Actions run on main | 2026-06-24T10:50:31Z |
| Sandbox Ready Evidence Gate | PASS | GitHub Actions run on main | 2026-06-24T11:07:32Z |
| Backend Health | PASS | Django system check: 0 issues | 2026-06-24 |
| Release Certification Packet | GENERATED | `audit-artifacts/release-verification/current-20260624/` | 2026-06-24 |
| Sandbox Gate Final | PASS | GitHub Actions run on same SHA | 2026-06-24T11:07:32Z |

### Follow-up fixes after 2026-06-24

| PR | Status | Release impact | Remaining requirement |
| --- | --- | --- | --- |
| #1173 | MERGED | Corrects sandbox/prod env flag behavior in dashboard deploy workflow | Live proof remains required before buyer access |
| #1176 | MERGED | Removes workflow BOM hygiene risk | No further action if workflow parses and runs cleanly |
| #1184 | MERGED | Fixes CI dashboard build gate native binding blocker | Confirm current-main dashboard build gate green after merge |
| #1185 | MERGED | Fixes flagship sandbox reset protected-aid cleanup failure | Confirm `sandbox_seed_flagship --reset` and focused regression on current main |

## Allowed Language Now

Allowed:

- "CROWN is in controlled sandbox release-candidate posture."
- "CROWN has completed module, dashboard, wizard, component, and widget certification per current repository evidence."
- "Recent merged fixes addressed sandbox deployment, CI dashboard build, and sandbox seed/reset blockers."
- "Tier 0 internal sandbox review is eligible after authority approval and current live proof refresh."
- "Production release is not yet approved."

Not allowed:

- "CROWN is unrestricted production ready."
- "CROWN is production GO."
- "Independent review is complete" unless independently evidenced and documented.
- "Sandbox is broadly approved" beyond the controlled/Tier 0 authority scope.
- "Follow-up unmerged PRs are part of shipped release authority."

## Next Actions for Authority

### To approve controlled Tier 0 sandbox review

1. Confirm current main includes #1173, #1176, #1184, and #1185.
2. Confirm current PR state has no open release-blocking PRs.
3. Confirm current-main dashboard build gate is green after #1184.
4. Confirm `python manage.py sandbox_seed_flagship --reset` passes after #1185.
5. Confirm live sandbox endpoint proof after the latest main deployment.
6. Record owner authority approval for Tier 0 internal review.

### To approve broader sandbox / buyer / investor cohort access

1. Complete all Tier 0 checks above.
2. Confirm role-based sandbox launch paths for target personas.
3. Confirm school selector and flagship demo data reset stability.
4. Confirm no live endpoint regression after latest deployment.
5. Record authority approval for the named cohort and scope.

### To approve production release

1. Complete independent governance review and document it.
2. Prepare and commit release notes and changelog.
3. Confirm production deployment process per separate operational runbook.
4. Confirm same-SHA gate settlement: pending=0, failed=0, cancelled=0 for required release gates.
5. Confirm governance language: no false independent-review claim; solo-maintainer workaround recorded where applicable.
6. Update this file only after the evidence above is current, green, and same-SHA consistent.

## Current Final Status

**SANDBOX RELEASE CANDIDATE / PRODUCTION NOT APPROVED**.
