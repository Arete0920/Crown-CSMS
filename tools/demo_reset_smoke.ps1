<#
.SYNOPSIS
    Demo Reset + Smoke: migrate, seed, verify the runtime proof ceremony locally.

.DESCRIPTION
    Deterministic local counterpart to .github/workflows/demo-reset-smoke.yml.
    Runs against the local dev database (DATABASE_URL or default SQLite).

    Steps:
      1. migrate
      2. seed_demo_school --wipe  (wipes and re-seeds demo school data)
      3. seed_demo_ledger_min     (seeds minimum ledger entities for proof)
      4. runserver 127.0.0.1:8000 (background)
      5. Wait for /health/
      6. proof_phase3_runtime --verbose
      7. Stop server

.PARAMETER HealthTimeoutSeconds
    Seconds to wait for the server to become healthy.  Default: 30.

.EXAMPLE
    .\tools\demo_reset_smoke.ps1
    .\tools\demo_reset_smoke.ps1 -HealthTimeoutSeconds 60
#>
param(
    [int]$HealthTimeoutSeconds = 30,
    [string]$HostUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$msg) {
    Write-Host "==> $msg" -ForegroundColor Cyan
}
function Fail([string]$msg) {
    Write-Host "FAIL: $msg" -ForegroundColor Red
    throw $msg
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$backend  = Join-Path $repoRoot "backend"
$py       = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (!(Test-Path $py)) {
    Fail "Python venv not found at $py. Run: python -m venv .venv && .venv\Scripts\pip install -r requirements.txt"
}

# Required: demo mode so CROWN_DEMO_KEY is populated from settings defaults.
$env:CROWN_DEMO_MODE = "true"

Push-Location $backend

try {
    # ---------------------------------------------------------------
    Write-Step "Migrate"
    & $py manage.py migrate --noinput
    if ($LASTEXITCODE -ne 0) { Fail "migrate failed" }

    # ---------------------------------------------------------------
    Write-Step "Seed demo school (--wipe)"
    & $py manage.py seed_demo_school --wipe
    if ($LASTEXITCODE -ne 0) { Fail "seed_demo_school failed" }

    # ---------------------------------------------------------------
    Write-Step "Seed minimum ledger entities"
    & $py manage.py seed_demo_ledger_min --verbose
    if ($LASTEXITCODE -ne 0) { Fail "seed_demo_ledger_min failed" }

    # ---------------------------------------------------------------
    Write-Step "Start Django server (background)"
    $server = Start-Process `
        -FilePath $py `
        -ArgumentList @("manage.py", "runserver", "127.0.0.1:8000", "--noreload") `
        -PassThru `
        -WindowStyle Hidden
    if (-not $server -or -not $server.Id) { Fail "Failed to start runserver" }

    try {
        # ---------------------------------------------------------------
        Write-Step "Wait for /health/ (timeout: ${HealthTimeoutSeconds}s)"
        $healthUrl = $HostUrl.TrimEnd("/") + "/health/"
        $deadline  = (Get-Date).AddSeconds($HealthTimeoutSeconds)
        $healthy   = $false
        while ((Get-Date) -lt $deadline) {
            try {
                $r = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
                if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) {
                    $healthy = $true
                    break
                }
            } catch {
                Start-Sleep -Milliseconds 500
            }
        }
        if (-not $healthy) {
            Fail "Server did not become healthy within ${HealthTimeoutSeconds}s. Check port 8000."
        }
        Write-Host "   health ok" -ForegroundColor Green

        # ---------------------------------------------------------------
        Write-Step "Run Phase 3 runtime proof ceremony"
        & $py manage.py proof_phase3_runtime --verbose
        if ($LASTEXITCODE -ne 0) { Fail "proof_phase3_runtime failed" }

        Write-Host ""
        Write-Host "DEMO RESET + SMOKE: PASS" -ForegroundColor Green
    }
    finally {
        Write-Step "Stop server"
        try { Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue } catch {}
    }
}
finally {
    Pop-Location
}
