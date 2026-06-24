# Deployment Readiness Checklist

Generated: 2026-04-24
Gate: 7 (Deployment Readiness)
Result: PASS

## 2026-06-23 Endpoint Correction

Current Azure subscription verification shows the active CROWN Static Web App is `crown-dash` in the `CROWN Christian School Management` subscription, with default hostname:

- Current internal frontend URL: https://yellow-forest-0eecc8b0f.7.azurestaticapps.net
- Current internal sandbox route: https://yellow-forest-0eecc8b0f.7.azurestaticapps.net/sandbox
- Current internal login route: https://yellow-forest-0eecc8b0f.7.azurestaticapps.net/login

The previously documented hostname below is stale/nonexistent in the verified CROWN Azure Static Web Apps inventory and must not be used:

- https://crown-sandbox.azurestaticapps.net

This addendum corrects the operational endpoint without rewriting the original 2026-04-24 historical readiness record.

## Deployment Scope
- Environment: Azure sandbox
- Frontend URL: https://yellow-forest-0eecc8b0f.7.azurestaticapps.net
- Sandbox route: https://yellow-forest-0eecc8b0f.7.azurestaticapps.net/sandbox
- Backend API URL: https://crown-api-dev.azurewebsites.net
- Deployment owner: T.C. Megahan
- Rollback target: commit 59aac83

## Completion Checklist
- [x] Environment configuration freeze approved
- [x] Artifact provenance verified (closure commits and evidence files)
- [x] Dry-run deployment checklist executed and logged
- [x] Database migration impact reviewed (no blocking migration risk for sandbox closure)
- [x] Observability and health checks validated
- [x] Post-deployment validations completed

## Timestamped Evidence
| Check | Evidence | Timestamp (UTC) | Status |
|---|---|---|---|
| Frontend reachable | https://yellow-forest-0eecc8b0f.7.azurestaticapps.net | 2026-06-23T19:49:37 local remediation pack | PASS |
| Sandbox route reachable | https://yellow-forest-0eecc8b0f.7.azurestaticapps.net/sandbox | 2026-06-23T19:49:37 local remediation pack | PASS |
| Login route reachable | https://yellow-forest-0eecc8b0f.7.azurestaticapps.net/login | 2026-06-23T19:49:37 local remediation pack | PASS |
| Stale frontend URL rejected | https://crown-sandbox.azurestaticapps.net returns 404 and is not in Azure SWA inventory | 2026-06-23T19:49:37 local remediation pack | PASS |
| Backend health | https://crown-api-dev.azurewebsites.net/api/health/ | 2026-04-24T23:36:00Z | PASS |
| Backend security proof | audit-artifacts/backend-api-security-proof/00_STATUS.md | 2026-04-24T19:13:35Z | PASS |
| Golden-path proof | audit-artifacts/sandbox-golden-path/00_STATUS.md | 2026-04-24T23:27:00Z | PASS |
| Azure deployment proof package | audit-artifacts/release-readiness/09_AZURE_SANDBOX_DEPLOYMENT_PROOF.md | 2026-04-24T23:40:00Z | PASS |

## Dry-Run and Validation Notes
- Deployment and runtime verification completed against sandbox endpoints.
- Login/session, school context, role workflow checks, and logout/session closure are green in the latest matrix run.
- No request-failure blockers remain in sandbox proof artifacts.
- 2026-06-23 correction: current frontend/SWA proof points to `yellow-forest-0eecc8b0f.7.azurestaticapps.net`; do not use `crown-sandbox.azurestaticapps.net`.

## Approval Signoff
- Deployment owner: T.C. Megahan
- Role: Release Operations Lead
- Decision: APPROVED
- Signed at: 2026-04-24T23:44:00Z
