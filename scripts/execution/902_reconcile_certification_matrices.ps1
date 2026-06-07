param(
    [switch]$FailOnMappedDashboardVisible,
    [switch]$FailOnNotProvenModuleEvidenceMissing
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function New-Dir {
    param([string]$Path)
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Get-BranchNameSafe {
    $name = (git branch --show-current 2>$null)
    if (-not [string]::IsNullOrWhiteSpace($name)) { return $name.Trim() }
    $ref = (git rev-parse --abbrev-ref HEAD 2>$null)
    if (-not [string]::IsNullOrWhiteSpace($ref) -and $ref.Trim() -ne "HEAD") { return $ref.Trim() }
    if (-not [string]::IsNullOrWhiteSpace($env:GITHUB_REF_NAME)) { return $env:GITHUB_REF_NAME.Trim() }
    return "detached-head"
}

function Convert-SlugToCamel {
    param([string]$Slug)
    $parts = $Slug -split "-"
    if ($parts.Count -eq 0) { return $Slug }
    $first = $parts[0]
    if ($parts.Count -eq 1) { return $first }
    $rest = $parts[1..($parts.Count - 1)] | ForEach-Object {
        if ([string]::IsNullOrWhiteSpace($_)) { "" } else { $_.Substring(0,1).ToUpperInvariant() + $_.Substring(1) }
    }
    return ($first + ($rest -join ""))
}

function Parse-MarkdownMatrix {
    param([string]$Path, [string]$Kind)
    $rows = @()
    if (-not (Test-Path $Path)) { return $rows }
    $lines = Get-Content $Path
    foreach ($line in $lines) {
        if ($line -notmatch "^\|") { continue }
        if ($line -match "---") { continue }
        if ($line -match "certification_status") { continue }
        $cells = $line.Trim("|").Split("|") | ForEach-Object { $_.Trim() }
        if ($Kind -eq "dashboard" -and $cells.Count -ge 4) {
            $rows += [pscustomobject]@{
                artifact_type = "dashboard"
                key_or_id = $cells[0]
                old_status = $cells[1]
                evidence = $cells[2]
                owner = $cells[3]
            }
        }
        if ($Kind -eq "module" -and $cells.Count -ge 4) {
            $rows += [pscustomobject]@{
                artifact_type = "module"
                key_or_id = $cells[0]
                old_status = $cells[1]
                evidence = $cells[2]
                owner = $cells[3]
            }
        }
    }
    return $rows
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot ".crown-audit\certification-reconciliation\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\certification-reconciliation\latest"
New-Dir $outDir
New-Dir $latestDir

$dashboardMatrixPath = Join-Path $repoRoot "docs\release\DASHBOARD_CERTIFICATION_MATRIX_20260530.md"
$moduleMatrixPath = Join-Path $repoRoot "docs\release\MODULE_CERTIFICATION_MATRIX_20260530.md"
$dashboardRegistryPath = Join-Path $repoRoot "frontend\dashboards\src\config\dashboardRegistry.js"
$dashboardNavPath = Join-Path $repoRoot "frontend\dashboards\src\components\navigation\dashboardNavConfig.js"

$dashboardRows = Parse-MarkdownMatrix -Path $dashboardMatrixPath -Kind "dashboard"
$moduleRows = Parse-MarkdownMatrix -Path $moduleMatrixPath -Kind "module"
$registryText = if (Test-Path $dashboardRegistryPath) { Get-Content $dashboardRegistryPath -Raw } else { "" }
$navText = if (Test-Path $dashboardNavPath) { Get-Content $dashboardNavPath -Raw } else { "" }

$reconciliation = @()

foreach ($row in $dashboardRows) {
    $slug = $row.key_or_id
    $camel = Convert-SlugToCamel -Slug $slug
    $inRegistry = $registryText -match [regex]::Escape($slug) -or $registryText -match [regex]::Escape($camel)
    $navMentions = $navText -match [regex]::Escape($slug) -or $navText -match [regex]::Escape($camel)
    $sandboxFiltered = $navText -match "VITE_SANDBOX_READY_ONLY" -and $navText -match "isProductionReady"
    $result = "REVIEW"
    $action = "Verify current evidence before sandbox exposure."
    if (-not $inRegistry) {
        $result = "MISSING_FROM_CURRENT_REGISTRY"
        $action = "Either add dashboard registry entry or remove stale matrix row."
    } elseif ($row.old_status -eq "MAPPED" -and $navMentions -and -not $sandboxFiltered) {
        $result = "BLOCKED_MAPPED_DASHBOARD_NAV_VISIBLE"
        $action = "Hide from sandbox navigation or promote with current evidence."
    } elseif ($row.old_status -eq "MAPPED") {
        $result = "MAPPED_NOT_CERTIFIED"
        $action = "Do not treat as production-certified without live/runtime evidence."
    }

    $evidenceExists = $false
    if ($row.evidence -and $row.evidence -ne "none-captured") {
        $evidenceExists = Test-Path (Join-Path $repoRoot $row.evidence)
    }

    $reconciliation += [pscustomobject]@{
        artifact_type = "dashboard"
        key_or_id = $slug
        old_status = $row.old_status
        current_registry_signal = $inRegistry
        current_nav_signal = $navMentions
        sandbox_ready_filter_signal = $sandboxFiltered
        evidence = $row.evidence
        evidence_exists = $evidenceExists
        current_result = $result
        action_required = $action
    }
}

foreach ($row in $moduleRows) {
    $evidencePath = if ($row.evidence -and $row.evidence -ne "none-captured") { Join-Path $repoRoot $row.evidence } else { "" }
    $evidenceExists = if ($evidencePath) { Test-Path $evidencePath } else { $false }
    $result = if ($row.old_status -eq "PROVEN" -and $evidenceExists) { "LEGACY_PROOF_FILE_PRESENT" } elseif ($row.old_status -eq "PROVEN") { "PROVEN_BUT_EVIDENCE_FILE_MISSING" } elseif ($row.old_status -eq "NOT_PROVEN") { "NOT_PROVEN_FROM_LEGACY_MATRIX" } else { "REVIEW" }
    $action = if ($row.old_status -eq "NOT_PROVEN") { "Keep out of sandbox unless current proof now exists." } elseif (-not $evidenceExists) { "Restore/replace evidence file or downgrade certification." } else { "Verify test passes on current head." }
    $reconciliation += [pscustomobject]@{
        artifact_type = "module"
        key_or_id = $row.key_or_id
        old_status = $row.old_status
        current_registry_signal = ""
        current_nav_signal = ""
        sandbox_ready_filter_signal = ""
        evidence = $row.evidence
        evidence_exists = $evidenceExists
        current_result = $result
        action_required = $action
    }
}

$csvPath = Join-Path $outDir "30_certification_reconciliation.csv"
$summaryPath = Join-Path $outDir "00_SUMMARY.md"
$statusPath = Join-Path $outDir "99_STATUS.json"
$reconciliation | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8

$blockers = @($reconciliation | Where-Object { $_.current_result -match "BLOCKED|MISSING|NOT_PROVEN|EVIDENCE_FILE_MISSING" })
$dashboardCount = @($reconciliation | Where-Object { $_.artifact_type -eq "dashboard" }).Count
$moduleCount = @($reconciliation | Where-Object { $_.artifact_type -eq "module" }).Count

$summary = @(
    "# CROWN Certification Matrix Reconciliation",
    "",
    "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "- Branch: $(Get-BranchNameSafe)",
    "- Head: $((git rev-parse HEAD).Trim())",
    "- Dashboard rows reconciled: $dashboardCount",
    "- Module rows reconciled: $moduleCount",
    "- Blocker/review rows: $($blockers.Count)",
    "",
    "This gate reconciles legacy module/dashboard certification matrices against the current repository so historical certification work is not missed during sandbox/release review."
)
$summary | Set-Content -Path $summaryPath -Encoding UTF8

$status = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    branch = Get-BranchNameSafe
    head = (git rev-parse HEAD).Trim()
    dashboard_rows = $dashboardCount
    module_rows = $moduleCount
    blocker_rows = $blockers.Count
    passed = ($blockers.Count -eq 0)
    output_dir = $outDir
}
($status | ConvertTo-Json -Depth 8) | Set-Content -Path $statusPath -Encoding UTF8
Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host "Certification reconciliation complete."
Write-Host "Summary: $summaryPath"
Write-Host "CSV:     $csvPath"
Write-Host "Status:  $statusPath"

if ($FailOnMappedDashboardVisible -and @($reconciliation | Where-Object { $_.current_result -eq "BLOCKED_MAPPED_DASHBOARD_NAV_VISIBLE" }).Count -gt 0) { exit 1 }
if ($FailOnNotProvenModuleEvidenceMissing -and @($reconciliation | Where-Object { $_.current_result -match "NOT_PROVEN|EVIDENCE_FILE_MISSING" }).Count -gt 0) { exit 1 }
