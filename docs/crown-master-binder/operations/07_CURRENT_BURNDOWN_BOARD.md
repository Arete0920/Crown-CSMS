# CROWN Non-Azure Burn-Down Board
Generated: 2026-04-30T02:29:35
Source readiness packet: C:\w\crown_main_postmerge_verify\audit-artifacts\nonazure-production-readiness\20260430_022540

## Current Non-Azure Score
PASS: 4
REVIEW: 0
FAIL: 4
SKIPPED: 0
TOTAL: 9

## Queue Counts
P0: 4
P1: 4
P2: 2
UI polish rows: 883
Possible secret hits: 295
Placeholder/incomplete hits: 331
UI anti-pattern hits: 52
Accessibility review hits: 514
Route references: 7
Dashboard references: 923
Wizard references: 661

## Rule
Azure remains separate. This board is for everything the team can clean while Azure/admin secret setup is being completed.

## Immediate Execution Order
1. Clear P0 queue.
2. Review possible secret hits.
3. Clean repository state.
4. Approve canons and Definition of Done.
5. Burn down UI polish board.
6. Classify dashboards, routes, and wizards.
7. Run role/tenant/sandbox proof after Azure is ready.
8. Re-score both Azure and non-Azure gates.

## P0/P1/P2 Remediation Queue

Priority Area           Issue                                                  
-------- ----           -----                                                  
P0       Deploy secrets AZURE_SWA_TOKEN missing from repo secrets (dashboard...
P0       Deploy secrets Azure auth secrets missing from production env (back...
P0       Security       Possible secrets found in source (295 hits)            
P0       Security/Auth  Tenant isolation and RBAC proof not yet artifact-ver...
P1       Accessibility  Accessibility issues in source (514 hits)              
P1       Release proof  Azure production proof not yet green (SHA mismatch, ...
P1       UI Polish      Placeholder/TODO copy in source (331 hits)             
P1       UI Polish      UI anti-patterns in source (52 hits)                   
P2       Canons         Core, SIS, Modules canons not confirmed approved       
P2       Dashboards     Dashboard/KPI data source classification not complete  




## First UI Polish Rows

Priority FindingType    File                                                   
-------- -----------    ----                                                   
P1       UI-AntiPattern backend\crown_api\templates\registration\login.html    
P1       UI-AntiPattern frontend\dashboards\playwright-report\index.html       
P1       UI-AntiPattern frontend\dashboards\playwright-report\index.html       
P1       UI-AntiPattern frontend\dashboards\playwright-report\index.html       
P1       UI-AntiPattern frontend\dashboards\src\config\dashboardTemplates\ad...
P1       UI-AntiPattern frontend\dashboards\src\config\dashboardTemplates\at...
P1       UI-AntiPattern frontend\dashboards\src\config\dashboardTemplates\co...
P1       UI-AntiPattern frontend\dashboards\src\config\dashboardTemplates\fi...
P1       UI-AntiPattern frontend\dashboards\src\config\dashboardTemplates\gr...
P1       UI-AntiPattern frontend\dashboards\src\config\dashboardTemplates\pa...
P1       UI-AntiPattern frontend\dashboards\src\config\dashboardTemplates\sc...
P1       UI-AntiPattern frontend\dashboards\src\config\dashboardTemplates\st...
P1       UI-AntiPattern frontend\dashboards\src\config\dashboardTemplates\te...
P1       UI-AntiPattern frontend\dashboards\src\pages\BillingDashboard.jsx     
P1       UI-AntiPattern frontend\dashboards\src\pages\LoginPage.jsx            
P1       UI-AntiPattern frontend\dashboards\src\pages\LoginPage.jsx            
P1       UI-AntiPattern frontend\dashboards\src\pages\LoginPage.jsx            
P1       UI-AntiPattern frontend\dashboards\src\pages\LoginPage.jsx            
P1       UI-AntiPattern frontend\dashboards\src\utils\requestTracing.js        
P1       UI-AntiPattern frontend\dashboards\src\utils\requestTracing.js        
P1       UI-AntiPattern frontend\dashboards\src\utils\requestTracing.js        
P1       UI-AntiPattern frontend\dashboards\src\utils\requestTracing.js        
P1       UI-AntiPattern frontend\dashboards\src\utils\requestTracing.js        
P1       UI-AntiPattern frontend\dashboards\src\utils\requestTracing.js        
P1       UI-AntiPattern frontend\dashboards\src\utils\requestTracing.js        
P1       UI-AntiPattern frontend\dashboards\src\utils\requestTracing.js        
P1       UI-AntiPattern frontend\dashboards\tests\api\gradebook-api-proof.sp...
P1       UI-AntiPattern frontend\dashboards\tests\api\gradebook-api-proof.sp...
P1       UI-AntiPattern frontend\dashboards\tests\api\gradebook-api-proof.sp...
P1       UI-AntiPattern frontend\dashboards\tests\api\gradebook-api-proof.sp...
P1       UI-AntiPattern frontend\dashboards\tests\api\gradebook-api-proof.sp...
P1       UI-AntiPattern frontend\dashboards\tests\api\gradebook-api-proof.sp...
P1       UI-AntiPattern frontend\dashboards\tests\api\gradebook-api-proof.sp...
P1       UI-AntiPattern frontend\dashboards\tests\api\gradebook-api-proof.sp...
P1       UI-AntiPattern frontend\dashboards\tests\api\gradebook-api-proof.sp...
P1       UI-AntiPattern frontend\dashboards\tests\api\gradebook-api-proof.sp...
P1       UI-AntiPattern frontend\dashboards\tests\api\gradebook-api-proof.sp...
P1       UI-AntiPattern frontend\dashboards\tests\api\gradebook-api-proof.sp...
P1       UI-AntiPattern frontend\dashboards\tests\api\gradebook-api-proof.sp...
P1       UI-AntiPattern frontend\dashboards\tests\api\gradebook-api-proof.sp...




## Generated Files
- Team assignments: audit-artifacts\nonazure-burndown\20260430_022935\01_TEAM_ASSIGNMENTS.csv
- UI polish board: audit-artifacts\nonazure-burndown\20260430_022935\02_UI_POLISH_ACTION_BOARD.csv
- Production release proof board: audit-artifacts\nonazure-burndown\20260430_022935\03_PRODUCTION_RELEASE_PROOF_BOARD.csv
- Source scorecard: C:\w\crown_main_postmerge_verify\audit-artifacts\nonazure-production-readiness\20260430_022540\50_NONAZURE_SCORECARD.csv
- Source remediation queue: C:\w\crown_main_postmerge_verify\audit-artifacts\nonazure-production-readiness\20260430_022540\40_REMEDIATION_QUEUE.csv
