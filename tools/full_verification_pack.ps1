<#
.SYNOPSIS
  CrownMagus Full Verification Pack
  One command. Runs every local verification layer in order.
  Mirrors what CI/proof-ceremony runs — no surprises.

.USAGE
  From repo root (venv active):
    .\tools\full_verification_pack.ps1

.EXIT CODES
  0  — all layers passed
  1  — a layer failed (details in output)
#>
$ErrorActionPreference = "Stop"
$start = Get-Date

function Banner([string]$msg) {
    $line = "=" * 60
    Write-Host "`n$line" -ForegroundColor Cyan
    Write-Host "  $msg" -ForegroundColor Cyan
    Write-Host "$line" -ForegroundColor Cyan
}

Banner "CROWN FULL VERIFICATION PACK — $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# ----------------------------------------------------------------
# [1] Backend gate (compile + system check + migration drift + tenant AST)
# ----------------------------------------------------------------
Banner "[1/5] Backend gate"
& ".\.venv\Scripts\python.exe" tools\verify_backend_gate.py
if ($LASTEXITCODE -ne 0) { throw "Backend gate FAILED (exit $LASTEXITCODE)" }

# ----------------------------------------------------------------
# [2] URL surface collision audit
# ----------------------------------------------------------------
Banner "[2/5] URL surface audit"
& ".\.venv\Scripts\python.exe" tools\verify_url_surface.py
if ($LASTEXITCODE -ne 0) { throw "URL surface audit FAILED (exit $LASTEXITCODE)" }

# ----------------------------------------------------------------
# [3] Pytest proof (full suite, deterministic proof file)
# ----------------------------------------------------------------
Banner "[3/5] Pytest proof (full suite)"
& ".\tools\run_pytest_proof.ps1"
if ($LASTEXITCODE -ne 0) { throw "Pytest proof FAILED (exit $LASTEXITCODE)" }

# ----------------------------------------------------------------
# [4] Frontend install + build
# ----------------------------------------------------------------
Banner "[4/5] Frontend build"
Push-Location frontend\dashboards
try {
    npm ci --prefer-offline 2>&1
    if ($LASTEXITCODE -ne 0) { throw "npm ci FAILED" }
    npm run build 2>&1
    if ($LASTEXITCODE -ne 0) { throw "npm run build FAILED" }
} finally {
    Pop-Location
}

# ----------------------------------------------------------------
# [5] Runner env probe (local machine info)
# ----------------------------------------------------------------
Banner "[5/5] Runner env probe"
Write-Host "HOST     : $env:COMPUTERNAME"
Write-Host "USER     : $env:USERNAME"
& ".\.venv\Scripts\python.exe" --version
node --version
docker --version 2>$null || Write-Host "docker: not available on this machine (OK for local dev)"

$elapsed = (Get-Date) - $start
Banner "DONE: Full verification pack PASSED in $([math]::Round($elapsed.TotalSeconds))s"
