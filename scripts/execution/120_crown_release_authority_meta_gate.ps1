param(
    [switch]$AuthorityOnly
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
            if ($normalized -in @("PASS","GREEN","GO")) {
                $passValue = $true
                $reason = "passing status: $normalized"
            } else {
                $reason = "non-passing status: $normalized"
            }
        }
        return [pscustomobject]@{ Path = $Path; Exists = $true; Pass = $passValue; Reason = $reason }
    } catch {
        return [pscustomobject]@{ Path = $Path; Exists = $true; Pass = $false; Reason = "invalid json: $($_.Exception.Message)" }
    }
}

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) { throw "Not inside a git repository." }
Set-Location $repoRoot

$branchName = (git branch --show-current 2>$null)
if ([string]::IsNullOrWhiteSpace($branchName)) { $branchName = $env:GITHUB_HEAD_REF }
if ([string]::IsNullOrWhiteSpace($branchName)) { $branchName = $env:GITHUB_REF_NAME }
if ([string]::IsNullOrWhiteSpace($branchName)) { $branchName = "detached-head" } else { $branchName = $branchName.Trim() }

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot ".crown-audit\release-authority\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\release-authority\latest"
New-Dir $outDir
New-Dir $latestDir

# Current authority is defined only by canonical/current documents.
# Dated predecessor-era release campaigns remain historical provenance and must not control current release disposition.
$currentAuthorityArtifacts = @(
    "docs/CURRENT_RELEASE_STATUS.md",
    "docs/canonical/CANONICAL_DOCUMENT_INDEX.md",
    "docs/canonical/DILIGENCE_EVIDENCE_INDEX.md",
    "docs/release/CROWN_PRODUCTION_READY_ENGINEERING_CERTIFICATION_20260818.md",
    "docs/operations/README.md",
    "docs/ownership/OWNER_HANDOFF.md",
    "docs/ownership/BUYER_OPERATIONAL_TRANSFER_REGISTER.md"
)

$requiredScripts = @(
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

$authorityRows = @()
foreach ($relative in @($currentAuthorityArtifacts + $requiredScripts)) {
    $path = Join-Path $repoRoot $relative
    $authorityRows += [pscustomobject]@{
        Path = $relative
        Exists = (Test-Path $path)
    }
}

# Guard against reintroducing obsolete May-era files as executable authority inputs.
$retiredAuthorityTokens = @(
    "CROWN_FULL_COMPLETION_BLOCKERS_20260529",
    "CROWN_CORE_SIS_SUPERIORITY_GATE_20260529",
    "CROWN_CORE_SIS_COMPETITOR_MATRIX_20260529",
    "CROWN_RELEASE_AUTHORITY_INDEX_20260529"
)
$selfText = Get-Content (Join-Path $repoRoot "scripts/execution/120_crown_release_authority_meta_gate.ps1") -Raw
$workflowText = Get-Content (Join-Path $repoRoot ".github/workflows/crown-release-authority-gates.yml") -Raw
$retiredRefs = @()
foreach ($token in $retiredAuthorityTokens) {
    foreach ($source in @(
        [pscustomobject]@{ Name = "meta-gate"; Text = $selfText },
        [pscustomobject]@{ Name = "workflow"; Text = $workflowText }
    )) {
        # The token list itself is allowed in the guard. Any additional occurrence is a regression.
        $count = ([regex]::Matches($source.Text, [regex]::Escape($token))).Count
        $allowed = if ($source.Name -eq "meta-gate") { 1 } else { 0 }
        if ($count -gt $allowed) {
            $retiredRefs += [pscustomobject]@{ Source = $source.Name; Token = $token; Count = $count }
        }
    }
}

$missingAuthority = @($authorityRows | Where-Object { -not $_.Exists })
$authorityPass = ($missingAuthority.Count -eq 0 -and $retiredRefs.Count -eq 0)

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
if (-not $AuthorityOnly) {
    foreach ($relative in $statusJsons) {
        $jsonRows += Test-JsonPass -Path (Join-Path $repoRoot $relative)
    }
}

$failingJsonCount = @($jsonRows | Where-Object { -not $_.Pass }).Count
$pass = if ($AuthorityOnly) { $authorityPass } else { ($authorityPass -and $failingJsonCount -eq 0) }

$authorityRows | Export-Csv -Path (Join-Path $outDir "10_current_authority_inputs.csv") -NoTypeInformation -Encoding UTF8
$retiredRefs | Export-Csv -Path (Join-Path $outDir "15_retired_authority_regressions.csv") -NoTypeInformation -Encoding UTF8
if (-not $AuthorityOnly) {
    $jsonRows | Export-Csv -Path (Join-Path $outDir "20_required_status_jsons.csv") -NoTypeInformation -Encoding UTF8
}

$summary = New-Object System.Collections.Generic.List[string]
$summary.Add("# CROWN Release Authority Meta Gate")
$summary.Add("")
$summary.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$summary.Add("- Branch: $branchName")
$summary.Add("- Head: $((git rev-parse HEAD).Trim())")
$summary.Add("- Mode: $(if ($AuthorityOnly) { 'repository-authority' } else { 'operational-certification' })")
$summary.Add("- Current authority inputs: $($currentAuthorityArtifacts.Count)")
$summary.Add("- Missing authority/script inputs: $($missingAuthority.Count)")
$summary.Add("- Retired authority regressions: $($retiredRefs.Count)")
if (-not $AuthorityOnly) {
    $summary.Add("- Failing/missing operational status JSON count: $failingJsonCount")
}
$summary.Add("")
$summary.Add($(if ($pass) { "PASS" } else { "REVIEW REQUIRED" }))
if (-not $AuthorityOnly -and -not $pass) {
    $summary.Add("")
    $summary.Add("Operational production certification remains fail-closed until current environment-specific runtime evidence passes all required operational gates.")
}
Write-Utf8 -Path (Join-Path $outDir "00_SUMMARY.md") -Lines $summary

$status = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    branch = $branchName
    head = (git rev-parse HEAD).Trim()
    mode = if ($AuthorityOnly) { "repository-authority" } else { "operational-certification" }
    authority_pass = $authorityPass
    pass = $pass
    missing_authority_or_script_count = $missingAuthority.Count
    retired_authority_regression_count = $retiredRefs.Count
    failing_operational_status_json_count = $failingJsonCount
    current_authority_inputs = $authorityRows
    retired_authority_regressions = $retiredRefs
    required_status_jsons = $jsonRows
}
Write-JsonFile -Path (Join-Path $outDir "99_STATUS.json") -Object $status
Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host "DONE"
Write-Host "SUMMARY: $(Join-Path $outDir '00_SUMMARY.md')"
Write-Host "STATUS:  $(Join-Path $outDir '99_STATUS.json')"

if (-not $pass) { exit 1 }
