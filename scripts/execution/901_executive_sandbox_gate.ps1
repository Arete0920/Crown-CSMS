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

function Get-BranchNameSafe {
    $name = (git branch --show-current 2>$null)
    if (-not [string]::IsNullOrWhiteSpace($name)) { return $name.Trim() }

    $ref = (git rev-parse --abbrev-ref HEAD 2>$null)
    if (-not [string]::IsNullOrWhiteSpace($ref) -and $ref.Trim() -ne "HEAD") { return $ref.Trim() }

    if (-not [string]::IsNullOrWhiteSpace($env:GITHUB_REF_NAME)) { return $env:GITHUB_REF_NAME.Trim() }

    return "detached-head"
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

    @(
        "==> $Name",
        "Started: $($start.ToString('s'))",
        "WorkingDirectory: $WorkingDirectory",
        "Command: $Command",
        ""
    ) | Set-Content -Path $LogPath -Encoding UTF8

    Push-Location $WorkingDirectory
    try {
        if (Get-Command cmd.exe -ErrorAction SilentlyContinue) {
            cmd.exe /c $Command 1>> $LogPath 2>&1
        } else {
            pwsh -NoLogo -NoProfile -Command $Command 1>> $LogPath 2>&1
        }
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
    @(
        "",
        "Completed: $((Get-Date).ToString('s'))",
        "ExitCode: $exitCode",
        "Passed: $ok",
        "Seconds: $elapsed"
    ) | Add-Content -Path $LogPath -Encoding UTF8

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

function Write-GateOutputs {
    param(
        [System.Collections.Generic.List[object]]$ScanRows,
        [System.Collections.Generic.List[object]]$Steps,
        [string]$OutDir,
        [string]$LatestDir,
        [string]$Branch,
        [string]$Head,
        [string]$Stage = "running"
    )

    New-Dir $OutDir
    New-Dir $LatestDir

    $scanCsv = Join-Path $OutDir "10_static_scan.csv"
    $stepsCsv = Join-Path $OutDir "20_execution_steps.csv"
    $summaryPath = Join-Path $OutDir "00_SUMMARY.md"
    $statusPath = Join-Path $OutDir "99_STATUS.json"

    $ScanRows | Export-Csv -Path $scanCsv -NoTypeInformation -Encoding UTF8
    $Steps | Export-Csv -Path $stepsCsv -NoTypeInformation -Encoding UTF8

    $failScanCount = @($ScanRows | Where-Object { $_.Severity -eq "FAIL" }).Count
    $warnScanCount = @($ScanRows | Where-Object { $_.Severity -eq "WARN" }).Count
    $failedSteps = @($Steps | Where-Object { -not $_.Passed })
    $passedSteps = @($Steps | Where-Object { $_.Passed })
    $passed = ($Stage -eq "complete" -and $failScanCount -eq 0 -and $failedSteps.Count -eq 0)

    $summary = New-Object System.Collections.Generic.List[string]
    $summary.Add("# CROWN Executive Sandbox Gate")
    $summary.Add("")
    $summary.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
    $summary.Add("- Stage: $Stage")
    $summary.Add("- Branch: $Branch")
    $summary.Add("- Head: $Head")
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
    } elseif ($Stage -ne "complete") {
        $summary.Add("RESULT: RUNNING_OR_INTERRUPTED")
        $summary.Add("")
        $summary.Add("This partial artifact was written before the gate completed. Continue or inspect logs if the run stopped.")
    } else {
        $summary.Add("RESULT: ACTION REQUIRED")
        $summary.Add("")
        $summary.Add("Fix failed scans or failed execution steps before exposing sandbox access.")
    }

    Write-Utf8 -Path $summaryPath -Lines $summary

    $status = [ordered]@{
        generated_at = (Get-Date).ToString("s")
        stage = $Stage
        branch = $Branch
        head = $Head
        passed = $passed
        static_scan_failures = $failScanCount
        static_scan_warnings = $warnScanCount
        passed_steps = $passedSteps.Count
        failed_steps = $failedSteps.Count
        output_dir = $OutDir
    }
    ($status | ConvertTo-Json -Depth 8) | Set-Content -Path $statusPath -Encoding UTF8

    Copy-Item -Path (Join-Path $OutDir "*") -Destination $LatestDir -Recurse -Force

    return [pscustomobject]@{
        Passed = $passed
        SummaryPath = $summaryPath
        StatusPath = $statusPath
        StepsCsv = $stepsCsv
    }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Not inside a git repository."
}
Set-Location $repoRoot

Require-Command git

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
$env:PYTHONFAULTHANDLER = "1"
$env:PYTHONUNBUFFERED = "1"
if (-not $env:DJANGO_SECRET_KEY) { $env:DJANGO_SECRET_KEY = "local-ci-test-key" }

$head = (git rev-parse HEAD).Trim()
$branch = Get-BranchNameSafe
$dirty = @((git status --porcelain=v1) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })

$scanRows = New-Object System.Collections.Generic.List[object]
$steps = New-Object System.Collections.Generic.List[object]
$logsDir = Join-Path $outDir "logs"
New-Dir $logsDir

try {
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
        if ($nav -notmatch "visibleStaticSections\s*=\s*readyOnly") {
            Add-ScanResult $scanRows "WARN" "sandbox-nav" "Static nav may still show in sandbox-ready-only mode." "frontend/dashboards/src/components/navigation/dashboardNavConfig.js"
        }
    }

    Write-GateOutputs -ScanRows $scanRows -Steps $steps -OutDir $outDir -LatestDir $latestDir -Branch $branch -Head $head -Stage "static-scan-complete" | Out-Null

    if (-not $SkipBackend) {
        if (-not $SkipInstall) {
            $steps.Add((Invoke-Step "Install backend dependencies" "python -m pip install --upgrade pip && pip install -r backend\requirements.txt" $repoRoot (Join-Path $logsDir "backend_install.log"))) | Out-Null
            Write-GateOutputs -ScanRows $scanRows -Steps $steps -OutDir $outDir -LatestDir $latestDir -Branch $branch -Head $head -Stage "backend-install-complete" | Out-Null
        }
        $steps.Add((Invoke-Step "Django system check" "python backend\manage.py check" $repoRoot (Join-Path $logsDir "backend_check.log"))) | Out-Null
        Write-GateOutputs -ScanRows $scanRows -Steps $steps -OutDir $outDir -LatestDir $latestDir -Branch $branch -Head $head -Stage "backend-check-complete" | Out-Null
        $dashboardPytestCommand = "python -X faulthandler -m pytest backend\crown_api\tests\test_dashboard_snapshot_summary_api.py -vv -s --tb=long --setup-show --durations=20"
        $steps.Add((Invoke-Step "Dashboard sample gate tests" $dashboardPytestCommand $repoRoot (Join-Path $logsDir "dashboard_sample_gate_tests.log"))) | Out-Null
        Write-GateOutputs -ScanRows $scanRows -Steps $steps -OutDir $outDir -LatestDir $latestDir -Branch $branch -Head $head -Stage "backend-tests-complete" | Out-Null
    }

    if (-not $SkipFrontend) {
        $frontendDir = Join-Path $repoRoot "frontend\dashboards"
        if (-not $SkipInstall) {
            $steps.Add((Invoke-Step "Install frontend dependencies" "npm ci" $frontendDir (Join-Path $logsDir "frontend_npm_ci.log"))) | Out-Null
            Write-GateOutputs -ScanRows $scanRows -Steps $steps -OutDir $outDir -LatestDir $latestDir -Branch $branch -Head $head -Stage "frontend-install-complete" | Out-Null
        }
        $steps.Add((Invoke-Step "Frontend unit tests" "npm run test:unit --if-present" $frontendDir (Join-Path $logsDir "frontend_unit.log"))) | Out-Null
        Write-GateOutputs -ScanRows $scanRows -Steps $steps -OutDir $outDir -LatestDir $latestDir -Branch $branch -Head $head -Stage "frontend-unit-complete" | Out-Null
        $steps.Add((Invoke-Step "Frontend shell certification" "npm run check:shell-certification --if-present" $frontendDir (Join-Path $logsDir "frontend_shell_certification.log"))) | Out-Null
        Write-GateOutputs -ScanRows $scanRows -Steps $steps -OutDir $outDir -LatestDir $latestDir -Branch $branch -Head $head -Stage "frontend-shell-complete" | Out-Null
        $steps.Add((Invoke-Step "Frontend build" "npm run build --if-present" $frontendDir (Join-Path $logsDir "frontend_build.log"))) | Out-Null
        Write-GateOutputs -ScanRows $scanRows -Steps $steps -OutDir $outDir -LatestDir $latestDir -Branch $branch -Head $head -Stage "frontend-build-complete" | Out-Null
    }

    if (-not $SkipHeavyGates) {
        if (Test-Path (Join-Path $repoRoot "scripts\execution\106_crown_full_completion_truth_gate.ps1")) {
            $steps.Add((Invoke-Step "Full completion truth gate" "powershell -ExecutionPolicy Bypass -File scripts\execution\106_crown_full_completion_truth_gate.ps1 -Deep" $repoRoot (Join-Path $logsDir "106_full_completion_truth_gate.log"))) | Out-Null
            Write-GateOutputs -ScanRows $scanRows -Steps $steps -OutDir $outDir -LatestDir $latestDir -Branch $branch -Head $head -Stage "truth-gate-complete" | Out-Null
        }
        if (Test-Path (Join-Path $repoRoot "scripts\execution\105_dashboard_module_completion_gate.ps1")) {
            $steps.Add((Invoke-Step "Dashboard module completion gate" "powershell -ExecutionPolicy Bypass -File scripts\execution\105_dashboard_module_completion_gate.ps1 -Deep" $repoRoot (Join-Path $logsDir "105_dashboard_module_completion_gate.log"))) | Out-Null
            Write-GateOutputs -ScanRows $scanRows -Steps $steps -OutDir $outDir -LatestDir $latestDir -Branch $branch -Head $head -Stage "dashboard-gate-complete" | Out-Null
        }
    }

    $result = Write-GateOutputs -ScanRows $scanRows -Steps $steps -OutDir $outDir -LatestDir $latestDir -Branch $branch -Head $head -Stage "complete"

    Write-Host ""
    Write-Host "Executive sandbox gate complete."
    Write-Host "Summary: $($result.SummaryPath)"
    Write-Host "Latest:  $latestDir"
    Write-Host "Status:  $($result.StatusPath)"

    if (-not $result.Passed) { exit 1 }
} catch {
    Add-ScanResult $scanRows "FAIL" "gate-runner" (($_ | Out-String).Trim()) "scripts/execution/901_executive_sandbox_gate.ps1"
    Write-GateOutputs -ScanRows $scanRows -Steps $steps -OutDir $outDir -LatestDir $latestDir -Branch $branch -Head $head -Stage "exception" | Out-Null
    throw
}
