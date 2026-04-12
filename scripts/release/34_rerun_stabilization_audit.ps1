$ErrorActionPreference = "Stop"

function Write-Utf8File {
    param([string]$Path,[string]$Content)
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    [System.IO.File]::WriteAllText((Join-Path (Get-Location) $Path), $Content, (New-Object System.Text.UTF8Encoding($false)))
}

New-Item -ItemType Directory -Force audit-artifacts/stabilization | Out-Null

Write-Host "=== INSTALL / REFRESH PYTHON PREREQS ===" -ForegroundColor Cyan
python -m pip install --upgrade pip 2>&1 | Tee-Object -FilePath audit-artifacts/stabilization/01_pip_upgrade.txt

if (Test-Path "backend/requirements.txt") {
  python -m pip install -r backend/requirements.txt 2>&1 | Tee-Object -FilePath audit-artifacts/stabilization/02_backend_requirements_install.txt
} elseif (Test-Path "requirements.txt") {
  python -m pip install -r requirements.txt 2>&1 | Tee-Object -FilePath audit-artifacts/stabilization/02_backend_requirements_install.txt
} else {
  "No requirements file found" | Out-File audit-artifacts/stabilization/02_backend_requirements_install.txt
}

Write-Host "=== VERIFY PREREQS ===" -ForegroundColor Cyan
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/release/34a_verify_audit_prereqs.ps1 2>&1 | Tee-Object -FilePath audit-artifacts/stabilization/03_verify_audit_prereqs.txt

Write-Host "=== RERUN AUDIT PACK ===" -ForegroundColor Cyan
if ($env:CROWN_HEALTH_BASE_URL) {
  powershell -NoProfile -ExecutionPolicy Bypass -File tools/audit/make_workspace_index.ps1 -HealthBaseUrl $env:CROWN_HEALTH_BASE_URL 2>&1 | Tee-Object -FilePath audit-artifacts/stabilization/04_make_workspace_index.txt
} else {
  powershell -NoProfile -ExecutionPolicy Bypass -File tools/audit/make_workspace_index.ps1 2>&1 | Tee-Object -FilePath audit-artifacts/stabilization/04_make_workspace_index.txt
}

$latestPack = Get-ChildItem -Directory AUDIT_PACK_* -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1
if (-not $latestPack) { throw "No AUDIT_PACK_* generated." }

$packName = $latestPack.Name
Write-Utf8File -Path "audit-artifacts/stabilization/05_latest_pack.txt" -Content $packName

Write-Host "=== QUICK PACK CHECK ===" -ForegroundColor Cyan
$summary = @()
$summary += "PACK=$packName"

foreach ($file in @(
  "05_BRANCH_PROTECTION_MAIN.json",
  "06_BACKEND_URLS.txt",
  "07_MIGRATIONS.txt",
  "08_PY_DEPS.txt",
  "13_HEALTH_PROBE.txt",
  "14_DEPLOY_PROD_RECENT.txt"
)) {
  $path = Join-Path $latestPack.FullName $file
  $summary += ""
  $summary += "FILE=$file"
  if (Test-Path $path) {
    $summary += Get-Content $path -TotalCount 30
  } else {
    $summary += "MISSING"
  }
}

Write-Utf8File -Path "audit-artifacts/stabilization/06_quick_pack_check.txt" -Content ($summary -join "`r`n")

Write-Host "DONE"
Write-Host "Latest pack: $packName"
