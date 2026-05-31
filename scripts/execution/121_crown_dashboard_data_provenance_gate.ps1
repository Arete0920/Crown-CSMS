param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function New-Dir { param([string]$Path) New-Item -ItemType Directory -Force -Path $Path | Out-Null }
function Write-Utf8 { param([string]$Path, [string[]]$Lines) $Lines | Set-Content -Path $Path -Encoding UTF8 }
function Write-JsonFile { param([string]$Path, $Object) ($Object | ConvertTo-Json -Depth 12) | Set-Content -Path $Path -Encoding UTF8 }
function Get-RelativePathSafe { param([string]$Root, [string]$Path) return $Path.Replace($Root + [System.IO.Path]::DirectorySeparatorChar, "").Replace("\", "/") }

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) { throw "Not inside a git repository." }
Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot ".crown-audit\dashboard-provenance\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\dashboard-provenance\latest"
New-Dir $outDir
New-Dir $latestDir

$templateDir = Join-Path $repoRoot "frontend\dashboards\src\config\dashboardTemplates"
$rows = @()
$violations = @()

if (Test-Path $templateDir) {
    $files = Get-ChildItem $templateDir -File -Filter "*Dashboard.js" | Sort-Object Name
    foreach ($file in $files) {
        $content = Get-Content $file.FullName -Raw
        $path = Get-RelativePathSafe -Root $repoRoot -Path $file.FullName
        $usesBaseNote = $content -match "BASE_NOTE"
        $usesBaseTrend = $content -match "BASE_TREND"
        $usesBaseStatus = $content -match "BASE_STATUS"
        $usesBaseActivity = $content -match "BASE_ACTIVITY"
        $hasDataState = $content -match "dataState\s*:"
        $hasLiveState = $content -match "dataState\s*:\s*['\"]live['\"]"
        $hasSource = $content -match "source(Service|Endpoint|Type|Label)\s*:"
        $hasTenantSignal = $content -match "tenantFiltered\s*:\s*true"
        $hasRoleSignal = $content -match "roleScoped\s*:\s*true"
        $status = if ($hasLiveState -and $hasSource -and $hasTenantSignal -and $hasRoleSignal -and -not ($usesBaseNote -or $usesBaseTrend -or $usesBaseStatus -or $usesBaseActivity)) { "PASS" } else { "BLOCKED_INVALID_OR_MISSING_PROVENANCE" }
        $row = [pscustomobject]@{
            Path = $path
            UsesBaseNote = $usesBaseNote
            UsesBaseTrend = $usesBaseTrend
            UsesBaseStatus = $usesBaseStatus
            UsesBaseActivity = $usesBaseActivity
            HasDataState = $hasDataState
            HasLiveState = $hasLiveState
            HasSourceSignal = $hasSource
            HasTenantSignal = $hasTenantSignal
            HasRoleSignal = $hasRoleSignal
            CompletionStatus = $status
        }
        $rows += $row
        if ($status -ne "PASS") { $violations += $row }
    }
}

$fallbackViolations = @($rows | Where-Object { $_.UsesBaseNote -or $_.UsesBaseTrend -or $_.UsesBaseStatus -or $_.UsesBaseActivity })
$rows | Export-Csv -Path (Join-Path $outDir "10_widget_provenance.csv") -NoTypeInformation -Encoding UTF8
$violations | Export-Csv -Path (Join-Path $outDir "20_missing_or_invalid_provenance.csv") -NoTypeInformation -Encoding UTF8
$fallbackViolations | Export-Csv -Path (Join-Path $outDir "30_sample_fallback_violations.csv") -NoTypeInformation -Encoding UTF8

$pass = ($violations.Count -eq 0 -and $rows.Count -gt 0)
$summary = @(
    "# CROWN Dashboard Data Provenance Gate",
    "",
    "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "- Branch: $((git branch --show-current).Trim())",
    "- Head: $((git rev-parse HEAD).Trim())",
    "- Dashboard template rows: $($rows.Count)",
    "- Invalid/missing provenance rows: $($violations.Count)",
    "- Sample/fallback/base-data rows: $($fallbackViolations.Count)",
    "",
    $(if ($pass) { "PASS" } else { "REVIEW REQUIRED" }),
    "",
    "Dashboard certification requires live, sourced, tenant-filtered, role-scoped provenance for every ready dashboard widget."
)
Write-Utf8 -Path (Join-Path $outDir "00_SUMMARY.md") -Lines $summary

$status = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    branch = (git branch --show-current).Trim()
    head = (git rev-parse HEAD).Trim()
    pass = $pass
    dashboard_template_count = $rows.Count
    invalid_or_missing_provenance_count = $violations.Count
    sample_fallback_violation_count = $fallbackViolations.Count
    rows = $rows
}
Write-JsonFile -Path (Join-Path $outDir "99_STATUS.json") -Object $status
Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host "DONE"
Write-Host "SUMMARY: $(Join-Path $outDir '00_SUMMARY.md')"
Write-Host "STATUS:  $(Join-Path $outDir '99_STATUS.json')"
if (-not $pass) { exit 1 }
