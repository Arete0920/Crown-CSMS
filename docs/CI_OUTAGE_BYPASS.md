# CI Outage Bypass Procedure

**Last updated:** 2026-02-27  
**Author:** ops  
**Status:** Active procedure — follow exactly during Actions quota exhaustion or runner failure

---

## Enforcement Architecture (current)

### What blocks a merge into `main`

| Layer | Mechanism | Can admin bypass? |
|---|---|---|
| Classic branch protection | Linear history, no force-push, no deletion, PR required (0 approvals) | No — `enforce_admins: true` |
| Ruleset `main-protection` (ID 12558681) | 7 required CI status checks (see below) | **Yes — bypass_mode: always for admin role** |

Classic branch protection has **no required_status_checks** — it only enforces structural rules (linear history, PR gate). All CI check enforcement lives in the ruleset.

### 7 Required status checks (enforced by ruleset)

```
pytest
test
Scan for secrets
spine-audit
verify-immutable-tags
phase3-runtime-proof
proof-ceremony
```

---

## When to use this bypass

Use this procedure **only** when:

- GitHub Actions minutes are exhausted (free-tier quota reset is monthly), OR
- A runner infrastructure failure causes checks to fail in < 5 seconds with empty `runner_name`, OR
- An upstream GitHub Actions outage blocks all workflow triggers

**Do NOT use** to skip status checks because tests seem likely to pass. Run local cert gates instead (see below).

---

## Required local cert gates before bypass

You **must** run all of these locally and they must all pass before bypassing. Record the output.

```powershell
# From repo root
git checkout main
git pull --ff-only
git log --oneline -3  # confirm HEAD SHA

# A: Django system check
& ".venv\Scripts\python.exe" backend\manage.py check

# B: Pytest (contract + discovery + all wizard apps)
& ".venv\Scripts\python.exe" -m pytest `
  backend/tests/test_wizard_contract.py `
  backend/tests/test_wizard_discovery.py `
  backend/`
  -q --tb=short 2>&1 | Select-String -Pattern "passed|failed|error" | Select-Object -Last 3

# C: Backend gate (tenant tripwires + migration drift check)
& ".venv\Scripts\python.exe" tools\verify_backend_gate.py

# D: Frontend build
Set-Location frontend\dashboards
npm run build
Set-Location ..\..
```

All four must exit 0 / report 0 failures.

---

## Bypass procedure

The ruleset `main-protection` has `bypass_mode: always` for the admin role (RepositoryRole ID 5). The `gh pr merge --admin` flag invokes this bypass.

```powershell
# Step 1: Confirm the PR is open and the branch is correct
gh pr view <PR_NUMBER> --json state,headRefName,url

# Step 2: Confirm bypass is available (should print "always")
gh api repos/tcmegahan/Crown2026/rulesets/12558681 --jq '.current_user_can_bypass'
# Note: --jq only works in bash; in PowerShell use:
# (gh api repos/tcmegahan/Crown2026/rulesets/12558681 | ConvertFrom-Json).current_user_can_bypass

# Step 3: Merge with admin bypass (invokes ruleset bypass, NOT enforce_admins toggle)
gh pr merge <PR_NUMBER> --squash --delete-branch --admin

# Step 4: Pull main and verify
git checkout main
git pull --ff-only
git log --oneline -3
```

**Do NOT** toggle `enforce_admins` on/off as the bypass mechanism. The ruleset bypass is the correct lever. `enforce_admins` governs structural rules (linear history, PR required), not CI checks.

---

## Diagnosing quota exhaustion vs. real failures

| Signal | Quota exhaustion | Real failure |
|---|---|---|
| Check elapsed time | 2-5 seconds | 30+ seconds for pytest, 45+ for full CI |
| `runner_name` in job API | empty string | populated (e.g., `ubuntu-latest-xxxx`) |
| Log retrieval | "log not found: ..." (404) | Log content available |
| Pattern | ALL checks fail simultaneously | Specific checks fail, others pass |

```powershell
# Check runner_name for a failing run
gh api repos/tcmegahan/Crown2026/actions/runs/<RUN_ID>/jobs |
  ConvertFrom-Json | Select-Object -ExpandProperty jobs |
  Select-Object name, conclusion, runner_name
```

---

## Root cause log

| Date | Cause | Resolution |
|---|---|---|
| 2026-02-27 | Free-tier GitHub Actions minutes exhausted after PR #464 merged | Bypassed via ruleset bypass for PRs #465, #466 |

---

## Restoring normal CI

When Actions minutes reset (monthly billing date) or quota is replenished:

1. Re-run a push to a feature branch — checks should trigger and run for 45+ seconds
2. Confirm `runner_name` is populated in failing/passing jobs
3. Normal PR flow resumes — no bypass needed

---

## Enforcement architecture change log

| Date | Change | Reason |
|---|---|---|
| 2026-02-27 | Moved required_status_checks from classic BP to ruleset `main-protection` | Enable proper admin bypass without toggling `enforce_admins` |
| 2026-02-27 | Added `main-ci-gates` ruleset (deleted same day) | Duplicate — consolidated into `main-protection` |
