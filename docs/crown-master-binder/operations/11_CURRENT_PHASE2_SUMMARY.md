# CROWN Phase 2 Non-Azure Validation Summary
Generated: 2026-04-30T02:54:19
Repo: C:\w\crown_main_postmerge_verify
Branch: readiness/sandbox-operator-freeze-20260427_222113
HEAD: 667d63f
HEAD_FULL: 667d63fa3760f4f3626a9a55739ed4896ac29d31

## Decision
NON_AZURE_PHASE2_REMEDIATION_REQUIRED

## Validation Results
PASS: 18
not-PASS: 3
TOTAL: 21

## Blocker Counts
P0: 5
P1: 3
TOTAL: 8

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

## Execution Order
1. Open release blocker board -- work P0 first.
2. Review possible secret hits (P0).
3. Burn down UI polish and placeholder hits (P1).
4. Complete UI completion checklist.
5. Await Azure team: secrets + workflow reruns.
6. Run final combined scorecard.

## Validation Table

Area           Status ExitCode Command                                    
----           ------ -------- -------                                    
Backend_Django REVIEW        1 python backend\manage.py check             
Backend_Django PASS          0 python backend\manage.py check --deploy    
Backend_Django PASS          0 python backend\manage.py showmigrations    
Backend_Python PASS          0 python -m pytest                           
Frontend_Node  PASS          0 npm run build                              
Frontend_Node  PASS          0 npm run check:module-readiness             
Frontend_Node  PASS          0 npm run check:shell-contracts              
Frontend_Node  PASS          0 npm run check:shell-certification          
Frontend_Node  PASS          0 npm run build:shell-backend-contract       
Frontend_Node  PASS          0 npm run check:shell-backend-contract-parity
Frontend_Node  PASS          0 npm run check:shell-backend-contract       
Frontend_Node  PASS          0 npm run test:release:routes                
Frontend_Node  PASS          0 npm run test:release:a11y                  
Frontend_Node  PASS          0 npm run test                               
Frontend_Node  PASS          0 npm run test:unit                          
Frontend_Node  PASS          0 npm run test:contracts                     
Frontend_Node  REVIEW        1 npm run lint                               
Frontend_Node  REVIEW        1 npm run lint:fix                           
Frontend_Node  PASS          0 npm run test:e2e                           
Frontend_Node  PASS          0 npm run test:e2e:smoke                     
Frontend_Node  PASS          0 npm run test:e2e:magus                     




## Blocker Table

Priority Area           Issue                                                  
-------- ----           -----                                                  
P0       Backend_Django Validation command flagged: python backend\manage.py...
P0       Frontend_Node  Validation command flagged: npm run lint:fix           
P0       Frontend_Node  Validation command flagged: npm run lint               
P0       Repository     Worktree has uncommitted changes.                      
P0       Security       295 possible secret/token hits.                        
P1       Accessibility  514 accessibility review hits.                         
P1       UI Polish      52 UI anti-pattern hits.                               
P1       UI/Product     331 placeholder/incomplete markers.                    



