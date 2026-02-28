# CROWN_MAGUS0_AUDIT.ps1 -- Crown2026 Deep / Trust-Nothing Audit Pack
# -----------------------------------------------------------------------
# Enumerates every surface (backend, frontend, DB, CI/CD, secrets,
# tenant boundaries, auth, comms) and fails hard on anything ambiguous.
#
# Compatible with Windows PowerShell 5.1 and PowerShell 7+.
#
# Usage:
#   powershell -File tools/audit/CROWN_MAGUS0_AUDIT.ps1           # full
#   powershell -File tools/audit/CROWN_MAGUS0_AUDIT.ps1 -Fast     # skip slow steps
#   powershell -File tools/audit/CROWN_MAGUS0_AUDIT.ps1 -NoSecrets
#
# Output:
#   artifacts/audit/CrownMagus0/audit-<timestamp>/
#     audit.log            <- full transcript
#     SUMMARY.txt          <- pass/fail index
#     django-migrations.txt
#     settings-scan.txt
#     tenant-surface.txt
#     backend-gate.txt
#     dep-python.txt
#     dep-node.txt
#     secret-scan.txt
#     ci-workflows.txt
#     permission-surface.txt
#     pii-field-scan.txt
#     audit-log-coverage.txt
#

param(
    [switch]$Fast,
    [switch]$NoSecrets
)

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

$script:PassList = @()
$script:FailList = @()
$script:WarnList = @()
$script:OutDir   = $null

function Write-Divider {
    param([string]$text, [string]$color = "Cyan")
    $line = ("=" * 68)
    Write-Host ""
    Write-Host $line -ForegroundColor $color
    Write-Host "  $text" -ForegroundColor $color
    Write-Host $line -ForegroundColor $color
}

function Step {
    param([string]$name, [scriptblock]$fn)
    Write-Divider "STEP: $name" "DarkCyan"
    try {
        & $fn
        $script:PassList += $name
        Write-Host "  PASS: $name" -ForegroundColor Green
    } catch {
        $script:FailList += $name
        Write-Host "  FAIL: $name" -ForegroundColor Red
        Write-Host "        $($_.Exception.Message)" -ForegroundColor Red
        throw
    }
}

function SoftStep {
    param([string]$name, [scriptblock]$fn)
    Write-Divider "SOFT: $name" "DarkYellow"
    try {
        & $fn
        $script:PassList += $name
        Write-Host "  PASS: $name" -ForegroundColor Green
    } catch {
        $script:WarnList += $name
        Write-Host "  WARN (non-blocking): $name" -ForegroundColor Yellow
        Write-Host "       $($_.Exception.Message)" -ForegroundColor DarkYellow
    }
}

function Require-Command {
    param([string]$cmd, [string]$hint)
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        throw "Required command not found: '$cmd'. $hint"
    }
}

function Out-Artifact {
    param([string]$name, $content)
    $path = Join-Path $script:OutDir $name
    $content | Out-File -FilePath $path -Encoding utf8
    return $path
}

# ---------------------------------------------------------------------------
# Locate repo root (script lives in tools/audit/)
# ---------------------------------------------------------------------------

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$backend  = Join-Path $repoRoot "backend"
$frontend = Join-Path $repoRoot "frontend\dashboards"

# Crown2026 venv is at REPO ROOT -- not inside backend/
$py = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    $pyCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pyCmd) {
        $py = $pyCmd.Source
    } else {
        throw "Python not found. Install Python 3.11+ or create .venv at repo root."
    }
}

# ---------------------------------------------------------------------------
# Artifact directory
# ---------------------------------------------------------------------------

$ts      = Get-Date -Format "yyyyMMdd-HHmmss"
$artBase = Join-Path $repoRoot "artifacts\audit\CrownMagus0"
$outDir  = Join-Path $artBase ("audit-" + $ts)
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$script:OutDir = $outDir

$logFile = Join-Path $outDir "audit.log"
Start-Transcript -Path $logFile | Out-Null

Write-Host ""
Write-Host "***** CROWN MAGUS 0 -- TRUST-NOTHING AUDIT PACK *****" -ForegroundColor Magenta
Write-Host "  Crown2026 Deep Security / Integrity / Completeness Audit" -ForegroundColor Magenta
Write-Host ""
Write-Host "  Timestamp   : $ts"
Write-Host "  Repo root   : $repoRoot"
Write-Host "  Python      : $py"
Write-Host "  Artifacts   : $outDir"
Write-Host "  Fast mode   : $Fast"
Write-Host "  Skip secrets: $NoSecrets"

try {

# ===========================================================================
# PHASE A -- PREFLIGHT
# ===========================================================================

Step "A1: Preflight -- required commands present" {
    Require-Command "git"  "Install git and add to PATH."
    Require-Command "node" "Install Node 18+ and add to PATH."
    Require-Command "npm"  "Install npm."
    if (-not (Test-Path $py))                               { throw "Python not found at: $py" }
    if (-not (Test-Path $backend))                          { throw "backend/ directory missing" }
    if (-not (Test-Path $frontend))                         { throw "frontend/dashboards/ directory missing" }
    if (-not (Test-Path (Join-Path $backend "manage.py")))  { throw "backend/manage.py missing" }
    Write-Host "  All required commands and directories found."
}

Step "A2: Git state -- branch, HEAD SHA, dirty files" {
    Push-Location $repoRoot
    $branch = (git rev-parse --abbrev-ref HEAD) -join ""
    $sha    = (git rev-parse HEAD) -join ""
    $dirty  = git status --porcelain
    $recent = git log --oneline -10
    Write-Host "  Branch: $branch"
    Write-Host "  SHA   : $sha"
    if ($dirty) {
        Write-Host "  DIRTY (uncommitted changes):" -ForegroundColor Yellow
        $dirty | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
    } else {
        Write-Host "  Working tree: clean" -ForegroundColor Green
    }
    $lines = @("Branch: $branch", "SHA: $sha", "", "Recent commits:") +
             @($recent) +
             @("", "Dirty files:") +
             @(if ($dirty) { $dirty } else { "(clean)" })
    Out-Artifact "git-state.txt" $lines | Out-Null
    Pop-Location
}

# ===========================================================================
# PHASE B -- SECRETS SCAN
# ===========================================================================

if (-not $NoSecrets) {
    Step "B1: Secret scan -- pattern grep (METADATA ONLY; values not printed)" {
        Push-Location $repoRoot
        $literalPatterns = @(
            "PRIVATE KEY-----",
            "BEGIN RSA PRIVATE KEY",
            "BEGIN EC PRIVATE KEY",
            "BEGIN OPENSSH PRIVATE KEY"
        )
        $regexPatterns = @(
            "AWS_SECRET_ACCESS_KEY\s*=\s*[A-Za-z0-9/+]{20,}",
            "stripe.*sk_live_[A-Za-z0-9]{24,}"
        )
        # git pathspecs to exclude generated/minified files and the scanner itself
        $excl = @(":(exclude)*.min.js",":(exclude)package-lock.json",":(exclude)yarn.lock",
                  ":(exclude)artifacts/**",":(exclude)*.log",":(exclude)*.lock",
                  ":(exclude).github/workflows/**",":(exclude)tools/audit/**")

        $scanResults = @()
        $hitCount    = 0

        foreach ($p in $literalPatterns) {
            $hits = git grep -l -i $p -- @excl 2>$null
            if ($hits) {
                $hitCount++
                $scanResults += "HIT | literal=$p | files=$($hits -join ',')"
                Write-Host "  WARNING: literal pattern hit: '$p'" -ForegroundColor Red
                Write-Host "           files (metadata only): $($hits -join ', ')" -ForegroundColor DarkRed
            }
        }
        foreach ($p in $regexPatterns) {
            $hits = git grep -l -E $p -- @excl 2>$null
            if ($hits) {
                $hitCount++
                $scanResults += "HIT | regex=$p | files=$($hits -join ',')"
                Write-Host "  WARNING: regex pattern hit: '$p'" -ForegroundColor Red
                Write-Host "           files (metadata only): $($hits -join ', ')" -ForegroundColor DarkRed
            }
        }

        if ($scanResults.Count -eq 0) { $scanResults = @("No hits found.") }
        Out-Artifact "secret-scan.txt" $scanResults | Out-Null

        if ($hitCount -gt 0) {
            throw "Secret scan: $hitCount pattern match(es). See secret-scan.txt. Redact/rotate before proceeding."
        }
        Write-Host "  No secret patterns found in tracked files." -ForegroundColor Green
        Pop-Location
    }
} else {
    Write-Host "  [NoSecrets] Skipping secret scan" -ForegroundColor Yellow
    $script:WarnList += "B1: Secret scan SKIPPED (NoSecrets flag)"
}

# ===========================================================================
# PHASE C -- BACKEND GATES
# ===========================================================================

# Set deterministic CI env vars
$env:DJANGO_SETTINGS_MODULE = "crown_api.settings"
$env:SECRET_KEY             = "ci-audit-not-a-real-secret"
$env:DEBUG                  = "0"
$env:ALLOWED_HOSTS          = "localhost,127.0.0.1"
$env:DATABASE_URL           = "sqlite:///./ci_audit.sqlite3"

Step "C1: Backend -- compile all Python (syntax check)" {
    $res = & $py -m compileall -q (Join-Path $repoRoot "backend") 2>&1
    if ($LASTEXITCODE -ne 0) {
        Out-Artifact "compile-errors.txt" $res | Out-Null
        throw "compileall failed -- syntax errors exist. See compile-errors.txt."
    }
    Write-Host "  Python compile: OK"
}

Step "C2: Backend -- Django system checks" {
    Push-Location $backend
    $res = & $py manage.py check 2>&1
    Out-Artifact "django-check.txt" $res | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Django system checks failed. See django-check.txt." }
    Write-Host "  Django system checks: OK"
    Pop-Location
}

Step "C3: Backend -- migration drift (no pending uninspected model changes)" {
    Push-Location $backend
    $res = & $py manage.py makemigrations --check --dry-run 2>&1
    Out-Artifact "migrations-drift.txt" $res | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Pending model changes exist without migrations. Run makemigrations. See migrations-drift.txt."
    }
    Write-Host "  No migration drift."
    Pop-Location
}

Step "C4: Backend -- migration state list (evidence)" {
    Push-Location $backend
    $res = & $py manage.py showmigrations --list 2>&1
    Out-Artifact "django-migrations.txt" $res | Out-Null
    Write-Host "  Migration state captured -- django-migrations.txt"
    Pop-Location
}

Step "C5: Backend -- tenant isolation tripwires (AST scan)" {
    Push-Location $repoRoot
    $res = & $py tools\verify_backend_gate.py --tenant-checks-only 2>&1
    Out-Artifact "tenant-surface.txt" $res | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Tenant tripwire violations found. See tenant-surface.txt." }
    Write-Host "  Tenant isolation: CLEAN"
    Pop-Location
}

Step "C6: Backend -- URL collision scan" {
    Push-Location $repoRoot
    $res = & $py tools\verify_url_surface.py 2>&1
    Out-Artifact "url-collision-scan.txt" $res | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "URL collision or scan errors. See url-collision-scan.txt."
    }
    Write-Host "  URL collision scan: CLEAN"
    Pop-Location
}

Step "C7: Backend -- dangerous settings scan (CORS/DEBUG/CSRF)" {
    $settingsFile = Join-Path $backend "crown_api\settings.py"
    if (-not (Test-Path $settingsFile)) {
        $settingsFile = Join-Path $backend "crown_api\settings\base.py"
    }
    if (-not (Test-Path $settingsFile)) { throw "Cannot locate settings.py." }

    $flagPatterns = @(
        "DEBUG","DEMO_MODE","CORS_ALLOW_ALL_ORIGINS","CORS_ALLOW_CREDENTIALS",
        "CSRF_TRUSTED_ORIGINS","ALLOWED_HOSTS","SECURE_","SESSION_COOKIE_SECURE",
        "CSRF_COOKIE_SECURE","X_FRAME_OPTIONS","TENANT_HEADER_REQUIRED","BUILD_SHA"
    )
    $out = @("Settings security scan: $(Split-Path $settingsFile -Leaf)", ("=" * 60))
    foreach ($f in $flagPatterns) {
        $hits = Select-String -Path $settingsFile -Pattern $f -SimpleMatch -ErrorAction SilentlyContinue
        if ($hits) {
            foreach ($h in $hits) { $out += "  L$($h.LineNumber): $($h.Line.Trim())" }
        }
    }
    Out-Artifact "settings-scan.txt" $out | Out-Null
    Write-Host "  Settings scan written -- settings-scan.txt"

    $corsUnsafe = Select-String -Path $settingsFile -Pattern "CORS_ALLOW_ALL_ORIGINS\s*=\s*True" -ErrorAction SilentlyContinue
    if ($corsUnsafe) { throw "DANGER: CORS_ALLOW_ALL_ORIGINS = True in settings." }
    Write-Host "  CORS_ALLOW_ALL_ORIGINS: safe."
}

Step "C8: Backend -- full backend gate (compile + checks + migration + tenant)" {
    Push-Location $repoRoot
    $res = & $py tools\verify_backend_gate.py 2>&1
    Out-Artifact "backend-gate.txt" $res | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Backend gate FAILED. See backend-gate.txt." }
    Write-Host "  Backend gate: PASS"
    Pop-Location
}

if (-not $Fast) {
    Step "C9: Backend -- full pytest suite" {
        Push-Location $repoRoot
        $res = & $py -m pytest backend -q --tb=short 2>&1
        Out-Artifact "pytest-results.txt" $res | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "pytest failures. See pytest-results.txt." }
        Write-Host "  All tests pass."
        Pop-Location
    }
} else {
    Write-Host "  [Fast] Skipping full pytest" -ForegroundColor Yellow
    $script:WarnList += "C9: Full pytest SKIPPED (Fast mode)"

    Step "C9-fast: Contract + permission + subscription tests (fast subset)" {
        Push-Location $repoRoot
        $testDirs = @("backend\subscriptions\tests","backend\tests") |
            Where-Object { Test-Path (Join-Path $repoRoot $_) }
        if ($testDirs.Count -gt 0) {
            $res = & $py -m pytest @testDirs -q --tb=short 2>&1
            Out-Artifact "pytest-fast.txt" $res | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "Fast pytest subset failed. See pytest-fast.txt." }
            Write-Host "  Fast pytest subset: PASS"
        } else {
            Write-Host "  No test directories found; nothing to run." -ForegroundColor Yellow
        }
        Pop-Location
    }
}

# ===========================================================================
# PHASE D -- DEPENDENCY AUDIT
# ===========================================================================

Step "D1: Python dependency audit (pip-audit)" {
    Push-Location $repoRoot
    & $py -m pip install -q pip-audit 2>&1 | Out-Null
    $reqFile = Join-Path $repoRoot "requirements.txt"
    if (-not (Test-Path $reqFile)) { $reqFile = Join-Path $backend "requirements.txt" }
    if (-not (Test-Path $reqFile)) { throw "requirements.txt not found." }
    $res = & $py -m pip_audit -r $reqFile 2>&1
    Out-Artifact "dep-python.txt" $res | Out-Null
    if ($LASTEXITCODE -ne 0) {
        $script:WarnList += "D1: Python dep-audit found vulnerabilities (review dep-python.txt)"
        Write-Host "  pip-audit: vulnerabilities found -- dep-python.txt (WARN, not hard fail)" -ForegroundColor Yellow
        # To hard-fail, replace the above with: throw "Python dep vulnerabilities found."
    } else {
        Write-Host "  Python deps: clean."
    }
    Pop-Location
}

Step "D2: Node dependency audit (npm audit --audit-level=high)" {
    Push-Location $frontend
    $res = npm audit --audit-level=high 2>&1
    Out-Artifact "dep-node.txt" $res | Out-Null
    if ($LASTEXITCODE -ne 0) {
        $script:WarnList += "D2: Node HIGH/CRIT vulnerabilities found (review dep-node.txt)"
        Write-Host "  npm audit: HIGH/CRITICAL issues -- dep-node.txt (WARN)" -ForegroundColor Yellow
    } else {
        Write-Host "  Node deps: no HIGH/CRITICAL issues."
    }
    Pop-Location
}

# ===========================================================================
# PHASE E -- FRONTEND
# ===========================================================================

Step "E1: Frontend -- npm ci (clean install)" {
    Push-Location $frontend
    npm ci 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "npm ci failed." }
    Write-Host "  npm ci: OK"
    Pop-Location
}

Step "E2: Frontend -- lint" {
    Push-Location $frontend
    $pkgRaw = Get-Content "package.json" -Raw
    $pkg    = $pkgRaw | ConvertFrom-Json
    $hasLint = $pkg.scripts.PSObject.Properties.Name -contains "lint"
    if ($hasLint) {
        $res = npm run lint 2>&1
        Out-Artifact "frontend-lint.txt" $res | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Frontend lint failed. See frontend-lint.txt." }
        Write-Host "  Lint: PASS"
    } else {
        Write-Host "  No 'lint' script defined -- skipping." -ForegroundColor Yellow
        $script:WarnList += "E2: Frontend lint SKIPPED (no lint script)"
    }
    Pop-Location
}

Step "E3: Frontend -- production build" {
    Push-Location $frontend
    $res = npm run build 2>&1
    Out-Artifact "frontend-build.txt" $res | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed. See frontend-build.txt." }
    Write-Host "  Build: SUCCESS"
    Pop-Location
}

if (-not $Fast) {
    SoftStep "E4: Frontend -- Playwright smoke (if configured)" {
        Push-Location $frontend
        $hasE2E = (Get-ChildItem "playwright.config.*" -ErrorAction SilentlyContinue).Count -gt 0
        if (-not $hasE2E) { throw "No playwright.config.* -- no E2E tests configured." }
        $res = npm run test:e2e 2>&1
        Out-Artifact "frontend-playwright.txt" $res | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Playwright E2E failed. See frontend-playwright.txt." }
        Pop-Location
    }
} else {
    Write-Host "  [Fast] Skipping Playwright" -ForegroundColor Yellow
    $script:WarnList += "E4: Playwright E2E SKIPPED (Fast mode)"
}

# ===========================================================================
# PHASE F -- OPERATIONAL CHECKS
# ===========================================================================

SoftStep "F1: Health probe (requires backend running on :8000)" {
    $healthUrl = "http://127.0.0.1:8000/api/health/"
    $resp = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    Out-Artifact "health-probe.txt" $resp.Content | Out-Null
    $preview = $resp.Content.Substring(0, [Math]::Min(200, $resp.Content.Length))
    Write-Host "  Health: $($resp.StatusCode) -- $preview"
}

SoftStep "F2: Integrity probe (requires backend running on :8000)" {
    $intUrl = "http://127.0.0.1:8000/api/integrity/"
    $resp   = Invoke-WebRequest -Uri $intUrl -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    Out-Artifact "integrity-probe.txt" $resp.Content | Out-Null
    Write-Host "  Integrity: $($resp.StatusCode)"
}

Step "F3: CI/CD -- workflow inventory" {
    $wfDir = Join-Path $repoRoot ".github\workflows"
    if (-not (Test-Path $wfDir)) { throw ".github/workflows not found." }
    $wfs = Get-ChildItem $wfDir -Filter "*.yml" | Sort-Object Name
    $out = @("GitHub Actions Workflows ($($wfs.Count) total)", ("=" * 50))
    foreach ($w in $wfs) {
        $out += ""
        $out += "File: $($w.Name)"
        $triggers = Select-String -Path $w.FullName `
            -Pattern "^\s*(on:|push:|pull_request:|workflow_dispatch:|schedule:)" `
            -ErrorAction SilentlyContinue
        foreach ($t in $triggers) { $out += "  $($t.Line.Trim())" }
    }
    Out-Artifact "ci-workflows.txt" $out | Out-Null
    Write-Host "  Found $($wfs.Count) workflow(s) -- ci-workflows.txt"
}

# ===========================================================================
# PHASE G -- PERMISSION / ROLE / TENANT SURFACE MAP
# ===========================================================================

Step "G1: Permission class surface scan" {
    Push-Location $repoRoot
    $permOut = @("Permission class usage across backend", ("=" * 60))
    $patterns = @(
        "IsAuthenticated","IsAdminUser","RequiresEntitlement",
        "permission_classes","has_permission","has_object_permission"
    )
    foreach ($p in $patterns) {
        $hits = git grep -n $p -- "backend/" 2>$null |
            Where-Object { $_ -notmatch "__pycache__|migrations" }
        if ($hits) {
            $permOut += ""
            $permOut += "--- $p ---"
            $permOut += ($hits | Select-Object -First 50)
        }
    }
    Out-Artifact "permission-surface.txt" $permOut | Out-Null
    Write-Host "  Permission surface -- permission-surface.txt"
    Pop-Location
}

Step "G2: Tenant header usage scan" {
    Push-Location $repoRoot
    $tenantOut = @("Tenant header calls (get_request_school_id / X-School-Id)", ("=" * 60))
    $hits = git grep -n "get_request_school_id\|X-School-Id\|TENANT_HEADER_REQUIRED" -- "backend/" 2>$null |
        Where-Object { $_ -notmatch "__pycache__|migrations|0001_|0002_" } |
        Select-Object -First 300
    $tenantOut += if ($hits) { $hits } else { "(no hits)" }
    Out-Artifact "tenant-header-usage.txt" $tenantOut | Out-Null
    Write-Host "  Tenant header usage -- tenant-header-usage.txt"
    Pop-Location
}

# ===========================================================================
# PHASE H -- DATA & MIGRATION SURFACE
# ===========================================================================

Step "H1: PII field surface scan (email, SSN, date_of_birth, phone)" {
    Push-Location $repoRoot
    $piiOut = @("PII field scan across models", ("=" * 60))
    $piiPatterns = @("email","ssn","date_of_birth","phone","address","dob","social_security")
    foreach ($p in $piiPatterns) {
        $hits = git grep -n -i $p -- "backend/**/models.py" 2>$null |
            Where-Object { $_ -notmatch "__pycache__|migrations" }
        if ($hits) {
            $piiOut += ""
            $piiOut += "--- $p ---"
            $piiOut += ($hits | Select-Object -First 50)
        }
    }
    Out-Artifact "pii-field-scan.txt" $piiOut | Out-Null
    Write-Host "  PII field scan -- pii-field-scan.txt"
    Pop-Location
}

Step "H2: Audit log coverage (AuditLog/AuditEvent in views)" {
    Push-Location $repoRoot
    $auditOut = @("AuditLog / AuditEvent usage", ("=" * 60))
    $hits = git grep -n "AuditLog\|AuditEvent\|audit_log\|audit_event" -- "backend/" 2>$null |
        Where-Object { $_ -notmatch "__pycache__|migrations" }
    if ($hits) {
        $auditOut += $hits
    } else {
        $auditOut += "[WARN] No AuditLog/AuditEvent references found -- mutation endpoints may be unaudited."
    }
    Out-Artifact "audit-log-coverage.txt" $auditOut | Out-Null
    Write-Host "  Audit log coverage -- audit-log-coverage.txt"
    Pop-Location
}

# ===========================================================================
# PHASE I -- SUMMARY ARTIFACT + EXIT
# ===========================================================================

$passCount = $script:PassList.Count
$warnCount = $script:WarnList.Count
$failCount = $script:FailList.Count

$summaryLines = @(
    "CROWN MAGUS 0 -- AUDIT SUMMARY",
    ("=" * 40),
    "Timestamp   : $ts",
    "Fast mode   : $Fast",
    "Skip secrets: $NoSecrets",
    "Repo root   : $repoRoot",
    "",
    "PASS ($passCount):"
) + ($script:PassList | ForEach-Object { "  PASS: $_" }) + @(
    "",
    "WARN ($warnCount) -- non-blocking:"
) + ($script:WarnList | ForEach-Object { "  WARN: $_" }) + @(
    "",
    "FAIL ($failCount):"
) + ($script:FailList | ForEach-Object { "  FAIL: $_" }) + @(
    "",
    "Artifacts:"
) + (Get-ChildItem $outDir | Sort-Object Name |
        ForEach-Object { "  $($_.Name)  ($($_.Length) bytes)" })

Out-Artifact "SUMMARY.txt" $summaryLines | Out-Null

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Magenta
Write-Host "  PASS: $passCount   WARN: $warnCount   FAIL: $failCount" -ForegroundColor Cyan
Write-Host "  Artifacts: $outDir" -ForegroundColor Cyan
Write-Host "  Log      : $logFile" -ForegroundColor Cyan
Write-Host ""
if ($failCount -eq 0) {
    Write-Host "  CrownMagus0 Audit: PASS" -ForegroundColor Green
} else {
    Write-Host "  CrownMagus0 Audit: FAIL" -ForegroundColor Red
}
Write-Host ("=" * 60) -ForegroundColor Magenta

} catch {
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Red
    Write-Host "  CrownMagus0 Audit: HARD FAIL" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Log: $logFile" -ForegroundColor DarkRed
    Write-Host ("=" * 60) -ForegroundColor Red

    @(
        "CROWN MAGUS 0 -- AUDIT FAILED",
        "Timestamp: $ts",
        "Error    : $($_.Exception.Message)",
        "",
        "Completed (PASS): $($script:PassList -join ', ')",
        "Warnings        : $($script:WarnList -join ', ')",
        "Failed step     : $($script:FailList -join ', ')"
    ) | Out-File (Join-Path $outDir "SUMMARY-FAIL.txt") -Encoding utf8

    exit 1
} finally {
    Stop-Transcript | Out-Null
}
