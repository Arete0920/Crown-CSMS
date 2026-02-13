# Demo Reset & Boot Script
# Use when you need: guaranteed clean process state + two boots
# Kills all Python and Node processes explicitly (allowed for development)
# Then runs back-to-back boots to verify boot logic

param(
    [int]$APITimeout = 30
)

$ErrorActionPreference = "Stop"

function Stop-AllProcesses {
    Write-Host "Stopping all Python and Node processes..." -ForegroundColor Yellow
    
    Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Start-Sleep -Milliseconds 500
    Write-Host "Process cleanup complete." -ForegroundColor Green
}

function Run-Boot {
    param([int]$RunNumber)
    
    Write-Host ""
    Write-Host "=== Boot Run $RunNumber ===" -ForegroundColor Cyan
    
    & .\tools\dev_scripts\demo_boot_feb16.ps1 -APITimeout $APITimeout
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -ne 0) {
        throw "Boot run $RunNumber failed with exit code $exitCode"
    }
    
    Write-Host "=== Boot Run $RunNumber Complete ===" -ForegroundColor Green
}

Write-Host ""
Write-Host "┌─ Demo Reset & Boot (Local Development) ─┐" -ForegroundColor Cyan
Write-Host "│ Manual cleanup ALLOWED (not production)  │" -ForegroundColor Cyan
Write-Host "└─────────────────────────────────────────┘" -ForegroundColor Cyan
Write-Host ""

try {
    # Manual process kill (development only)
    Stop-AllProcesses
    
    # Boot 1
    Run-Boot -RunNumber 1
    
    # Boot 2
    Run-Boot -RunNumber 2
    
    Write-Host ""
    Write-Host "✓ Reset & boot sequence complete" -ForegroundColor Green
    exit 0
}
catch {
    Write-Host ""
    Write-Host "✗ Error: $_" -ForegroundColor Red
    exit 1
}
