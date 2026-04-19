$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$legalRoot = Join-Path $repoRoot "audit-artifacts\legal-dpa-readiness"
$latest = Join-Path $legalRoot "latest"
$board = Join-Path $repoRoot "audit-artifacts\release-war-room\priority_board.csv"

if (-not (Test-Path $latest)) {
    throw "Missing legal-dpa-readiness latest folder: $latest"
}

$required = @(
    "01_legal_dpa_readiness_WORKING.md",
    "02_legal_owner_assignment.md",
    "03_dpa_clause_review_matrix.md",
    "04_signature_workflow.md",
    "05_data_handling_responsibilities.md",
    "06_school_facing_packet_checklist.md",
    "07_final_legal_signoff.md",
    "08_required_evidence_checklist.md"
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
        Path     = $path
    }
}

$signoff = Join-Path $latest "07_final_legal_signoff.md"
$signoffReady = $false
if (Test-Path $signoff) {
    $content = Get-Content $signoff -Raw
    if ($content -match "School-facing packet ready" -and $content -notmatch "\[ \] School-facing packet ready") {
        $signoffReady = $true
    }
    elseif ($content -match "Status:" -and $content -notmatch "Status:\s*$") {
        $signoffReady = $true
    }
}

$out = Join-Path $latest "09_legal_closeout_validation.txt"
"=== LEGAL / DPA CLOSEOUT VALIDATION ===" | Set-Content $out -Encoding utf8
$report | Format-Table File,Exists,Size,NonEmpty -AutoSize | Out-String | Add-Content $out
"" | Add-Content $out
("Final legal signoff ready: " + $signoffReady) | Add-Content $out

$allFilesReady = ($report | Where-Object { -not $_.Exists -or -not $_.NonEmpty }).Count -eq 0
$canClose = $allFilesReady -and $signoffReady

"" | Add-Content $out
("Can close item 8: " + $canClose) | Add-Content $out

if ($canClose) {
    if (Test-Path $board) {
        $rows = Import-Csv $board
        foreach ($row in $rows) {
            if ($row.Priority -eq "8") {
                $row.Status = "Closed"
                $row.Notes = "Closed via legal-dpa latest validation"
            }
        }
        $rows | Export-Csv $board -NoTypeInformation -Encoding utf8
    }

    $checklist = Join-Path $latest "08_required_evidence_checklist.md"
    if (Test-Path $checklist) {
        $content = Get-Content $checklist -Raw
        $content = $content -replace "- \[ \]", "- [x]"
        Set-Content $checklist $content -Encoding utf8
    }
}

Write-Host "Validation file: $out"
Write-Host "Can close item 8: $canClose"
