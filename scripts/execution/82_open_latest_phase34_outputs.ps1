$ErrorActionPreference = "Stop"

function Get-LatestPhaseDir {
    param([string]$BasePath)
    if (-not (Test-Path $BasePath)) { return $null }
    return Get-ChildItem -Path $BasePath -Directory | Sort-Object Name -Descending | Select-Object -First 1
}

$root = (git rev-parse --show-toplevel).Trim()
$base = Join-Path $root "audit-artifacts"

$paths = @(
    (Join-Path $base "phase3_archive_and_purge_enforcement"),
    (Join-Path $base "phase4_purge_enforcement"),
    (Join-Path $base "phase34_master_summary")
)

foreach ($p in $paths) {
    $latest = Get-LatestPhaseDir -BasePath $p
    if ($latest) {
        $summary = Join-Path $latest.FullName "SUMMARY.md"
        if (Test-Path $summary) { code $summary }
    }
}

code .\docs\Crown_Master_Binder\03_Operations_and_Delivery\09_Phase_Gate_Register.csv
code .\docs\Crown_Master_Binder\03_Operations_and_Delivery\04_Risk_Register.csv
code .\docs\Crown_Master_Binder\04_Inventory_Keep_Rewrite_Drop\01_Master_Inventory.csv
