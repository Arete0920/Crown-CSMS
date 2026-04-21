$ErrorActionPreference = "Stop"
$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot
$p = ".\scripts\execution\83_phase567_core_module_release_enforcement.ps1"
$code = Get-Content -Raw -Path $p
try {
    [void][scriptblock]::Create($code)
    Write-Host "PARSE_OK"
    exit 0
}
catch {
    Write-Host "PARSE_FAIL"
    Write-Host $_.Exception.Message
    exit 1
}
