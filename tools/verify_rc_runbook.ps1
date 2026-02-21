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
#   # Gate-only (no server, no probes):
#   pwsh -File tools/verify_rc_runbook.ps1 -GatesOnly

param(
    [string]$BaseUrl       = $(if ($env:RC_BASE_URL)   { $env:RC_BASE_URL }   else { "http://127.0.0.1:8000" }),
    [string]$SchoolId      = $(if ($env:RC_SCHOOL_ID)  { $env:RC_SCHOOL_ID }  else { "19801b59-8c05-4c84-9312-5d792e4e839d" }),
    [switch]$SkipServerStart = $(if ($env:RC_SKIP_SERVER_START -eq "1") { $true } else { $false }),
    [switch]$GatesOnly,
    [int]$TimeoutSeconds   = 60
)

$ErrorActionPreference = "Stop"

$repoRoot   = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot "backend"
$venvPy     = Join-Path $repoRoot ".venv\Scripts\python.exe"
$py         = if (Test-Path $venvPy) { $venvPy } else { "python" }

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

if ($GatesOnly) {
    Write-Host ""
    Write-Host "RC RUNBOOK PASSED  (gates-only mode)" -ForegroundColor Green
    exit 0
}

# ── 2) Start server (background) ──────────────────────────────────────────────
$script:serverProc = $null
if (-not $SkipServerStart) {
    Step "Start Django dev server (background)" {
        Push-Location $backendDir
        try {
            if (-not $env:DJANGO_SETTINGS_MODULE) { $env:DJANGO_SETTINGS_MODULE = "crown_api.settings" }
            if (-not $env:DATABASE_URL)            { $env:DATABASE_URL            = "sqlite:///./rc.sqlite3" }
            if (-not $env:SECRET_KEY)              { $env:SECRET_KEY              = "rc-not-secret" }
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

    # ── 4) Critical endpoint probes ───────────────────────────────────────────
    $authHdrs = $baseHdrs.Clone()
    $authHdrs["Authorization"] = "Bearer $token"

    # Endpoints taken directly from the CONTRACT GATE (verified real paths).
    # Each entry: name, method, path, headers, expected HTTP status codes.
    $probes = @(
        # Health — public, no auth
        [pscustomobject]@{ Name="GET /health/";                    Method="GET";  Path="/health/";                    Hdrs=$baseHdrs; Expect=@(200,204) }
        [pscustomobject]@{ Name="GET /api/health/";                Method="GET";  Path="/api/health/";                Hdrs=$baseHdrs; Expect=@(200,204) }

        # Auth surface
        [pscustomobject]@{ Name="GET /api/auth/me/";               Method="GET";  Path="/api/auth/me/";               Hdrs=$authHdrs; Expect=@(200)     }

        # Director / persona summaries (auth + tenant)
        [pscustomobject]@{ Name="GET /api/director/dashboard/";    Method="GET";  Path="/api/director/dashboard/";    Hdrs=$authHdrs; Expect=@(200)     }
        [pscustomobject]@{ Name="GET /api/director/aid/summary/";  Method="GET";  Path="/api/director/aid/summary/";  Hdrs=$authHdrs; Expect=@(200)     }
        [pscustomobject]@{ Name="GET /api/director/finance/summary/"; Method="GET"; Path="/api/director/finance/summary/"; Hdrs=$authHdrs; Expect=@(200) }

        # SIS / roster
        [pscustomobject]@{ Name="GET /api/students/";              Method="GET";  Path="/api/students/";              Hdrs=$authHdrs; Expect=@(200)     }
        [pscustomobject]@{ Name="GET /api/households/";            Method="GET";  Path="/api/households/";            Hdrs=$authHdrs; Expect=@(200)     }

        # Finance
        [pscustomobject]@{ Name="GET /api/ledger/invariants/";     Method="GET";  Path="/api/ledger/invariants/";     Hdrs=$authHdrs; Expect=@(200)     }
        [pscustomobject]@{ Name="GET /api/billing/invoices/";      Method="GET";  Path="/api/billing/invoices/";      Hdrs=$authHdrs; Expect=@(200)     }

        # Academics
        [pscustomobject]@{ Name="GET /api/academics/courses/";     Method="GET";  Path="/api/academics/courses/";     Hdrs=$authHdrs; Expect=@(200)     }
        [pscustomobject]@{ Name="GET /api/academics/sections/";    Method="GET";  Path="/api/academics/sections/";    Hdrs=$authHdrs; Expect=@(200)     }

        # Applications
        [pscustomobject]@{ Name="GET /api/applications/";          Method="GET";  Path="/api/applications/";          Hdrs=$authHdrs; Expect=@(200)     }

        # Ops / system (no auth required)
        [pscustomobject]@{ Name="GET /api/ops/summary/";           Method="GET";  Path="/api/ops/summary/";           Hdrs=$baseHdrs; Expect=@(200)     }
    )

    Write-Host ""
    Write-Host "==> Critical endpoint probes  ($($probes.Count) checks)" -ForegroundColor Cyan

    $results = foreach ($p in $probes) {
        $r = Api $p.Method $p.Path $p.Hdrs
        $pass = $p.Expect -contains $r.status
        [pscustomobject]@{
            Result  = if ($pass) { "PASS" } else { "FAIL" }
            Status  = $r.status
            Probe   = $p.Name
        }
    }

    $results | Format-Table -AutoSize

    $failures = $results | Where-Object { $_.Result -eq "FAIL" }
    if ($failures) {
        $n = ($failures | Measure-Object).Count
        Bail "$n probe(s) failed (see table). Common causes: missing/wrong token, missing RC_SCHOOL_ID, or endpoint not seeded."
    }

    Write-Host ""
    Write-Host "RC RUNBOOK PASSED  ($($probes.Count) probes + 4 gates green)" -ForegroundColor Green
    exit 0

} finally {
    if ($script:serverProc) {
        try {
            Stop-Process -Id $script:serverProc.Id -Force
            Write-Host "  Stopped dev server PID $($script:serverProc.Id)" -ForegroundColor DarkGray
        } catch {}
    }
}
