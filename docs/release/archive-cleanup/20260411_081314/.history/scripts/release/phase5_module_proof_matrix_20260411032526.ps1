$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-Git {
    param([Parameter(Mandatory = $true)][string[]]$Args)
    $output = & git @Args 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Args -join ' ') failed.`n$((($output | ForEach-Object { "$_" }) -join "`n"))"
    }
    return (($output | ForEach-Object { "$_" }) -join "`n").Trim()
}

function Get-RepoRelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$FullPath,
        [Parameter(Mandatory = $true)][string]$RepoRoot
    )
    return ($FullPath.Substring($RepoRoot.Length).TrimStart('\', '/') -replace '\\', '/')
}

function Get-GitFileCommitIso {
    param([Parameter(Mandatory = $true)][string]$RelativePath)
    try {
        $output = & git log -1 --format=%cI -- $RelativePath 2>&1
        if ($LASTEXITCODE -ne 0) { return $null }
        return (($output | ForEach-Object { "$_" }) -join "`n").Trim()
    } catch {
        return $null
    }
}

$script:RepoRoot = Invoke-Git -Args @("rev-parse", "--show-toplevel")
Set-Location $script:RepoRoot

$outDir = Join-Path $script:RepoRoot "docs\release\live-audit\phase5"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$backendRoot = Join-Path $script:RepoRoot "backend"
$frontendRoot = Join-Path $script:RepoRoot "frontend"
$workflowsRoot = Join-Path $script:RepoRoot ".github\workflows"
$docsReleaseRoot = Join-Path $script:RepoRoot "docs\release"

$moduleFamilies = @(
    [pscustomobject]@{
        module_key  = "platform_core"
        label       = "Platform Core"
        backend_dirs = @("core","accounts","auth","tenants","platform_ops","api","integrations","notifications")
        frontend_dirs = @("src","dashboards")
        doc_keywords = @("tenant","rbac","auth","platform","isolation")
        workflow_keywords = @("proof","security","deploy","health","integrity")
    },
    [pscustomobject]@{
        module_key  = "admissions_enrollment"
        label       = "Admissions and Enrollment"
        backend_dirs = @("admissions","applications","reenrollment","guardian_household_wizard","enrollment_conversion_wizard","enrollment_period_wizard")
        frontend_dirs = @("src","dashboards")
        doc_keywords = @("admissions","enrollment","reenrollment","application")
        workflow_keywords = @("proof","smoke","gate")
    },
    [pscustomobject]@{
        module_key  = "finance_ledger"
        label       = "Finance Ledger Payments Aid"
        backend_dirs = @("billing","finance","finance_setup","financial_aid","ledger","payments","subscriptions","journal","billing_wizard","financial_aid_wizard","invoice_run_wizard")
        frontend_dirs = @("src","dashboards")
        doc_keywords = @("billing","finance","ledger","payments","financial")
        workflow_keywords = @("proof","security","deploy","gate")
    },
    [pscustomobject]@{
        module_key  = "academics_gradebook"
        label       = "Academics Attendance Gradebook"
        backend_dirs = @("academics","academics_ro","gradebook","graduation","attendance_codes_wizard","attendance_rules_wizard","bell_schedule_wizard","course_catalog_wizard","grade_scale_wizard","grade_weights_wizard","gradebook_setup_wizard","promotion_wizard","section_assign_wizard","section_scheduler_wizard","section_staffing_wizard","term_structure_wizard")
        frontend_dirs = @("src","dashboards")
        doc_keywords = @("academics","attendance","gradebook","transcript","graduation")
        workflow_keywords = @("gradebook","ui","proof","gate")
    },
    [pscustomobject]@{
        module_key  = "dashboards_portals"
        label       = "Dashboards and Portals"
        backend_dirs = @("student360","parent360","executive360")
        frontend_dirs = @("dashboards","src")
        doc_keywords = @("dashboard","portal","parent","student","executive")
        workflow_keywords = @("dashboard","frontend","ui","shell")
    },
    [pscustomobject]@{
        module_key  = "communications_discipline"
        label       = "Communications Discipline Safety"
        backend_dirs = @("comms","discipline","safety","support")
        frontend_dirs = @("src","dashboards")
        doc_keywords = @("announcements","messaging","discipline","safety")
        workflow_keywords = @("ui","proof","gate")
    },
    [pscustomobject]@{
        module_key  = "extended_operations"
        label       = "Extended Operations"
        backend_dirs = @("aftercare","athletics","transportation","hr","facops","classroom","foodservice","volunteer")
        frontend_dirs = @("src","dashboards")
        doc_keywords = @("aftercare","athletics","transportation","operations")
        workflow_keywords = @("proof","smoke","ui")
    },
    [pscustomobject]@{
        module_key  = "mission_addons"
        label       = "Mission Add-ons"
        backend_dirs = @("advancement","board_oversight","outreach","pdhub","servicehours","spiritual_life")
        frontend_dirs = @("src","dashboards")
        doc_keywords = @("spiritual","service","board","pdhub","outreach","advancement")
        workflow_keywords = @("proof","ui","gate")
    },
    [pscustomobject]@{
        module_key  = "release_controls"
        label       = "Release Controls"
        backend_dirs = @()
        frontend_dirs = @()
        doc_keywords = @("release","signoff","workflow","branch protection","security gate")
        workflow_keywords = @("release","deploy","proof","security","stale","cleanup")
    }
)

$workflowFiles = @()
if (Test-Path $workflowsRoot) {
    $workflowFiles = @(Get-ChildItem -Path $workflowsRoot -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in @('.yml', '.yaml') })
}

$releaseDocs = @()
if (Test-Path $docsReleaseRoot) {
    $releaseDocs = @(Get-ChildItem -Path $docsReleaseRoot -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in @('.md', '.json') })
}

$moduleRows = New-Object System.Collections.Generic.List[object]
$pathRows = New-Object System.Collections.Generic.List[object]

foreach ($family in $moduleFamilies) {
    $backendHits = New-Object System.Collections.Generic.List[string]
    $backendTests = 0
    foreach ($dirName in $family.backend_dirs) {
        $fullDir = Join-Path $backendRoot $dirName
        if (Test-Path $fullDir) {
            $backendHits.Add(("backend/{0}" -f $dirName)) | Out-Null
            $backendTests += (Get-ChildItem -Path $fullDir -Recurse -File -Include test_*.py,*.py -ErrorAction SilentlyContinue |
                Where-Object { $_.FullName -match '\\tests\\' -or $_.Name -like 'test_*.py' } |
                Measure-Object).Count
        }
    }

    $frontendHits = New-Object System.Collections.Generic.List[string]
    foreach ($dirName in $family.frontend_dirs) {
        $fullDir = Join-Path $frontendRoot $dirName
        if (Test-Path $fullDir) {
            $frontendHits.Add(("frontend/{0}" -f $dirName)) | Out-Null
        }
    }

    $docHits = New-Object System.Collections.Generic.List[string]
    foreach ($doc in $releaseDocs) {
        $content = Get-Content -Path $doc.FullName -Raw -Encoding UTF8
        $matched = $false
        foreach ($keyword in $family.doc_keywords) {
            if ($content -match [regex]::Escape($keyword)) {
                $matched = $true
                break
            }
        }
        if ($matched) {
            $docHits.Add((Get-RepoRelativePath -FullPath $doc.FullName -RepoRoot $script:RepoRoot)) | Out-Null
        }
    }
    $docHits = [System.Collections.Generic.List[string]](@($docHits | Select-Object -Unique))

    $workflowHits = New-Object System.Collections.Generic.List[string]
    foreach ($wf in $workflowFiles) {
        $content = Get-Content -Path $wf.FullName -Raw -Encoding UTF8
        $matched = $false
        foreach ($keyword in $family.workflow_keywords) {
            if (($wf.Name -match [regex]::Escape($keyword)) -or ($content -match [regex]::Escape($keyword))) {
                $matched = $true
                break
            }
        }
        if ($matched) {
            $workflowHits.Add((Get-RepoRelativePath -FullPath $wf.FullName -RepoRoot $script:RepoRoot)) | Out-Null
        }
    }
    $workflowHits = [System.Collections.Generic.List[string]](@($workflowHits | Select-Object -Unique))

    $score = 0
    if ($backendHits.Count -gt 0) { $score += 30 }
    if ($backendTests -gt 0) { $score += 20 }
    if ($frontendHits.Count -gt 0) { $score += 15 }
    if ($docHits.Count -gt 0) { $score += 15 }
    if ($workflowHits.Count -gt 0) { $score += 20 }
    if ($score -gt 100) { $score = 100 }

    $status = if ($score -ge 85) { "STRONG" }
    elseif ($score -ge 65) { "GOOD" }
    elseif ($score -ge 45) { "PARTIAL" }
    else { "THIN" }

    $moduleRows.Add([pscustomobject]@{
        module_key              = $family.module_key
        label                   = $family.label
        backend_path_count      = $backendHits.Count
        backend_test_count      = $backendTests
        frontend_path_count     = $frontendHits.Count
        release_doc_hit_count   = $docHits.Count
        workflow_hit_count      = $workflowHits.Count
        proof_score             = $score
        proof_status            = $status
        representative_paths    = ((@($backendHits) + @($frontendHits) + @($docHits) + @($workflowHits)) | Select-Object -First 12) -join ', '
    }) | Out-Null

    foreach ($path in $backendHits) {
        $pathRows.Add([pscustomobject]@{ module_key = $family.module_key; path_type = "backend"; path = $path; last_commit_iso = Get-GitFileCommitIso -RelativePath $path }) | Out-Null
    }
    foreach ($path in $frontendHits) {
        $pathRows.Add([pscustomobject]@{ module_key = $family.module_key; path_type = "frontend"; path = $path; last_commit_iso = Get-GitFileCommitIso -RelativePath $path }) | Out-Null
    }
    foreach ($path in $docHits) {
        $pathRows.Add([pscustomobject]@{ module_key = $family.module_key; path_type = "release_doc"; path = $path; last_commit_iso = Get-GitFileCommitIso -RelativePath $path }) | Out-Null
    }
    foreach ($path in $workflowHits) {
        $pathRows.Add([pscustomobject]@{ module_key = $family.module_key; path_type = "workflow"; path = $path; last_commit_iso = Get-GitFileCommitIso -RelativePath $path }) | Out-Null
    }
}

$moduleCsv = Join-Path $outDir "phase5_module_proof_matrix.csv"
$pathsCsv = Join-Path $outDir "phase5_module_proof_paths.csv"
$summaryJson = Join-Path $outDir "phase5_module_proof_matrix.json"
$summaryMd = Join-Path $outDir "phase5_module_proof_matrix.md"
$liveMd = Join-Path $script:RepoRoot "docs\release\LIVE_MODULE_PROOF_MATRIX.md"
$liveJson = Join-Path $script:RepoRoot "docs\release\LIVE_MODULE_PROOF_MATRIX.json"

$moduleRows | Export-Csv -Path $moduleCsv -NoTypeInformation -Encoding UTF8
$pathRows | Export-Csv -Path $pathsCsv -NoTypeInformation -Encoding UTF8

$strongModules = @($moduleRows | Where-Object { $_.proof_status -eq "STRONG" })
$goodModules = @($moduleRows | Where-Object { $_.proof_status -eq "GOOD" })
$partialModules = @($moduleRows | Where-Object { $_.proof_status -eq "PARTIAL" })
$thinModules = @($moduleRows | Where-Object { $_.proof_status -eq "THIN" })

$summary = [ordered]@{
    generated_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    module_count     = $moduleRows.Count
    strong_count     = $strongModules.Count
    good_count       = $goodModules.Count
    partial_count    = $partialModules.Count
    thin_count       = $thinModules.Count
}

$summary | ConvertTo-Json -Depth 6 | Set-Content -Path $summaryJson -Encoding UTF8
@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
    modules          = $moduleRows
    paths            = $pathRows
} | ConvertTo-Json -Depth 8 | Set-Content -Path $liveJson -Encoding UTF8

$moduleLines = ($moduleRows | Sort-Object module_key | ForEach-Object {
    "- $($_.label) | score=$($_.proof_score) | status=$($_.proof_status) | backend_paths=$($_.backend_path_count) | tests=$($_.backend_test_count) | docs=$($_.release_doc_hit_count) | workflows=$($_.workflow_hit_count)"
}) -join "`r`n"

$markdown = @"
# LIVE MODULE PROOF MATRIX

Generated UTC: $($summary.generated_at_utc)

## Module Summary
- module count: $($summary.module_count)
- strong: $($summary.strong_count)
- good: $($summary.good_count)
- partial: $($summary.partial_count)
- thin: $($summary.thin_count)

## Module Scores
$moduleLines

## Artifact Paths
- docs/release/live-audit/phase5/phase5_module_proof_matrix.csv
- docs/release/live-audit/phase5/phase5_module_proof_paths.csv
"@

Set-Content -Path $liveMd -Value $markdown -Encoding UTF8
Set-Content -Path $summaryMd -Value $markdown -Encoding UTF8

Write-Host ""
Write-Host "PHASE 5 COMPLETE"
Write-Host "Output directory: $outDir"
Write-Host "Live module proof matrix: $liveMd"
Write-Host ""
