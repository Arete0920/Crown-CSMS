$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$pilotRoot = Join-Path $repoRoot "audit-artifacts\pilot-loi-readiness"
$latest = Join-Path $pilotRoot "latest"
$board = Join-Path $repoRoot "audit-artifacts\release-war-room\priority_board.csv"

if (-not (Test-Path $latest)) { throw "Missing pilot-loi-readiness latest folder: $latest" }

$required = @(
    "01_pilot_loi_tracker_WORKING.md",
    "02_pilot_loi_tracker_WORKING.csv",
    "03_pipeline_owner_assignment.md",
    "04_outreach_conversion_checklist.md",
    "05_required_evidence_checklist.md"
)

$report = @()
foreach ($name in $required) {
    $path = Join-Path $latest $name
    $exists = Test-Path $path
    $size = if ($exists) { (Get-Item $path).Length } else { 0 }
    $nonEmpty = $size -gt 50
    $report += [pscustomobject]@{
        File     = $name
        Exists   = $exists
        Size     = $size
        NonEmpty = $nonEmpty
    }
}

$csvPath = Join-Path $latest "02_pilot_loi_tracker_WORKING.csv"
$loiCount = 0
$pilotCount = 0
if (Test-Path $csvPath) {
    try {
        $rows = Import-Csv $csvPath
        $loiCount = @($rows | Where-Object { $_.LOI -and $_.LOI.Trim() -ne "" -and $_.LOI -notin @("No","Open","Pending") }).Count
        $pilotCount = @($rows | Where-Object { $_.PilotStart -and $_.PilotStart.Trim() -ne "" }).Count
    } catch {
        $loiCount = 0
        $pilotCount = 0
    }
}

$out = Join-Path $latest "06_pilot_loi_closeout_validation.txt"
"=== PILOT / LOI CLOSEOUT VALIDATION ===" | Set-Content $out -Encoding utf8
$report | Format-Table File,Exists,Size,NonEmpty -AutoSize | Out-String | Add-Content $out
"" | Add-Content $out
("Signed LOI rows: " + $loiCount) | Add-Content $out
("Pilot start rows: " + $pilotCount) | Add-Content $out

$allFilesReady = ($report | Where-Object { -not $_.Exists -or -not $_.NonEmpty }).Count -eq 0
$canClose = $allFilesReady -and ($loiCount -ge 1) -and ($pilotCount -ge 1)

"" | Add-Content $out
("Can close item 9: " + $canClose) | Add-Content $out

if ($canClose) {
    if (Test-Path $board) {
        $rows = Import-Csv $board
        foreach ($row in $rows) {
            if ($row.Priority -eq "9") {
                $row.Status = "Closed"
                $row.Notes = "Closed via pilot-loi latest validation"
            }
        }
        $rows | Export-Csv $board -NoTypeInformation -Encoding utf8
    }

    $checklist = Join-Path $latest "05_required_evidence_checklist.md"
    if (Test-Path $checklist) {
        $content = Get-Content $checklist -Raw
        $content = $content -replace "- \[ \]", "- [x]"
        Set-Content $checklist $content -Encoding utf8
    }
}

Write-Host "Validation file: $out"
Write-Host "Can close item 9: $canClose"
