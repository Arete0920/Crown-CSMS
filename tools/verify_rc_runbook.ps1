# tools/verify_rc_runbook.ps1
# Phase 6 Move #2 -- RC Verification Runbook (one-command proof)
#
# What it does:
# 1) Runs all 4 Phase 5 gates  (no server, no DB required for static gates)
# 2) Optionally starts Django dev server (background)
# 3) Acquires auth token deterministically:
#      Priority 1: $env:RC_TOKEN (caller-supplied)
#      Priority 2: POST /api/dev/token/ with X-Demo-Key  (requires CROWN_DEMO_MODE=true)
#      Priority 3: POST /api/auth/login/ with RC_EMAIL + RC_PASSWORD
# 4) Probes a minimal critical endpoint set with required headers
# 5) Prints a PASS/FAIL report and exits non-zero on any failure
#
# Required for endpoint probes:
#   $env:RC_SCHOOL_ID   -- the school UUID (default: demo constant)
#   $env:RC_TOKEN       -- a pre-minted JWT (skips acquisition if set)
#   $env:CROWN_DEMO_KEY -- required by dev-token endpoint
#
# Optional:
#   $env:RC_EMAIL + $env:RC_PASSWORD  -- fallback login if dev-token fails
#   $env:RC_BASE_URL    -- e.g. http://127.0.0.1:9000 (default: http://127.0.0.1:8000)
#   $env:RC_SKIP_SERVER_START=1  -- skip launching Django (assumes already running)
#
# Usage examples:
#   # Full local proof (starts its own server):
#   pwsh -File tools/verify_rc_runbook.ps1
#
#   # With explicit token, external server:
#   $env:RC_TOKEN = "eyJ..."
#   $env:RC_SCHOOL_ID = "19801b59-8c05-4c84-9312-5d792e4e839d"
#   $env:RC_SKIP_SERVER_START = "1"
#   pwsh -File tools/verify_rc_runbook.ps1
#
#   # Gate-only / CI-safe (no server, no probes):
#   pwsh -File tools/verify_rc_runbook.ps1 -SkipProbes -SkipServerStart
#   powershell -ExecutionPolicy Bypass -File tools/verify_rc_runbook.ps1 -SkipProbes -SkipServerStart
#
# Environment toggles:
#   RC_SKIP_PROBES=1         -- same as -SkipProbes (CI mode)
#   RC_SKIP_SERVER_START=1   -- same as -SkipServerStart
#   RC_PROBES_FILE           -- override probe contract JSON path

param(
    [string]$BaseUrl         = $(if ($env:RC_BASE_URL)      { $env:RC_BASE_URL }      else { "http://127.0.0.1:8000" }),
    [string]$SchoolId        = $(if ($env:RC_SCHOOL_ID)     { $env:RC_SCHOOL_ID }     else { "19801b59-8c05-4c84-9312-5d792e4e839d" }),
    [switch]$SkipServerStart = $(if ($env:RC_SKIP_SERVER_START -eq "1") { $true } else { $false }),
    [switch]$SkipProbes      = $(if ($env:RC_SKIP_PROBES    -eq "1") { $true } else { $false }),
    [switch]$GatesOnly,   # alias for -SkipProbes (backward compat)
    [string]$ProbesFile      = $(if ($env:RC_PROBES_FILE)   { $env:RC_PROBES_FILE }   else { "tools/rc_endpoint_probes.json" }),
    [int]$TimeoutSeconds     = 60
)

$ErrorActionPreference = "Stop"

$repoRoot   = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot "backend"
$venvPy     = Join-Path $repoRoot ".venv\Scripts\python.exe"
$py         = if (Test-Path $venvPy) { $venvPy } else { "python" }
. (Join-Path $repoRoot "scripts\Get-RequiredEnv.ps1")

# ── helpers ──────────────────────────────────────────────────────────────────
function Step([string]$name, [scriptblock]$body) {
    Write-Host ""
    Write-Host "==> $name" -ForegroundColor Cyan
    & $body
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { Bail "$name exited $LASTEXITCODE" }
}

function Bail([string]$msg) {
    Write-Host ""
    Write-Host "RC RUNBOOK FAILED: $msg" -ForegroundColor Red
    if ($script:serverProc) { try { Stop-Process -Id $script:serverProc.Id -Force } catch {} }
    exit 1
}

function Wait-Server([string]$url, [int]$sec) {
    Write-Host "  Polling $url (up to ${sec}s)..." -ForegroundColor DarkGray
    $deadline = (Get-Date).AddSeconds($sec)
    while ((Get-Date) -lt $deadline) {
        try {
            $r = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 4 -UseBasicParsing -ErrorAction SilentlyContinue
            if ($r -and $r.StatusCode -lt 600) { return $true }
        } catch {}
        Start-Sleep -Seconds 2
    }
    return $false
}

function Api([string]$method, [string]$path, [hashtable]$hdrs, [hashtable]$body = $null) {
    $url = $BaseUrl.TrimEnd("/") + $path
    $params = @{ Uri=$url; Method=$method; Headers=$hdrs; TimeoutSec=30; UseBasicParsing=$true }
    if ($body) {
        $params["ContentType"] = "application/json"
        $params["Body"] = ($body | ConvertTo-Json -Depth 6 -Compress)
    }
    try {
        $resp = Invoke-WebRequest @params -ErrorAction Stop
        return [pscustomobject]@{ ok=$true; status=[int]$resp.StatusCode; body=$resp.Content }
    } catch [System.Net.WebException] {
        $code = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
        return [pscustomobject]@{ ok=$false; status=$code; body=$_.Exception.Message }
    } catch {
        return [pscustomobject]@{ ok=$false; status=0; body=$_.Exception.Message }
    }
}

# ── 0) sanity ────────────────────────────────────────────────────────────────
if (!(Test-Path $backendDir)) { Bail "missing backend/ directory" }

# ── 1) Phase 5 gates (no server) ─────────────────────────────────────────────
Step "Backend gate  (compileall + manage.py check + makemigrations --check)" {
    & $py tools/verify_backend_gate.py
}
Step "Pytest gate   (curated fast suite: RBAC + tenant + ledger invariants)" {
    & $py tools/verify_pytest_gate.py
}
Step "Contract gate (55 endpoints: existence + allowed methods)" {
    & $py tools/verify_contract_gate.py
}
Step "Migration lock gate (migrate + migrate --check + showmigrations scan)" {
    & $py tools/verify_migration_lock_gate.py
}

if ($GatesOnly -or $SkipProbes) {
    Write-Host ""
    Write-Host "RC RUNBOOK PASSED  (gate-only mode: 4 gates green, probes skipped)" -ForegroundColor Green
    exit 0
}

# ── 2) Start server (background) ──────────────────────────────────────────────
$script:serverProc = $null
if (-not $SkipServerStart) {
    Step "Start Django dev server (background)" {
        Push-Location $backendDir
        try {
            if (-not $env:DJANGO_SETTINGS_MODULE) { $env:DJANGO_SETTINGS_MODULE = "crown_api.settings" }
            $env:DATABASE_URL = Get-RequiredEnv "DATABASE_URL"
            $env:SECRET_KEY = Get-RequiredEnv "DJANGO_SECRET_KEY"
            if (-not $env:DEBUG)                   { $env:DEBUG                   = "1" }
            if (-not $env:ALLOWED_HOSTS)           { $env:ALLOWED_HOSTS           = "127.0.0.1,localhost" }

            $port = if ($BaseUrl -match ":(\d+)") { $Matches[1] } else { "8000" }
            $script:serverProc = Start-Process `
                -FilePath $py `
                -ArgumentList @("manage.py","runserver","127.0.0.1:$port","--noreload") `
                -PassThru -WindowStyle Hidden
        } finally { Pop-Location }
    }

    $healthUrl = $BaseUrl.TrimEnd("/") + "/health/"
    if (-not (Wait-Server $healthUrl $TimeoutSeconds)) {
        if ($script:serverProc) { try { Stop-Process -Id $script:serverProc.Id -Force } catch {} }
        Bail "server did not become healthy within ${TimeoutSeconds}s at $healthUrl"
    }
    Write-Host "  Server up." -ForegroundColor DarkGray
}

try {
    # ── 3) Acquire token ─────────────────────────────────────────────────────
    $token    = $env:RC_TOKEN
    $demoKey  = $env:CROWN_DEMO_KEY
    $baseHdrs = @{}
    if ($SchoolId) { $baseHdrs["X-School-Id"] = $SchoolId }

    if (-not $token) {
        Write-Host ""
        Write-Host "==> Acquire auth token" -ForegroundColor Cyan

        # Priority 2: dev-token endpoint (POST, requires X-Demo-Key)
        if ($demoKey) {
            $devHdrs = $baseHdrs.Clone()
            $devHdrs["X-Demo-Key"] = $demoKey
            $r = Api "POST" "/api/dev/token/" $devHdrs
            if ($r.ok -or $r.status -eq 200) {
                try {
                    $j = $r.body | ConvertFrom-Json
                    if ($j.access) {
                        $token = $j.access
                        # dev-token also returns school_id — use it if caller did not override
                        if ($j.school_id -and -not $env:RC_SCHOOL_ID) {
                            $SchoolId = $j.school_id
                            $baseHdrs["X-School-Id"] = $SchoolId
                        }
                        Write-Host "  Token acquired from dev-token endpoint." -ForegroundColor DarkGray
                    }
                } catch {}
            }
        }

        # Priority 3: login endpoint
        if (-not $token -and $env:RC_EMAIL -and $env:RC_PASSWORD) {
            $r = Api "POST" "/api/auth/login/" $baseHdrs @{ email=$env:RC_EMAIL; password=$env:RC_PASSWORD }
            if ($r.status -eq 200) {
                try {
                    $j = $r.body | ConvertFrom-Json
                    if ($j.access) {
                        $token = $j.access
                        Write-Host "  Token acquired via login." -ForegroundColor DarkGray
                    }
                } catch {}
            }
        }
    }

    if (-not $token) {
        Bail "no auth token. Set RC_TOKEN, or CROWN_DEMO_KEY (for dev-token), or RC_EMAIL+RC_PASSWORD."
    }

    # ── 4) Endpoint probes (JSON-driven -- edit tools/rc_endpoint_probes.json, not this file) ──
    $authHdrs = $baseHdrs.Clone()
    $authHdrs["Authorization"] = "Bearer $token"

    # Resolve probe file (absolute or relative to repo root)
    $contractPath = if ([System.IO.Path]::IsPathRooted($ProbesFile)) {
        $ProbesFile
    } else {
        Join-Path $repoRoot $ProbesFile
    }

    if (!(Test-Path $contractPath)) {
        Bail "probe contract not found: $contractPath`n  Set -ProbesFile or RC_PROBES_FILE, or create tools/rc_endpoint_probes.json."
    }

    $contract = Get-Content -Path $contractPath -Raw | ConvertFrom-Json
    if (-not $contract.probes -or $contract.probes.Count -eq 0) {
        Bail "probe contract has no probes: $contractPath"
    }

    Write-Host ""
    Write-Host "==> Endpoint probes  ($($contract.probes.Count) checks from $([System.IO.Path]::GetFileName($contractPath)))" -ForegroundColor Cyan

    $results = foreach ($p in $contract.probes) {
        $method  = ([string]$p.method).ToUpperInvariant()
        $path    = [string]$p.path
        $expect  = @($p.expect | ForEach-Object { [int]$_ })
        $needAuth    = [bool]$p.requiresAuth
        $needSchool  = [bool]$p.requiresSchoolId

        # Build per-probe headers
        $hdr = @{}
        if ($needSchool) {
            if ([string]::IsNullOrWhiteSpace($SchoolId)) {
                Write-Warning "Skipping '$($p.name)': requires X-School-Id but RC_SCHOOL_ID is not set."
                [pscustomobject]@{ Result="SKIP"; Status=0; Probe="$method $path" }
                continue
            }
            $hdr["X-School-Id"] = $SchoolId
        }
        if ($needAuth) { $hdr["Authorization"] = "Bearer $token" }

        $r    = Api $method $path $hdr
        $pass = $expect -contains $r.status
        [pscustomobject]@{
            Result = if ($pass) { "PASS" } else { "FAIL" }
            Status = $r.status
            Probe  = "$method $path"
        }
    }

    $results | Format-Table -AutoSize

    $failures = @($results | Where-Object { $_.Result -eq "FAIL" })
    if ($failures.Count -gt 0) {
        Bail "$($failures.Count) probe(s) failed (see table). Edit $contractPath if paths changed."
    }

    $total = ($results | Measure-Object).Count
    Write-Host "RC RUNBOOK PASSED  ($total probes + 4 gates green)" -ForegroundColor Green
    exit 0

} finally {
    if ($script:serverProc) {
        try {
            Stop-Process -Id $script:serverProc.Id -Force
            Write-Host "  Stopped dev server PID $($script:serverProc.Id)" -ForegroundColor DarkGray
        } catch {}
    }
}
