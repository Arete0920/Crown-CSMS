param(
    [switch]$OpenFiles
)

$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$latest = Join-Path $repoRoot "audit-artifacts\release-launch\latest"
if (-not (Test-Path $latest)) { throw "Missing release-launch latest folder." }

$validationPath = Join-Path $latest "17_release_launch_validation.txt"
"=== RELEASE LAUNCH VALIDATION ===" | Set-Content $validationPath -Encoding utf8

$required = @(
    "06_release_context.md",
    "07_release_window_log.csv",
    "13_smoke_capture.csv",
    "14_release_decision.md",
    "15_hypercare_WORKING.csv",
    "16_release_launch_summary.md"
)

$report = foreach ($name in $required) {
    $path = Join-Path $latest $name
    [pscustomobject]@{
        File     = $name
        Exists   = Test-Path $path
        Size     = if (Test-Path $path) { (Get-Item $path).Length } else { 0 }
        NonEmpty = if (Test-Path $path) { (Get-Item $path).Length -gt 50 } else { $false }
    }
}
$report | Format-Table File, Exists, Size, NonEmpty -AutoSize | Out-String | Add-Content $validationPath

$smokePath = Join-Path $latest "13_smoke_capture.csv"
$smokeGreen = $false
if (Test-Path $smokePath) {
    $rows = Import-Csv $smokePath
    $health = @($rows | Where-Object { $_.Area -eq "Health" -and $_.Status -eq "Pass" }).Count -ge 1
    $integrity = @($rows | Where-Object { $_.Area -eq "Integrity" -and $_.Status -eq "Pass" }).Count -ge 1
    $smokeGreen = $health -and $integrity
}

$decisionPath = Join-Path $latest "14_release_decision.md"
$decisionSet = $false
if (Test-Path $decisionPath) {
    $content = Get-Content $decisionPath -Raw
    if ($content -match "Current:") {
        $decisionSet = $true
    }
}

$allFilesReady = ($report | Where-Object { -not $_.Exists -or -not $_.NonEmpty }).Count -eq 0
$ready = $allFilesReady -and $smokeGreen -and $decisionSet

"" | Add-Content $validationPath
("Smoke green: " + $smokeGreen) | Add-Content $validationPath
("Decision set: " + $decisionSet) | Add-Content $validationPath
("Ready for release execution completion: " + $ready) | Add-Content $validationPath

if ($OpenFiles) {
    code $validationPath
    code (Join-Path $latest "13_smoke_capture.csv")
    code (Join-Path $latest "14_release_decision.md")
    code (Join-Path $latest "15_hypercare_WORKING.csv")
}

Write-Host "Validation file: $validationPath"
Write-Host "Ready for release execution completion: $ready"

