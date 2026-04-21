param(
    [switch]$OpenFiles
)

$ErrorActionPreference = "Stop"

function Open-IfExists {
    param([string]$Path)
    if (Test-Path $Path) { code $Path }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\execution\48_build_release_execution_window.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\audit-artifacts\release-execution-window\latest\16_validate_release_execution_window.ps1

if ($OpenFiles) {
    Open-IfExists ".\audit-artifacts\release-execution-window\latest\18_release_execution_summary.md"
    Open-IfExists ".\audit-artifacts\release-execution-window\latest\17_release_execution_validation.txt"
    Open-IfExists ".\audit-artifacts\release-execution-window\latest\07_release_preflight_WORKING.md"
    Open-IfExists ".\audit-artifacts\release-execution-window\latest\10_go_no_go_WORKING.md"
    Open-IfExists ".\audit-artifacts\release-execution-window\latest\14_release_runbook_WORKING.md"
    Open-IfExists ".\audit-artifacts\release-execution-window\latest\15_release_command_shell.ps1"
}

Write-Host "Refresh complete."
