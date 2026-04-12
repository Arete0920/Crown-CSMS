$ErrorActionPreference = "Stop"
$base = "audit-artifacts\verify-high-risk"
New-Item -ItemType Directory -Force -Path $base | Out-Null

"=== REPO ===" | Out-File "$base\00_repo.txt"
Get-Location | Add-Content "$base\00_repo.txt"
git rev-parse --show-toplevel | Add-Content "$base\00_repo.txt"
git branch --show-current | Add-Content "$base\00_repo.txt"
git rev-parse HEAD | Add-Content "$base\00_repo.txt"

"=== SEARCH: core.tenant_guard ===" | Out-File "$base\01_tenant_guard_search.txt"
$allFiles = Get-ChildItem -Recurse -File | ForEach-Object FullName
Select-String -Path $allFiles -Pattern "core.tenant_guard" -SimpleMatch 2>$null |
  ForEach-Object { "{0}:{1}:{2}" -f $_.Path, $_.LineNumber, $_.Line.Trim() } |
  Add-Content "$base\01_tenant_guard_search.txt"

"=== SEARCH: tenant_guard ===" | Add-Content "$base\01_tenant_guard_search.txt"
Select-String -Path $allFiles -Pattern "tenant_guard" -SimpleMatch 2>$null |
  ForEach-Object { "{0}:{1}:{2}" -f $_.Path, $_.LineNumber, $_.Line.Trim() } |
  Add-Content "$base\01_tenant_guard_search.txt"

"=== FILE EXISTENCE CHECK ===" | Out-File "$base\02_tenant_guard_file_check.txt"
Get-ChildItem -Recurse -File -Filter "tenant_guard.py" 2>$null |
  Select-Object FullName | Format-Table -AutoSize | Out-String |
  Add-Content "$base\02_tenant_guard_file_check.txt"

"=== DJANGO CHECK ===" | Out-File "$base\03_django_check.txt"
if (Test-Path "backend\manage.py") {
  python backend\manage.py check 2>&1 | Add-Content "$base\03_django_check.txt"
} elseif (Test-Path "manage.py") {
  python manage.py check 2>&1 | Add-Content "$base\03_django_check.txt"
} else {
  "manage.py not found" | Add-Content "$base\03_django_check.txt"
}

"=== DJANGO MIGRATIONS CHECK ===" | Out-File "$base\04_migrations_check.txt"
if (Test-Path "backend\manage.py") {
  python backend\manage.py showmigrations 2>&1 | Add-Content "$base\04_migrations_check.txt"
} elseif (Test-Path "manage.py") {
  python manage.py showmigrations 2>&1 | Add-Content "$base\04_migrations_check.txt"
} else {
  "manage.py not found" | Add-Content "$base\04_migrations_check.txt"
}

"=== DJANGO DEPLOY CHECK ===" | Out-File "$base\05_deploy_check.txt"
if (Test-Path "backend\manage.py") {
  python backend\manage.py check --deploy 2>&1 | Add-Content "$base\05_deploy_check.txt"
} elseif (Test-Path "manage.py") {
  python manage.py check --deploy 2>&1 | Add-Content "$base\05_deploy_check.txt"
} else {
  "manage.py not found" | Add-Content "$base\05_deploy_check.txt"
}

Write-Host "Done: $base"