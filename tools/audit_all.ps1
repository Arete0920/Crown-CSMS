# tools/audit_all.ps1
# Crown2026 Audit Gate: one command to verify strength, integrity, consistency.
# Usage:
#   pwsh -File tools/audit_all.ps1
#   pwsh -File tools/audit_all.ps1 -Fast
#   pwsh -File tools/audit_all.ps1 -NoUI

param(
  [switch]$Fast,
  [switch]$NoUI
)

$ErrorActionPreference = "Stop"

function Step($name, [scriptblock]$fn) {
  Write-Host ""
  Write-Host "=== $name ===" -ForegroundColor Cyan
  & $fn
  Write-Host "OK: $name" -ForegroundColor Green
}

function Cmd($cmd) {
  Write-Host ">> $cmd" -ForegroundColor DarkGray
  $previousErrorPreference = $ErrorActionPreference
  try {
    # Native commands in this shell can emit stderr as error records even on success.
    # Use exit code as the source of truth for gate pass/fail.
    $ErrorActionPreference = "Continue"
    Invoke-Expression $cmd
  }
  finally {
    $ErrorActionPreference = $previousErrorPreference
  }
  if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
    throw "Command failed (exit $LASTEXITCODE): $cmd"
  }
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$reportDir = Join-Path $repoRoot "artifacts/audit"
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$reportPath = Join-Path $reportDir "audit-$ts.txt"

"Audit started: $(Get-Date -Format o)" | Out-File -FilePath $reportPath -Encoding utf8

Step "Repo sanity" {
  Cmd "git status --short | Tee-Object -FilePath $reportPath -Append"
  Cmd "git rev-parse HEAD | Tee-Object -FilePath $reportPath -Append"
}

Step "Backend: Python tooling check" {
  Cmd ".venv\Scripts\python.exe --version 2>&1 | Tee-Object -FilePath $reportPath -Append"
}

Step "Backend: tenant/integrity scan" {
  Cmd ".venv\Scripts\python.exe tools/audit_backend_integrity.py 2>&1 | Tee-Object -FilePath $reportPath -Append"
}

Step "Backend: Django system checks" {
  Cmd ".venv\Scripts\python.exe backend\manage.py check 2>&1 | Tee-Object -FilePath $reportPath -Append"
}

Step "Backend: migrations consistency" {
  Cmd ".venv\Scripts\python.exe backend\manage.py makemigrations --check --dry-run 2>&1 | Tee-Object -FilePath $reportPath -Append"
}

if (-not $Fast) {
  Step "Backend: full unit tests" {
    Cmd ".venv\Scripts\python.exe -m pytest -q 2>&1 | Tee-Object -FilePath $reportPath -Append"
  }
}
else {
  Step "Backend: unit tests (fast subset - tenant + ledger + admissions)" {
    Cmd ".venv\Scripts\python.exe -m pytest -q -k 'tenant or ledger or admissions or isolation' 2>&1 | Tee-Object -FilePath $reportPath -Append"
  }
}

if (-not $NoUI) {
  Step "Frontend: dependency + env hygiene" {
    if (Test-Path "tools/audit_frontend.ps1") {
      $psExe = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }
      Cmd "$psExe -File tools/audit_frontend.ps1 2>&1 | Tee-Object -FilePath $reportPath -Append"
    }
    else {
      Write-Host "tools/audit_frontend.ps1 not found; skipping"
    }
  }

  if (-not $Fast) {
    Step "Frontend: tests (if present)" {
      if (Test-Path "frontend/dashboards/package.json") {
        Push-Location "frontend/dashboards"
        Cmd "npm test --silent 2>&1 | Tee-Object -FilePath $reportPath -Append"
        Pop-Location
      }
      else {
        Write-Host "frontend/dashboards not found; skipping"
      }
    }
  }
}

Write-Host ""
Write-Host "=============================" -ForegroundColor Green
Write-Host "AUDIT COMPLETE" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green
Write-Host "Report: $reportPath" -ForegroundColor Yellow
