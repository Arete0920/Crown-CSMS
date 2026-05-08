# CROWN Phase 2 Non-Azure Validation Summary

Generated: 2026-04-30T03:18:04
Repo: C:\w\crown_main_postmerge_verify
Branch: readiness/sandbox-operator-freeze-20260427_222113
HEAD: 667d63f
HEAD_FULL: 667d63fa3760f4f3626a9a55739ed4896ac29d31

## Decision

NON_AZURE_PHASE2_REMEDIATION_REQUIRED

## Validation Results

PASS: 16
FAIL: 5
ERROR: 0
TOTAL: 21

## Blocker Counts

P0: 7
P1: 3
P2: 0
TOTAL: 10

## Prior Scan Counts

Possible secret hits: 295
Placeholder/incomplete hits: 331
UI anti-pattern hits: 52
Accessibility review hits: 514

## Key Files

- Validation results: C:\w\crown_main_postmerge_verify\audit-artifacts\nonazure-phase2-validation\20260430_024221\06_validation_results.csv
- Release blocker board: C:\w\crown_main_postmerge_verify\audit-artifacts\nonazure-phase2-validation\20260430_024221\07_RELEASE_BLOCKER_BOARD.csv
- UI completion checklist: C:\w\crown_main_postmerge_verify\audit-artifacts\nonazure-phase2-validation\20260430_024221\08_UI_COMPLETION_CHECKLIST.csv
- Final release acceptance checklist: C:\w\crown_main_postmerge_verify\audit-artifacts\nonazure-phase2-validation\20260430_024221\09_FINAL_RELEASE_ACCEPTANCE_CHECKLIST.csv
- Git status before: C:\w\crown_main_postmerge_verify\audit-artifacts\nonazure-phase2-validation\20260430_024221\01_git_status_before.txt

## Execution Order

1. Open release blocker board.
2. Clear all P0 blockers first.
3. Clear validation failures.
4. Review possible secret hits.
5. Burn down UI polish and placeholder hits.
6. Complete UI completion checklist.
7. Wait for Azure team to finish secrets/deploys.
8. Run final Azure + non-Azure combined scorecard.

## Validation Table

```text
Area           WorkingDirectory      Command
----           ----------------      -------
Frontend/Node  .\frontend\dashboards npm run build
Frontend/Node  .\frontend\dashboards npm run test
Frontend/Node  .\frontend\dashboards npm run test:unit
Frontend/Node  .\frontend\dashboards npm run test:contracts
Frontend/Node  .\frontend\dashboards npm run lint
Frontend/Node  .\frontend\dashboards npm run lint:fix
Frontend/Node  .\frontend\dashboards npm run test:e2e
Frontend/Node  .\frontend\dashboards npm run test:e2e:smoke
Frontend/Node  .\frontend\dashboards npm run test:e2e:magus
Frontend/Node  .\frontend\dashboards npm run check:module-readiness
Frontend/Node  .\frontend\dashboards npm run check:shell-contracts
Frontend/Node  .\frontend\dashboards npm run check:shell-certification
Frontend/Node  .\frontend\dashboards npm run build:shell-backend-contract
Frontend/Node  .\frontend\dashboards npm run check:shell-backend-contract-pa...
Frontend/Node  .\frontend\dashboards npm run check:shell-backend-contract
Frontend/Node  .\frontend\dashboards npm run test:release:routes
Frontend/Node  .\frontend\dashboards npm run test:release:a11y
Backend/Django .                     python backend\manage.py check
Backend/Django .                     python backend\manage.py check --deploy
Backend/Django .                     python backend\manage.py showmigrations
Backend/Python .                     python -m pytest
```

## Blocker Table

```text
Priority Area           Issue
-------- ----           -----
P0       Backend/Python Validation command failed: python -m pytest
P0       Frontend/Node  Validation command failed: npm run test:e2e:smoke
P0       Frontend/Node  Validation command failed: npm run test
P0       Frontend/Node  Validation command failed: npm run test:unit
P0       Frontend/Node  Validation command failed: npm run test:e2e
P0       Repository     Worktree has uncommitted changes before Phase 2 commit.
P0       Security       295 possible secret/token hits require review.
P1       Accessibility  514 accessibility review hits require review.
P1       UI Polish      52 UI anti-pattern hits require review.
P1       UI/Product     331 placeholder/incomplete markers require review.
```
