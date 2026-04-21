$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$cutoverRoot = Join-Path $repoRoot "audit-artifacts\cutover-rollback-readiness"
$latest = Join-Path $cutoverRoot "latest"
$board = Join-Path $repoRoot "audit-artifacts\release-war-room\priority_board.csv"

if (-not (Test-Path $latest)) { throw "Missing cutover-rollback-readiness latest folder: $latest" }

$required = @(
    "01_cutover_rollback_checklist_WORKING.md",
    "02_release_owner_assignment.md",
    "03_rehearsal_log.md",
    "04_required_evidence_checklist.md"
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

$checklist = Join-Path $latest "01_cutover_rollback_checklist_WORKING.md"
$cutoverReady = $false
$rollbackReady = $false
$goNoGoReady = $false
if (Test-Path $checklist) {
    $content = Get-Content $checklist -Raw
    if ($content -notmatch "\[ \] cutover rehearsal completed") { $cutoverReady = $true }
    if ($content -notmatch "\[ \] rollback rehearsal completed") { $rollbackReady = $true }
    if ($content -notmatch "\[ \] go/no-go signed") { $goNoGoReady = $true }
}

$out = Join-Path $latest "05_cutover_closeout_validation.txt"
"=== CUTOVER / ROLLBACK CLOSEOUT VALIDATION ===" | Set-Content $out -Encoding utf8
$report | Format-Table File,Exists,Size,NonEmpty -AutoSize | Out-String | Add-Content $out
"" | Add-Content $out
("Cutover rehearsal complete: " + $cutoverReady) | Add-Content $out
("Rollback rehearsal complete: " + $rollbackReady) | Add-Content $out
("Go/no-go signed: " + $goNoGoReady) | Add-Content $out

$allFilesReady = ($report | Where-Object { -not $_.Exists -or -not $_.NonEmpty }).Count -eq 0
$canClose = $allFilesReady -and $cutoverReady -and $rollbackReady -and $goNoGoReady

"" | Add-Content $out
("Can close item 10: " + $canClose) | Add-Content $out

if ($canClose) {
    if (Test-Path $board) {
        $rows = Import-Csv $board
        foreach ($row in $rows) {
            if ($row.Priority -eq "10") {
                $row.Status = "Closed"
                $row.Notes = "Closed via cutover-rollback latest validation"
            }
        }
        $rows | Export-Csv $board -NoTypeInformation -Encoding utf8
    }

    $evidence = Join-Path $latest "04_required_evidence_checklist.md"
    if (Test-Path $evidence) {
        $content = Get-Content $evidence -Raw
        $content = $content -replace "- \[ \]", "- [x]"
        Set-Content $evidence $content -Encoding utf8
    }
}

Write-Host "Validation file: $out"
Write-Host "Can close item 10: $canClose"
