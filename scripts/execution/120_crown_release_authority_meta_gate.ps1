param(
    [switch]$AllowDraftOnly
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

function Write-JsonFile {
    param([string]$Path, $Object)
    ($Object | ConvertTo-Json -Depth 12) | Set-Content -Path $Path -Encoding UTF8
}

function Test-JsonPass {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        return [pscustomobject]@{ Path = $Path; Exists = $false; Pass = $false; Reason = "missing" }
    }
    try {
        $json = Get-Content $Path -Raw | ConvertFrom-Json
        $passValue = $false
        $reason = "pass not true"

        if ($null -ne $json.pass) {
            $passValue = [bool]$json.pass
            $reason = if ($passValue) { "pass true" } else { "pass false" }
        }
        elseif ($null -ne $json.status) {
            $normalized = ([string]$json.status).Trim().ToUpperInvariant()
            if ($normalized -eq "PASS" -or $normalized -eq "GREEN" -or $normalized -eq "GO") {
                $passValue = $true
                $reason = "passing status: $normalized"
            } else {
                $passValue = $false
                $reason = "non-passing status: $normalized"
            }
        }

        return [pscustomobject]@{ Path = $Path; Exists = $true; Pass = $passValue; Reason = $reason }
    } catch {
        return [pscustomobject]@{ Path = $Path; Exists = $true; Pass = $false; Reason = "invalid json: $($_.Exception.Message)" }
    }
}

function Find-BlockingMarkers {
    param([string]$Path)
    $markers = @(
        "NO-GO",
        "NOT_GREEN",
        "BLOCKED",
        "PROOF_REQUIRED",
        "UNKNOWN",
        "IN_PROGRESS",
        "NOT_CERTIFIED",
        "TBD",
        "UNVERIFIED",
        "NOT SIGNED",
        "TEMPLATE ONLY",
        "REQUIRES_CONFIRMATION",
        "REQUIRES LEGAL REVIEW",
        "NOT LEGAL-SIGNED",
        "NOT IMPLEMENTED GREEN",
        "NOT APPROVED"
    )

    if (-not (Test-Path $Path)) {
        return @([pscustomobject]@{ Path = $Path; LineNumber = 0; Marker = "MISSING_FILE"; Text = "Required authority artifact is missing." })
    }

    $rows = @()
    $lines = Get-Content $Path
    for ($i = 0; $i -lt $lines.Count; $i++) {
        foreach ($marker in $markers) {
            if ($lines[$i] -match [regex]::Escape($marker)) {
                $rows += [pscustomobject]@{
                    Path = $Path
                    LineNumber = $i + 1
                    Marker = $marker
                    Text = $lines[$i].Trim()
                }
            }
        }
    }
    return $rows
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) { throw "Not inside a git repository." }
Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot ".crown-audit\release-authority\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\release-authority\latest"
New-Dir $outDir
New-Dir $latestDir

$requiredArtifacts = @(
    "README.md",
    "SECURITY.md",
    "docs/CURRENT_RELEASE_STATUS.md",
    "docs/KNOWN_LIMITATIONS.md",
    "docs/canonical/CANONICAL_DOCUMENT_INDEX.md",
    "docs/canonical/DILIGENCE_EVIDENCE_INDEX.md",
    "docs/architecture/ARCHITECTURE_MAP.md",
    "docs/engineering/REPOSITORY_WORKFLOW.md",
    "docs/compliance/PRIVACY_COMPLIANCE_EVIDENCE_STATUS.md",
    "docs/compliance/FERPA_POSITION.md",
    "docs/compliance/COPPA_POSITION.md",
    "docs/compliance/DPA_TEMPLATE.md",
    "docs/compliance/SUBPROCESSOR_REGISTER.md",
    "docs/compliance/RETENTION_POLICY.md",
    "docs/operations/README.md"
)

$scriptArtifacts = @(
    "scripts/execution/118_run_crown_release_authority_stack.ps1",
    "scripts/execution/120_crown_release_authority_meta_gate.ps1",
    "scripts/execution/121_crown_dashboard_data_provenance_gate.ps1",
    "scripts/execution/122_crown_domain_model_certification_gate.ps1",
    "scripts/execution/130_crown_data_migration_reconciliation_gate.ps1",
    "scripts/execution/140_crown_financial_controls_gate.ps1",
    "scripts/execution/150_crown_performance_load_gate.ps1",
    "scripts/execution/160_crown_observability_incident_gate.ps1",
    ".github/workflows/crown-release-authority-gates.yml"
)

$markerRows = @()
foreach ($relative in $requiredArtifacts) {
    $markerRows += Find-BlockingMarkers -Path (Join-Path $repoRoot $relative)
}
foreach ($relative in $scriptArtifacts) {
    $scriptPath = Join-Path $repoRoot $relative
    if (-not (Test-Path $scriptPath)) {
        $markerRows += [pscustomobject]@{ Path = $scriptPath; LineNumber = 0; Marker = "MISSING_FILE"; Text = "Required authority script is missing." }
    }
}

$statusJsons = @(
    ".crown-audit/full-completion-truth/latest/99_STATUS.json",
    ".crown-audit/dashboard-provenance/latest/99_STATUS.json",
    ".crown-audit/domain-model/latest/99_STATUS.json",
    ".crown-audit/dashboard-completion/latest/99_STATUS.json",
    ".crown-audit/data-migration/latest/99_STATUS.json",
    ".crown-audit/financial-controls/latest/99_STATUS.json",
    ".crown-audit/performance/latest/99_STATUS.json",
    ".crown-audit/observability/latest/99_STATUS.json"
)

$jsonRows = @()
foreach ($relative in $statusJsons) {
    $jsonRows += Test-JsonPass -Path (Join-Path $repoRoot $relative)
}

$blockingMarkerCount = @($markerRows).Count
$failingJsonCount = @($jsonRows | Where-Object { -not $_.Pass }).Count
$pass = ($blockingMarkerCount -eq 0 -and $failingJsonCount -eq 0)
if ($AllowDraftOnly) { $pass = $false }

$markerRows | Export-Csv -Path (Join-Path $outDir "10_blocking_markers.csv") -NoTypeInformation -Encoding UTF8
$jsonRows | Export-Csv -Path (Join-Path $outDir "20_required_status_jsons.csv") -NoTypeInformation -Encoding UTF8

$summary = New-Object System.Collections.Generic.List[string]
$summary.Add("# CROWN Release Authority Meta Gate")
$summary.Add("")
$summary.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$summary.Add("- Branch: $((git branch --show-current).Trim())")
$summary.Add("- Head: $((git rev-parse HEAD).Trim())")
$summary.Add("- Required artifacts: $($requiredArtifacts.Count)")
$summary.Add("- Required scripts/workflow files: $($scriptArtifacts.Count)")
$summary.Add("- Blocking marker count: $blockingMarkerCount")
$summary.Add("- Failing/missing status JSON count: $failingJsonCount")
$summary.Add("")
if ($pass) {
    $summary.Add("PASS")
} else {
    $summary.Add("REVIEW REQUIRED")
    $summary.Add("")
    $summary.Add("Release, pilot, and GA claims are blocked until all required artifacts are green and all required runtime evidence status files pass.")
}
Write-Utf8 -Path (Join-Path $outDir "00_SUMMARY.md") -Lines $summary

$status = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    branch = (git branch --show-current).Trim()
    head = (git rev-parse HEAD).Trim()
    required_artifact_count = $requiredArtifacts.Count
    required_script_artifact_count = $scriptArtifacts.Count
    blocking_marker_count = $blockingMarkerCount
    failing_required_status_json_count = $failingJsonCount
    pass = $pass
    blocking_markers = $markerRows
    required_status_jsons = $jsonRows
}
Write-JsonFile -Path (Join-Path $outDir "99_STATUS.json") -Object $status
Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host "DONE"
Write-Host "SUMMARY: $(Join-Path $outDir '00_SUMMARY.md')"
Write-Host "STATUS:  $(Join-Path $outDir '99_STATUS.json')"

if (-not $pass) { exit 1 }
