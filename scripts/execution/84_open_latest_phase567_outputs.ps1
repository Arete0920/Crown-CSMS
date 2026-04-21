$ErrorActionPreference = "Stop"

function Get-LatestPhaseDir {
    param([string]$BasePath)
    if (-not (Test-Path $BasePath)) { return $null }
    return Get-ChildItem -Path $BasePath -Directory | Sort-Object Name -Descending | Select-Object -First 1
}

$root = (git rev-parse --show-toplevel).Trim()
$base = Join-Path $root "audit-artifacts"

$paths = @(
    (Join-Path $base "phase5_core_build_enforcement"),
    (Join-Path $base "phase6_first_wave_module_enforcement"),
    (Join-Path $base "phase7_hardening_release_enforcement"),
    (Join-Path $base "phase567_master_summary")
)

foreach ($p in $paths) {
    $latest = Get-LatestPhaseDir -BasePath $p
    if ($latest) {
        $summary = Join-Path $latest.FullName "SUMMARY.md"
        if (Test-Path $summary) { code $summary }
    }
}

code .\docs\Crown_Master_Binder\03_Operations_and_Delivery\09_Phase_Gate_Register.csv
code .\docs\Crown_Master_Binder\03_Operations_and_Delivery\03_Phase_Progress_Scorecard.csv
code .\docs\Crown_Master_Binder\03_Operations_and_Delivery\04_Risk_Register.csv
