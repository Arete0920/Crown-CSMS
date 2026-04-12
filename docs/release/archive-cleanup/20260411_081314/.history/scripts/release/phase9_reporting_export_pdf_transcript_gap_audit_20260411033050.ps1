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

$script:RepoRoot = Invoke-Git -Args @("rev-parse", "--show-toplevel")
Set-Location $script:RepoRoot

$outDir = Join-Path $script:RepoRoot "docs\release\live-audit\phase9"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$searchRoots = @(
    (Join-Path $script:RepoRoot "backend"),
    (Join-Path $script:RepoRoot "frontend"),
    (Join-Path $script:RepoRoot "docs")
) | Where-Object { Test-Path $_ }

$allFiles = New-Object System.Collections.Generic.List[string]
foreach ($root in $searchRoots) {
    Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
        $allFiles.Add($_.FullName) | Out-Null
    }
}

$keywordMap = @(
    [pscustomobject]@{ area = "pdf_engine"; keywords = @("reportlab", "weasyprint", "xhtml2pdf", "wkhtmltopdf", "pdfkit", "pydyf", "pdf") },
    [pscustomobject]@{ area = "reporting_exports"; keywords = @("export", "csv", "xlsx", "report", "download") },
    [pscustomobject]@{ area = "transcripts_reportcards"; keywords = @("transcript", "report card", "report_card", "graduation") },
    [pscustomobject]@{ area = "board_packs"; keywords = @("board pack", "board_packet", "board report", "board_oversight") },
    [pscustomobject]@{ area = "analytics_rollups"; keywords = @("aggregate", "rollup", "analytics", "dashboard metrics") }
)

$hitRows = New-Object System.Collections.Generic.List[object]
$areaRows = New-Object System.Collections.Generic.List[object]

foreach ($entry in $keywordMap) {
    $areaHitCount = 0
    $areaTestCount = 0
    $uniquePaths = New-Object System.Collections.Generic.HashSet[string]

    foreach ($file in $allFiles) {
        $relative = Get-RepoRelativePath -FullPath $file -RepoRoot $script:RepoRoot
        $content = ""
        try {
            $content = Get-Content -Path $file -Raw -Encoding UTF8 -ErrorAction Stop
        } catch {
            continue
        }

        $matchedKeywords = New-Object System.Collections.Generic.List[string]
        foreach ($keyword in $entry.keywords) {
            if ($content -match [regex]::Escape($keyword) -or $relative -match [regex]::Escape($keyword)) {
                $matchedKeywords.Add($keyword) | Out-Null
            }
        }

        if ($matchedKeywords.Count -gt 0) {
            $areaHitCount += 1
            [void]$uniquePaths.Add($relative)
            if ($relative -match '/tests/|\\tests\\|test_') {
                $areaTestCount += 1
            }
            $hitRows.Add([pscustomobject]@{
                area     = $entry.area
                path     = $relative
                keywords = (@($matchedKeywords | Select-Object -Unique) -join ', ')
                is_test  = ($relative -match '/tests/|\\tests\\|test_')
            }) | Out-Null
        }
    }

    $status = if ($areaHitCount -ge 15 -and $areaTestCount -ge 2) {
        "READY"
    } elseif ($areaHitCount -ge 5) {
        "PARTIAL"
    } else {
        "GAP"
    }

    $areaRows.Add([pscustomobject]@{
        area                = $entry.area
        evidence_path_count = $areaHitCount
        unique_path_count   = $uniquePaths.Count
        test_hit_count      = $areaTestCount
        status              = $status
        representative_paths = ((@($uniquePaths) | Select-Object -First 10) -join ', ')
    }) | Out-Null
}

$requirementsFiles = @(Get-ChildItem -Path $script:RepoRoot -Recurse -File -Include requirements*.txt,pyproject.toml,package.json -ErrorAction SilentlyContinue)
$dependencyHits = New-Object System.Collections.Generic.List[object]
$dependencyKeywords = @("reportlab", "weasyprint", "xhtml2pdf", "pdfkit", "openpyxl", "xlsxwriter")

foreach ($file in $requirementsFiles) {
    $content = ""
    try {
        $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8 -ErrorAction Stop
    } catch {
        continue
    }

    foreach ($keyword in $dependencyKeywords) {
        if ($content -match [regex]::Escape($keyword)) {
            $dependencyHits.Add([pscustomobject]@{
                dependency = $keyword
                path       = Get-RepoRelativePath -FullPath $file.FullName -RepoRoot $script:RepoRoot
            }) | Out-Null
        }
    }
}

$areasCsv = Join-Path $outDir "phase9_reporting_export_area_status.csv"
$hitsCsv = Join-Path $outDir "phase9_reporting_export_hits.csv"
$depsCsv = Join-Path $outDir "phase9_reporting_export_dependency_hits.csv"
$summaryJson = Join-Path $outDir "phase9_reporting_export_pdf_transcript_gap_audit.json"
$summaryMd = Join-Path $outDir "phase9_reporting_export_pdf_transcript_gap_audit.md"
$liveMd = Join-Path $script:RepoRoot "docs\release\LIVE_REPORTING_EXPORT_AUDIT.md"
$liveJson = Join-Path $script:RepoRoot "docs\release\LIVE_REPORTING_EXPORT_AUDIT.json"

$areaRows | Export-Csv -Path $areasCsv -NoTypeInformation -Encoding UTF8
$hitRows | Export-Csv -Path $hitsCsv -NoTypeInformation -Encoding UTF8
$dependencyHits | Export-Csv -Path $depsCsv -NoTypeInformation -Encoding UTF8

$readyRows = @($areaRows | Where-Object { $_.status -eq "READY" })
$partialRows = @($areaRows | Where-Object { $_.status -eq "PARTIAL" })
$gapRows = @($areaRows | Where-Object { $_.status -eq "GAP" })
$uniqueDependencyHits = @($dependencyHits | Select-Object dependency, path -Unique)

$readyCount = $readyRows.Count
$partialCount = $partialRows.Count
$gapCount = $gapRows.Count

$score = 0
foreach ($row in $areaRows) {
    if ($row.status -eq "READY") {
        $score += 20
    } elseif ($row.status -eq "PARTIAL") {
        $score += 10
    }
}
if ($score -gt 100) { $score = 100 }

$summary = [ordered]@{
    generated_at_utc   = (Get-Date).ToUniversalTime().ToString("o")
    area_count         = $areaRows.Count
    ready_count        = $readyCount
    partial_count      = $partialCount
    gap_count          = $gapCount
    dependency_hit_count = $uniqueDependencyHits.Count
    evidence_hit_count = $hitRows.Count
    reporting_score    = $score
}

$summary | ConvertTo-Json -Depth 6 | Set-Content -Path $summaryJson -Encoding UTF8
@{
    generated_at_utc = $summary.generated_at_utc
    summary          = $summary
    areas            = $areaRows
    hits             = $hitRows
    dependency_hits  = $dependencyHits
} | ConvertTo-Json -Depth 8 | Set-Content -Path $liveJson -Encoding UTF8

$areaLines = ($areaRows | ForEach-Object {
    "- $($_.area) | status=$($_.status) | evidence_paths=$($_.evidence_path_count) | tests=$($_.test_hit_count)"
}) -join "`r`n"

$depLines = if ($dependencyHits.Count -gt 0) {
    ($dependencyHits | ForEach-Object {
        "- $($_.dependency) | $($_.path)"
    }) -join "`r`n"
} else {
    "- none"
}

$markdown = @"
# LIVE REPORTING EXPORT AUDIT

Generated UTC: $($summary.generated_at_utc)

## Reporting Summary
- area count: $($summary.area_count)
- ready count: $($summary.ready_count)
- partial count: $($summary.partial_count)
- gap count: $($summary.gap_count)
- dependency hit count: $($summary.dependency_hit_count)
- evidence hit count: $($summary.evidence_hit_count)
- reporting score: $($summary.reporting_score)

## Area Status
$areaLines

## Dependency Hits
$depLines

## Artifact Paths
- docs/release/live-audit/phase9/phase9_reporting_export_area_status.csv
- docs/release/live-audit/phase9/phase9_reporting_export_hits.csv
- docs/release/live-audit/phase9/phase9_reporting_export_dependency_hits.csv
"@

Set-Content -Path $liveMd -Value $markdown -Encoding UTF8
Set-Content -Path $summaryMd -Value $markdown -Encoding UTF8

Write-Host ""
Write-Host "PHASE 9 COMPLETE"
Write-Host "Output directory: $outDir"
Write-Host "Live reporting export audit: $liveMd"
Write-Host ""
