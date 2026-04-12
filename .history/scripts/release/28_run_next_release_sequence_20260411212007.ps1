$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

$verifyDir = "audit-artifacts\release-verify"
$manifestDir = "audit-artifacts\release-manifest"
$docsDir = "docs\release"

New-Item -ItemType Directory -Force -Path $verifyDir, $manifestDir, $docsDir | Out-Null

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Action,
        [Parameter(Mandatory = $true)][string]$LogPath
    )

    Write-Host "=== $Name ===" -ForegroundColor Cyan
    try {
        & $Action 2>&1 | Tee-Object -FilePath $LogPath
        if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
            throw "Step failed with exit code $LASTEXITCODE"
        }
        return @{ name = $Name; status = "pass"; log = $LogPath }
    }
    catch {
        Write-Host "Step failed: $Name" -ForegroundColor Red
        Write-Host "Log: $LogPath" -ForegroundColor Yellow
        return @{ name = $Name; status = "fail"; log = $LogPath; error = $_.Exception.Message }
    }
}

$results = @()

$results += Invoke-Step -Name "Fix 15" -LogPath "$verifyDir\50_fix_15_to_green.txt" -Action {
    powershell -ExecutionPolicy Bypass -File "scripts\release\fix_15_to_green.ps1"
}
if ($results[-1].status -ne "pass") { goto Summary }

$results += Invoke-Step -Name "Fix 16-31" -LogPath "$verifyDir\51_fix_16_31_to_green.txt" -Action {
    powershell -ExecutionPolicy Bypass -File "scripts\release\fix_16_31_to_green.ps1"
}
if ($results[-1].status -ne "pass") { goto Summary }

$results += Invoke-Step -Name "Fix 32-46" -LogPath "$verifyDir\52_fix_32_46_to_green.txt" -Action {
    powershell -ExecutionPolicy Bypass -File "scripts\release\fix_32_46_to_green.ps1"
}
if ($results[-1].status -ne "pass") { goto Summary }

$results += Invoke-Step -Name "Fix 47-61" -LogPath "$verifyDir\53_fix_47_61_to_green.txt" -Action {
    powershell -ExecutionPolicy Bypass -File "scripts\release\fix_47_61_to_green.ps1"
}
if ($results[-1].status -ne "pass") { goto Summary }

$results += Invoke-Step -Name "Schema Green Pass" -LogPath "$verifyDir\54_schema_green_pass.txt" -Action {
    powershell -ExecutionPolicy Bypass -File "scripts\release\27_schema_green_pass.ps1"
}
if ($results[-1].status -ne "pass") { goto Summary }

$results += Invoke-Step -Name "Release Verify" -LogPath "$verifyDir\55_release_verify.txt" -Action {
    powershell -ExecutionPolicy Bypass -File "scripts\release\20_release_verify.ps1"
}
if ($results[-1].status -ne "pass") { goto Summary }

$results += Invoke-Step -Name "Build Ship Candidate" -LogPath "$verifyDir\56_build_ship_candidate.txt" -Action {
    powershell -ExecutionPolicy Bypass -File "scripts\release\25_build_ship_candidate.ps1"
}
if ($results[-1].status -ne "pass") { goto Summary }

$results += Invoke-Step -Name "Release Doctor" -LogPath "$verifyDir\57_release_doctor.txt" -Action {
    powershell -ExecutionPolicy Bypass -File "scripts\release\26_release_doctor.ps1"
}

:Summary
$failed = $results | Where-Object { $_.status -eq "fail" } | Select-Object -First 1

$reportLines = @(
    "# NEXT RELEASE SEQUENCE REPORT",
    "",
    "Generated: $(Get-Date -Format s)",
    "",
    "| Step | Status | Log |",
    "|---|---|---|"
)

foreach ($r in $results) {
    $reportLines += "| $($r.name) | $($r.status) | $($r.log) |"
}

if ($failed) {
    $reportLines += ""
    $reportLines += "First blocker: $($failed.name)"
    $reportLines += "Error: $($failed.error)"
    $reportLines += "Log: $($failed.log)"
}

$reportPath = "$docsDir\NEXT_RELEASE_SEQUENCE_REPORT.md"
$reportLines | Out-File -FilePath $reportPath -Encoding utf8

$results | ConvertTo-Json -Depth 5 | Out-File "$verifyDir\58_next_release_sequence_results.json" -Encoding utf8

if ($failed) {
    Write-Host "First blocker: $($failed.name)" -ForegroundColor Red
    Write-Host "See log: $($failed.log)" -ForegroundColor Yellow
    exit 1
}

Write-Host "Next release sequence completed successfully." -ForegroundColor Green
Write-Host "Report: $reportPath" -ForegroundColor Cyan
