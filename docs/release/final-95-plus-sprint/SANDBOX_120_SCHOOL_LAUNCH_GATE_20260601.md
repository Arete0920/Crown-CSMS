# CROWN 120-School Sandbox Launch Gate - Target 2026-06-01

Status: ACTIVE 120-SCHOOL SANDBOX BLOCKER GATE
Authority: Non-shipping control artifact until promoted by `docs/CURRENT_RELEASE_STATUS.md`.

## Purpose

This gate defines the hard readiness standard for beginning sandbox with 120 schools. A 120-school sandbox is not a casual pilot. It is a high-visibility operating environment and must be clean, complete, deterministic, and evidence-backed.

## Current decision

SANDBOX 120-SCHOOL LAUNCH: NO-GO until every required gate below is PASS or formally marked NOT APPLICABLE with rationale.

There is no acceptable `partial`, `deferred`, `placeholder`, `known broken`, `mostly working`, or `we will fix after onboarding` status for any surface exposed to the 120-school sandbox cohort.

## Non-negotiable launch rules

1. No exposed broken routes.
2. No fake-ready dashboards.
3. No unguarded sensitive routes.
4. No unverified tenant isolation.
5. No unresolved login ambiguity.
6. No production data in sandbox.
7. No real student data in sandbox unless a separate approved legal/customer data agreement exists.
8. No stale release authority claims.
9. No unresolved open blocker issue treated as harmless.
10. No uncommitted local proof treated as repo truth.
11. No hidden partials or deferred surfaces.
12. No launch claim without current candidate-SHA evidence.

## Launch decision states

| Decision | Meaning |
|---|---|
| SANDBOX 120 GO | Every required row is PASS, evidence is committed, and exposed limitations are explicit |
| SANDBOX 120 NO-GO | Any required row is FAIL, NOT VERIFIED, NOT DONE, missing evidence, or unresolved |

For a 120-school launch, there is no `conditional go` unless the condition is unrelated to exposed sandbox experience and has explicit owner approval.

## Required global gates

| Gate | Required result | Current status | Evidence required |
|---|---|---|---|
| Repo truth freeze | PASS | NOT VERIFIED | Branch, SHA, status, latest commits |
| Worktree hygiene | PASS | NOT VERIFIED | Clean or intentionally scoped changes only |
| Open PR audit | PASS | NOT VERIFIED | No unmerged release-critical PR, or explicit NO-GO |
| Open issue audit | PASS | NOT VERIFIED | No unresolved sandbox blocker issue |
| Backend Django check | PASS | NOT VERIFIED | `manage.py check` output |
| Migration dry-run | PASS | NOT VERIFIED | `makemigrations --check --dry-run` output |
| Critical backend smoke | PASS | NOT VERIFIED | Tenant/auth/admissions/billing/parent/teacher/admin smoke proof |
| Critical frontend install/lint/build | PASS | NOT VERIFIED | npm install/lint/build output |
| Frontend route smoke | PASS | NOT VERIFIED | route/navigation verifier or smoke proof |
| Dashboard readiness verifier | PASS | NOT VERIFIED | no fake-ready or template-only production-visible dashboards |
| Wizard readiness verifier | PASS | NOT VERIFIED | no exposed incomplete wizard |
| Tenant isolation proof | PASS | NOT VERIFIED | 120-school-safe tenant scoping proof |
| Login proof | PASS | NOT VERIFIED | sandbox login options are clear and working |
| Sandbox data policy | PASS | NOT VERIFIED | synthetic/demo/no-production-data proof |
| Sandbox reset/provisioning | PASS | NOT VERIFIED | deterministic seed/reset/provisioning proof |
| IP clean-room review | PASS | NOT VERIFIED | no unreviewed competitor-derived exposed content |
| Compliance sandbox limits | PASS | NOT VERIFIED | privacy/security/sandbox limitation notice |
| Support/incident path | PASS | NOT VERIFIED | escalation and triage owner path |
| Final sandbox authority | PASS | NOT DONE | `FINAL_SANDBOX_120_READY_PACKET.md` |

## 120-school cohort gates

| Gate | Required result | Current status | Evidence required |
|---|---|---|---|
| 120 tenant records provisioned or provision-ready | PASS | NOT VERIFIED | tenant list/count/provisioning script output |
| Each tenant has unique school identity | PASS | NOT VERIFIED | school slug/name/domain/environment matrix |
| Each tenant has isolated demo dataset | PASS | NOT VERIFIED | no shared mutable cross-tenant records |
| Each tenant has sandbox admin path | PASS | NOT VERIFIED | admin user/role proof or onboarding flow proof |
| Each tenant has parent journey smoke | PASS | NOT VERIFIED | start/apply/status route proof |
| Each tenant has teacher journey smoke | PASS | NOT VERIFIED | attendance/gradebook/communication route proof or hidden if unavailable |
| Each tenant has staff/admin journey smoke | PASS | NOT VERIFIED | command center/navigation proof |
| Each tenant has dashboard state truth | PASS | NOT VERIFIED | ready/live/hidden status matrix |
| Cohort-level reset procedure | PASS | NOT VERIFIED | deterministic reset command and rollback note |
| Cohort-level support playbook | PASS | NOT VERIFIED | support owner, intake, severity, response workflow |

## Exposed surface requirements

Every exposed sandbox surface must be one of:

- COMPLETE AND PASSING;
- HIDDEN;
- EXPLICITLY LABELED SANDBOX SAMPLE/DEMO;
- NOT APPLICABLE TO SANDBOX with rationale.

No exposed surface may be:

- broken;
- blank without explanation;
- placeholder without label;
- sample-backed while pretending to be live;
- route-visible but role/tenant unverified;
- linked from navigation but not implemented;
- dependent on uncommitted local-only evidence.

## Required final artifacts

Before any 120-school sandbox start, create and commit:

1. `FINAL_SANDBOX_120_READY_PACKET.md`
2. `FINAL_SANDBOX_120_TENANT_PROVISIONING_MATRIX.md`
3. `FINAL_SANDBOX_120_ROUTE_NAVIGATION_PROOF.md`
4. `FINAL_SANDBOX_120_LOGIN_PROOF.md`
5. `FINAL_SANDBOX_120_DEMO_DATA_POLICY.md`
6. `FINAL_SANDBOX_120_DASHBOARD_WIZARD_STATE_MATRIX.md`
7. `FINAL_SANDBOX_120_SUPPORT_PLAYBOOK.md`
8. `FINAL_SANDBOX_120_LIMITATIONS_AND_HIDDEN_SURFACES.md`
9. `FINAL_SANDBOX_120_GO_NO_GO_SIGNOFF.md`

## Required VS Code evidence command block

Run from repo root.

```powershell
$ErrorActionPreference = "Stop"

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$base = "audit-artifacts\final-95-plus-sprint\sandbox-120-$stamp"
New-Item -ItemType Directory -Force -Path $base | Out-Null

"=== SANDBOX 120 REPO TRUTH ===" | Tee-Object "$base\01_repo_truth.txt"
git branch --show-current 2>&1 | Tee-Object -Append "$base\01_repo_truth.txt"
git rev-parse HEAD 2>&1 | Tee-Object -Append "$base\01_repo_truth.txt"
git status --short 2>&1 | Tee-Object -Append "$base\01_repo_truth.txt"
git log --oneline -n 12 2>&1 | Tee-Object -Append "$base\01_repo_truth.txt"

"=== BACKEND CHECK ===" | Tee-Object "$base\02_backend_check.txt"
.\.venv\Scripts\python.exe backend\manage.py check 2>&1 | Tee-Object -Append "$base\02_backend_check.txt"

"=== MIGRATION DRY RUN ===" | Tee-Object "$base\03_migration_dry_run.txt"
.\.venv\Scripts\python.exe backend\manage.py makemigrations --check --dry-run 2>&1 | Tee-Object -Append "$base\03_migration_dry_run.txt"

"=== TENANT / AUTH / SANDBOX SMOKE ===" | Tee-Object "$base\04_backend_sandbox_smoke.txt"
.\.venv\Scripts\python.exe -m pytest backend\core\tests\test_permission_engine.py backend\tests\test_tenant_isolation.py backend\crown_api\tests\test_health.py -q --nomigrations 2>&1 | Tee-Object -Append "$base\04_backend_sandbox_smoke.txt"

Push-Location frontend\dashboards

"=== FRONTEND INSTALL ===" | Tee-Object "..\..\$base\05_npm_ci.txt"
npm ci 2>&1 | Tee-Object -Append "..\..\$base\05_npm_ci.txt"

"=== FRONTEND LINT ===" | Tee-Object "..\..\$base\06_frontend_lint.txt"
npm run lint 2>&1 | Tee-Object -Append "..\..\$base\06_frontend_lint.txt"

"=== FRONTEND CONTRACTS ===" | Tee-Object "..\..\$base\07_frontend_contracts.txt"
npm run test:contracts 2>&1 | Tee-Object -Append "..\..\$base\07_frontend_contracts.txt"

"=== DASHBOARD COMPLETENESS ===" | Tee-Object "..\..\$base\08_dashboard_completeness.txt"
npm run verify:dashboard-completeness 2>&1 | Tee-Object -Append "..\..\$base\08_dashboard_completeness.txt"

"=== FRONTEND BUILD ===" | Tee-Object "..\..\$base\09_frontend_build.txt"
npm run build 2>&1 | Tee-Object -Append "..\..\$base\09_frontend_build.txt"

Pop-Location

"=== RELEASE API CONTRACTS ===" | Tee-Object "$base\10_api_contracts.txt"
node scripts\release\verify-api-contracts.mjs 2>&1 | Tee-Object -Append "$base\10_api_contracts.txt"

"=== NAVIGATION SURFACE ===" | Tee-Object "$base\11_navigation_surface.txt"
node scripts\release\verify-navigation-surface.mjs 2>&1 | Tee-Object -Append "$base\11_navigation_surface.txt"

"=== SANDBOX 120 MANIFEST ===" | Tee-Object "$base\99_manifest.txt"
"timestamp=$stamp" | Tee-Object -Append "$base\99_manifest.txt"
"repo_head=$(git rev-parse HEAD)" | Tee-Object -Append "$base\99_manifest.txt"
"repo_branch=$(git branch --show-current)" | Tee-Object -Append "$base\99_manifest.txt"
Get-ChildItem $base | Select-Object Name,Length,LastWriteTime | Format-Table -AutoSize | Out-String | Tee-Object -Append "$base\99_manifest.txt"

Write-Host "SANDBOX_120_EVIDENCE_ROOT=$base"
```

## Evidence interpretation rule

- Any failed command means SANDBOX 120 NO-GO.
- Any missing output means NOT VERIFIED.
- Any dirty worktree requires explicit scope classification before launch.
- Any open release-critical PR or issue blocks sandbox launch.
- Any unproven exposed module must be hidden or removed from sandbox navigation.

## Current conclusion

CROWN is not approved to begin a 120-school sandbox until this gate is closed with evidence.
