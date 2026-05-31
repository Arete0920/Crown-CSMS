# CROWN 120-School Sandbox Deep Dive Evaluation Matrix - Target 2026-06-01

Status: ACTIVE SANDBOX DEEP-DIVE CONTROL ARTIFACT
Authority: Non-shipping control artifact until promoted by `docs/CURRENT_RELEASE_STATUS.md`.

## Purpose

This matrix defines the deep-dive evaluations required before CROWN can begin a 120-school sandbox. The objective is zero avoidable launch failure: no exposed broken routes, no incomplete workflows, no fake-ready dashboards, no tenant leakage, no login ambiguity, no unsupported claims, no noisy evidence, and no deferred fixes visible to schools.

## Current decision

120-school sandbox deep-dive status: NOT DONE.

Sandbox launch remains NO-GO until every critical deep dive below is PASS or explicitly NOT APPLICABLE with rationale.

## Scoring rule

Every deep dive receives a score from 0 to 100.

| Score | Meaning |
|---|---|
| 95-100 | Ready for 120-school sandbox exposure |
| 85-94 | Not ready; fix before launch |
| 70-84 | Serious risk; launch blocker |
| Below 70 | Critical risk; immediate NO-GO |

Any critical deep dive below 95 blocks the 120-school sandbox.

## Deep-dive priority matrix

| Priority | Deep dive | Why it matters | Required score | Current status | Required evidence |
|---:|---|---|---:|---|---|
| 1 | Login, identity, and tenant routing | First user experience; failure blocks all use and creates trust damage | 95+ | NOT DONE | `FINAL_SANDBOX_120_LOGIN_PROOF.md` and tenant routing proof |
| 2 | Tenant isolation across 120 schools | Any cross-school visibility is a critical trust/privacy failure | 100 | NOT DONE | `FINAL_SANDBOX_120_TENANT_ISOLATION_PROOF.md` |
| 3 | Open PR/issue and worktree hygiene | Unmerged blockers or dirty local-only proof cannot support launch | 95+ | NOT DONE | `FINAL_SANDBOX_120_REPO_HYGIENE_AUDIT.md` |
| 4 | Navigation and exposed-route truth | Dead links and unguarded sensitive pages cause immediate user-visible failure | 95+ | NOT DONE | `FINAL_SANDBOX_120_ROUTE_NAVIGATION_PROOF.md` |
| 5 | Dashboard and wizard truth | Fake-ready dashboards/wizards undermine confidence and data trust | 95+ | NOT DONE | `FINAL_SANDBOX_120_DASHBOARD_WIZARD_STATE_MATRIX.md` |
| 6 | 120-school provisioning/reset | Sandbox must be reproducible, isolated, supportable, and resettable | 95+ | NOT DONE | `FINAL_SANDBOX_120_TENANT_PROVISIONING_MATRIX.md` |
| 7 | Parent journey | Most visible customer journey; admissions/status/billing confusion damages trust | 95+ | NOT DONE | `FINAL_SANDBOX_120_PARENT_JOURNEY_PROOF.md` |
| 8 | Teacher journey | Schools will judge product usefulness through classroom workflow quality | 95+ | NOT DONE | `FINAL_SANDBOX_120_TEACHER_JOURNEY_PROOF.md` |
| 9 | Admin/staff journey | Administrators must be able to orient, inspect, and explain the system | 95+ | NOT DONE | `FINAL_SANDBOX_120_ADMIN_STAFF_JOURNEY_PROOF.md` |
| 10 | Demo data and privacy | No production data or real student data may appear in sandbox without approved agreement | 100 | NOT DONE | `FINAL_SANDBOX_120_DEMO_DATA_POLICY.md` |
| 11 | Backend health, migrations, and smoke | Backend must be clean before schools use any route | 95+ | NOT DONE | backend evidence output |
| 12 | Frontend install/lint/contracts/build | Frontend must be clean and deterministic | 95+ | NOT DONE | frontend evidence output |
| 13 | API contract and navigation verifier | UI/API mismatch causes visible failures | 95+ | NOT DONE | API/navigation verifier output |
| 14 | Compliance sandbox limits | Schools need explicit privacy/security/sandbox boundaries | 95+ | NOT DONE | `FINAL_SANDBOX_120_COMPLIANCE_LIMITS.md` |
| 15 | IP clean-room/customer-facing content | Competitor-derived or unreviewed material must not be exposed | 95+ | NOT DONE | IP scan/originality evidence |
| 16 | Support and incident readiness | 120 schools require triage owners, intake path, severity rules, and response flow | 95+ | NOT DONE | `FINAL_SANDBOX_120_SUPPORT_PLAYBOOK.md` |
| 17 | Performance and load sanity | 120 schools can create concurrent navigation/login/demo traffic | 90+ minimum, 95+ target | NOT DONE | `FINAL_SANDBOX_120_PERFORMANCE_SANITY.md` |
| 18 | Communications/notification safety | Sandbox emails/messages must not leak, spam, or misrepresent production readiness | 95+ | NOT DONE | `FINAL_SANDBOX_120_NOTIFICATION_SAFETY.md` |
| 19 | Reporting/export privacy | Exports/reports must be tenant/role scoped or hidden | 95+ | NOT DONE | `FINAL_SANDBOX_120_REPORTING_EXPORT_PRIVACY.md` |
| 20 | Known limitations and hidden surfaces | Anything not ready must be hidden or explicitly documented; no surprise gaps | 95+ | NOT DONE | `FINAL_SANDBOX_120_LIMITATIONS_AND_HIDDEN_SURFACES.md` |

## Required deep-dive packets

Before launch, create and commit:

1. `FINAL_SANDBOX_120_READY_PACKET.md`
2. `FINAL_SANDBOX_120_LOGIN_PROOF.md`
3. `FINAL_SANDBOX_120_TENANT_ISOLATION_PROOF.md`
4. `FINAL_SANDBOX_120_REPO_HYGIENE_AUDIT.md`
5. `FINAL_SANDBOX_120_ROUTE_NAVIGATION_PROOF.md`
6. `FINAL_SANDBOX_120_DASHBOARD_WIZARD_STATE_MATRIX.md`
7. `FINAL_SANDBOX_120_TENANT_PROVISIONING_MATRIX.md`
8. `FINAL_SANDBOX_120_PARENT_JOURNEY_PROOF.md`
9. `FINAL_SANDBOX_120_TEACHER_JOURNEY_PROOF.md`
10. `FINAL_SANDBOX_120_ADMIN_STAFF_JOURNEY_PROOF.md`
11. `FINAL_SANDBOX_120_DEMO_DATA_POLICY.md`
12. `FINAL_SANDBOX_120_COMPLIANCE_LIMITS.md`
13. `FINAL_SANDBOX_120_SUPPORT_PLAYBOOK.md`
14. `FINAL_SANDBOX_120_LIMITATIONS_AND_HIDDEN_SURFACES.md`
15. `FINAL_SANDBOX_120_GO_NO_GO_SIGNOFF.md`

## Deep-dive worksheet template

Use one row per finding.

| ID | Deep dive | Finding | Severity | Evidence | Required fix | Owner | Status |
|---|---|---|---|---|---|---|---|
| TBD | TBD | TBD | Critical/High/Medium/Low | TBD | TBD | TBD | NOT DONE |

Severity definitions:

| Severity | Launch impact |
|---|---|
| Critical | Blocks 120-school sandbox |
| High | Blocks exposed route/workflow unless hidden |
| Medium | Must be fixed or documented before launch |
| Low | Can remain only if non-exposed and tracked |

## Evidence command block

Run from repo root after pulling latest `main`.

```powershell
$ErrorActionPreference = "Stop"

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$base = "audit-artifacts\final-95-plus-sprint\sandbox-120-deep-dive-$stamp"
New-Item -ItemType Directory -Force -Path $base | Out-Null

"=== SANDBOX 120 DEEP DIVE REPO STATE ===" | Tee-Object "$base\01_repo_state.txt"
git branch --show-current 2>&1 | Tee-Object -Append "$base\01_repo_state.txt"
git rev-parse HEAD 2>&1 | Tee-Object -Append "$base\01_repo_state.txt"
git status --short --branch 2>&1 | Tee-Object -Append "$base\01_repo_state.txt"
git log --oneline -n 15 2>&1 | Tee-Object -Append "$base\01_repo_state.txt"

"=== OPEN ITEMS LOCAL SEARCH ===" | Tee-Object "$base\02_open_items_search.txt"
git grep -n -i -- "TODO\|FIXME\|NOT DONE\|NOT VERIFIED\|placeholder\|sample\|mock\|coming soon\|deferred\|partial" -- docs frontend backend scripts ':!node_modules' ':!.venv' ':!dist' ':!build' 2>&1 | Tee-Object -Append "$base\02_open_items_search.txt"

"=== BACKEND SANDBOX CORE ===" | Tee-Object "$base\03_backend_sandbox_core.txt"
.\.venv\Scripts\python.exe backend\manage.py check 2>&1 | Tee-Object -Append "$base\03_backend_sandbox_core.txt"
.\.venv\Scripts\python.exe backend\manage.py makemigrations --check --dry-run 2>&1 | Tee-Object -Append "$base\03_backend_sandbox_core.txt"
.\.venv\Scripts\python.exe -m pytest backend\core\tests\test_permission_engine.py backend\tests\test_tenant_isolation.py backend\crown_api\tests\test_health.py -q --nomigrations 2>&1 | Tee-Object -Append "$base\03_backend_sandbox_core.txt"

Push-Location frontend\dashboards

"=== FRONTEND SANDBOX CORE ===" | Tee-Object "..\..\$base\04_frontend_sandbox_core.txt"
npm ci 2>&1 | Tee-Object -Append "..\..\$base\04_frontend_sandbox_core.txt"
npm run lint 2>&1 | Tee-Object -Append "..\..\$base\04_frontend_sandbox_core.txt"
npm run test:contracts 2>&1 | Tee-Object -Append "..\..\$base\04_frontend_sandbox_core.txt"
npm run verify:dashboard-completeness 2>&1 | Tee-Object -Append "..\..\$base\04_frontend_sandbox_core.txt"
npm run build 2>&1 | Tee-Object -Append "..\..\$base\04_frontend_sandbox_core.txt"

Pop-Location

"=== RELEASE CONTRACTS AND NAVIGATION ===" | Tee-Object "$base\05_release_contracts_navigation.txt"
node scripts\release\verify-api-contracts.mjs 2>&1 | Tee-Object -Append "$base\05_release_contracts_navigation.txt"
node scripts\release\verify-navigation-surface.mjs 2>&1 | Tee-Object -Append "$base\05_release_contracts_navigation.txt"

"=== SANDBOX 120 DEEP DIVE MANIFEST ===" | Tee-Object "$base\99_manifest.txt"
"timestamp=$stamp" | Tee-Object -Append "$base\99_manifest.txt"
"repo_head=$(git rev-parse HEAD)" | Tee-Object -Append "$base\99_manifest.txt"
"repo_branch=$(git branch --show-current)" | Tee-Object -Append "$base\99_manifest.txt"
Get-ChildItem $base | Select-Object Name,Length,LastWriteTime | Format-Table -AutoSize | Out-String | Tee-Object -Append "$base\99_manifest.txt"

Write-Host "SANDBOX_120_DEEP_DIVE_EVIDENCE_ROOT=$base"
```

## Launch blocker rules

A 120-school sandbox cannot begin if any of the following is true:

- login is ambiguous or failing;
- tenant isolation is unverified;
- any exposed route is broken;
- any sensitive route is unguarded;
- any dashboard or wizard is fake-ready;
- any visible workflow is incomplete without label;
- demo data is not clearly synthetic;
- real student/production data is present without approved agreement;
- frontend build fails;
- backend check fails;
- migration drift exists;
- API/navigation contract verification fails;
- open release-critical PR or issue remains unresolved;
- support/incident path is missing;
- known limitations are hidden from the sandbox context.

## Current conclusion

The 120-school sandbox must remain NO-GO until this matrix is completed, evidence is committed, and a final GO/NO-GO packet is signed off.
