# Workspace / Path Noise Inventory

## Purpose

Reduce false Problems Panel noise caused by stale local clones, old worktrees, and mixed VS Code workspace roots.

## Rule

This step does not modify source code.
This step does not delete folders automatically.
This step only classifies local workspace noise and identifies safe cleanup candidates.

## Current Main

- Date/time: 2026-04-25 09:03:35 -04:00
- Branch: hygiene/01-workspace-noise-classification
- HEAD: 5d828a88d23f72ed0ac294fc4f3d3cd15ca69e37

## Git Worktrees

```text
C:/Users/JMega/OneDrive/Desktop/Crown2026_deploypr_clean f0b911e [hardening/dashboard-perfection-sprint] C:/w/crown_main_postmerge_verify                         5d828a8 [hygiene/01-workspace-noise-classification] C:/w/crown_main_validation_hotfix                        5fcae89 [hotfix/main-release-readiness-artifacts] C:/w/crown_main_verify                                   b629364 (detached HEAD) C:/w/crown_pr756_replacement                             e5d02f6 [release-readiness/freshness-closeout] C:/w/pr756_repair                                        e5e6118 [pr756_fix_tmp]
```

## C:\w Folders

### C:\w\crown_main_postmerge_verify

Git repo/worktree: YES
- Branch: hygiene/01-workspace-noise-classification
- HEAD: 5d828a88d23f72ed0ac294fc4f3d3cd15ca69e37
- Dirty: False

### C:\w\crown_main_validation_hotfix

Git repo/worktree: YES
- Branch: hotfix/main-release-readiness-artifacts
- HEAD: 5fcae89f26ff278b2576fc5f820b18cd9c30950d
- Dirty: False

### C:\w\crown_main_verify

Git repo/worktree: YES
- Branch: 
- HEAD: b629364f22e138ba50fd92a0dfd1da3e7e43e72f
- Dirty: False

### C:\w\crown_pr756_replacement

Git repo/worktree: YES
- Branch: release-readiness/freshness-closeout
- HEAD: e5d02f685778f98fa92a4c474bda420141a6af22
- Dirty: True

```text
 M .github/workflows/ui-proof-gates.yml
 M frontend/dashboards/tests/ui/executive-dashboard-v1.spec.ts
```

### C:\w\pr756_fix

Git repo/worktree: YES
- Branch: 
- HEAD: 3299c08c1243134a3ecb5173a7179f95bbe5cb62
- Dirty: False

### C:\w\pr756_repair

Git repo/worktree: YES
- Branch: pr756_fix_tmp
- HEAD: e5e61182cb72ede87444a6c8ec00476132aa5b06
- Dirty: True

```text
 M frontend/dashboards/tests/proof-smoke.spec.ts
 M frontend/dashboards/tests/ui/executive-dashboard-v1.spec.ts
?? .tmp_backend_contract_fix.diff
?? .tmp_runlist.json
?? am_current_patch.txt
?? am_patch_err.txt
?? latest_tmp_branch_commit.txt
?? ls_remote_heads.txt
?? pr756_repair_status.txt
?? pr_state_after_final_push.json
?? pr_state_after_fix_push.json
?? pr_state_after_worktree_push.json
?? remote_branches.txt
?? remotes.txt
?? status_now.txt
?? tmp/
```


## Initial Cleanup Recommendation

| Path | Recommendation | Reason |
|---|---|---|
| C:\w\crown_main_postmerge_verify | KEEP | Current clean main verification workspace |
| C:\w\crown_pr756_replacement | ARCHIVE/CLOSE IN VS CODE | PR #757 replacement work is complete |
| C:\w\pr756_repair | ARCHIVE/CLOSE IN VS CODE | PR #756 is closed/evidence-only |
| C:\w\crown_main_validation_hotfix | ARCHIVE/CLOSE IN VS CODE | PR #760 hotfix is merged |
| C:\w\crown_main_verify | REVIEW | Older verification workspace; keep only if still needed |
| C:\w\pr756_fix | REVIEW | Older PR repair workspace; likely stale |

## Manual VS Code Cleanup

1. Close all VS Code windows.
2. Reopen only: C:\w\crown_main_postmerge_verify
3. Remove old folders from the current VS Code workspace.
4. Do not delete folders until each has clean git status.
5. Do not use Save All across mixed workspaces.

## Next Step

After this inventory is reviewed, stale workspaces can be closed or archived locally.
