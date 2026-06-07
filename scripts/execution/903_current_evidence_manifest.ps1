param([switch]$FailOnStaleArtifacts)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function New-Dir([string]$Path) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Branch-Name {
    $name = (git branch --show-current 2>$null)
    if ($name) { return $name.Trim() }
    $ref = (git rev-parse --abbrev-ref HEAD 2>$null)
    if ($ref -and $ref.Trim() -ne "HEAD") { return $ref.Trim() }
    return "detached-head"
}

function Read-Head-From-Markdown([string]$Path) {
    if (-not (Test-Path $Path)) { return "" }
    $line = Get-Content $Path | Where-Object { $_ -match "^- Head:" } | Select-Object -First 1
    if (-not $line) { return "" }
    return ($line -replace "^- Head:\s*", "").Trim()
}

function Read-Head-From-Json([string]$Path) {
    if (-not (Test-Path $Path)) { return "" }
    try {
        $json = Get-Content $Path -Raw | ConvertFrom-Json
        if ($null -eq $json.head) { return "" }
        return [string]$json.head
    } catch {
        return ""
    }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$head = (git rev-parse HEAD).Trim()
$branch = Branch-Name
$originMain = ""
try { $originMain = (git rev-parse origin/main 2>$null).Trim() } catch { $originMain = "" }
$aheadBehind = "unknown"
if ($originMain) {
    try { $aheadBehind = (git rev-list --left-right --count origin/main...HEAD 2>$null).Trim() } catch { $aheadBehind = "unknown" }
}

$dirty = @((git status --short) | Where-Object { $_ })

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot ".crown-audit\current-evidence-manifest\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\current-evidence-manifest\latest"
New-Dir $outDir
New-Dir $latestDir

$rows = New-Object System.Collections.Generic.List[object]

$rows.Add([pscustomobject]@{ name="repo-head"; path="HEAD"; tier="CURRENT_REPO"; status="CURRENT"; current_head=$head; artifact_head=$head; notes="branch=$branch origin_main=$originMain ahead_behind=$aheadBehind" }) | Out-Null
$rows.Add([pscustomobject]@{ name="worktree"; path="git status --short"; tier="CURRENT_LOCAL"; status=$(if ($dirty.Count -eq 0) { "CLEAN" } else { "DIRTY" }); current_head=$head; artifact_head=""; notes="status_lines=$($dirty.Count)" }) | Out-Null

$artifactSpecs = @(
    @{ name="901-summary"; path=".crown-audit\executive-sandbox-gate\latest\00_SUMMARY.md"; kind="md" },
    @{ name="901-status"; path=".crown-audit\executive-sandbox-gate\latest\99_STATUS.json"; kind="json" },
    @{ name="902-summary"; path=".crown-audit\certification-reconciliation\latest\00_SUMMARY.md"; kind="md" },
    @{ name="902-status"; path=".crown-audit\certification-reconciliation\latest\99_STATUS.json"; kind="json" }
)

foreach ($spec in $artifactSpecs) {
    $fullPath = Join-Path $repoRoot $spec.path
    if (-not (Test-Path $fullPath)) {
        $rows.Add([pscustomobject]@{ name=$spec.name; path=$spec.path; tier="UNKNOWN"; status="MISSING"; current_head=$head; artifact_head=""; notes="not present" }) | Out-Null
        continue
    }
    $artifactHead = if ($spec.kind -eq "json") { Read-Head-From-Json $fullPath } else { Read-Head-From-Markdown $fullPath }
    $status = if ($artifactHead -eq $head) { "CURRENT" } elseif ($artifactHead) { "STALE" } else { "UNKNOWN" }
    $tier = if ($status -eq "CURRENT") { "CURRENT_LOCAL_EVIDENCE" } elseif ($status -eq "STALE") { "STALE_LOCAL_EVIDENCE" } else { "UNKNOWN" }
    $rows.Add([pscustomobject]@{ name=$spec.name; path=$spec.path; tier=$tier; status=$status; current_head=$head; artifact_head=$artifactHead; notes="artifact head classification" }) | Out-Null
}

$historical = @(
    "docs\release\MODULE_CERTIFICATION_MATRIX_20260530.md",
    "docs\release\DASHBOARD_CERTIFICATION_MATRIX_20260530.md",
    "docs\release\FULL_COMPLETION_EXECUTION_BOARD_20260530.md"
)
foreach ($path in $historical) {
    $rows.Add([pscustomobject]@{ name=(Split-Path $path -Leaf); path=$path; tier="HISTORICAL_RECONCILIATION_INPUT"; status=$(if (Test-Path (Join-Path $repoRoot $path)) { "PRESENT" } else { "MISSING" }); current_head=$head; artifact_head=""; notes="not current proof by itself" }) | Out-Null
}

$csvPath = Join-Path $outDir "10_evidence_manifest.csv"
$summaryPath = Join-Path $outDir "00_SUMMARY.md"
$statusPath = Join-Path $outDir "99_STATUS.json"
$rows | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8

$stale = @($rows | Where-Object { $_.status -eq "STALE" }).Count
$missing = @($rows | Where-Object { $_.status -eq "MISSING" -or $_.status -eq "UNKNOWN" }).Count
$dirtyCount = @($rows | Where-Object { $_.status -eq "DIRTY" }).Count

@(
    "# CROWN Current Evidence Manifest",
    "",
    "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "- Branch: $branch",
    "- Head: $head",
    "- Origin main: $originMain",
    "- Ahead/behind vs origin/main: $aheadBehind",
    "- Dirty rows: $dirtyCount",
    "- Stale rows: $stale",
    "- Missing/unknown rows: $missing",
    "",
    "Rule: historical matrices are reconciliation inputs only. They are not current completion proof unless a current-head artifact proves them."
) | Set-Content -Path $summaryPath -Encoding UTF8

$status = [ordered]@{ generated_at=(Get-Date).ToString("s"); branch=$branch; head=$head; origin_main=$originMain; ahead_behind=$aheadBehind; dirty_rows=$dirtyCount; stale_rows=$stale; missing_or_unknown_rows=$missing; passed=($dirtyCount -eq 0 -and $stale -eq 0 -and $missing -eq 0); output_dir=$outDir }
($status | ConvertTo-Json -Depth 5) | Set-Content -Path $statusPath -Encoding UTF8
Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host "Current evidence manifest complete."
Write-Host "Summary: $summaryPath"
Write-Host "CSV:     $csvPath"
Write-Host "Status:  $statusPath"

if ($FailOnStaleArtifacts -and ($stale -gt 0 -or $missing -gt 0)) { exit 1 }
