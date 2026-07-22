$ErrorActionPreference = "Continue"
Set-StrictMode -Version Latest

if ($PSVersionTable.PSVersion.Major -ge 7) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$repoRoot = (git rev-parse --show-toplevel 2>$null).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Not inside a git repository."
}
Set-Location $repoRoot

$repositoryDiagnosticsModule = Join-Path $repoRoot "scripts/execution/modules/gauntlet_repository_diagnostics.psm1"
$backendValidationModule = Join-Path $repoRoot "scripts/execution/modules/gauntlet_backend_validation.psm1"
Import-Module $repositoryDiagnosticsModule -Force
Import-Module $backendValidationModule -Force

$base = Join-Path $repoRoot "audit-artifacts/finish-right-4h-$stamp"
New-Item -ItemType Directory -Force -Path $base | Out-Null

$results = New-Object System.Collections.Generic.List[object]

function Resolve-PythonCommand {
    $venvPython = Join-Path $repoRoot ".venv/Scripts/python.exe"
    if (Test-Path $venvPython) { return $venvPython }
    if (Get-Command python -ErrorAction SilentlyContinue) { return "python" }
    if (Get-Command py -ErrorAction SilentlyContinue) { return "py" }
    throw "Missing required Python command. Expected .venv/Scripts/python.exe, python, or py."
}

function Resolve-NpmCommand {
    if (Get-Command npm.cmd -ErrorAction SilentlyContinue) { return "npm.cmd" }
    if (Get-Command npm -ErrorAction SilentlyContinue) { return "npm" }
    throw "Missing required npm command."
}

function Resolve-PowerShellCommand {
    if (Get-Command pwsh -ErrorAction SilentlyContinue) { return "pwsh" }
    if (Get-Command powershell -ErrorAction SilentlyContinue) { return "powershell" }
    throw "Missing required PowerShell command."
}

function Add-Result {
    param(
        [string]$Name,
        [int]$ExitCode,
        [string]$Log,
        [string]$Required = "YES"
    )

    $results.Add([pscustomobject]@{
        Step = $Name
        ExitCode = $ExitCode
        Log = $Log
        Required = $Required
        Passed = ($ExitCode -eq 0)
    })
}

function Invoke-Step {
    param(
        [string]$Name,
        [string]$WorkingDirectory,
        [string]$Exe,
        [string[]]$Args = @(),
        [string]$Required = "YES"
    )

    $safeName = $Name -replace '[^a-zA-Z0-9_\-]', '_'
    $log = Join-Path $base "$safeName.txt"
    "=== $Name ===" | Set-Content -Path $log -Encoding UTF8
    "started=$(Get-Date -Format s)" | Add-Content -Path $log -Encoding UTF8
    "pwd=$WorkingDirectory" | Add-Content -Path $log -Encoding UTF8
    "cmd=$Exe $($Args -join ' ')" | Add-Content -Path $log -Encoding UTF8
    "" | Add-Content -Path $log -Encoding UTF8

    Push-Location $WorkingDirectory
    try {
        $global:LASTEXITCODE = 0
        & $Exe @Args 1>> $log 2>&1
        $code = $LASTEXITCODE
        if ($null -eq $code) { $code = 0 }
    }
    catch {
        $_ | Out-String | Add-Content -Path $log -Encoding UTF8
        $code = 1
    }
    finally {
        Pop-Location
    }

    "" | Add-Content -Path $log -Encoding UTF8
    "exit_code=$code" | Add-Content -Path $log -Encoding UTF8
    "finished=$(Get-Date -Format s)" | Add-Content -Path $log -Encoding UTF8
    Add-Result -Name $Name -ExitCode $code -Log $log -Required $Required
}

function Invoke-InfoStep {
    param(
        [string]$Name,
        [scriptblock]$Block
    )
    $safeName = $Name -replace '[^a-zA-Z0-9_\-]', '_'
    $log = Join-Path $base "$safeName.txt"
    "=== $Name ===" | Set-Content -Path $log -Encoding UTF8
    try {
        & $Block 1>> $log 2>&1
        $code = 0
    }
    catch {
        $_ | Out-String | Add-Content -Path $log -Encoding UTF8
        $code = 1
    }
    Add-Result -Name $Name -ExitCode $code -Log $log -Required "INFO"
}

function Invoke-StaticAssertion {
    param(
        [string]$Name,
        [string]$Path,
        [string[]]$Patterns
    )
    $safeName = $Name -replace '[^a-zA-Z0-9_\-]', '_'
    $log = Join-Path $base "$safeName.txt"
    "=== $Name ===" | Set-Content -Path $log -Encoding UTF8
    "file=$Path" | Add-Content -Path $log -Encoding UTF8
    $ok = $true
    if (-not (Test-Path $Path)) {
        "MISSING_FILE=$Path" | Add-Content -Path $log -Encoding UTF8
        $ok = $false
    }
    else {
        foreach ($pattern in $Patterns) {
            $hit = Select-String -Path $Path -Pattern $pattern -SimpleMatch -ErrorAction SilentlyContinue
            if ($hit) {
                "PASS pattern=$pattern" | Add-Content -Path $log -Encoding UTF8
            }
            else {
                "FAIL missing_pattern=$pattern" | Add-Content -Path $log -Encoding UTF8
                $ok = $false
            }
        }
    }
    $code = if ($ok) { 0 } else { 1 }
    Add-Result -Name $Name -ExitCode $code -Log $log -Required "YES"
}

$pythonExe = Resolve-PythonCommand
$npmExe = Resolve-NpmCommand
$psExe = Resolve-PowerShellCommand

Invoke-InfoStep -Name "01_repo_truth" -Block {
    Invoke-GauntletRepositoryTruth
}

Invoke-InfoStep -Name "02_blocker_signal_scan" -Block {
    Invoke-GauntletBlockerSignalScan
}

$backendValidationSteps = Get-GauntletBackendValidationSteps -RepoRoot $repoRoot -PythonExe $pythonExe
foreach ($step in $backendValidationSteps) {
    Invoke-Step -Name $step.Name -WorkingDirectory $step.WorkingDirectory -Exe $step.Exe -Args $step.Args -Required $step.Required
}

$frontendRoot = Join-Path $repoRoot "frontend/dashboards"
Invoke-Step -Name "07_frontend_npm_ci" -WorkingDirectory $frontendRoot -Exe $npmExe -Args @("ci")
Invoke-Step -Name "08_frontend_lint" -WorkingDirectory $frontendRoot -Exe $npmExe -Args @("run", "lint")
Invoke-Step -Name "09_frontend_contracts" -WorkingDirectory $frontendRoot -Exe $npmExe -Args @("run", "test:contracts")
Invoke-Step -Name "10_frontend_shell_certification" -WorkingDirectory $frontendRoot -Exe $npmExe -Args @("run", "check:shell-certification")
Invoke-Step -Name "11_frontend_shell_backend_contract_parity" -WorkingDirectory $frontendRoot -Exe $npmExe -Args @("run", "check:shell-backend-contract-parity")
Invoke-Step -Name "12_frontend_dashboard_completeness" -WorkingDirectory $frontendRoot -Exe $npmExe -Args @("run", "verify:dashboard-completeness")
Invoke-Step -Name "13_frontend_build" -WorkingDirectory $frontendRoot -Exe $npmExe -Args @("run", "build")

Invoke-Step -Name "14_release_api_contracts" -WorkingDirectory $repoRoot -Exe "node" -Args @("scripts/release/verify-api-contracts.mjs")
Invoke-Step -Name "15_release_navigation_surface" -WorkingDirectory $repoRoot -Exe "node" -Args @("scripts/release/verify-navigation-surface.mjs")

Invoke-Step -Name "16_dashboard_completion_gate_deep" -WorkingDirectory $repoRoot -Exe $psExe -Args @("-ExecutionPolicy", "Bypass", "-File", "./scripts/execution/105_dashboard_module_completion_gate.ps1", "-Deep")
Invoke-Step -Name "17_full_completion_truth_gate_deep" -WorkingDirectory $repoRoot -Exe $psExe -Args @("-ExecutionPolicy", "Bypass", "-File", "./scripts/execution/106_crown_full_completion_truth_gate.ps1", "-Deep")

Invoke-StaticAssertion -Name "18_sandbox_nav_flag_static_assertions" -Path "frontend/dashboards/src/components/navigation/dashboardNavConfig.js" -Patterns @(
    "VITE_SANDBOX_READY_ONLY",
    "VITE_HIDE_UNREADY_NAV",
    "VITE_SANDBOX_MODE",
    "isProductionReady",
    "visibleStaticSections = readyOnly"
)

Invoke-StaticAssertion -Name "19_backend_dashboard_sample_fail_closed_assertions" -Path "backend/crown_api/dashboards/views.py" -Patterns @(
    "CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS",
    "dashboard_live_data_required",
    "No live or snapshot payload is available",
    "sample_payload_allowed"
)

Invoke-InfoStep -Name "20_final_git_diff" -Block {
    git status --short --branch
    git diff --stat
    git diff --name-only
}

$resultsPath = Join-Path $base "00_results.csv"
$results | Export-Csv -Path $resultsPath -NoTypeInformation -Encoding UTF8

$requiredFailures = @($results | Where-Object { $_.Required -eq "YES" -and -not $_.Passed })
$summaryPath = Join-Path $base "00_SUMMARY.md"
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Finish Right 4H Gauntlet Summary")
$lines.Add("")
$lines.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$lines.Add("- Repo root: $repoRoot")
$lines.Add("- Evidence root: $base")
$lines.Add("- Required failures: $($requiredFailures.Count)")
$lines.Add("")
if ($requiredFailures.Count -eq 0) {
    $lines.Add("## Verdict")
    $lines.Add("")
    $lines.Add("PASS")
} else {
    $lines.Add("## Verdict")
    $lines.Add("")
    $lines.Add("FAIL")
    $lines.Add("")
    $lines.Add("## Required failures")
    $lines.Add("")
    foreach ($f in $requiredFailures) {
        $lines.Add("- $($f.Step) exit=$($f.ExitCode) log=$($f.Log)")
    }
}
$lines | Set-Content -Path $summaryPath -Encoding UTF8

Write-Host "FINISH_RIGHT_4H_EVIDENCE=$base"
Write-Host "SUMMARY=$summaryPath"
Write-Host "RESULTS=$resultsPath"

if ($requiredFailures.Count -gt 0) {
    exit 1
}
