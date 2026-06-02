param(
    [switch]$SkipDashboardCompletionDeep
)

$ErrorActionPreference = "Continue"
Set-StrictMode -Version Latest

function New-Dir { param([string]$Path) New-Item -ItemType Directory -Force -Path $Path | Out-Null }
function Write-Utf8 { param([string]$Path, [string[]]$Lines) $Lines | Set-Content -Path $Path -Encoding UTF8 }
function Write-JsonFile { param([string]$Path, $Object) ($Object | ConvertTo-Json -Depth 12) | Set-Content -Path $Path -Encoding UTF8 }

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) { throw "Not inside a git repository." }
Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot ".crown-audit\release-authority-stack\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\release-authority-stack\latest"
New-Dir $outDir
New-Dir $latestDir

$steps = New-Object System.Collections.Generic.List[object]

function Invoke-Gate {
    param([string]$Name, [string]$Command)
    Write-Host "RUNNING: $Name"
    $logPath = Join-Path $outDir ("$Name.log" -replace "[^A-Za-z0-9_.-]", "_")
    $exitCode = 0
    try {
        powershell -ExecutionPolicy Bypass -Command $Command *> $logPath
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) { $exitCode = 0 }
    } catch {
        $_ | Out-File -FilePath $logPath -Append -Encoding UTF8
        $exitCode = 1
    }
    $status = if ($exitCode -eq 0) { "PASS" } else { "FAIL" }
    $steps.Add([pscustomobject]@{ Name = $Name; Command = $Command; ExitCode = $exitCode; Status = $status; LogPath = $logPath })
}

Invoke-Gate -Name "106_full_completion_truth" -Command ".\scripts\execution\106_crown_full_completion_truth_gate.ps1"
Invoke-Gate -Name "121_dashboard_provenance" -Command ".\scripts\execution\121_crown_dashboard_data_provenance_gate.ps1"
Invoke-Gate -Name "122_domain_model" -Command ".\scripts\execution\122_crown_domain_model_certification_gate.ps1"
Invoke-Gate -Name "130_data_migration" -Command ".\scripts\execution\130_crown_data_migration_reconciliation_gate.ps1"
Invoke-Gate -Name "140_financial_controls" -Command ".\scripts\execution\140_crown_financial_controls_gate.ps1"
Invoke-Gate -Name "150_performance_load" -Command ".\scripts\execution\150_crown_performance_load_gate.ps1"
Invoke-Gate -Name "160_observability_incident" -Command ".\scripts\execution\160_crown_observability_incident_gate.ps1"

if (-not $SkipDashboardCompletionDeep -and (Test-Path ".\scripts\execution\105_dashboard_module_completion_gate.ps1")) {
    $env:CROWN_105_RUN_95_BASELINE = "1"
    $env:CROWN_105_RUN_95_DEEP = "1"
    $env:CROWN_105_RUN_HEAVY_FRONTEND = "1"
    $env:CROWN_105_RUN_BACKEND_PYTEST = "1"
    Invoke-Gate -Name "105_dashboard_completion_deep" -Command ".\scripts\execution\105_dashboard_module_completion_gate.ps1 -Deep"
}

Invoke-Gate -Name "120_release_authority_meta" -Command ".\scripts\execution\120_crown_release_authority_meta_gate.ps1"

$failures = @($steps | Where-Object { $_.Status -ne "PASS" })
$pass = ($failures.Count -eq 0)

$steps | Export-Csv -Path (Join-Path $outDir "10_stack_results.csv") -NoTypeInformation -Encoding UTF8
$failures | Export-Csv -Path (Join-Path $outDir "20_stack_failures.csv") -NoTypeInformation -Encoding UTF8

$summary = @(
    "# CROWN Release Authority Stack",
    "",
    "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "- Branch: $((git branch --show-current).Trim())",
    "- Head: $((git rev-parse HEAD).Trim())",
    "- Steps: $($steps.Count)",
    "- Failures: $($failures.Count)",
    "",
    $(if ($pass) { "PASS" } else { "REVIEW REQUIRED" }),
    "",
    "This wrapper runs the CROWN release-authority gate stack and records aggregate results. A GO decision still requires signed final release authority."
)
Write-Utf8 -Path (Join-Path $outDir "00_SUMMARY.md") -Lines $summary

$status = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    branch = (git branch --show-current).Trim()
    head = (git rev-parse HEAD).Trim()
    pass = $pass
    step_count = $steps.Count
    failure_count = $failures.Count
    steps = $steps
}
Write-JsonFile -Path (Join-Path $outDir "99_STATUS.json") -Object $status
Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host "DONE"
Write-Host "SUMMARY: $(Join-Path $outDir '00_SUMMARY.md')"
Write-Host "STATUS:  $(Join-Path $outDir '99_STATUS.json')"

if (-not $pass) { exit 1 }
