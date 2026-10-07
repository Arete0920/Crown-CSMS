param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function New-Dir { param([string]$Path) New-Item -ItemType Directory -Force -Path $Path | Out-Null }
function Write-Utf8 { param([string]$Path, [string[]]$Lines) $Lines | Set-Content -Path $Path -Encoding UTF8 }
function Write-JsonFile { param([string]$Path, $Object) ($Object | ConvertTo-Json -Depth 12) | Set-Content -Path $Path -Encoding UTF8 }

$repoRoot = (git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) { throw "Not inside a git repository." }
Set-Location $repoRoot

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $repoRoot ".crown-audit\security-compliance\$timestamp"
$latestDir = Join-Path $repoRoot ".crown-audit\security-compliance\latest"
New-Dir $outDir
New-Dir $latestDir

$requiredWorkflows = @(
    ".github/workflows/secret-scan.yml",
    ".github/workflows/codeql.yml",
    ".github/workflows/dependency-audit.yml",
    ".github/workflows/dependency-review.yml",
    ".github/workflows/sbom-generation.yml",
    ".github/workflows/license-audit.yml",
    ".github/workflows/repository-policy.yml",
    ".github/workflows/workflow-permissions-audit.yml"
)

$requiredArtifacts = @(
    "docs/security/CROWN_SECURITY_COMPLIANCE_RESILIENCE_TEST_PLAN_20260529.md",
    "docs/compliance/CROWN_COMPLIANCE_CUSTOMER_READINESS_PACKET_20260529.md",
    "docs/compliance/CROWN_DPA_TEMPLATE_20260529.md",
    "docs/compliance/CROWN_SUBPROCESSOR_REGISTER_20260529.csv",
    "docs/operations/CROWN_OBSERVABILITY_AND_INCIDENT_READINESS_20260529.md",
    "docs/release/CROWN_RELEASE_AUTHORITY_INDEX_20260529.md",
    "docs/release/CROWN_FINAL_RELEASE_AUTHORITY_SIGNOFF_TEMPLATE_20260529.md"
)

$scanRows = @()
foreach ($workflow in $requiredWorkflows) {
    $scanRows += [pscustomobject]@{
        Type = "workflow"
        Path = $workflow
        Exists = Test-Path (Join-Path $repoRoot $workflow)
        Status = if (Test-Path (Join-Path $repoRoot $workflow)) { "PRESENT" } else { "MISSING" }
    }
}

$artifactRows = @()
foreach ($artifact in $requiredArtifacts) {
    $artifactRows += [pscustomobject]@{
        Type = "artifact"
        Path = $artifact
        Exists = Test-Path (Join-Path $repoRoot $artifact)
        Status = if (Test-Path (Join-Path $repoRoot $artifact)) { "PRESENT" } else { "MISSING" }
    }
}

$findings = @()
$missingWorkflowRows = @($scanRows | Where-Object { -not $_.Exists })
$missingArtifactRows = @($artifactRows | Where-Object { -not $_.Exists })
foreach ($row in $missingWorkflowRows) {
    $findings += [pscustomobject]@{ Severity = "BLOCKER"; Category = "workflow_missing"; Path = $row.Path; Detail = "Required security/compliance workflow is missing." }
}
foreach ($row in $missingArtifactRows) {
    $findings += [pscustomobject]@{ Severity = "BLOCKER"; Category = "artifact_missing"; Path = $row.Path; Detail = "Required security/compliance artifact is missing." }
}

# Lightweight repository claim marker check for unsupported release language.
$claimPatterns = @(
    "CROWN is GA",
    "CROWN is pilot-approved",
    "unrestricted-production ready", # forbidden claim
    "superior to all 25",
    "all modules.*complete"
)
$scanRoots = @("docs", "README.md", "SECURITY.md")
foreach ($root in $scanRoots) {
    $path = Join-Path $repoRoot $root
    if (-not (Test-Path $path)) { continue }
    $files = @()
    if ((Get-Item $path).PSIsContainer) {
        $files = Get-ChildItem $path -Recurse -File -Include *.md,*.txt,*.csv -ErrorAction SilentlyContinue
    } else {
        $files = @(Get-Item $path)
    }
    foreach ($file in $files) {
        $text = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
        foreach ($pattern in $claimPatterns) {
            if ($text -match $pattern) {
                $findings += [pscustomobject]@{
                    Severity = "REVIEW"
                    Category = "release_claim_review"
                    Path = $file.FullName.Replace($repoRoot + [System.IO.Path]::DirectorySeparatorChar, "")
                    Detail = "Potential unsupported release/completion claim pattern: $pattern"
                }
            }
        }
    }
}

$scanRows | Export-Csv -Path (Join-Path $outDir "10_scan_inventory.csv") -NoTypeInformation -Encoding UTF8
$findings | Export-Csv -Path (Join-Path $outDir "20_findings.csv") -NoTypeInformation -Encoding UTF8
$artifactRows | Export-Csv -Path (Join-Path $outDir "30_required_artifacts.csv") -NoTypeInformation -Encoding UTF8

$blockerCount = @($findings | Where-Object { $_.Severity -eq "BLOCKER" }).Count
$pass = ($blockerCount -eq 0)
$summary = @(
    "# CROWN Security and Compliance Scan Gate",
    "",
    "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "- Branch: $((git branch --show-current).Trim())",
    "- Head: $((git rev-parse HEAD).Trim())",
    "- Required workflows: $($requiredWorkflows.Count)",
    "- Required artifacts: $($requiredArtifacts.Count)",
    "- Findings: $($findings.Count)",
    "- Blockers: $blockerCount",
    "",
    $(if ($pass) { "PASS" } else { "REVIEW REQUIRED" }),
    "",
    "This gate verifies the presence of safe, non-destructive security/compliance scanning controls and required governance artifacts."
)
Write-Utf8 -Path (Join-Path $outDir "00_SUMMARY.md") -Lines $summary

$status = [ordered]@{
    generated_at = (Get-Date).ToString("s")
    branch = (git branch --show-current).Trim()
    head = (git rev-parse HEAD).Trim()
    pass = $pass
    required_workflow_count = $requiredWorkflows.Count
    required_artifact_count = $requiredArtifacts.Count
    finding_count = $findings.Count
    blocker_count = $blockerCount
    scan_inventory = $scanRows
    required_artifacts = $artifactRows
    findings = $findings
}
Write-JsonFile -Path (Join-Path $outDir "99_STATUS.json") -Object $status
Copy-Item -Path (Join-Path $outDir "*") -Destination $latestDir -Recurse -Force

Write-Host "DONE"
Write-Host "SUMMARY: $(Join-Path $outDir '00_SUMMARY.md')"
Write-Host "STATUS:  $(Join-Path $outDir '99_STATUS.json')"
if (-not $pass) { exit 1 }
