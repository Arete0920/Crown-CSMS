$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
Set-Location $Root

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Out = Join-Path $Root "audit-artifacts\priority-07-hygiene-closure\$Stamp"
$Docs = Join-Path $Root "docs\crown-master-binder"
$Ops = Join-Path $Docs "operations"
$Design = Join-Path $Docs "design-system"
$Checklist = Join-Path $Ops "10_FINAL_RELEASE_ACCEPTANCE_CHECKLIST.csv"

New-Item -ItemType Directory -Force -Path $Out,$Ops,$Design | Out-Null
Start-Transcript -Path (Join-Path $Out "00_RUN_LOG.txt") -Force | Out-Null

Write-Host "CROWN Priority 7 hygiene closure"
Write-Host "Repo:   $Root"
Write-Host "Output: $Out"

$Branch = git branch --show-current
$Head = git rev-parse --short HEAD
$HeadFull = git rev-parse HEAD

function Export-ActionableScan {
    param(
        [string]$Type,
        [string[]]$Roots,
        [string[]]$Patterns,
        [string]$Output
    )

    $rows = [System.Collections.Generic.List[pscustomobject]]::new()
    foreach ($root in $Roots) {
        if (-not (Test-Path $root)) { continue }
        $files = Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Extension -in @('.js','.jsx','.ts','.tsx','.css','.html','.py') }

        foreach ($file in $files) {
            foreach ($pattern in $Patterns) {
                $hits = Select-String -Path $file.FullName -Pattern $pattern -AllMatches -SimpleMatch -ErrorAction SilentlyContinue
                foreach ($hit in $hits) {
                    $rows.Add([pscustomobject]@{
                        Type = $Type
                        File = $file.FullName.Replace($Root + "\", "")
                        Line = $hit.LineNumber
                        Text = $hit.Line.Trim()
                        Pattern = $pattern
                    })
                }
            }
        }
    }

    $rows | Export-Csv $Output -NoTypeInformation
    return $rows
}

$frontendPages = Join-Path $Root "frontend\dashboards\src\pages"
$frontendViews = Join-Path $Root "frontend\dashboards\src\views"
$frontendComponents = Join-Path $Root "frontend\dashboards\src\components"

$placeholderPatterns = @('TODO','FIXME','TBD','coming soon','lorem ipsum','dummy data','not implemented')
$uiRiskPatterns = @('href="#"','href=''#''','javascript:void','debugger;')

$placeholderHits = Export-ActionableScan -Type 'Placeholder' -Roots @($frontendPages,$frontendViews) -Patterns $placeholderPatterns -Output (Join-Path $Out "10_placeholder_actionable.csv")
$uiRiskHits = Export-ActionableScan -Type 'UI Risk' -Roots @($frontendPages,$frontendViews,$frontendComponents) -Patterns $uiRiskPatterns -Output (Join-Path $Out "11_ui_risk_actionable.csv")

$mojibakeHits = Export-ActionableScan -Type 'Encoding' -Roots @($frontendPages,$frontendViews,$frontendComponents) -Patterns @('ï¿½','â€”','â”€','â†»','ï¼‹') -Output (Join-Path $Out "12_encoding_actionable.csv")

$dashboardMetricRows = [System.Collections.Generic.List[pscustomobject]]::new()
$dashboardFiles = Get-ChildItem -Path $frontendPages -File -Filter "*Dashboard*.jsx" -ErrorAction SilentlyContinue
foreach ($f in $dashboardFiles) {
    $text = Get-Content $f.FullName -Raw
    $hasKpiStrip = $text -match 'KpiStrip'
    $hasDataSourceLabel = $text -match 'dataSource:'
    $hasSuspiciousPlaceholder = $text -match 'value:\s*"--"'
    $dashboardMetricRows.Add([pscustomobject]@{
        File = $f.FullName.Replace($Root + "\", "")
        UsesKpiStrip = $hasKpiStrip
        HasDataSourceMetadata = $hasDataSourceLabel
        HasStaticPlaceholderValue = $hasSuspiciousPlaceholder
        Status = if ($hasKpiStrip -and $hasDataSourceLabel) { 'PASS' } else { 'REVIEW' }
    })
}
$dashboardMetricRows | Export-Csv (Join-Path $Out "13_dashboard_metric_review.csv") -NoTypeInformation

$testLog = Join-Path $Out "14_ui_polish_tests.txt"
Push-Location (Join-Path $Root "frontend\dashboards")
try {
    npm run test -- src/tests/loginPagePolish.test.jsx tests/ui/shared-design-system-render-screen-userEvent.test.tsx 2>&1 | Tee-Object -FilePath $testLog | Out-Host
    $testExit = $LASTEXITCODE
} finally {
    Pop-Location
}

$blockers = [System.Collections.Generic.List[pscustomobject]]::new()
function Add-Blocker([string]$Priority,[string]$Area,[string]$Issue,[string]$Owner,[string]$Evidence,[string]$RequiredFix) {
    $script:blockers.Add([pscustomobject]@{
        Priority = $Priority
        Area = $Area
        Issue = $Issue
        Owner = $Owner
        Evidence = $Evidence
        RequiredFix = $RequiredFix
        Status = 'Open'
    })
}

if ($placeholderHits.Count -gt 0) {
    Add-Blocker 'P0' 'Placeholder cleanup' "Found $($placeholderHits.Count) production-facing placeholder markers." 'Dev 4 / Dev 5' (Join-Path $Out "10_placeholder_actionable.csv") 'Remove or replace placeholder/incomplete copy from production-facing views.'
}
if ($uiRiskHits.Count -gt 0) {
    Add-Blocker 'P0' 'UI polish' "Found $($uiRiskHits.Count) production-facing dead-link/debug UI risks." 'Dev 4 / Dev 5' (Join-Path $Out "11_ui_risk_actionable.csv") 'Remove dead links and debug-only interactions from user-facing views.'
}
if ($mojibakeHits.Count -gt 0) {
    Add-Blocker 'P0' 'UI text hygiene' "Found $($mojibakeHits.Count) mojibake encoding defects." 'Dev 4 / Dev 5' (Join-Path $Out "12_encoding_actionable.csv") 'Normalize encoding to clean UTF-8 text.'
}
if ($testExit -ne 0) {
    Add-Blocker 'P0' 'UI validation' 'Focused UI polish tests failed.' 'Dev 4 / Dev 5' $testLog 'Fix frontend regressions and rerun Priority 7 hygiene closure.'
}

$blockerCsv = Join-Path $Out "15_HYGIENE_BLOCKER_BOARD.csv"
$blockers | Export-Csv $blockerCsv -NoTypeInformation

$p0 = @($blockers | Where-Object { $_.Priority -eq 'P0' }).Count
$decision = if ($p0 -eq 0) { 'HYGIENE_LOCAL_PASS' } else { 'HYGIENE_P0_REMEDIATION_REQUIRED' }

$summary = @(
    '# CROWN Priority 7 - Hygiene Closure Summary',
    ('Generated: ' + (Get-Date -Format s)),
    ('Repo:      ' + $Root),
    ('Branch:    ' + $Branch),
    ('HEAD:      ' + $Head),
    ('HEAD_FULL: ' + $HeadFull),
    '',
    '## Decision',
    $decision,
    '',
    '## Counts',
    ('Placeholder hits: ' + $placeholderHits.Count),
    ('UI risk hits: ' + $uiRiskHits.Count),
    ('Encoding hits: ' + $mojibakeHits.Count),
    ('Focused UI test exit code: ' + $testExit),
    ('P0 blockers: ' + $p0),
    '',
    '## Evidence',
    ('1. ' + (Join-Path $Out '10_placeholder_actionable.csv')),
    ('2. ' + (Join-Path $Out '11_ui_risk_actionable.csv')),
    ('3. ' + (Join-Path $Out '12_encoding_actionable.csv')),
    ('4. ' + (Join-Path $Out '13_dashboard_metric_review.csv')),
    ('5. ' + $testLog),
    ('6. ' + $blockerCsv)
)

$summaryPath = Join-Path $Out "99_SUMMARY.md"
$summary | Set-Content $summaryPath -Encoding UTF8
Copy-Item $summaryPath (Join-Path $Ops "HYGIENE_CURRENT_SUMMARY.md") -Force

if ($p0 -eq 0 -and (Test-Path $Checklist)) {
    $rows = Import-Csv $Checklist
    foreach ($row in $rows) {
        if ($row.Gate -eq 'Placeholder cleanup') {
            $row.Status = 'PASS'
            $row.Evidence = (Join-Path $Out '10_placeholder_actionable.csv')
        }
        if ($row.Gate -eq 'UI polish') {
            $row.Status = 'PASS'
            $row.Evidence = $summaryPath
        }
        if ($row.Gate -eq 'Dashboards') {
            $row.Status = 'PASS'
            $row.Evidence = (Join-Path $Out '13_dashboard_metric_review.csv')
        }
    }
    $rows | Export-Csv $Checklist -NoTypeInformation
}

Write-Host ''
Write-Host 'CROWN Priority 7 hygiene closure complete.'
Write-Host "Decision: $decision"
Write-Host "Output:   $Out"
Write-Host ''
Stop-Transcript | Out-Null