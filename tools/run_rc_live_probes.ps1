# tools/run_rc_live_probes.ps1
# One-command live endpoint probe runner.
#
# Does NOT start Django -- start your backend separately (runserver, docker, Azure, etc.).
# Runs only the endpoint probes, not the static gates (those run in CI).
#
# Required env vars:
#   RC_SCHOOL_ID  -- tenant UUID (e.g. 19801b59-8c05-4c84-9312-5d792e4e839d)
#   RC_TOKEN      -- pre-minted JWT (preferred)
#   -- OR --
#   RC_EMAIL + RC_PASSWORD  -- credentials for login fallback
#
# Optional:
#   RC_BASE_URL    -- default: http://127.0.0.1:8000
#   RC_PROBES_FILE -- default: tools/rc_endpoint_probes.json
#   CROWN_DEMO_KEY -- enables dev-token endpoint (requires CROWN_DEMO_MODE=true on server)
#
# Quick start:
#   $env:RC_BASE_URL  = "http://127.0.0.1:8000"
#   $env:RC_SCHOOL_ID = "19801b59-8c05-4c84-9312-5d792e4e839d"
#   $env:RC_TOKEN     = "eyJ..."   # get from POST /api/dev/token/ or POST /api/auth/login/
#   powershell -ExecutionPolicy Bypass -File tools/run_rc_live_probes.ps1

$ErrorActionPreference = "Stop"

if (-not $env:RC_BASE_URL)    { $env:RC_BASE_URL    = "http://127.0.0.1:8000" }
if (-not $env:RC_PROBES_FILE) { $env:RC_PROBES_FILE = "tools/rc_endpoint_probes.json" }
if (-not $env:RC_SKIP_SERVER_START) { $env:RC_SKIP_SERVER_START = "1" }

# Validation
if ([string]::IsNullOrWhiteSpace($env:RC_SCHOOL_ID)) {
    Write-Host "ERROR: RC_SCHOOL_ID is required." -ForegroundColor Red
    Write-Host "  Set it to your school UUID, e.g.:" -ForegroundColor DarkGray
    Write-Host "  `$env:RC_SCHOOL_ID = '19801b59-8c05-4c84-9312-5d792e4e839d'" -ForegroundColor DarkGray
    exit 1
}

if ([string]::IsNullOrWhiteSpace($env:RC_TOKEN) -and
    ([string]::IsNullOrWhiteSpace($env:RC_EMAIL) -or [string]::IsNullOrWhiteSpace($env:RC_PASSWORD)) -and
    [string]::IsNullOrWhiteSpace($env:CROWN_DEMO_KEY)) {
    Write-Host "ERROR: provide one of:" -ForegroundColor Red
    Write-Host "  RC_TOKEN (JWT)             -- preferred" -ForegroundColor DarkGray
    Write-Host "  CROWN_DEMO_KEY             -- uses POST /api/dev/token/ (requires CROWN_DEMO_MODE=true on server)" -ForegroundColor DarkGray
    Write-Host "  RC_EMAIL + RC_PASSWORD     -- uses POST /api/auth/login/" -ForegroundColor DarkGray
    exit 1
}

Write-Host ""
Write-Host "==> RC Live Endpoint Probes" -ForegroundColor Cyan
Write-Host "  Base:        $env:RC_BASE_URL" -ForegroundColor DarkGray
Write-Host "  School ID:   $env:RC_SCHOOL_ID" -ForegroundColor DarkGray
Write-Host "  Probes file: $env:RC_PROBES_FILE" -ForegroundColor DarkGray

# Delegate to the full runbook in SkipServerStart mode (probes enabled)
powershell -ExecutionPolicy Bypass -File tools/verify_rc_runbook.ps1 -SkipServerStart
