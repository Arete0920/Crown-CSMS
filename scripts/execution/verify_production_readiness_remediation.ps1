$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $repoRoot

$base = "audit-artifacts\prod-readiness-remediation\verification"
New-Item -ItemType Directory -Force -Path $base | Out-Null

"=== REPO ===" | Out-File "$base\00_repo.txt"
git status -sb | Add-Content "$base\00_repo.txt"
git branch --show-current | Add-Content "$base\00_repo.txt"
git rev-parse HEAD | Add-Content "$base\00_repo.txt"

"=== APPLY REMEDIATION SCRIPT ===" | Out-File "$base\01_apply_remediation.txt"
python tools\apply_production_readiness_remediation.py 2>&1 | Tee-Object -FilePath "$base\01_apply_remediation.txt" -Append

"=== MAKE MIGRATIONS ===" | Out-File "$base\02_makemigrations.txt"
python backend\manage.py makemigrations spiritual_life aftercare 2>&1 | Tee-Object -FilePath "$base\02_makemigrations.txt" -Append

"=== AUTH USER MODEL ===" | Out-File "$base\03_auth_user_model.txt"
Select-String -Path "backend\crown_api\settings.py" -Pattern "AUTH_USER_MODEL" -SimpleMatch | ForEach-Object { "$($_.Path):$($_.LineNumber):$($_.Line.Trim())" } | Add-Content "$base\03_auth_user_model.txt"

"=== NO FAKE AFTERCARE RETURNS ===" | Out-File "$base\04_aftercare_fake_return_scan.txt"
Select-String -Path "backend\aftercare\services.py" -Pattern "return 0" -SimpleMatch | ForEach-Object { "$($_.Path):$($_.LineNumber):$($_.Line.Trim())" } | Add-Content "$base\04_aftercare_fake_return_scan.txt"

"=== DEPLOY CHECK STRICTNESS ===" | Out-File "$base\05_deploy_check_scan.txt"
Select-String -Path ".github\workflows\release-verify.yml" -Pattern "check --deploy" -SimpleMatch | ForEach-Object { "$($_.Path):$($_.LineNumber):$($_.Line.Trim())" } | Add-Content "$base\05_deploy_check_scan.txt"
Select-String -Path ".github\workflows\release-verify.yml" -Pattern "check --deploy || true" -SimpleMatch | ForEach-Object { "BYPASS: $($_.Path):$($_.LineNumber):$($_.Line.Trim())" } | Add-Content "$base\05_deploy_check_scan.txt"

"=== DJANGO CHECK ===" | Out-File "$base\06_django_check.txt"
python backend\manage.py check 2>&1 | Tee-Object -FilePath "$base\06_django_check.txt" -Append

"=== MIGRATION DRY RUN ===" | Out-File "$base\07_migration_check.txt"
python backend\manage.py makemigrations --check --dry-run 2>&1 | Tee-Object -FilePath "$base\07_migration_check.txt" -Append

"=== MIGRATE PLAN ===" | Out-File "$base\08_migrate_plan.txt"
python backend\manage.py migrate --plan 2>&1 | Tee-Object -FilePath "$base\08_migrate_plan.txt" -Append

"=== TARGETED TESTS ===" | Out-File "$base\09_targeted_tests.txt"
pytest backend\aftercare -q 2>&1 | Tee-Object -FilePath "$base\09_targeted_tests.txt" -Append
pytest backend\discipline -q 2>&1 | Tee-Object -FilePath "$base\09_targeted_tests.txt" -Append
pytest backend\core -q 2>&1 | Tee-Object -FilePath "$base\09_targeted_tests.txt" -Append

"=== FRONTEND SOURCE CHECK ===" | Out-File "$base\10_frontend_source_check.txt"
"frontend=$(Test-Path frontend)" | Add-Content "$base\10_frontend_source_check.txt"
"frontend/dashboards=$(Test-Path frontend\dashboards)" | Add-Content "$base\10_frontend_source_check.txt"
"package.json=$(Test-Path frontend\dashboards\package.json)" | Add-Content "$base\10_frontend_source_check.txt"
"package-lock.json=$(Test-Path frontend\dashboards\package-lock.json)" | Add-Content "$base\10_frontend_source_check.txt"

"=== FINAL STATUS ===" | Out-File "$base\11_final_status.txt"
git status -sb | Add-Content "$base\11_final_status.txt"
git diff --stat | Add-Content "$base\11_final_status.txt"

Write-Host "Done: $base"
