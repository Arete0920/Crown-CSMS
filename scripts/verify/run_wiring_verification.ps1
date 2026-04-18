$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repoRoot

$out = Join-Path $repoRoot "artifacts\wiring-proof"
New-Item -ItemType Directory -Force -Path $out | Out-Null

function Write-Step([string]$msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

function Invoke-Checked([scriptblock]$block, [string]$failMessage) {
    try {
        & $block
        if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
            throw $failMessage
        }
    } catch {
        Write-Host "FAIL: $failMessage" -ForegroundColor Red
        throw
    }
}

Write-Step "Django sanity"
Invoke-Checked { python --version | Tee-Object -FilePath (Join-Path $out "python-version.txt") } "Python not available"
Invoke-Checked { python manage.py check 2>&1 | Tee-Object -FilePath (Join-Path $out "django-check.txt") } "Django check failed"
Invoke-Checked { python manage.py showmigrations 2>&1 | Tee-Object -FilePath (Join-Path $out "django-migrations.txt") } "showmigrations failed"

Write-Step "Frontend route wiring"
Invoke-Checked { powershell -ExecutionPolicy Bypass -File .\tools\verify\check_frontend_wiring.ps1 } "Frontend wiring check failed"

Write-Step "Tenant isolation test suite"
if (-not (Test-Path ".\tests\test_tenant_isolation.py")) {
    throw "Missing tests\test_tenant_isolation.py"
}
Invoke-Checked { pytest tests/test_tenant_isolation.py -v 2>&1 | Tee-Object -FilePath (Join-Path $out "tenant-isolation-pytest-output.txt") } "Tenant isolation tests failed"

Write-Step "Golden path test suite"
if (-not (Test-Path ".\tests\test_golden_path.py")) {
    throw "Missing tests\test_golden_path.py"
}
Invoke-Checked { pytest tests/test_golden_path.py -v 2>&1 | Tee-Object -FilePath (Join-Path $out "golden-path-pytest-output.txt") } "Golden path tests failed"

Write-Step "HTTP health and docs surface"
Invoke-Checked { powershell -ExecutionPolicy Bypass -File .\tools\verify\check_http_surface.ps1 } "HTTP health/docs verification failed"

Write-Step "Playwright route and login smoke"
Push-Location frontend\dashboards
$env:DEMO_BASE_URL = if ($env:DEMO_BASE_URL) { $env:DEMO_BASE_URL } else { "http://localhost:3000" }
$env:DEMO_EMAIL = if ($env:DEMO_EMAIL) { $env:DEMO_EMAIL } else { "playwright@crown-demo.local" }
$env:DEMO_PASSWORD = if ($env:DEMO_PASSWORD) { $env:DEMO_PASSWORD } else { "PlaywrightDemo1!" }
Invoke-Checked { npx playwright test tests/wiring-proof.spec.ts --reporter=line } "Playwright wiring proof failed"
Pop-Location

Write-Step "Summary"
@"
PASS

Generated artifacts:
- artifacts\wiring-proof\python-version.txt
- artifacts\wiring-proof\django-check.txt
- artifacts\wiring-proof\django-migrations.txt
- artifacts\wiring-proof\frontend-wiring-summary.md
- artifacts\wiring-proof\missing-routes.csv
- artifacts\wiring-proof\tenant-isolation-pytest-output.txt
- artifacts\wiring-proof\golden-path-pytest-output.txt
- artifacts\wiring-proof\http-health-check.txt
- artifacts\wiring-proof\http-docs-check.txt
- frontend\dashboards\artifacts\wiring-proof\playwright\*.png
"@ | Set-Content (Join-Path $out "WIRING_PROOF_RESULT.txt")

Write-Host "PASS: full wiring verification is green." -ForegroundColor Green