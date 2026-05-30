param(
    [switch]$AllowPreviewData
)

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

function Write-CsvSafe {
    param([string]$Path, [object[]]$Rows)
    if ($null -eq $Rows -or $Rows.Count -eq 0) {
        [pscustomobject]@{ Notice = "none" } | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
    } else {
        $Rows | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
    }
}

function Write-JsonFile {
    param([string]$Path, $Object)
    ($Object | ConvertTo-Json -Depth 12) | Set-Content -Path $Path -Encoding UTF8
}

function Get-RelativePathSafe {
    param([string]$Root, [string]$Path)
    return $Path.Replace($Root + [System.IO.Path]::DirectorySeparatorChar, "").Replace("\", "/")
}

function Get-ModuleKeyFromTemplateName {
    param([string]$FileName)
    $base = [System.IO.Path]::GetFileNameWithoutExtension($FileName)
    return $base -replace "Dashboard$", ""
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Not inside a git repository."
}

Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot ".crown-audit\full-completion-truth\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\full-completion-truth\latest"
New-Dir $outDir
New-Dir $latestDir

$requiredScope = @(
    "attendance",
    "billing",
    "financial-aid",
    "registrar",
    "scheduling",
    "gradebook",
    "student-care",
    "activities-athletics",
    "communications",
    "hr",
    "facilities",
    "health-office",
    "transportation",
    "food-service",
    "it-support",
    "fine-arts",
    "library-media",
    "extended-care",
    "safety-security",
    "curriculum-pd",
    "spiritual-life",
    "advancement-operations",
    "volunteer-management",
    "alumni",
    "network-benchmarking",
    "platform-operations"
)

$templateDir = Join-Path $repoRoot "frontend\dashboards\src\config\dashboardTemplates"
$templateRows = @()
$templateBlockers = @()

if (Test-Path $templateDir) {
    $templateFiles = Get-ChildItem $templateDir -File -Filter "*Dashboard.js" | Sort-Object Name
    foreach ($file in $templateFiles) {
        $content = Get-Content $file.FullName -Raw
        $usesBaseNote = $content -match 'BASE_NOTE'
        $hasStaticMetricValues = $content -match 'metrics\s*:\s*\[' -and $content -match 'value\s*:'
        $hasExplicitLiveState = $content -match 'dataState\s*:\s*["'']live["'']' -or $content -match 'sourceLabel\s*:'
        $moduleKey = Get-ModuleKeyFromTemplateName -FileName $file.Name
        $relativePath = Get-RelativePathSafe -Root $repoRoot -Path $file.FullName

        $row = [pscustomobject]@{
            ModuleKey = $moduleKey
            Path = $relativePath
            UsesBaseNote = $usesBaseNote
            HasStaticMetricValues = $hasStaticMetricValues
            HasExplicitLiveState = $hasExplicitLiveState
            CompletionTruthStatus = if ($usesBaseNote -or (-not $hasExplicitLiveState)) { "BLOCKED_PREVIEW_OR_UNPROVEN_DATA" } else { "REVIEW" }
        }
        $templateRows += $row

        if (-not $AllowPreviewData -and ($usesBaseNote -or (-not $hasExplicitLiveState))) {
            $templateBlockers += $row
        }
    }
}

$backendSamplePath = Join-Path $repoRoot "backend\crown_api\dashboards\sample_payloads.py"
$backendRows = @()
if (Test-Path $backendSamplePath) {
    $lines = Get-Content $backendSamplePath
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ($line -match 'served_from["'']?\s*:\s*["'']sample["'']' -or $line -match 'def\s+.*_sample_payload') {
            $backendRows += [pscustomobject]@{
                Path = Get-RelativePathSafe -Root $repoRoot -Path $backendSamplePath
                LineNumber = $i + 1
                Signal = $line.Trim()
                CompletionTruthStatus = "BLOCKED_SAMPLE_PAYLOAD_OR_FALLBACK"
            }
        }
    }
}

$registryPath = Join-Path $repoRoot "frontend\dashboards\src\config\dashboardRegistry.js"
$pathsPath = Join-Path $repoRoot "frontend\dashboards\src\routes\paths.js"
$settingsPath = Join-Path $repoRoot "backend\crown_api\settings.py"

$registryText = if (Test-Path $registryPath) { Get-Content $registryPath -Raw } else { "" }
$pathsText = if (Test-Path $pathsPath) { Get-Content $pathsPath -Raw } else { "" }
$settingsText = if (Test-Path $settingsPath) { Get-Content $settingsPath -Raw } else { "" }

$scopeRows = @()
foreach ($scope in $requiredScope) {
    $compact = $scope.Replace("-", "")
    $snake = $scope.Replace("-", "_")
    $titleish = ($scope -split "-") | ForEach-Object { if ($_.Length -gt 0) { $_.Substring(0,1).ToUpperInvariant() + $_.Substring(1) } else { $_ } }
    $pascal = ($titleish -join "")

    $registryHit = $registryText -match [regex]::Escape($scope) -or $registryText -match [regex]::Escape($pascal)
    $pathHit = $pathsText -match [regex]::Escape($scope) -or $pathsText -match [regex]::Escape($scope.Replace("-", "_")) -or $pathsText -match [regex]::Escape($pascal)
    $backendHit = $settingsText -match [regex]::Escape($scope) -or $settingsText -match [regex]::Escape($snake) -or $settingsText -match [regex]::Escape($compact) -or $settingsText -match [regex]::Escape($pascal)
    $templateBlockerHit = @($templateBlockers | Where-Object { $_.ModuleKey -match $compact -or $_.ModuleKey -match $pascal -or $_.Path -match $scope -or $_.Path -match $compact }).Count -gt 0

    $scopeRows += [pscustomobject]@{
        Scope = $scope
        FrontendRegistrySignal = $registryHit
        FrontendPathSignal = $pathHit
        BackendInstalledAppSignal = $backendHit
        PreviewOrUnprovenTemplateSignal = $templateBlockerHit
        CompletionStatus = if ($templateBlockerHit) { "BLOCKED_LIVE_DATA_PROOF" } elseif ($registryHit -and $pathHit -and $backendHit) { "IN_PROGRESS_NEEDS_RUNTIME_PROOF" } else { "UNKNOWN_OR_MISSING_SURFACE" }
    }
}

Write-CsvSafe -Path (Join-Path $outDir "10_dashboard_template_preview_blockers.csv") -Rows $templateBlockers
Write-CsvSafe -Path (Join-Path $outDir "11_dashboard_template_inventory.csv") -Rows $templateRows
Write-CsvSafe -Path (Join-Path $outDir "20_backend_sample_payload_blockers.csv") -Rows $backendRows
Write-CsvSafe -Path (Join-Path $outDir "30_required_scope_status.csv") -Rows $scopeRows

$summary = New-Object System.Collections.Generic.List[string]
$summary.Add("# CROWN Full Completion Truth Gate")
$summary.Add("")
$summary.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$summary.Add("- Branch: $((git branch --show-current).Trim())")
$summary.Add("- Head: $((git rev-parse HEAD).Trim())")
$summary.Add("- Required scope rows: $($scopeRows.Count)")
$summary.Add("- Dashboard template preview/unproven-data blockers: $($templateBlockers.Count)")
$summary.Add("- Backend sample-payload signals: $($backendRows.Count)")
$summary.Add("")

if ($templateBlockers.Count -gt 0 -or $backendRows.Count -gt 0) {
    $summary.Add("REVIEW REQUIRED")
    $summary.Add("")
    $summary.Add("Completion cannot be certified while ready dashboards are template/sample/fallback backed or while backend dashboard payloads serve sample contracts without live-service proof.")
} else {
    $summary.Add("PASS")
}

Write-Utf8 -Path (Join-Path $outDir "00_SUMMARY.md") -Lines $summary

$status = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    repo_root = $repoRoot
    branch = (git branch --show-current).Trim()
    head = (git rev-parse HEAD).Trim()
    required_scope_count = $scopeRows.Count
    dashboard_template_blocker_count = $templateBlockers.Count
    backend_sample_payload_signal_count = $backendRows.Count
    pass = ($AllowPreviewData -or ($templateBlockers.Count -eq 0 -and $backendRows.Count -eq 0))
    scope = $scopeRows
    dashboard_template_blockers = $templateBlockers
    backend_sample_payload_signals = $backendRows
}

Write-JsonFile -Path (Join-Path $outDir "99_STATUS.json") -Object $status
Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host "DONE"
Write-Host "SUMMARY: $(Join-Path $outDir '00_SUMMARY.md')"
Write-Host "LATEST:  $(Join-Path $latestDir '00_SUMMARY.md')"
Write-Host "STATUS:  $(Join-Path $outDir '99_STATUS.json')"

if (-not $status.pass) {
    exit 1
}
