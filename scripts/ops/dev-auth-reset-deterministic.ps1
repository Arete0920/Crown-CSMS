#!/usr/bin/env pwsh
param(
    [Parameter(Mandatory = $true)]
    [string]$SchoolId
)

$ErrorActionPreference = "Stop"

Write-Host "CROWN2026 deterministic DEV auth reset starting..."
Write-Host "SchoolId: $SchoolId"

# Single source-of-truth reset path for DEV auth determinism.
powershell -ExecutionPolicy Bypass -File ./scripts/ops-reset-dev.ps1 -SchoolId $SchoolId

Write-Host "Deterministic DEV auth reset triggered via scripts/ops-reset-dev.ps1"
Write-Host "Use this command before smoke:"
Write-Host "pwsh scripts/ops/dev-auth-reset-deterministic.ps1 -SchoolId $SchoolId"
