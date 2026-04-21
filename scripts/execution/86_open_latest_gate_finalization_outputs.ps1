$ErrorActionPreference = "Stop"

function Get-LatestPhaseDir {
    param([string]$BasePath)
    if (-not (Test-Path $BasePath)) { return $null }
    return Get-ChildItem -Path $BasePath -Directory | Sort-Object Name -Descending | Select-Object -First 1
}

$root = (git rev-parse --show-toplevel).Trim()
$base = Join-Path $root "audit-artifacts\gate_finalization_and_executive_completion"

$latest = Get-LatestPhaseDir -BasePath $base
if ($latest) {
    code (Join-Path $latest.FullName "gate_decision_matrix.csv")
    code (Join-Path $latest.FullName "EXECUTIVE_COMPLETION_SUMMARY.md")
    code (Join-Path $latest.FullName "GATE_FINALIZATION_SUMMARY.md")
}

code .\docs\Crown_Master_Binder\03_Operations_and_Delivery\09_Phase_Gate_Register.csv
code .\docs\Crown_Master_Binder\03_Operations_and_Delivery\03_Phase_Progress_Scorecard.csv
code .\docs\Crown_Master_Binder\03_Operations_and_Delivery\04_Risk_Register.csv
