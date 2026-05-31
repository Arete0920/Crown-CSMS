# CROWN Final 95+ Sprint - Single-Block Evidence Runner - 2026-05-30

Status: REQUIRED LOCAL EXECUTION AID
Authority: Non-shipping execution aid until evidence is produced and reviewed.

## Purpose

This is a single copy/paste PowerShell block for VS Code. It runs the same baseline evidence sequence as the multi-section command pack, captures output under a timestamped evidence root, and stops on the first failure because `$ErrorActionPreference = "Stop"` is enabled.

Run from the repository root.

## Single-block command

```powershell
$ErrorActionPreference = "Stop"

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$base = "audit-artifacts\final-95-plus-sprint\$stamp"
New-Item -ItemType Directory -Force -Path $base | Out-Null

"evidence_root=$base" | Tee-Object "$base\00_EVIDENCE_ROOT.txt"

"=== REPO TRUTH FREEZE ===" | Tee-Object "$base\01_repo_truth_freeze.txt"
git status --short --branch 2>&1 | Tee-Object -Append "$base\01_repo_truth_freeze.txt"
git branch --show-current 2>&1 | Tee-Object -Append "$base\01_repo_truth_freeze.txt"
git rev-parse HEAD 2>&1 | Tee-Object -Append "$base\01_repo_truth_freeze.txt"
git rev-parse --short HEAD 2>&1 | Tee-Object -Append "$base\01_repo_truth_freeze.txt"
git log --oneline -n 12 2>&1 | Tee-Object -Append "$base\01_repo_truth_freeze.txt"

"=== PYTHON VERSION ===" | Tee-Object "$base\02_backend_environment.txt"
.\.venv\Scripts\python.exe --version 2>&1 | Tee-Object -Append "$base\02_backend_environment.txt"

"=== DJANGO CHECK ===" | Tee-Object "$base\03_django_check.txt"
.\.venv\Scripts\python.exe backend\manage.py check 2>&1 | Tee-Object -Append "$base\03_django_check.txt"

"=== SHOW MIGRATIONS ===" | Tee-Object "$base\04_showmigrations.txt"
.\.venv\Scripts\python.exe backend\manage.py showmigrations 2>&1 | Tee-Object -Append "$base\04_showmigrations.txt"

"=== MAKEMIGRATIONS DRY RUN ===" | Tee-Object "$base\05_makemigrations_check_dry_run.txt"
.\.venv\Scripts\python.exe backend\manage.py makemigrations --check --dry-run 2>&1 | Tee-Object -Append "$base\05_makemigrations_check_dry_run.txt"

"=== DEPLOY CHECK ===" | Tee-Object "$base\06_django_deploy_check.txt"
.\.venv\Scripts\python.exe backend\manage.py check --deploy 2>&1 | Tee-Object -Append "$base\06_django_deploy_check.txt"

"=== TENANT ISOLATION ===" | Tee-Object "$base\07_tenant_isolation.txt"
.\.venv\Scripts\python.exe -m pytest backend\tests\test_tenant_isolation.py -q 2>&1 | Tee-Object -Append "$base\07_tenant_isolation.txt"

"=== ADMISSIONS ENDPOINTS ===" | Tee-Object "$base\08_admissions_endpoints.txt"
.\.venv\Scripts\python.exe -m pytest backend\applications\tests\test_admissions_endpoints.py -q -s 2>&1 | Tee-Object -Append "$base\08_admissions_endpoints.txt"

"=== AFTERCARE ===" | Tee-Object "$base\09_aftercare.txt"
.\.venv\Scripts\python.exe -m pytest backend\aftercare -q 2>&1 | Tee-Object -Append "$base\09_aftercare.txt"

"=== LATER TIER METRICS ===" | Tee-Object "$base\10_later_tier_metrics.txt"
.\.venv\Scripts\python.exe -m pytest backend\tests\test_later_tier_metrics_api.py -q 2>&1 | Tee-Object -Append "$base\10_later_tier_metrics.txt"

Push-Location frontend\dashboards

"=== NPM CI ===" | Tee-Object "..\..\$base\11_npm_ci.txt"
npm ci 2>&1 | Tee-Object -Append "..\..\$base\11_npm_ci.txt"

"=== FRONTEND LINT ===" | Tee-Object "..\..\$base\12_frontend_lint.txt"
npm run lint 2>&1 | Tee-Object -Append "..\..\$base\12_frontend_lint.txt"

"=== FRONTEND CONTRACT TESTS ===" | Tee-Object "..\..\$base\13_frontend_contracts.txt"
npm run test:contracts 2>&1 | Tee-Object -Append "..\..\$base\13_frontend_contracts.txt"

"=== SHELL CERTIFICATION ===" | Tee-Object "..\..\$base\14_shell_certification.txt"
npm run check:shell-certification 2>&1 | Tee-Object -Append "..\..\$base\14_shell_certification.txt"

"=== SHELL BACKEND CONTRACT PARITY ===" | Tee-Object "..\..\$base\15_shell_backend_contract_parity.txt"
npm run check:shell-backend-contract-parity 2>&1 | Tee-Object -Append "..\..\$base\15_shell_backend_contract_parity.txt"

"=== DASHBOARD COMPLETENESS ===" | Tee-Object "..\..\$base\16_dashboard_completeness.txt"
npm run verify:dashboard-completeness 2>&1 | Tee-Object -Append "..\..\$base\16_dashboard_completeness.txt"

"=== FRONTEND BUILD ===" | Tee-Object "..\..\$base\17_frontend_build.txt"
npm run build 2>&1 | Tee-Object -Append "..\..\$base\17_frontend_build.txt"

Pop-Location

"=== RELEASE API CONTRACTS ===" | Tee-Object "$base\18_release_api_contracts.txt"
node scripts\release\verify-api-contracts.mjs 2>&1 | Tee-Object -Append "$base\18_release_api_contracts.txt"

"=== RELEASE NAVIGATION SURFACE ===" | Tee-Object "$base\19_release_navigation_surface.txt"
node scripts\release\verify-navigation-surface.mjs 2>&1 | Tee-Object -Append "$base\19_release_navigation_surface.txt"

"=== FRONTEND RC VERIFY ===" | Tee-Object "$base\20_frontend_rc_verify.txt"
node scripts\release\verify-frontend-rc.mjs 2>&1 | Tee-Object -Append "$base\20_frontend_rc_verify.txt"

"=== FINAL 95 PLUS LOCAL EVIDENCE MANIFEST ===" | Tee-Object "$base\99_manifest.txt"
"timestamp=$stamp" | Tee-Object -Append "$base\99_manifest.txt"
"repo_head=$(git rev-parse HEAD)" | Tee-Object -Append "$base\99_manifest.txt"
"repo_branch=$(git branch --show-current)" | Tee-Object -Append "$base\99_manifest.txt"
Get-ChildItem $base | Select-Object Name,Length,LastWriteTime | Format-Table -AutoSize | Out-String | Tee-Object -Append "$base\99_manifest.txt"

Write-Host "FINAL_95_PLUS_LOCAL_EVIDENCE_ROOT=$base"
```

## Commit evidence

After reviewing the generated evidence root, commit it exactly as produced:

```powershell
git status --short
git add audit-artifacts\final-95-plus-sprint
git commit -m "audit(release): add final 95 plus sprint local evidence"
git rev-parse HEAD
```

## Rule

If this command stops or fails, do not continue to broad repairs. Use `FIRST_FAILURE_TRIAGE_RUNBOOK_20260530.md` and fix the first failed gate only.
