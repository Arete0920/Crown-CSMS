param(
  [string]$OutputDir,
  [string]$LatestDir
)

$ErrorActionPreference = "Stop"

$summaryMd = Join-Path $OutputDir "SUMMARY.md"
$csv = Join-Path $OutputDir "00_release_gate_results.csv"
$rows = Import-Csv $csv

$green = @($rows | Where-Object {$_.status -eq "GREEN"}).Count
$amber = @($rows | Where-Object {$_.status -eq "AMBER"}).Count
$red = @($rows | Where-Object {$_.status -eq "RED"}).Count

$lines = @()
$lines += "# Crown2026 Release Certification Summary"
$lines += ""
$lines += "- GREEN: $green"
$lines += "- AMBER: $amber"
$lines += "- RED: $red"
$lines += "- FINAL: " + ($(if ($red -eq 0 -and $amber -eq 0) { "PASS" } else { "FAIL" }))
$lines += ""
$lines += "## Gates"
$lines += ""
foreach ($r in $rows) {
  $lines += "- [$($r.status)] $($r.lane) :: $($r.gate) :: $($r.detail) :: $($r.evidence)"
}
$lines += ""
$lines += "## Manual remaining items"
$lines += ""
$lines += "- branch protection screenshot"
$lines += "- blocked PR screenshots for CodeQL and dependency audit"
$lines += "- transcript/export/reporting product proof if not yet live"
$lines += "- final signoff review"

$lines -join "`r`n" | Out-File $summaryMd -Encoding utf8

Copy-Item "$OutputDir\*" $LatestDir -Recurse -Force
