$ErrorActionPreference = "Stop"

function Get-Python {
    if (Test-Path ".\.venv\Scripts\python.exe") { return ".\.venv\Scripts\python.exe" }
    if (Test-Path ".\venv\Scripts\python.exe") { return ".\venv\Scripts\python.exe" }
    return "python"
}

$python = Get-Python
New-Item -ItemType Directory -Force audit-artifacts\stabilization, audit-artifacts\release-verify, audit-artifacts\frontend-a11y | Out-Null

Write-Host "=== APPLY STABILIZATION PATCHES ===" -ForegroundColor Cyan
& $python scripts\stabilize\apply_repo_stabilization.py 2>&1 | Tee-Object -FilePath audit-artifacts\stabilization\02_apply_repo_stabilization.txt

Write-Host "=== FRONTEND LINT ===" -ForegroundColor Cyan
Push-Location frontend\dashboards
npm run lint 2>&1 | Tee-Object -FilePath ..\..\audit-artifacts\stabilization\03_frontend_lint.txt
Pop-Location

Write-Host "=== DJANGO CHECK ===" -ForegroundColor Cyan
Remove-Item Env:VIRTUAL_ENV -ErrorAction SilentlyContinue
Remove-Item Env:PYTHONHOME -ErrorAction SilentlyContinue
Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
. "$PSScriptRoot\..\Get-RequiredEnv.ps1"
$env:DJANGO_DEBUG = "0"
$env:DJANGO_ENV = "production"
$env:CROWN_ENV = "prod"
$env:DJANGO_SECRET_KEY = Get-RequiredEnv "DJANGO_SECRET_KEY"

& $python backend\manage.py check 2>&1 | Tee-Object -FilePath audit-artifacts\stabilization\04_django_check.txt

Write-Host "=== SCHEMA W002 MEASURE ===" -ForegroundColor Cyan
cmd.exe /d /c ".venv\Scripts\python.exe backend\manage.py check --deploy > _tmp_schema_check_cmd.txt 2>&1"

$lines = Get-Content .\_tmp_schema_check_cmd.txt
$paths = foreach ($line in $lines) {
    if ($line -match 'drf_spectacular\.W002\)\s+([A-Za-z]:\\.*?):\s+Error') { $matches[1] }
}

$total = $paths.Count
"TOTAL=$total" | Out-File audit-artifacts\release-verify\_w002_total.txt -Encoding utf8

$top = $paths |
    Group-Object |
    Sort-Object Count -Descending |
    Select-Object -First 25 |
    ForEach-Object { "{0}`t{1}" -f $_.Count, $_.Name }

$top | Out-File audit-artifacts\release-verify\_w002_top25.txt -Encoding utf8

Write-Host "=== QUICK A11Y HIT LIST ===" -ForegroundColor Cyan
if (Test-Path "audit-artifacts\frontend-a11y\04_missing_control_labels.txt") {
    Get-Content audit-artifacts\frontend-a11y\04_missing_control_labels.txt | Select-Object -First 80 |
        Out-File audit-artifacts\stabilization\05_missing_control_labels_preview.txt -Encoding utf8
}

Write-Host "=== OPTIONAL PR SNAPSHOT ===" -ForegroundColor Cyan
if (Get-Command gh -ErrorAction SilentlyContinue) {
    try {
        gh pr checks 704 2>&1 | Tee-Object -FilePath audit-artifacts\stabilization\06_pr704_checks.txt
    } catch {
        "gh pr checks 704 failed: $($_.Exception.Message)" | Out-File audit-artifacts\stabilization\06_pr704_checks.txt -Encoding utf8
    }
}

Write-Host "DONE" -ForegroundColor Green
Write-Host "Review:"
Write-Host "  audit-artifacts\stabilization\03_frontend_lint.txt"
Write-Host "  audit-artifacts\release-verify\_w002_total.txt"
Write-Host "  audit-artifacts\release-verify\_w002_top25.txt"
Write-Host "  audit-artifacts\frontend-a11y\04_missing_control_labels.txt"
