# Live Hosted CI Handoff (2026-05-26)

## Purpose

- Move the current local green state to hosted proof with the minimum necessary steps.
- Convert the canonical signoff memo from `CONDITIONAL NO-GO` to a final decision once GitHub Actions confirms the latest branch state.

## Recommended Commit Message

- `feat(release): enforce public surface policy gate and complete dashboard truth disclosure`

## Stage Scope

Tracked modified files in the current closure slice:

- `.github/workflows/contract-gate.yml`
- `.github/workflows/release-verify.yml`
- `frontend/dashboards/src/components/crown-dashboard/CrownDashboardFlipCard.jsx`
- `frontend/dashboards/src/components/crown-dashboard/CrownDashboardMetricCard.jsx`
- `frontend/dashboards/src/components/crown-dashboard/CrownDashboardTemplate.jsx`
- `frontend/dashboards/src/pages/AdmissionsDashboard.jsx`
- `frontend/dashboards/src/pages/FinanceDashboard.jsx`

Tracked new files to stage explicitly:

- `tools/verify_public_surface_policy.py`
- `tests/test_public_surface_policy_gate.py`
- `docs/security/public_endpoint_policy_matrix.json`
- `docs/security/csrf_exception_policy_matrix.json`
- `docs/security/PUBLIC_ENDPOINT_POLICY_MATRIX.md`
- `docs/security/CSRF_EXCEPTION_POLICY_MATRIX.md`
- `frontend/dashboards/src/components/crown-dashboard/CrownDashboardTemplate.test.jsx`
- `frontend/dashboards/src/pages/AdmissionsDashboard.test.jsx`
- `frontend/dashboards/src/pages/FinanceDashboard.test.jsx`
- `docs/release/LIVE_RELEASE_AUTHORITY_SIGNOFF_20260526.md`
- `docs/release/LIVE_RUNTIME_GOVERNANCE_COMMIT_READY_CHANGELOG_20260526.md`
- `docs/release/LIVE_RUNTIME_GOVERNANCE_PR_SUMMARY_20260526.md`
- `docs/release/LIVE_HOSTED_CI_HANDOFF_20260526.md`

Supporting audit artifacts modified locally in this wave:

- `audit-artifacts/runtime-release-closure/20260418_070051/ALL_PRIORITIES_EXECUTION_STATUS_20260526.md`
- `audit-artifacts/runtime-release-closure/20260418_070051/LIVE_RELEASE_READINESS_ASSESSMENT_AUDIT_SCORECARD_20260526_0558.md`

## Pre-Push Local Validation Already Completed

- `python tools/verify_public_surface_policy.py` -> PASS
- `python -m pytest tests/test_public_surface_policy_gate.py -q` -> PASS (`4 passed`)
- `npm run test:unit -- src/components/crown-dashboard/CrownDashboardTemplate.test.jsx src/pages/AdmissionsDashboard.test.jsx src/pages/FinanceDashboard.test.jsx` -> PASS (`33 passed files / 131 passed tests`)

## Push / PR Sequence

1. Stage the files above.
2. Commit with the recommended message.
3. Push the current branch: `feature/teacher-route-truth-slice1`.
4. Ensure there is an open PR to `main`.

## Actual Current State

- Branch pushed: `feature/teacher-route-truth-slice1`
- Release slice commit: `d898829766185a7db716b899f3ae6be7cf4bdd4a`
- Retrigger commit: `8691042b3662054a60e68fd467a92244e08d7d14`
- Merge-resolution commit: `04e81b057417b90126cc1539abdd100a8d6b6189`
- Workflow-refresh retrigger commit: `fdc2913faa9ee4ba522119f913f5615a2f93968c`
- Escalation-packet commit: `c91d01bdf6aee94b262f363d3442ccf0a7f319aa`
- Dashboard-truth review correction commit: `2e8f3c49ad1459e8f791cf13d99d350036f74776`
- Branch-scheduling diagnosis commit: `4228e74d5d00b4fe68d3e46b170df2181acfb3fb`
- Open PR: `#854` -> `https://github.com/tcmegahan/Crown2026/pull/854`
- PR API state: `OPEN` (mergeability fields currently unstable / lagging in GitHub responses for this PR)
- Current blocker: GitHub Actions still has not attached any checks to PR `#854` even after the branch conflict was resolved, the PR was reopened, both affected workflows were disabled and re-enabled, a fresh retrigger commit was pushed, and the admissions dashboard truth-label correction was pushed on top.
- Observation evidence:
  - `gh api repos/tcmegahan/Crown2026/actions/permissions` -> `enabled: true`, `allowed_actions: selected`
  - `gh api repos/tcmegahan/Crown2026/actions/permissions/selected-actions` -> `github_owned_allowed: true`, `verified_allowed: true`, no custom deny-patterns
  - `gh workflow list` -> `contract-gate` and `Release Verify` remain `active`
  - `gh run list --limit 10` -> recent scheduled runs continue on `main`
  - `gh pr view 854 --json state,isDraft,baseRefName,headRefName,headRefOid` -> PR remains `OPEN`, non-draft, targeting `main` from `feature/teacher-route-truth-slice1`, but `headRefOid` is lagging behind the branch ref
  - `gh pr checks 854` -> `no checks reported on the 'feature/teacher-route-truth-slice1' branch`
  - `gh api repos/tcmegahan/Crown2026/git/ref/heads/feature/teacher-route-truth-slice1` -> canonical branch head is `4228e74d5d00b4fe68d3e46b170df2181acfb3fb`
  - `gh api repos/tcmegahan/Crown2026/commits/4228e74d5d00b4fe68d3e46b170df2181acfb3fb/check-suites` -> `{"total_count":0,"check_suites":[]}`
  - `gh run list --branch feature/teacher-route-truth-slice1 --event pull_request --limit 20` -> `no runs found`
  - `gh api repos/tcmegahan/Crown2026/actions/workflows/release-verify.yml/dispatches -X POST -f ref=feature/teacher-route-truth-slice1` -> GitHub HTTP `500` (`Failed to run workflow dispatch`)
  - Workflow refresh attempted: `gh workflow disable/enable contract-gate.yml` and `gh workflow disable/enable release-verify.yml`
  - `gh api repos/tcmegahan/Crown2026/rulesets` -> GitHub returned HTTP `403` because rulesets API is unavailable on this repo tier, so ruleset inspection could not be completed from the API
  - PR comments recorded:
    - `https://github.com/tcmegahan/Crown2026/pull/854#issuecomment-4543850021`
    - `https://github.com/tcmegahan/Crown2026/pull/854#issuecomment-4543862091`

Why the PR matters:

- `contract-gate` is triggered by `pull_request` or `push` to `main` only.
- A branch push without an open PR will not prove `contract-gate` for this slice.

## Hosted Workflows To Watch

- `contract-gate`
- `Release Verify`
- Optional supporting signal: `Frontend Shell Certification`
- Optional supporting signal: `dashboard-release-proof`

## Additional Routing Signal

- Repository Actions is enabled and workflows are still active.
- Selected-actions policy is permissive for GitHub-owned and verified actions.
- GitHub continues to execute other repository workflows on `main`.
- The missing suites appear isolated to PR `#854` / branch `feature/teacher-route-truth-slice1` scheduling and PR metadata refresh rather than a blanket repository shutdown.

## Escalation Packet

- `docs/release/GITHUB_ACTIONS_ESCALATION_PACKET_PR854_20260526.md`

## Exact Post-Push Commands

Check the latest runs for the branch/PR:

```powershell
gh run list --limit 20
```

If needed, manually dispatch `Release Verify` after push:

```powershell
gh workflow run "Release Verify" --ref feature/teacher-route-truth-slice1
```

View the latest run details:

```powershell
gh run view --log
```

## Decision Update Rule

- If `contract-gate` and `Release Verify` both pass on the pushed branch/PR state, update `docs/release/LIVE_RELEASE_AUTHORITY_SIGNOFF_20260526.md` from `CONDITIONAL NO-GO` to the appropriate final decision.
- If either hosted workflow fails, treat that failure as the next first blocker and do not soften the current signoff posture.
- If GitHub Actions fails to attach checks or returns workflow-dispatch HTTP `500`, treat the platform failure itself as the next first blocker and preserve the current conditional signoff.

## Known Non-Blocking Note

- Git reports a line-ending warning for `frontend/dashboards/src/pages/FinanceDashboard.jsx` (`CRLF will be replaced by LF the next time Git touches it`). This is not currently an executable blocker.
