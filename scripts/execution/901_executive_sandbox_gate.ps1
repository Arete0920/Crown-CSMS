param(
    [switch]$SkipInstall,
    [switch]$SkipFrontend,
    [switch]$SkipBackend,
    [switch]$SkipHeavyGates
)

$ErrorActionPreference = "Continue"
Set-StrictMode -Version Latest

function New-Dir {
    param([string]$Path)
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Write-Utf8 {
    param([string]$Path, [string[]]$Lines)
    $Lines | Set-Content -Path $Path -Encoding UTF8
}

function Invoke-Step {
    param(
        [string]$Name,
        [string]$Command,
        [string]$WorkingDirectory,
        [string]$LogPath
    )

    Write-Host "==> $Name"
    $start = Get-Date
    $ok = $true
    $exitCode = 0

    Push-Location $WorkingDirectory
    try {
        cmd.exe /c $Command 1> $LogPath 2>&1
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) { $exitCode = 0 }
        if ($exitCode -ne 0) { $ok = $false }
    } catch {
        $ok = $false
        $_ | Out-String | Add-Content -Path $LogPath
        $exitCode = 1
    } finally {
        Pop-Location
    }

    $elapsed = [int]((Get-Date) - $start).TotalSeconds
    return [pscustomobject]@{
        Name = $Name
        Command = $Command
        WorkingDirectory = $WorkingDirectory
        LogPath = $LogPath
        ExitCode = $exitCode
        Passed = $ok
        Seconds = $elapsed
    }
}

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing required command: $Name"
    }
}

function Add-ScanResult {
    param(
        [System.Collections.Generic.List[object]]$Rows,
        [string]$Severity,
        [string]$Area,
        [string]$Message,
        [string]$Path = ""
    )
    $Rows.Add([pscustomobject]@{
        Severity = $Severity
        Area = $Area
        Message = $Message
        Path = $Path
    }) | Out-Null
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Not inside a git repository."
}
Set-Location $repoRoot

Require-Command git
Require-Command powershell

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot ".crown-audit\executive-sandbox-gate\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\executive-sandbox-gate\latest"
New-Dir $outDir
New-Dir $latestDir

$env:VITE_SANDBOX_READY_ONLY = "true"
$env:VITE_HIDE_UNREADY_NAV = "true"
$env:VITE_SANDBOX_MODE = "1"
$env:CROWN_ENV = "production"
$env:CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS = "0"
$env:TENANT_HEADER_REQUIRED = "0"
if (-not $env:DJANGO_SECRET_KEY) { $env:DJANGO_SECRET_KEY = "local-ci-test-key" }

$head = (git rev-parse HEAD).Trim()
$branch = (git branch --show-current).Trim()
$dirty = @((git status --porcelain=v1) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })

$scanRows = New-Object System.Collections.Generic.List[object]

if ($dirty.Count -gt 0) {
    Add-ScanResult $scanRows "WARN" "git" "Worktree has local changes before gate run." "git status"
}

$requiredFiles = @(
    "backend\crown_api\dashboards\views.py",
    "backend\crown_api\tests\test_dashboard_snapshot_summary_api.py",
    "frontend\dashboards\src\components\navigation\dashboardNavConfig.js",
    "frontend\dashboards\src\components\routing\ReleaseStateRoute.jsx",
    "frontend\dashboards\src\config\releaseState.js",
    "scripts\execution\105_dashboard_module_completion_gate.ps1",
    "scripts\execution\106_crown_full_completion_truth_gate.ps1"
)

foreach ($f in $requiredFiles) {
    $p = Join-Path $repoRoot $f
    if (-not (Test-Path $p)) {
        Add-ScanResult $scanRows "FAIL" "required-file" "Required file missing." $f
    }
}

$viewsPath = Join-Path $repoRoot "backend\crown_api\dashboards\views.py"
if (Test-Path $viewsPath) {
    $views = Get-Content $viewsPath -Raw
    if ($views -notmatch "dashboard_live_data_required") {
        Add-ScanResult $scanRows "FAIL" "dashboard-api" "Dashboard API does not expose dashboard_live_data_required fail-closed response." "backend/crown_api/dashboards/views.py"
    }
    if ($views -notmatch "CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS") {
        Add-ScanResult $scanRows "FAIL" "dashboard-api" "Explicit sample payload allowance flag missing." "backend/crown_api/dashboards/views.py"
    }
    if ($views -notmatch "sample_payload_allowed") {
        Add-ScanResult $scanRows "FAIL" "dashboard-api" "Sample payload responses are not explicitly tagged." "backend/crown_api/dashboards/views.py"
    }
}

$navPath = Join-Path $repoRoot "frontend\dashboards\src\components\navigation\dashboardNavConfig.js"
if (Test-Path $navPath) {
    $nav = Get-Content $navPath -Raw
    if ($nav -notmatch "VITE_SANDBOX_READY_ONLY") {
        Add-ScanResult $scanRows "FAIL" "sandbox-nav" "Sandbox-ready-only nav flag missing." "frontend/dashboards/src/components/navigation/dashboardNavConfig.js"
    }
    if ($nav -notmatch "isProductionReady") {
        Add-ScanResult $scanRows "FAIL" "sandbox-nav" "Navigation does not filter dashboard items by production-ready state." "frontend/dashboards/src/components/navigation/dashboardNavConfig.js"
    }
    if ($nav -notmatch "visibleStaticSections = readyOnly\s*\?\s*\[\]") {
        Add-ScanResult $scanRows "WARN" "sandbox-nav" "Static nav may still show in sandbox-ready-only mode." "frontend/dashboards/src/components/navigation/dashboardNavConfig.js"
    }
}

$steps = New-Object System.Collections.Generic.List[object]
$logsDir = Join-Path $outDir "logs"
New-Dir $logsDir

if (-not $SkipBackend) {
    if (-not $SkipInstall) {
        $steps.Add((Invoke-Step "Install backend dependencies" "python -m pip install --upgrade pip && pip install -r backend\requirements.txt" $repoRoot (Join-Path $logsDir "backend_install.log"))) | Out-Null
    }
    $steps.Add((Invoke-Step "Django system check" "python backend\manage.py check" $repoRoot (Join-Path $logsDir "backend_check.log"))) | Out-Null
    $steps.Add((Invoke-Step "Dashboard sample gate tests" "python -m pytest backend\crown_api\tests\test_dashboard_snapshot_summary_api.py -q" $repoRoot (Join-Path $logsDir "dashboard_sample_gate_tests.log"))) | Out-Null
}

if (-not $SkipFrontend) {
    $frontendDir = Join-Path $repoRoot "frontend\dashboards"
    if (-not $SkipInstall) {
        $steps.Add((Invoke-Step "Install frontend dependencies" "npm ci" $frontendDir (Join-Path $logsDir "frontend_npm_ci.log"))) | Out-Null
    }
    $steps.Add((Invoke-Step "Frontend unit tests" "npm run test:unit --if-present" $frontendDir (Join-Path $logsDir "frontend_unit.log"))) | Out-Null
    $steps.Add((Invoke-Step "Frontend shell certification" "npm run check:shell-certification --if-present" $frontendDir (Join-Path $logsDir "frontend_shell_certification.log"))) | Out-Null
    $steps.Add((Invoke-Step "Frontend build" "npm run build --if-present" $frontendDir (Join-Path $logsDir "frontend_build.log"))) | Out-Null
}

if (-not $SkipHeavyGates) {
    if (Test-Path (Join-Path $repoRoot "scripts\execution\106_crown_full_completion_truth_gate.ps1")) {
        $steps.Add((Invoke-Step "Full completion truth gate" "powershell -ExecutionPolicy Bypass -File scripts\execution\106_crown_full_completion_truth_gate.ps1 -Deep" $repoRoot (Join-Path $logsDir "106_full_completion_truth_gate.log"))) | Out-Null
    }
    if (Test-Path (Join-Path $repoRoot "scripts\execution\105_dashboard_module_completion_gate.ps1")) {
        $steps.Add((Invoke-Step "Dashboard module completion gate" "powershell -ExecutionPolicy Bypass -File scripts\execution\105_dashboard_module_completion_gate.ps1 -Deep" $repoRoot (Join-Path $logsDir "105_dashboard_module_completion_gate.log"))) | Out-Null
    }
}

$scanCsv = Join-Path $outDir "10_static_scan.csv"
$stepsCsv = Join-Path $outDir "20_execution_steps.csv"
$summaryPath = Join-Path $outDir "00_SUMMARY.md"
$statusPath = Join-Path $outDir "99_STATUS.json"

$scanRows | Export-Csv -Path $scanCsv -NoTypeInformation -Encoding UTF8
$steps | Export-Csv -Path $stepsCsv -NoTypeInformation -Encoding UTF8

$failScanCount = @($scanRows | Where-Object { $_.Severity -eq "FAIL" }).Count
$warnScanCount = @($scanRows | Where-Object { $_.Severity -eq "WARN" }).Count
$failedSteps = @($steps | Where-Object { -not $_.Passed })
$passedSteps = @($steps | Where-Object { $_.Passed })
$passed = ($failScanCount -eq 0 -and $failedSteps.Count -eq 0)

$summary = New-Object System.Collections.Generic.List[string]
$summary.Add("# CROWN Executive Sandbox Gate")
$summary.Add("")
$summary.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$summary.Add("- Branch: $branch")
$summary.Add("- Head: $head")
$summary.Add("- Sandbox ready only: $env:VITE_SANDBOX_READY_ONLY")
$summary.Add("- Hide unready nav: $env:VITE_HIDE_UNREADY_NAV")
$summary.Add("- Backend environment: $env:CROWN_ENV")
$summary.Add("- Sample dashboard payloads allowed: $env:CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS")
$summary.Add("- Static scan failures: $failScanCount")
$summary.Add("- Static scan warnings: $warnScanCount")
$summary.Add("- Passed steps: $($passedSteps.Count)")
$summary.Add("- Failed steps: $($failedSteps.Count)")
$summary.Add("")
if ($passed) {
    $summary.Add("RESULT: PASS")
    $summary.Add("")
    $summary.Add("Sandbox gate passed locally. Review logs and commit-current artifacts before external sandbox access.")
} else {
    $summary.Add("RESULT: ACTION REQUIRED")
    $summary.Add("")
    $summary.Add("Fix failed scans or failed execution steps before exposing sandbox access.")
}

Write-Utf8 -Path $summaryPath -Lines $summary

$status = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    branch = $branch
    head = $head
    passed = $passed
    static_scan_failures = $failScanCount
    static_scan_warnings = $warnScanCount
    passed_steps = $passedSteps.Count
    failed_steps = $failedSteps.Count
    output_dir = $outDir
}
($status | ConvertTo-Json -Depth 8) | Set-Content -Path $statusPath -Encoding UTF8

Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host ""
Write-Host "Executive sandbox gate complete."
Write-Host "Summary: $summaryPath"
Write-Host "Latest:  $latestDir"
Write-Host "Status:  $statusPath"

if (-not $passed) {
    exit 1
}
