<#
ci_runtime_canary.ps1

Purpose:
  Deterministic runtime canary for CI/ops verification.
  Canonicalized from the previous ephemeral "Block 6 runtime canary" script.

Notes:
  - StrictMode-safe: always treat collections as arrays using @()
  - Designed to be copy-paste runnable in PowerShell 7+ (pwsh) and Windows PowerShell 5.1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Canary([string]$msg) {
    Write-Host $msg
}

function Assert([bool]$condition, [string]$message) {
    if (-not $condition) { throw "CANARY FAIL: $message" }
}

Write-Canary "=== CI Runtime Canary (Canonical) ==="

# Collect staged changes (StrictMode-safe)
$staged = @(git diff --cached --name-only 2>$null)
if ($LASTEXITCODE -ne 0) { throw "CANARY FAIL: git diff --cached failed" }

Write-Canary ("Staged file count: {0}" -f $staged.Count)

# Sanity: if nothing staged, canary still passes (this is a runtime canary, not a commit gate)
if ($staged.Count -eq 0) {
    Write-Canary "No staged files. Canary OK."
    exit 0
}

# Optional: print staged file list
Write-Canary "Staged files:"
$staged | ForEach-Object { Write-Canary ("  - {0}" -f $_) }

Write-Canary "Canary OK."
exit 0
