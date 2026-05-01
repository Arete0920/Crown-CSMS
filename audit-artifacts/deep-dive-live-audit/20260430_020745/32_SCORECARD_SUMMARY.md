# CROWN Live Audit Scorecard
Timestamp: 2026-04-30T02:08:02
Branch: readiness/sandbox-operator-freeze-20260427_222113
HEAD: 4c103b9
Approved SHA: b9dad81
Deploy Tag: prod-deploy-20260429-rc1

## Counts
PASS: 5
PASS_WITH_EXCEPTION: 
FAIL: 6
TOTAL: 12

## Decision
NO-GO_AZURE_OR_RELEASE_GATES_FAILING

## Current Rule
Production GO requires:
- clean worktree
- dashboard deploy workflow green
- production deploy workflow green
- backend health on approved SHA
- frontend live, not SWA 404
- Azure browser/login/role proof green
- rollback plan documented

## Scorecard Detail

Area                       Status              Evidence                        
----                       ------              --------                        
Repo worktree              PASS                git status --short              
Backend prod health        PASS                HTTP:200...                     
Backend approved SHA match FAIL                Expected b9dad81 in health body 
Frontend root live         FAIL                HTTP:404...                     
Frontend build.json live   FAIL                HTTP:404...                     
Frontend build SHA match   FAIL                Expected b9dad81 in build.json  
Dashboard deploy workflow  FAIL                GitHub Actions push run for p...
Production deploy workflow FAIL                GitHub Actions push run for p...
Final clean packet         PASS                audit-artifacts/final-release...
Governance acceptance      PASS                audit-artifacts/governance-ac...
Real sandbox login proof   PASS                real-sandbox-login-proof-2026...
KPI + sandbox smoke proof  PASS_WITH_EXCEPTION kpi-sandbox-final-proof-20260...



