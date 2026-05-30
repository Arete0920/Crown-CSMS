# Demo Proof Script: Back-to-back boot validation
# Proves: Port kill + readiness gate work WITHOUT manual process cleanup
# Run from demo tag: demo-feb16-gradebook-edit-pp-003
# Output: PROOF_RUN1.log and PROOF_RUN2.log

param(
    [int]$APITimeout = 30,
    [string]$LogDir = "."
)

$ErrorActionPreference = "Stop"

function Run-ProofBoot {
    param([int]$RunNumber)
    
    Write-Host ""
    Write-Host "=== Proof Run $RunNumber Start ===" -ForegroundColor Cyan
    Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
    Write-Host ""
    
    # Call the hardened boot script from the tag
    $bootScript = ".\tools\dev_scripts\demo_boot_feb16.ps1"
    if (-not (Test-Path $bootScript)) {
        throw "Boot script not found: $bootScript"
    }
    
    # Run boot with same parameters as investor demo
    & $bootScript -APITimeout $APITimeout
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -ne 0) {
        throw "Boot run $RunNumber failed with exit code $exitCode"
    }
    
    Write-Host ""
    Write-Host "=== Proof Run $RunNumber Complete ===" -ForegroundColor Green
    Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Yellow
Write-Host "║  Demo Hardening Proof: No Manual Cleanup       ║" -ForegroundColor Yellow
Write-Host "║  Back-to-back boots from frozen demo tag      ║" -ForegroundColor Yellow
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Yellow
Write-Host ""

Write-Host "Tag: $(git describe --tags --exact-match 2>$null || 'detached')" -ForegroundColor Cyan
Write-Host "SHA: $(git rev-parse HEAD)" -ForegroundColor Cyan
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host ""

try {
    # RUN 1: Cold boot
    Run-ProofBoot -RunNumber 1
    
    # RUN 2: Back-to-back reboot (tests port kill + readiness gate)
    # NO manual process cleanup between runs
    Run-ProofBoot -RunNumber 2
    
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  ✓ PROOF COMPLETE: Hardening validated        ║" -ForegroundColor Green
    Write-Host "║  Both boots passed without manual intervention ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    
    exit 0
}
catch {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║  ✗ PROOF FAILED                               ║" -ForegroundColor Red
    Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    exit 1
}
