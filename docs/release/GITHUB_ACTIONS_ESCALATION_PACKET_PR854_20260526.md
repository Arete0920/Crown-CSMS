# GitHub Actions Escalation Packet - PR 854 (2026-05-26)

## Summary

Repository-side remediation for PR `#854` is complete, but GitHub Actions is still not scheduling any pull request runs and still rejects manual workflow dispatch with HTTP `500`.

## Repository Context

- Repository: `tcmegahan/Crown2026`
- Branch: `feature/teacher-route-truth-slice1`
- PR: `#854`
- PR URL: `https://github.com/tcmegahan/Crown2026/pull/854`
- Current canonical branch SHA: `4228e74d5d00b4fe68d3e46b170df2181acfb3fb`
- Current PR API head SHA (lagging): `03bec0da3c6587528668f7743a8cb99b12a7ee60`
- PR state: `OPEN`
- PR merge fields: currently unstable / lagging in GitHub API responses for this PR

## Completed Repository-Side Remediation

1. Isolated and committed only the release-governance and dashboard-truth slice.
2. Pushed the branch and opened PR `#854` to `main`.
3. Resolved the PR merge conflict by merging `main` into the branch in an isolated worktree.
4. Reconciled the single conflict in `.github/workflows/deploy-prod-dispatch.yml`.
5. Reopened the PR to force a fresh pull request event.
6. Disabled and re-enabled both affected workflows to refresh GitHub workflow registration:
   - `contract-gate`
   - `Release Verify`
7. Pushed a fresh empty retrigger commit after the workflow refresh.
8. Pushed a follow-up admissions dashboard truth-label fix after dashboard review and reran the targeted frontend suite successfully.
9. Pushed a branch-scheduling diagnosis update after proving Actions is enabled, workflows are active, and other runs continue on `main`.

## Evidence

### PR state is healthy

```text
gh pr view 854 --json state,isDraft,baseRefName,headRefName,headRefOid
```

Observed result after the latest branch-diagnosis push:

```text
state: OPEN
isDraft: false
baseRefName: main
headRefName: feature/teacher-route-truth-slice1
headRefOid: 03bec0da3c6587528668f7743a8cb99b12a7ee60
```

Note: the PR API head SHA is lagging the canonical branch ref, which now points at `4228e74d5d00b4fe68d3e46b170df2181acfb3fb`.

### No PR checks attach

```text
gh pr checks 854
```

Observed result:

```text
no checks reported on the 'feature/teacher-route-truth-slice1' branch
```

### Raw Actions API confirms zero pull_request runs

```text
gh api "repos/tcmegahan/Crown2026/actions/runs?event=pull_request&branch=feature%2Fteacher-route-truth-slice1&per_page=20"
```

Observed result:

```json
{
  "total_count": 0,
  "workflow_runs": []
}
```

### Raw check suites API confirms zero suites for branch heads

Example query used:

```text
gh api repos/tcmegahan/Crown2026/commits/4228e74d5d00b4fe68d3e46b170df2181acfb3fb/check-suites
```

Observed result:

```json
{
  "total_count": 0,
  "check_suites": []
}
```

### Repository Actions is enabled and other workflows are still running

```text
gh api repos/tcmegahan/Crown2026/actions/permissions
```

Observed result:

```json
{
  "enabled": true,
  "allowed_actions": "selected",
  "sha_pinning_required": false
}
```

```text
gh api repos/tcmegahan/Crown2026/actions/permissions/selected-actions
```

Observed result:

```json
{
  "github_owned_allowed": true,
  "patterns_allowed": [],
  "verified_allowed": true
}
```

```text
gh workflow list
```

Observed result excerpt:

```text
contract-gate   active
Release Verify  active
```

```text
gh run list --limit 10
```

Observed result summary:

```text
Recent scheduled workflow runs continue on branch main while PR #854 still receives zero pull_request suites.
```

### PR metadata is lagging behind the branch ref

```text
gh api repos/tcmegahan/Crown2026/git/ref/heads/feature/teacher-route-truth-slice1
```

Observed result excerpt:

```text
object.sha: 4228e74d5d00b4fe68d3e46b170df2181acfb3fb
```

This differs from the current PR API `headRefOid`, which still reports `03bec0da3c6587528668f7743a8cb99b12a7ee60`.

### Ruleset inspection is unavailable from this repository tier

```text
gh api repos/tcmegahan/Crown2026/rulesets
```

Observed result:

```json
{
  "message": "Upgrade to GitHub Pro or make this repository public to enable this feature.",
  "status": "403"
}
```

### Manual workflow dispatch fails upstream

```text
gh api repos/tcmegahan/Crown2026/actions/workflows/259605514/dispatches -X POST -f ref=feature/teacher-route-truth-slice1
```

Observed result:

```json
{
  "message": "Failed to run workflow dispatch",
  "documentation_url": "https://docs.github.com/rest/actions/workflows#create-a-workflow-dispatch-event",
  "status": "500"
}
```

## Workflow Targets Affected

- `.github/workflows/contract-gate.yml`
- `.github/workflows/release-verify.yml`

## Why This Appears External

- The PR is mergeable and conflict-free.
- Repository Actions is enabled.
- Selected-actions policy is permissive for GitHub-owned and verified actions.
- The affected workflows remain active.
- Other workflows are still running on `main`.
- The canonical branch ref has advanced while PR metadata is lagging behind it.
- The repository can read Actions metadata and artifacts normally.
- Workflow registration is active for both affected workflows.
- Re-registration plus a fresh retrigger commit did not change behavior.
- GitHub still creates zero check suites and zero pull request runs.
- Direct workflow dispatch fails with server-side HTTP `500`.

## Requested Support Action

1. Investigate why GitHub Actions is not creating any `pull_request` workflow runs for PR `#854`.
2. Investigate why manual dispatch for workflow `259605514` fails with HTTP `500`.
3. Confirm whether there is a repository-side service incident, hidden policy gate, or backend scheduling failure affecting this private repository.

## Related Branch Evidence Already Recorded

- `docs/release/LIVE_RELEASE_AUTHORITY_SIGNOFF_20260526.md`
- `docs/release/LIVE_HOSTED_CI_HANDOFF_20260526.md`
- PR comment: `https://github.com/tcmegahan/Crown2026/pull/854#issuecomment-4543850021`
- PR comment: `https://github.com/tcmegahan/Crown2026/pull/854#issuecomment-4543862091`
