# CROWN Judgment Day Release Gauntlet Summary
Generated: 2026-05-01T09:35:21
Repo: C:\w\crown_main_postmerge_verify
Branch: readiness/sandbox-operator-freeze-20260427_222113
HEAD: d4f309b
HEAD_FULL: d4f309bcf471b45c52ddd708f8749941e1dc3399
BackendBaseUrl: https://crown-api-prod.azurewebsites.net
FrontendBaseUrl: https://yellow-forest-0eecc8b0f.7.azurestaticapps.net
ApprovedShaForGate: 84b780b97001c1fb4f7ce8f3b2f099e99835ae4f

## Decision
NO-GO

## Score
Earned: 685 / 1000
Percent: 68.5 / 100

## Blockers
P0: 3
P1: 2
P2: 0

## Automatic NO-GO Reasons
P0 blockers remain: 3

## Critical Live Probe Results
Backend health status: 200
Backend SHA match: True
Frontend root status: 200
Frontend build.json status: 200
Frontend SHA match: True

## Static Scan Counts
Possible secret hits: 588
Placeholder/incomplete hits: 717
UI risk hits: 56
Tenant signals: 14405
Tenant risk hits: 212
Permission/RBAC signals: 4140
Route references: 1627
Dashboard/KPI references: 9656
Wizard references: 8049

## Validation Counts
Validation total: 7
Validation pass: 7
Validation non-pass: 0

## Browser and Load
Browser smoke: PASS
Safe load: PASS

## Open First
1. C:\w\crown_main_postmerge_verify\audit-artifacts\judgment-day-gauntlet\20260501_085908\81_JUDGMENT_DAY_BLOCKER_BOARD.csv
2. C:\w\crown_main_postmerge_verify\audit-artifacts\judgment-day-gauntlet\20260501_085908\80_JUDGMENT_DAY_SCORECARD.csv
3. C:\w\crown_main_postmerge_verify\audit-artifacts\judgment-day-gauntlet\20260501_085908\60_required_runtime_proof_matrix.csv
4. C:\w\crown_main_postmerge_verify\audit-artifacts\judgment-day-gauntlet\20260501_085908\70_JUDGMENT_DAY_RUNBOOK.md

## Scorecard

Lane                                   MaxPoints EarnedPoints Status          E
                                                                              v
                                                                              i
                                                                              d
                                                                              e
                                                                              n
                                                                              c
                                                                              e
----                                   --------- ------------ ------          -
Repo hygiene                                  50            0 FAIL            C
Local validation                             100          100 PASS            C
Security secret scan                         100          100 PASS            C
Tenant isolation static scan                  75           45 REVIEW          C
RBAC static scan                              50           50 PASS            C
UI/routes/dashboard/wizard static scan       100           40 REVIEW          C
Deployment integrity read-only probe         100          100 PASS            C
Browser smoke                                100          100 PASS            C
Safe load probe                               50           50 PASS            C
Required runtime proof matrix                175            0 MANUAL_REQUIRED C
Evidence/operations completeness             100          100 PASS            C




## Blocker Board

Priority Lane             Issue                                                
-------- ----             -----                                                
P0       Repo hygiene     Worktree is not clean.                               
P0       Runtime proof    Tenant/RBAC/workflow/security runtime proof matrix...
P0       Tenant isolation 212 tenant-risk hits require manual review.          
P1       UI polish        56 UI risk hits found.                               
P1       UI/Product       717 placeholder or incomplete markers found.         



