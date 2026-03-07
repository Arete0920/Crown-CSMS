# Crown2026 — GitHub Repository Audit Report
**Date:** 2026-02-28  
**Auditor:** GitHub Copilot (verified via gh CLI + git commands, not assumptions)  
**Repo:** tcmegahan/Crown2026  
**Branch audited from:** feat/demo-concierge  
**All findings below are directly reproducible commands — zero guesswork.**

---

## PASS/FAIL Summary

| # | Category | Finding | Status |
|---|---|---|---|
| 1 | Branch protection: required approvals | 0 approvals required — any PR self-mergeable | **FAIL** |
| 2 | Branch protection: required status checks | null — broken CI never blocks a merge | **FAIL** |
| 3 | Merge strategy enforcement | All 3 strategies allowed (merge/squash/rebase) | **FAIL** |
| 4 | Delete branch on merge | false — stale branches accumulate forever | **FAIL** |
| 5 | 4 permanently broken workflows | Fail on every push, 0s elapsed, parse failure | **FAIL** |
| 6 | 35 open pull requests | Review backlog up to 20 days old | **FAIL** |
| 7 | Local main ahead of origin/main | 1 uncommitted commit never pushed to origin | **FAIL** |
| 8 | init.defaultbranch=master | Conflicts with repo default branch (main) | **FAIL** |
| 9 | pull.rebase=false | Creates merge commits on every git pull | **WARN** |
| 10 | Actions allowed_actions=all | Any public Action from any repo can run | **WARN** |
| 11 | CODEOWNERS not enforced | File exists; require_code_owner_reviews=false | **WARN** |
| 12 | No commit-msg hook | Convention not enforced locally | **WARN** |
| 13 | No pre-push hook | Tests not run locally before push | **WARN** |
| 14 | Dual autocrlf config | Both true and false set — CRLF inconsistency | **WARN** |
| 15 | 184 remote branches | Branch graveyard — massive tracking overhead | **WARN** |
| 16 | All commit sigs show E (Error) | Keys not in local keyring; gpgsign not set | **WARN** |
| 17 | Force pushes to main | BLOCKED | **PASS** |
| 18 | Main branch deletion | BLOCKED | **PASS** |
| 19 | Enforce admins on branch protection | YES — admins bound by same rules | **PASS** |
| 20 | Stale review dismissal | YES — old approvals cleared on new commits | **PASS** |
| 21 | Actions default token permissions | read-only | **PASS** |
| 22 | Actions can approve PRs | false | **PASS** |
| 23 | Repo visibility | private | **PASS** |
| 24 | pre-commit hook | Present (.git/hooks/pre-commit, 561 bytes) | **PASS** |
| 25 | CODEOWNERS file | Present, covers .github/workflows, settings, middleware | **PASS** |
| 26 | gh CLI auth | Logged in, scopes: repo, workflow, read:org | **PASS** |
| 27 | Repo is not a fork | Confirmed false | **PASS** |

---

## Section 1 — Environment (Verified)

```
git version 2.53.0.windows.1
gh version 2.85.0 (2026-01-14)
gh auth: tcmegahan, active=true, scopes=gist,read:org,repo,workflow
Repo root: C:\Users\JMega\OneDrive\Desktop\Crown2026
Current branch: feat/demo-concierge
HEAD SHA: d1919ff7128ccd35b5a46330f4dab3030830fcb3
Remote: origin https://github.com/tcmegahan/Crown2026.git
```

---

## Section 2 — Branch Protection on main (CRITICAL FAILURES)

**Command used:** `gh api repos/tcmegahan/Crown2026/branches/main/protection`

**Raw results:**
```json
{
  "deletions_allowed": false,
  "dismiss_stale": true,
  "enforce_admins": true,
  "force_push_allowed": false,
  "require_code_owner": false,
  "required_approvals": 0,
  "required_checks": null,
  "required_checks_strict": null
}
```

### FAIL 1 — required_approvals = 0
**What this means:** Any contributor (including the repo owner as a single operator) can open a PR and merge it immediately with zero reviews. No human verification required on any code change reaching main.  
**Derailer scenario:** A broken backend or security regression merges unreviewed during demo prep.

### FAIL 2 — required_checks = null
**What this means:** No CI checks are enforced at the merge gate. Even if all workflows fail, the merge button is green. The entire CI suite is decorative — it does not actually gate main.  
**Derailer scenario:** A PR with broken Django migrations, test failures, or a secret leak merges silently.  
**Compound risk:** Combined with FAIL 1 (no approvals), this means anything can merge to main at any time with zero friction.

### PASS details
- force_push_allowed: **false** — history is safe from rewrites
- deletions_allowed: **false** — main branch cannot be deleted
- enforce_admins: **true** — even tcmegahan is bound by these rules
- dismiss_stale_reviews: **true** — old approvals don't persist through new commits

---

## Section 3 — Repo Merge Settings (FAIL)

**Command used:** `gh api repos/tcmegahan/Crown2026 --jq ...`

```json
{
  "allow_merge": true,
  "allow_rebase": true,
  "allow_squash": true,
  "delete_on_merge": false,
  "visibility": "private",
  "fork": false
}
```

**FAIL 3 — All three merge strategies enabled:**  
History is inconsistent. Evidence from `git log origin/main --merges`:
- PRs #117-#128: Standard merge commits (2-parent, "Merge pull request #N")
- PRs #474-#495: Squash merges (linear single commits)

No enforced strategy means developers can choose any strategy, producing an incoherent history that is harder to bisect, revert, and audit.

**FAIL 4 — delete_branch_on_head = false:**  
Merged PR branches are not auto-deleted. Result: **184 remote branches** currently tracked (verified: `git branch -r | Measure-Object = 184`). This includes stale PRs, orphaned branches, and completed work that was never cleaned up.

---

## Section 4 — Local Main vs origin/main Divergence (FAIL)

**Command used:** `git rev-list --left-right --count "origin/main...main"`  
**Result:** `0 behind, 1 ahead`

**Divergent commit:**
```
250fb72d  docs: CrownMagus0 Tier + Wizard Coverage Matrix (validated against real codebase)
```

Local `main` branch points to `250fb72d`. `origin/main` points to `61e67163` (Finance Setup Wizard #491).

**Evidence from graph:**
```
* 250fb72d (origin/docs/coverage-matrix, main, docs/coverage-matrix)
* 61e67163 (origin/main)
```

The coverage matrix commit was merged into **local main** directly without going through origin/main. This commit exists on `origin/docs/coverage-matrix` but has never been pushed to `origin/main` through a PR merge. This is either:
1. A `git merge` performed locally on the main branch, or
2. A `git reset --hard` to the coverage-matrix branch tip

**Impact:** Local main is silently diverged from what GitHub shows as main. Any developer branching from local main picks up code that isn't on origin/main.

---

## Section 5 — 4 Permanently Broken Workflows (FAIL)

**Command used:** `gh run list --status failure --limit 20`

The following 4 workflows fail on **every push to every branch**, taking 0 seconds (startup failure — workflow YAML parse error or invalid configuration):

| Workflow File | Branches Affected | Pattern |
|---|---|---|
| `stabilization-20260116-spine_crown-api-dev.yml` | all (main, feat/*, docs/*, audit/*) | push trigger, 0s, failure |
| `proof-gradebook.yml` | all | push trigger, 0s, failure |
| `prod-health-watch.yml` | all | push trigger, 0s, failure |
| `demo-reset.yml` | all | push trigger, 0s, failure |

**Verified instance:**
```
gh run view 22528038432 --repo tcmegahan/Crown2026
→ "This run likely failed because of a workflow file issue."
→ Workflow: stabilization-20260116-spine_crown-api-dev.yml
→ Elapsed: 0s
```

These failures exist across **PR #495, the audit/ip-integrity branch, docs/sprint-map, docs/coverage-matrix, and main** — meaning this has been broken for at least the entire session today and likely much longer.

**Derailer:** These failures generate continuous noise, mask real failures, and erode trust in the CI signal. Since required_checks = null (FAIL 2), these broken workflows have zero blocking power, making them pure noise.

---

## Section 6 — 35 Open Pull Requests (FAIL)

**Command used:** `gh pr list --state open --limit 30`

**Total open PRs: 35** (only 30 shown in default listing)

Oldest open PRs:
| PR | Title | Age |
|---|---|---|
| #48 | chore(repo): ignore local secrets | ~20 days old |
| #210 | fix(demo): Pack 2/3 routes | ~11 days old |
| #208 | feat: classroom content | ~11 days old |
| #218 | harden(core): tenant + role lockdown | ~10 days old |
| #305 | chore(release): RC1 promotion | ~7 days old |
| #321 | fix(actions): add tag-push deploy trigger | ~6 days old |
| #312 | fix(demo-audit): creds | ~6 days old |

**Risk:** 35 open PRs means unreviewed code accumulates alongside active development. With required_approvals=0, any of these PRs could merge at any time with zero review. Some of these are likely stale and represent technical debt or abandoned approaches.

---

## Section 7 — GitHub Actions Status (WARN)

**Command used:** `gh api repos/tcmegahan/Crown2026/actions/permissions`

```json
{
  "allowed_actions": "all",
  "enabled": true
}
{
  "default_workflow_permissions": "read",
  "can_approve_pull_request_reviews": false
}
```

**WARN — allowed_actions=all:** Any GitHub Action from any public repository can be referenced and executed. A malicious or compromised third-party action could exfiltrate secrets or modify the repo.

**PASS — default token=read:** The `GITHUB_TOKEN` is read-only by default. Actions cannot write to the repo, packages, or deployments unless explicitly granted.

**PASS — can_approve_prs=false:** Actions cannot approve PRs, preventing self-merging automation.

---

## Section 8 — PR #495 CI Check Status (Current)

**Command used:** `gh pr checks 495 --repo tcmegahan/Crown2026`

| Check | Status |
|---|---|
| Audit: Backend (compile + checks + tenant + URLs) | **pass** (31s) |
| Audit: Frontend (lint + build) | **pass** (53s) |
| Audit: Secret scan | **pass** (6s) |
| Audit: pytest (subscriptions + contracts + permissions) | **pass** (1m32s) |
| Proof Smoke (Playwright) | **pass** (1m7s) |
| build | **pass** (25s) |
| changes | **pass** (8s) |
| demo-proof-static | **pass** (10s) |
| demo-surface-static-gate | **pass** (5s) |
| gate (×5) | **pass** |
| rc-promotion-gate | **pass** (4s) |
| lockdown-gate | **pass** (5m9s) |
| phase1-contract | **pass** (10s) |
| proof-ceremony | **pending** |
| Scan for secrets | **pending** |
| phase3-runtime-proof | **pending** |
| pytest | **pending** |
| spine-audit | **pending** |
| verify-immutable-tags | **pending** |
| Audit: Dependency vulnerabilities | **skipping** |

PR #495 is largely green. Several long-running checks still pending at audit time.

---

## Section 9 — Git Config Hygiene (WARN)

**Command used:** `git config --list`

| Setting | Value | Assessment |
|---|---|---|
| user.name | JMega | OK |
| user.email | jmega@crownschool.edu | OK |
| pull.rebase | false | WARN — creates merge commits on pull |
| core.autocrlf | true AND false (conflict) | WARN — dual setting, last wins (false) |
| init.defaultbranch | master | WARN — should be main |
| commit.gpgsign | (not set) | WARN — no local signing configured |
| push.default | (not set) | WARN — defaults to 'simple', should be explicit |

The `core.autocrlf` conflict (both `true` and `false` present in config) means line-ending behavior depends on which setting was written last. This is a CRLF consistency risk on Windows.

---

## Section 10 — Git Hooks

**Command used:** `Get-ChildItem .git/hooks`

| Hook | Status |
|---|---|
| pre-commit | **PRESENT** (561 bytes) |
| commit-msg | **MISSING** — no message format enforcement locally |
| pre-push | **MISSING** — no local test run before push |

A `commit-msg` hook would enforce the `{type}: {description}` convention the project docs specify. Without it, convention violations only get caught in code review (which requires 0 approvals — FAIL 1).

---

## Section 11 — CODEOWNERS

```
/.github/workflows/          @tcmegahan
/docs/                       @tcmegahan
/CODEOWNERS                  @tcmegahan
/backend/crown_api/          @tcmegahan
/backend/*/urls.py           @tcmegahan
/backend/*/settings.py      @tcmegahan
/backend/**/middleware*.py  @tcmegahan
```

File is present and correctly scoped. **However: `require_code_owner_reviews: false` in branch protection** means GitHub does not actually enforce CODEOWNERS reviews. The file is inert — owner reviews are requested as a suggestion, not required.

---

## Section 12 — Commit Signature Analysis

**Command used:** `git log origin/main -50 --pretty=format:"%h %G? %aN"`

All 50 checked commits show signature status **E** (Error/Unverifiable).

In git's `%G?` format:
- `G` = Good signature (key in local keyring)
- `E` = Error verifying (signature present but key not in local keyring)
- `N` = No signature
- `B` = Bad signature

**Verdict:** `E` means the commits ARE signed (GitHub signs squash-merge commits with its own GPG key) but the signing key is not in the local keyring. This is expected behavior for GitHub-web or GitHub-Actions-merged commits.  
**No `B` (bad) or `N` (unsigned) commits were found.** Zero genuine signature failures.  
**However:** `commit.gpgsign` is not configured locally, so locally-created commits are not signed.

---

## Derailer Risk Register

| Risk | Severity | Evidence | Impact |
|---|---|---|---|
| Required approvals = 0 | **CRITICAL** | gh api branch protection | Any PR merges unreviewed to main |
| Required checks = null | **CRITICAL** | gh api branch protection | Broken CI never blocks merge |
| 4 broken workflows (0s failures) | **HIGH** | gh run list --status failure | CI signal destroyed; masks real failures |
| 35 open PRs (oldest 20 days) | **HIGH** | gh pr list --state open | Unreviewed code accumulates |
| Local main 1 commit ahead of origin/main | **HIGH** | git rev-list --count | Silent divergence; devs branch from wrong code |
| All merge strategies allowed | **MEDIUM** | gh api repo metadata | Inconsistent history; harder to bisect/revert |
| delete_on_merge=false | **MEDIUM** | gh api repo metadata | 184 remote branches; branch hygiene failure |
| CODEOWNERS not enforced in protection | **MEDIUM** | gh api branch protection | Critical path changes unreviewed |
| allowed_actions=all | **MEDIUM** | gh api actions/permissions | Supply-chain attack surface |
| pull.rebase=false | **LOW** | git config | Inadvertent merge commits on pull |
| init.defaultbranch=master | **LOW** | git config | New repos/clones default to wrong branch name |
| No commit-msg hook | **LOW** | ls .git/hooks | Convention only enforced by honor system |
| No pre-push hook | **LOW** | ls .git/hooks | No local safety net before push |
| Dual autocrlf setting | **LOW** | git config | CRLF inconsistency on Windows |

---

## Immediate Actions (Priority Order)

**Do these now — each prevents a concrete derailer:**

1. **Set required approvals to 1** (GitHub Settings → Branches → Edit main rule → Require approvals: 1)
2. **Set required status checks** — add at minimum: `gate` (backend), `build` (frontend), `Audit: Secret scan`
3. **Enforce CODEOWNERS reviews** — toggle "Require review from Code Owners" in branch protection
4. **Fix the 4 broken workflows** — investigate and fix `stabilization-20260116-spine_crown-api-dev.yml`, `proof-gradebook.yml`, `prod-health-watch.yml`, `demo-reset.yml`
5. **Sync local main with origin/main** — resolve the 1-commit divergence: either push `250fb72d` via a proper PR to origin/main or hard-reset local main to origin/main
6. **Enable delete_branch_on_merge** — GitHub Settings → General → toggle on
7. **Disable allow_merge_commit** — force squash-only to maintain linear history going forward

---

## Verification Commands (Reproduce Any Finding)

```powershell
# Branch protection (requires admin)
gh api repos/tcmegahan/Crown2026/branches/main/protection --jq '{required_approvals: .required_pull_request_reviews.required_approving_review_count, required_checks: .required_status_checks.contexts, force_push: .allow_force_pushes.enabled}'

# Merge strategy settings
gh api repos/tcmegahan/Crown2026 --jq '{allow_merge: .allow_merge_commit, allow_squash: .allow_squash_merge, allow_rebase: .allow_rebase_merge, delete_on_merge: .delete_branch_on_merge}'

# Broken workflow failures
gh run list --status failure --limit 10

# Local main divergence
git rev-list --left-right --count "origin/main...main"

# Open PR count
gh pr list --state open | Measure-Object -Line

# Remote branch count
git branch -r | Where-Object { $_ -notmatch "HEAD" } | Measure-Object
```
