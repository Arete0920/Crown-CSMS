param(
  [switch]$Fast
)

$ErrorActionPreference = "Stop"
$env:GH_PAGER  = "cat"
$env:NO_COLOR  = "1"

function Exists($p) { Test-Path $p }

Write-Host "Repo  : $((Get-Location).Path)"
Write-Host "Fast  : $Fast"
Write-Host ""

# ------------------------------------------------------------------
# 1) Git hygiene — must be clean (audits must be repeatable)
# ------------------------------------------------------------------
Write-Host "[1] Git status" -ForegroundColor Cyan
git status -sb
$dirty = (git status --porcelain) | Where-Object { $_ -match "^\s*[MADRCU?]" }
if ($dirty) {
  Write-Host "Working tree is not clean. Commit or stash first." -ForegroundColor Red
  exit 3
}
git --no-pager log --oneline -1

# ------------------------------------------------------------------
# 2) Pattern scan
# ------------------------------------------------------------------
Write-Host ""
Write-Host "[2] Pattern scan" -ForegroundColor Cyan
& "$PSScriptRoot\audit_patterns.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# ------------------------------------------------------------------
# 3) Backend checks
# ------------------------------------------------------------------
if (Exists "backend\manage.py") {
  $py = if (Exists ".venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" }
        elseif (Exists "backend\.venv\Scripts\python.exe") { ".\backend\.venv\Scripts\python.exe" }
        else { "python" }

  Write-Host ""
  Write-Host "[3a] Django system check (python: $py)" -ForegroundColor Cyan
  & $py backend\manage.py check
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

  Write-Host ""
  Write-Host "[3b] Migration drift check" -ForegroundColor Cyan
  & $py backend\manage.py makemigrations --check --dry-run
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

  if (-not $Fast) {
    Write-Host ""
    Write-Host "[3c] pytest (full backend suite)" -ForegroundColor Cyan
    & $py -m pytest backend -q --tb=short 2>&1
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  } else {
    Write-Host ""
    Write-Host "[3c] pytest — SKIPPED (Fast mode)" -ForegroundColor Yellow
  }
} else {
  Write-Host ""
  Write-Host "[3] backend\manage.py not found — skipping Django checks" -ForegroundColor Yellow
}

# ------------------------------------------------------------------
# 4) Frontend checks
# ------------------------------------------------------------------
if (Exists "frontend\dashboards\package.json") {
  Write-Host ""
  Write-Host "[4] Frontend build" -ForegroundColor Cyan
  Push-Location "frontend\dashboards"
  try {
    if (-not $Fast) {
      npm ci; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
      npm run build; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    } else {
      npm -v; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
      Write-Host "npm -v OK (Fast: skipping install + build)" -ForegroundColor Yellow
    }
  } finally {
    Pop-Location
  }
} else {
  Write-Host ""
  Write-Host "[4] frontend\dashboards\package.json not found — skipping" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "AUDIT PASS" -ForegroundColor Green
exit 0
