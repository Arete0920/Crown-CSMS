# CROWN Azure Proof Packet
# Run: 2026-04-29T19:05:00
# Approved commit: b9dad81
# Governance acceptance: APPROVED (commit b9dad81)
# Environment target: staging → production

## Azure Endpoint Probe Results

### Backend Production
- URL: https://crown-api-prod.azurewebsites.net/api/health/
- HTTP: 200 OK
- status: ok
- build_sha: c7ab4328516ad0354d20606c5e6a60d05dc07b73
- prod_deploy_tag: prod-2026-03-28-02
- db: ok
- env: prod

### Backend Dev
- URL: https://crown-api-dev.azurewebsites.net/api/health/
- HTTP: 200 OK
- status: ok
- build_sha: dev-pass4fix-20260329150550-bg
- prod_deploy_tag: (empty)
- db: ok

### Frontend (Azure SWA)
- URL: https://crown-dash.azurestaticapps.net/
- HTTP: 000 (connection failed — SWA not live or URL is a placeholder)
- Result: UNREACHABLE

### Prod Integrity (no tenant)
- URL: https://crown-api-prod.azurewebsites.net/api/integrity/
- HTTP: 400
- Response: {"detail": "Missing required header: X-School-Id.", "code": "missing_tenant"}
- Result: CORRECT BEHAVIOR — tenant enforcement is active

### Prod Integrity (demo school ID)
- URL: https://crown-api-prod.azurewebsites.net/api/integrity/
- Header: X-School-Id: 19801b59-8c05-4c84-9312-5d792e4e839d
- HTTP: 404
- Response: {"detail": "Unknown X-School-Id.", "code": "invalid_tenant"}
- Result: EXPECTED — sandbox demo school is not seeded in production environment

---

## SHA Match Analysis

| Item | Value |
|---|---|
| Approved release commit | b9dad81 |
| Final proof-packet commit | 93f0afe |
| Currently deployed on Azure prod | c7ab4328516ad0354d20606c5e6a60d05dc07b73 |
| Azure prod deploy tag | prod-2026-03-28-02 |
| Git tag on deployed SHA | prod-2026-03-28-02, pre-private-lock-2026-03-28, audit-public-snapshot-2026-03-28 |
| SHA match (approved vs deployed) | MISMATCH |

### SHA Mismatch Finding

The currently deployed Azure production SHA (c7ab4328) corresponds to the March 28, 2026 production deploy (tag: prod-2026-03-28-02). This predates all Crown2026 release candidate work done this session.

The release candidate (b9dad81) has NOT yet been deployed to Azure.

This is expected. Governance accepted the local/sandbox proof as a GO-candidate. The Azure proof is the NEXT GATE — it requires the release candidate to be deployed first.

---

## Azure Proof Checklist Status

| # | Check | Status | Notes |
|---|---|---|---|
| 1 | Azure backend live | PASS | crown-api-prod.azurewebsites.net returns 200 |
| 2 | Azure frontend live | FAIL | crown-dash.azurestaticapps.net unreachable (HTTP 000) |
| 3 | /api/health/ returns 200 | PASS | Both prod and dev return 200 |
| 4 | /api/integrity/ returns 200 | DEFERRED | Returns 400 without tenant (correct) — needs seeded tenant |
| 5 | Real Entra/IAM token auth | DEFERRED | Not yet run — requires release candidate deployed to Azure |
| 6 | Real sandbox login against Azure URL | DEFERRED | Not yet run — requires release candidate deployed to Azure |
| 7 | Browser console proof against Azure URL | DEFERRED | Not yet run — requires release candidate deployed |
| 8 | Tenant/role/permission proof against Azure URL | DEFERRED | Not yet run — requires release candidate deployed |
| 9 | Build SHA matches approved commit | FAIL | Deployed SHA c7ab4328 ≠ approved b9dad81 |
| 10 | Rollback plan documented | DEFERRED | Not yet documented |

### Overall Azure Proof Status: BLOCKED — RELEASE CANDIDATE NOT DEPLOYED

---

## Blocking Requirements Before Azure Proof Can Be Green

1. Deploy release candidate (b9dad81 or the approved source commit) to Azure staging/production
   - Trigger: push tag prod-deploy-* from release candidate branch
   - Backend: deploy via deploy-prod.yml or deploy-prod-dispatch.yml
   - Frontend: deploy via deploy-dashboard.yml to Azure SWA
   - Expected: /api/health/ returns build_sha matching the approved commit

2. Verify frontend SWA is live and /build.json reports correct SHA

3. Seed demo/sandbox school in Azure environment (if running sandbox login proof against Azure)

4. Re-run this Azure proof packet after deployment confirms:
   - /api/health/ build_sha = approved commit
   - /api/integrity/ returns 200 for a known seeded school
   - Sandbox login routes correctly through Azure auth
   - Browser console clean
   - Tenant/role proof green

---

## Deployment Command Reference

Backend deploy:
  git tag prod-deploy-<YYYYMMDD>-rc1 b9dad81
  git push origin prod-deploy-<YYYYMMDD>-rc1
  (triggers deploy-prod.yml or deploy-prod-dispatch.yml)

Frontend deploy:
  (same tag triggers deploy-dashboard.yml to Azure SWA)

Proof ceremony after deploy:
  (triggers proof-ceremony-after-prod.yml)
  Verifies /api/health/ SHA and /build.json SHA match the deployed tag

---

## Decision

AZURE PROOF: NOT YET GREEN

Reason: Release candidate b9dad81 has not been deployed to Azure.
Azure backend is live but running old code (c7ab4328, prod-2026-03-28-02).
Azure frontend SWA is not reachable.

Action required:
- Deploy release candidate to Azure
- Re-run proof packet after deployment
- Full production GO cannot be granted until Azure proof is green

---

## Supporting Files

- probe_prod_health.json — prod /api/health/ response
- probe_dev_health.json — dev /api/health/ response
- probe_prod_integrity_notenant.json — prod /api/integrity/ no-tenant response
- git_log.txt — recent commits
- git_status.txt — worktree state
- branch.txt — current branch
- head_sha.txt — current HEAD SHA
