# Branch Protection Settings for main

## Current Status
**main branch**: NOT PROTECTED (no rules)

## Recommended Rules (Apply These)

### 1. Dismiss stale PR approvals
- âœ… **Enabled**
- When new commits are pushed, dismiss stale reviews

### 2. Require review from Code Owners
- âœ… **Enabled**
- PRs must have at least one approval from `.github/CODEOWNERS`

### 3. Require status checks to pass
- âœ… **Enabled**
- Require the following checks (strict):
  - `Secret Scan/Scan for secrets`
  - `Proof Ceremony/proof-ceremony`
  - `Tests/pytest (pull_request)`
  - `Spine Audit (Canon Guard)`
  - `CI - Tests and Checks/test-api`
  - `CI - Tests and Checks/verify-immutable-tags`

### 4. Require branches to be up to date
- âœ… **Enabled**
- Branches must be up to date before merging

### 5. Restrict who can push
- âœ… **Enabled (DO NOT allow forced pushes)**
- `Dismiss stale reviews`: Yes
- `Allow force pushes`: **NO**
- `Include administrators`: **YES** (admins also follow the rules)

### 6. Require approval count
- Minimum of **1** approval (can be you + CODEOWNERS member)

## How to Apply (Web UI)

1. Go to: https://github.com/tcmegahan/Crown2026/settings/branches
2. Click **Add rule**
3. Branch name: `main`
4. Enable:
   - âœ… Require a pull request before merging
   - âœ… Require approvals (1)
   - âœ… Dismiss stale pull request approvals when new commits are pushed
   - âœ… Require review from Code Owners
   - âœ… Require status checks to pass before merging
   - âœ… Require branches to be up to date before merging
   - âœ… Include administrators
   - âŒ Allow force pushes (keep disabled)
   - âœ… Allow deletions (your choice, typically disabled)

5. Status checks required (add these):
   ```
   Secret Scan/Scan for secrets
   Proof Ceremony/proof-ceremony
   Tests/pytest (pull_request)
   Spine Audit (Canon Guard)
   CI - Tests and Checks/test-api
   CI - Tests and Checks/verify-immutable-tags
   ```

6. Click **Create**

## Result

- No one (including you) can directly push to main
- All PRs must have:
  - âœ… Green CI checks
  - âœ… At least 1 approval (you or CODEOWNERS)
  - âœ… Up-to-date branch
- Stale reviews auto-dismiss on new commits
- Admins cannot bypass (enforce_admins = true)

## What This Prevents

| Scenario | Before | After |
|----------|--------|-------|
| Hot-fix push | âœ… Possible | âŒ Blocked |
| Merge broken CI | âœ… Possible | âŒ Blocked |
| Merge without review | âœ… Possible | âŒ Blocked |
| Admin bypass | âœ… Possible | âŒ Blocked |
| Stale review override | âœ… Possible | âŒ Auto-dismissed |

## CI Gate Authoring Rules (Enforced)

**Required checks must never be job-skipped on PRs.**

GitHub maps a skipped job to `neutral`. A `neutral` result on a required check blocks merge permanently.

### Rule

> Required checks must produce `SUCCESS` or `FAILURE` on every PR, never `SKIPPED`.
> Use **step-level** `if:` guards + a pass-through step for non-applicable branches.
> Never use a **job-level** `if:` to gate required checks.

### Correct Pattern

```yaml
jobs:
  my-required-gate:
    runs-on: ubuntu-latest
    steps:
      - name: Pass (not applicable to this branch)
        if: ${{ github.event.pull_request.head.ref != 'rc/target-branch' }}
        run: echo "Gate not applicable -- passed."

      - name: Real check step
        if: ${{ github.event.pull_request.head.ref == 'rc/target-branch' }}
        run: python tools/verify_something.py
```

### Anti-Pattern (Never Do This)

```yaml
jobs:
  my-required-gate:
    if: ${{ github.event.pull_request.head.ref == 'rc/target-branch' }}  # BLOCKS MERGE ON ALL OTHER PRs
    runs-on: ubuntu-latest
    steps:
      - run: python tools/verify_something.py
```

### Incident Reference

2026-02-22: `rc-promotion-gate` job-level `if:` caused `neutral` on PR #323, blocking merge.
Fixed by moving filter to step-level with a pass-through step. Confirmed via proof PR #324 (all checks SUCCESS).

