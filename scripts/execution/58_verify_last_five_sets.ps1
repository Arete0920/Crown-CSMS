param(
    [switch]$OpenReports
)

$ErrorActionPreference = "Stop"

function Set-Utf8File {
    param([string]$Path,[string]$Content)
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    $Content | Set-Content -Path $Path -Encoding utf8
}

function Get-LatestTimestampDir {
    param([string]$Root)
    if (-not (Test-Path $Root)) { return $null }
    return Get-ChildItem $Root -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^\d{8}_\d{6}$' } |
        Sort-Object Name -Descending |
        Select-Object -First 1
}

function Add-Result {
    param(
        [System.Collections.ArrayList]$List,
        [string]$Section,
        [string]$Item,
        [string]$Path,
        [bool]$Pass,
        [string]$Detail
    )
    [void]$List.Add([pscustomobject]@{
        Section = $Section
        Item    = $Item
        Path    = $Path
        Pass    = $Pass
        Detail  = $Detail
    })
}

function Open-IfExists {
    param([string]$Path)
    if (Test-Path $Path) { code $Path }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$outRoot = Join-Path $repoRoot ("audit-artifacts\verify-last-five\" + $ts)
New-Item -ItemType Directory -Force -Path $outRoot | Out-Null

$results = New-Object System.Collections.ArrayList

# --------------------------------------------------
# Script existence: 53-57
# --------------------------------------------------
$scriptMap = @(
    @{ N = "53_harden_release_truth.ps1";        P = ".\scripts\execution\53_harden_release_truth.ps1" },
    @{ N = "54_generate_pr_quality_ledger.ps1"; P = ".\scripts\execution\54_generate_pr_quality_ledger.ps1" },
    @{ N = "55_fix_workflow_permissions.ps1";   P = ".\scripts\execution\55_fix_workflow_permissions.ps1" },
    @{ N = "56_verify_workflow_permissions.ps1";P = ".\scripts\execution\56_verify_workflow_permissions.ps1" },
    @{ N = "57_repo_full_cleanup.ps1";          P = ".\scripts\execution\57_repo_full_cleanup.ps1" }
)

foreach ($s in $scriptMap) {
    $exists = Test-Path $s.P
    Add-Result -List $results -Section "Scripts" -Item $s.N -Path $s.P -Pass $exists -Detail ($(if ($exists) { "Found" } else { "Missing" }))
}

# --------------------------------------------------
# 53 output verification
# --------------------------------------------------
$truthLatest = Get-LatestTimestampDir -Root ".\audit-artifacts\release-truth-hardening"
if ($truthLatest) {
    $truthSummary = Join-Path $truthLatest.FullName "SUMMARY.md"
    $truthSelection = Join-Path $truthLatest.FullName "09_release_truth_selection.md"
    $truthAudit = Join-Path $truthLatest.FullName "10_audit_pack_completeness.csv"
    $truthManifest = Join-Path $truthLatest.FullName "11_artifacts_manifest.csv"

    foreach ($p in @($truthSummary,$truthSelection,$truthAudit,$truthManifest)) {
        Add-Result -List $results -Section "53 Outputs" -Item ([IO.Path]::GetFileName($p)) -Path $p -Pass (Test-Path $p) -Detail ($(if (Test-Path $p) { "Found" } else { "Missing" }))
    }

    $worktreePath = ""
    if (Test-Path $truthSelection) {
        $content = Get-Content $truthSelection -Raw
        $m = [regex]::Match($content, '## Worktree root\s*[\r\n]+(.+)$', 'Multiline')
        if ($m.Success) { $worktreePath = $m.Groups[1].Value.Trim() }
    }
    Add-Result -List $results -Section "53 Outputs" -Item "Release truth worktree" -Path $worktreePath -Pass ([string]::IsNullOrWhiteSpace($worktreePath) -eq $false -and (Test-Path $worktreePath)) -Detail ($(if ($worktreePath -and (Test-Path $worktreePath)) { "Worktree exists" } else { "Worktree missing or unreadable" }))
} else {
    Add-Result -List $results -Section "53 Outputs" -Item "release-truth-hardening latest" -Path ".\audit-artifacts\release-truth-hardening" -Pass $false -Detail "No timestamped output folder found"
}

# --------------------------------------------------
# 54 output verification
# --------------------------------------------------
$ledgerLatest = Get-LatestTimestampDir -Root ".\audit-artifacts\merged-pr-quality-ledger"
if ($ledgerLatest) {
    $ledgerFiles = @(
        "00_context.md",
        "02_merged_pr_quality_ledger.csv",
        "03_ranked_remediation_list.csv",
        "04_summary.md",
        "05_recommended_followup.md"
    )
    foreach ($f in $ledgerFiles) {
        $p = Join-Path $ledgerLatest.FullName $f
        Add-Result -List $results -Section "54 Outputs" -Item $f -Path $p -Pass (Test-Path $p) -Detail ($(if (Test-Path $p) { "Found" } else { "Missing" }))
    }

    $summaryPath = Join-Path $ledgerLatest.FullName "04_summary.md"
    $detail = "Summary unreadable"
    $pass = $false
    if (Test-Path $summaryPath) {
        $text = Get-Content $summaryPath -Raw
        $pass = ($text -match 'Total merged PRs analyzed:\s*\d+')
        $detail = $(if ($pass) { "Contains analyzed totals" } else { "Totals not found in summary" })
    }
    Add-Result -List $results -Section "54 Outputs" -Item "Ledger totals check" -Path $summaryPath -Pass $pass -Detail $detail
} else {
    Add-Result -List $results -Section "54 Outputs" -Item "merged-pr-quality-ledger latest" -Path ".\audit-artifacts\merged-pr-quality-ledger" -Pass $false -Detail "No timestamped output folder found"
}

# --------------------------------------------------
# 55/56 output verification
# --------------------------------------------------
$wfFixLatest = Get-LatestTimestampDir -Root ".\audit-artifacts\workflow-permissions-fix"
if ($wfFixLatest) {
    $wfSummary = Join-Path $wfFixLatest.FullName "SUMMARY.md"
    $wfReport = Join-Path $wfFixLatest.FullName "workflow_permissions_report.csv"
    $wfVerify = Join-Path $wfFixLatest.FullName "workflow_permissions_verify.txt"

    foreach ($p in @($wfSummary,$wfReport,$wfVerify)) {
        Add-Result -List $results -Section "55/56 Outputs" -Item ([IO.Path]::GetFileName($p)) -Path $p -Pass (Test-Path $p) -Detail ($(if (Test-Path $p) { "Found" } else { "Missing" }))
    }

    $remainingZero = $false
    if (Test-Path $wfSummary) {
        $summaryText = Get-Content $wfSummary -Raw
        $remainingZero = $summaryText -match 'Remaining missing:\s*0'
    }
    Add-Result -List $results -Section "55/56 Outputs" -Item "Remaining missing permissions" -Path $wfSummary -Pass $remainingZero -Detail ($(if ($remainingZero) { "Zero missing permissions" } else { "Non-zero or unreadable" }))

    $verifyAllTrue = $false
    if (Test-Path $wfVerify) {
        $lines = Get-Content $wfVerify
        $neg = @($lines | Where-Object { $_ -match 'permissions=False' }).Count
        $verifyAllTrue = ($neg -eq 0)
    }
    Add-Result -List $results -Section "55/56 Outputs" -Item "Verify pass" -Path $wfVerify -Pass $verifyAllTrue -Detail ($(if ($verifyAllTrue) { "No workflow missing permissions in verify output" } else { "One or more workflows still show permissions=False" }))
} else {
    Add-Result -List $results -Section "55/56 Outputs" -Item "workflow-permissions-fix latest" -Path ".\audit-artifacts\workflow-permissions-fix" -Pass $false -Detail "No timestamped output folder found"
}

# --------------------------------------------------
# 57 output verification
# --------------------------------------------------
$cleanupLatest = Get-LatestTimestampDir -Root ".\audit-artifacts\repo-full-cleanup"
if ($cleanupLatest) {
    $cleanupFiles = @(
        "README_REPO_FULL_CLEANUP.txt",
        "reports\SUMMARY.md",
        "reports\06_artifact_prune_plan.csv",
        "reports\07_zip_prune_plan.csv",
        "reports\08_sibling_dir_review.csv"
    )
    foreach ($f in $cleanupFiles) {
        $p = Join-Path $cleanupLatest.FullName $f
        Add-Result -List $results -Section "57 Outputs" -Item $f -Path $p -Pass (Test-Path $p) -Detail ($(if (Test-Path $p) { "Found" } else { "Missing" }))
    }
} else {
    Add-Result -List $results -Section "57 Outputs" -Item "repo-full-cleanup latest" -Path ".\audit-artifacts\repo-full-cleanup" -Pass $false -Detail "No timestamped output folder found"
}

# --------------------------------------------------
# Workspace hygiene files from the cleanup sets
# --------------------------------------------------
$workspaceFiles = @(
    ".\Crown2026_clean.code-workspace",
    ".\.vscode\settings.json",
    ".\.vscode\PSScriptAnalyzerSettings.psd1"
)
foreach ($p in $workspaceFiles) {
    Add-Result -List $results -Section "Workspace Files" -Item ([IO.Path]::GetFileName($p)) -Path $p -Pass (Test-Path $p) -Detail ($(if (Test-Path $p) { "Found" } else { "Missing" }))
}

# --------------------------------------------------
# Export reports
# --------------------------------------------------
$csvPath = Join-Path $outRoot "verify_last_five.csv"
$mdPath = Join-Path $outRoot "SUMMARY.md"
$results | Export-Csv $csvPath -NoTypeInformation -Encoding utf8

$total = @($results).Count
$passed = @($results | Where-Object { $_.Pass -eq $true }).Count
$failed = @($results | Where-Object { $_.Pass -eq $false }).Count

$summary = @()
$summary += "# Verify Last Five Sets"
$summary += ""
$summary += "- Total checks: $total"
$summary += "- Passed: $passed"
$summary += "- Failed: $failed"
$summary += ""
$summary += "## Failed items"
$failedRows = @($results | Where-Object { $_.Pass -eq $false })
if ($failedRows.Count -eq 0) {
    $summary += "- None"
} else {
    foreach ($r in $failedRows) {
        $summary += "- [$($r.Section)] $($r.Item) :: $($r.Detail)"
    }
}
$summary += ""
$summary += "## Latest folders checked"
$summary += "- release-truth-hardening: $(if ($truthLatest) { $truthLatest.FullName } else { 'MISSING' })"
$summary += "- merged-pr-quality-ledger: $(if ($ledgerLatest) { $ledgerLatest.FullName } else { 'MISSING' })"
$summary += "- workflow-permissions-fix: $(if ($wfFixLatest) { $wfFixLatest.FullName } else { 'MISSING' })"
$summary += "- repo-full-cleanup: $(if ($cleanupLatest) { $cleanupLatest.FullName } else { 'MISSING' })"
$summary += ""
$summary += "## Next"
$summary += "- If Failed = 0, VS Code completed the last five sets successfully."
$summary += "- If any item failed, open verify_last_five.csv and repair only those missing pieces."

Set-Utf8File -Path $mdPath -Content ($summary -join "`r`n")

Write-Host ""
Write-Host "DONE"
Write-Host "Report root: $outRoot"
Write-Host "Passed: $passed / $total"
Write-Host "Failed: $failed"

if ($OpenReports) {
    Open-IfExists $mdPath
    Open-IfExists $csvPath
    if ($truthLatest)   { Open-IfExists (Join-Path $truthLatest.FullName "SUMMARY.md") }
    if ($ledgerLatest)  { Open-IfExists (Join-Path $ledgerLatest.FullName "04_summary.md") }
    if ($wfFixLatest)   { Open-IfExists (Join-Path $wfFixLatest.FullName "SUMMARY.md") }
    if ($cleanupLatest) { Open-IfExists (Join-Path $cleanupLatest.FullName "reports\SUMMARY.md") }
}

if ($failed -gt 0) { exit 1 }
