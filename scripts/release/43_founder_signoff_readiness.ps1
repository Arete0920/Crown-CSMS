#Requires -Version 5.1
<#
.SYNOPSIS
    Founder signoff readiness precheck.

.DESCRIPTION
    Runs the canonical closeout proof gate and evaluates whether the remaining
    failures are only founder-signoff/governance items.

    This script never signs anything. It only reports readiness.
#>

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $repoRoot

$runId = Get-Date -Format "yyyyMMdd-HHmmss"
$outDir = Join-Path "audit-artifacts/founder-signoff-readiness" $runId
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$gateScript = "scripts/release_closeout_proof_gate.ps1"
if (-not (Test-Path $gateScript)) {
    Write-Error "Missing canonical gate script: $gateScript"
}

# Run canonical gate to refresh evidence; fail-closed exit code is expected when blockers remain.
$gateOutput = Join-Path $outDir "closeout-gate.stdout.txt"
$gateError = Join-Path $outDir "closeout-gate.stderr.txt"

$hostExe = (Get-Process -Id $PID).Path
if ([string]::IsNullOrWhiteSpace($hostExe)) {
    $hostCmd = Get-Command pwsh,powershell -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($hostCmd) {
        $hostExe = $hostCmd.Source
    }
}
if ([string]::IsNullOrWhiteSpace($hostExe)) {
    Write-Error "Unable to resolve a PowerShell host executable for gate invocation."
}

$proc = Start-Process -FilePath $hostExe `
    -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$gateScript) `
    -RedirectStandardOutput $gateOutput `
    -RedirectStandardError $gateError `
    -NoNewWindow -PassThru -Wait

$gateExit = [int]$proc.ExitCode

$latestScorecardDir = Get-ChildItem "audit-artifacts/release-closeout-proof" -Directory |
    Sort-Object Name -Descending |
    Select-Object -First 1

if (-not $latestScorecardDir) {
    Write-Error "No release-closeout-proof scorecard directories found."
}

$scorecardJsonPath = Join-Path $latestScorecardDir.FullName "release-closeout-scorecard.json"
if (-not (Test-Path $scorecardJsonPath)) {
    Write-Error "Missing scorecard json: $scorecardJsonPath"
}

$scorecard = Get-Content -Raw $scorecardJsonPath | ConvertFrom-Json
$failGates = @($scorecard.gates | Where-Object { $_.status -eq "FAIL" })
$failNames = @($failGates | ForEach-Object { $_.name })

$allowedBeforeHoldLift = @(
    "founder acceptance",
    "release authority hold"
)

$unexpectedFails = @($failNames | Where-Object { $_ -notin $allowedBeforeHoldLift })

$status = if ($unexpectedFails.Count -eq 0) {
    "READY_FOR_FOUNDER_REVIEW"
} else {
    "NOT_READY_FOR_FOUNDER_SIGNOFF"
}

$summary = [pscustomobject]@{
    run_id                        = $runId
    repo_root                     = [string]$repoRoot
    gate_exit_code                = $gateExit
    closeout_decision             = $scorecard.decision
    closeout_pass                 = $scorecard.pass
    closeout_fail                 = $scorecard.fail
    scorecard_json                = $scorecardJsonPath
    status                        = $status
    allowed_pre_hold_lift_fails   = $allowedBeforeHoldLift
    current_fail_gates            = $failNames
    unexpected_fail_gates         = $unexpectedFails
}

$summaryPath = Join-Path $outDir "founder-signoff-readiness.json"
$summary | ConvertTo-Json -Depth 10 | Out-File $summaryPath -Encoding UTF8

$md = @()
$md += "# Founder Signoff Readiness"
$md += ""
$md += "- Run ID: $runId"
$md += "- Gate decision: $($scorecard.decision)"
$md += "- PASS: $($scorecard.pass)"
$md += "- FAIL: $($scorecard.fail)"
$md += "- Status: **$status**"
$md += "- Scorecard: $scorecardJsonPath"
$md += ""
$md += "## Current FAIL Gates"

if ($failGates.Count -eq 0) {
    $md += "- None"
} else {
    foreach ($g in $failGates) {
        $md += "- $($g.name): $($g.detail)"
    }
}

$md += ""
$md += "## Policy"
$md += "- Do not apply founder signature unless there are no unexpected technical failures."
$md += "- Do not lift integrity hold without complete governance evidence and authorized review."

$mdPath = Join-Path $outDir "founder-signoff-readiness.md"
$md -join "`n" | Out-File $mdPath -Encoding UTF8

Write-Host ""
Write-Host "Founder signoff readiness: $status"
Write-Host "Scorecard decision: $($scorecard.decision)  PASS: $($scorecard.pass)  FAIL: $($scorecard.fail)"
Write-Host "Readiness artifact: $mdPath"
Write-Host ""

if ($unexpectedFails.Count -gt 0) {
    exit 1
}

exit 0
