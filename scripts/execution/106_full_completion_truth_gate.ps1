param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function New-Dir {
    param([string]$Path)
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Write-Utf8 {
    param([string]$Path, [string[]]$Lines)
    $Lines | Set-Content -Path $Path -Encoding UTF8
}

function Write-JsonFile {
    param([string]$Path, $Object)
    ($Object | ConvertTo-Json -Depth 15) | Set-Content -Path $Path -Encoding UTF8
}

function Write-CsvSafe {
    param([string]$Path, [object[]]$Rows)
    if ($null -eq $Rows -or $Rows.Count -eq 0) {
        [pscustomobject]@{ Notice = "none" } | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
    } else {
        $Rows | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
    }
}

function Convert-ToModuleKey {
    param([string]$TemplateFileName)

    $base = [System.IO.Path]::GetFileNameWithoutExtension($TemplateFileName)
    if ($base.EndsWith("Dashboard")) {
        $base = $base.Substring(0, $base.Length - "Dashboard".Length)
    }
    if ([string]::IsNullOrWhiteSpace($base)) {
        return $TemplateFileName
    }
    return $base.Substring(0, 1).ToLowerInvariant() + $base.Substring(1)
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Not inside a git repository."
}

$templateDir = Join-Path $repoRoot "frontend\dashboards\src\config\dashboardTemplates"
if (-not (Test-Path $templateDir)) {
    throw "Missing dashboard templates directory: $templateDir"
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot ".crown-audit\full-completion-truth\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\full-completion-truth\latest"
New-Dir $outDir
New-Dir $latestDir

$templateFiles = Get-ChildItem -Path $templateDir -File -Filter "*Dashboard.js" |
    Where-Object { $_.Name -ne "index.js" }

$inventory = @()
foreach ($file in $templateFiles) {
    $content = Get-Content -Path $file.FullName -Raw
    $moduleKey = Convert-ToModuleKey -TemplateFileName $file.Name
    $usesBaseNote = $content -match 'BASE_NOTE'
    $hasStaticMetricValues = $content -match 'metrics\s*:\s*\['

    $hasLiveDataSource = (
        ($content -match "dataSource\s*:\s*'live_api'") -or
        ($content -match 'dataSource\s*:\s*"live_api"')
    )
    $hasApiEndpoint = (
        ($content -match "apiEndpoint\s*:\s*'[^']+'") -or
        ($content -match 'apiEndpoint\s*:\s*"[^"]+"')
    )
    $hasLiveDataKey = (
        ($content -match "liveDataKey\s*:\s*'[^']+'") -or
        ($content -match 'liveDataKey\s*:\s*"[^"]+"')
    )

    $hasExplicitLiveState = (
        $hasLiveDataSource -and
        $hasApiEndpoint -and
        $hasLiveDataKey
    )

    $completionTruthStatus = if ($usesBaseNote -and $hasStaticMetricValues -and -not $hasExplicitLiveState) {
        "BLOCKED_PREVIEW_OR_UNPROVEN_DATA"
    } else {
        "REVIEW"
    }

    $inventory += [pscustomobject]@{
        ModuleKey = $moduleKey
        Path = ($file.FullName -replace "\\", "/")
        UsesBaseNote = $usesBaseNote
        HasStaticMetricValues = $hasStaticMetricValues
        HasExplicitLiveState = $hasExplicitLiveState
        CompletionTruthStatus = $completionTruthStatus
    }
}

$inventory = @($inventory | Sort-Object ModuleKey)
$templateBlockers = @($inventory | Where-Object { $_.CompletionTruthStatus -eq "BLOCKED_PREVIEW_OR_UNPROVEN_DATA" })

$postPatchCoverage = @(
    $inventory |
    Where-Object { $_.UsesBaseNote -and $_.HasStaticMetricValues } |
    ForEach-Object {
        [pscustomobject]@{
            ModuleKey = $_.ModuleKey
            Exists = $true
            HasInsertedLiveMeta = [bool]$_.HasExplicitLiveState
            Path = ("frontend\\dashboards\\src\\config\\dashboardTemplates\\{0}Dashboard.js" -f $_.ModuleKey)
        }
    }
)

$samplePayloadPath = Join-Path $repoRoot "backend\crown_api\dashboards\sample_payloads.py"
$backendSamplePayloadSignalCount = 0
if (Test-Path $samplePayloadPath) {
    $samplePayloadText = Get-Content -Path $samplePayloadPath -Raw
    $backendSamplePayloadSignalCount =
        [regex]::Matches($samplePayloadText, "served_from\s*:\s*'sample'").Count +
        [regex]::Matches($samplePayloadText, 'served_from\s*:\s*"sample"').Count
}

$branch = (git rev-parse --abbrev-ref HEAD).Trim()
$head = (git rev-parse HEAD).Trim()
$generatedAt = Get-Date
$generatedAtIso = $generatedAt.ToString("s")
$generatedAtHuman = $generatedAt.ToString("yyyy-MM-dd HH:mm:ss")
$requiredScopeCount = $postPatchCoverage.Count
$dashboardTemplateBlockerCount = $templateBlockers.Count
$pass = ($dashboardTemplateBlockerCount -eq 0)

Write-CsvSafe -Path (Join-Path $outDir "10_dashboard_template_preview_blockers.csv") -Rows $templateBlockers
Write-CsvSafe -Path (Join-Path $outDir "11_dashboard_template_inventory.csv") -Rows $inventory
Write-CsvSafe -Path (Join-Path $outDir "12_post_patch_live_meta_coverage.csv") -Rows $postPatchCoverage

$summary = @(
    "# CROWN Full Completion Truth Gate",
    "",
    "- Generated: $generatedAtHuman",
    "- Branch: $branch",
    "- Head: $head",
    "- Required scope rows: $requiredScopeCount",
    "- Dashboard template preview/unproven-data blockers: $dashboardTemplateBlockerCount",
    "- Backend sample-payload signals: $backendSamplePayloadSignalCount",
    "",
    $(if ($pass) { "PASS" } else { "REVIEW REQUIRED" }),
    "",
    "Completion cannot be certified while ready dashboards are template/sample/fallback backed or while backend dashboard payloads serve sample contracts without live-service proof."
)
Write-Utf8 -Path (Join-Path $outDir "00_SUMMARY.md") -Lines $summary

$status = [ordered]@{
    generated_at = $generatedAtIso
    repo_root = ($repoRoot -replace "\\", "/")
    branch = $branch
    head = $head
    required_scope_count = $requiredScopeCount
    dashboard_template_blocker_count = $dashboardTemplateBlockerCount
    backend_sample_payload_signal_count = $backendSamplePayloadSignalCount
    pass = $pass
    dashboard_template_blockers = $templateBlockers
}
Write-JsonFile -Path (Join-Path $outDir "99_STATUS.json") -Object $status

Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host "DONE"
Write-Host "SUMMARY: $(Join-Path $outDir '00_SUMMARY.md')"
Write-Host "LATEST:  $(Join-Path $latestDir '00_SUMMARY.md')"
Write-Host "STATUS:  $(Join-Path $outDir '99_STATUS.json')"
