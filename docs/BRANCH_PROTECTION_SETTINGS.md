# Branch Protection Settings for main

## Current Status
**main branch**: NOT PROTECTED (no rules)

## Recommended Rules (Apply These)

### 1. Dismiss stale PR approvals
- ✅ **Enabled**
- When new commits are pushed, dismiss stale reviews

### 2. Require review from Code Owners
- ✅ **Enabled**
- PRs must have at least one approval from `.github/CODEOWNERS`

### 3. Require status checks to pass
- ✅ **Enabled**
- Require the following checks (strict):
  - `Secret Scan/Scan for secrets`
  - `Proof Ceremony/proof-ceremony`
  - `Tests/pytest (pull_request)`
  - `Spine Audit (Canon Guard)`
  - `CI - Tests and Checks/test-api`
  - `CI - Tests and Checks/verify-immutable-tags`

### 4. Require branches to be up to date
- ✅ **Enabled**
- Branches must be up to date before merging

### 5. Restrict who can push
- ✅ **Enabled (DO NOT allow forced pushes)**
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
   - ✅ Require a pull request before merging
   - ✅ Require approvals (1)
   - ✅ Dismiss stale pull request approvals when new commits are pushed
   - ✅ Require review from Code Owners
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Include administrators
   - ❌ Allow force pushes (keep disabled)
   - ✅ Allow deletions (your choice, typically disabled)

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
  - ✅ Green CI checks
  - ✅ At least 1 approval (you or CODEOWNERS)
  - ✅ Up-to-date branch
- Stale reviews auto-dismiss on new commits
- Admins cannot bypass (enforce_admins = true)

## What This Prevents

| Scenario | Before | After |
|----------|--------|-------|
| Hot-fix push | ✅ Possible | ❌ Blocked |
| Merge broken CI | ✅ Possible | ❌ Blocked |
| Merge without review | ✅ Possible | ❌ Blocked |
| Admin bypass | ✅ Possible | ❌ Blocked |
| Stale review override | ✅ Possible | ❌ Auto-dismissed |
