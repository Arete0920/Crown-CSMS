# Azure Sandbox Deployment Proof

Generated: 2026-04-24
Gate tie-in: 7 (Deployment Readiness)
Result: PASS

## Deployment Checklist
- [x] Frontend URL documented
- [x] Backend API URL documented
- [x] Health check recorded
- [x] Login check recorded
- [x] School context check recorded
- [x] Golden path proof check recorded
- [x] Tenant isolation check recorded
- [x] Rollback target documented
- [x] Deployment owner documented
- [x] Timestamped evidence captured

## Deployment Metadata
- Frontend URL: https://crown-sandbox.azurestaticapps.net
- Backend API URL: https://crown-api-dev.azurewebsites.net
- Health endpoint: https://crown-api-dev.azurewebsites.net/api/health/
- Deployment owner: T.C. Megahan
- Rollback target: commit 59aac83

## Timestamped Evidence Table
| Validation item | Evidence | Timestamp (UTC) | Status |
|---|---|---|---|
| Frontend availability | HTTPS sandbox frontend reachable | 2026-04-24T23:35:00Z | PASS |
| API health | /api/health returns success | 2026-04-24T23:36:00Z | PASS |
| Login/session check | sandbox proof workflow login/session PASS | 2026-04-24T23:27:00Z | PASS |
| School context check | sandbox proof workflow school context PASS | 2026-04-24T23:27:00Z | PASS |
| Golden path matrix | 225 PASS / 0 FAIL / 0 SAFE | 2026-04-24T23:27:00Z | PASS |
| Tenant isolation | SEC-003 PASS in security findings | 2026-04-24T19:13:35Z | PASS |
| Request-failure check | request failures total = 0 | 2026-04-24T23:27:00Z | PASS |

## Evidence Sources
- audit-artifacts/sandbox-golden-path/00_STATUS.md
- audit-artifacts/sandbox-golden-path/02_golden_path_matrix.csv
- audit-artifacts/sandbox-golden-path/07_request_failures.csv
- audit-artifacts/backend-api-security-proof/00_STATUS.md
- audit-artifacts/backend-api-security-proof/04_security_findings.csv

## Deployment Owner Signoff
- Name: T.C. Megahan
- Role: Release Operations Lead
- Decision: APPROVED
- Signed at: 2026-04-24T23:49:00Z
